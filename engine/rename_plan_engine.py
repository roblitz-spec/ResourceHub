from __future__ import annotations

import os
from pathlib import Path

from models.file_item import FileItem
from models.rename_plan import (
    RenameAction,
    RenamePlan,
    RenamePlanStatus,
)
from models.rename_policy import RenamePolicy

_FORBIDDEN_CHARS = set(r'<>:"/\|?*')

_WIN_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


class RenamePlanEngine:
    """重命名计划引擎 —— 生成 RenamePlan 并完成全部决策。"""

    @staticmethod
    def generate(
        items: list[FileItem],
        policy: RenamePolicy = RenamePolicy.FAIL,
    ) -> list[RenamePlan]:
        plans: list[RenamePlan] = []

        # 第一步：生成基础计划 + 合法性检测
        for item in items:
            target_name = (item.preview_name or item.base_name) + item.extension
            target = item.full_path.parent / target_name
            needs_rename = target_name != item.original_name

            # 合法性
            base = item.preview_name or ""
            msg = _check_legality(base)
            if msg:
                plans.append(RenamePlan(
                    source=item.full_path,
                    source_name=item.original_name,
                    target_name=target_name,
                    target=target,
                    needs_rename=needs_rename,
                    status=RenamePlanStatus.INVALID,
                    action=RenameAction.FAIL,
                    message=msg,
                ))
                continue

            if not needs_rename:
                plans.append(RenamePlan(
                    source=item.full_path,
                    source_name=item.original_name,
                    target_name=target_name,
                    target=target,
                    status=RenamePlanStatus.NO_CHANGE,
                    action=RenameAction.SKIP,
                    message="无需重命名",
                ))
                continue

            plans.append(RenamePlan(
                source=item.full_path,
                source_name=item.original_name,
                target_name=target_name,
                target=target,
                needs_rename=True,
                status=RenamePlanStatus.READY,
                action=RenameAction.RENAME,
            ))

        # 第二步：检测目标冲突
        _detect_conflicts(plans)

        # 第三步：目标已存在 → 按 policy 决定 action
        for plan in plans:
            if plan.status != RenamePlanStatus.READY:
                continue
            # 目标与源文件名完全相同 → 无需操作（非冲突）
            # 使用字符串比较，避免 Windows Path 大小写不敏感导致误判
            if plan.target_name == plan.source_name:
                plan.status = RenamePlanStatus.NO_CHANGE
                plan.action = RenameAction.SKIP
                plan.message = "无需重命名"
                continue
            if not plan.target.exists():
                continue
            # 目标存在但可能与源是同一文件（Windows 大小写重命名）
            # Path.samefile() 通过 st_dev + st_ino 判断是否为同一文件
            try:
                if plan.target.samefile(plan.source):
                    continue  # 同一文件，大小写重命名 → 保持 READY
            except OSError:
                pass  # samefile 不可用 → 按常规冲突处理
            if policy == RenamePolicy.FAIL:
                plan.status = RenamePlanStatus.CONFLICT
                plan.action = RenameAction.FAIL
                plan.message = "目标文件已存在"
            elif policy == RenamePolicy.SKIP:
                plan.status = RenamePlanStatus.SKIPPED
                plan.action = RenameAction.SKIP
                plan.message = "目标已存在，已跳过"
            elif policy == RenamePolicy.OVERWRITE:
                plan.action = RenameAction.OVERWRITE
                plan.message = "将覆盖已存在的目标文件"

        return plans


def _check_legality(name: str) -> str:
    if not name or not name.strip():
        return "名称不能为空"
    if any(c in name for c in _FORBIDDEN_CHARS):
        return "包含非法字符"
    if name.rstrip() != name:
        return "名称不能以空格结尾"
    if name.rstrip(".") != name:
        return "名称不能以 . 结尾"
    if len(name) > 255:
        return "名称过长"
    if name.upper() in _WIN_RESERVED:
        return f"「{name}」是系统保留名称"
    return ""


def _detect_conflicts(plans: list[RenamePlan]) -> None:
    # 精确重名
    seen: dict[str, int] = {}
    for i, plan in enumerate(plans):
        if plan.status != RenamePlanStatus.READY:
            continue
        key = plan.target_name
        if key in seen:
            plan.status = RenamePlanStatus.CONFLICT
            plan.action = RenameAction.FAIL
            plan.message = "目标名称重复"
            plans[seen[key]].status = RenamePlanStatus.CONFLICT
            plans[seen[key]].action = RenameAction.FAIL
            plans[seen[key]].message = "目标名称重复"
        else:
            seen[key] = i

    # Windows 大小写冲突
    if os.name == "nt":
        seen_ci: dict[str, int] = {}
        for i, plan in enumerate(plans):
            if plan.status != RenamePlanStatus.READY:
                continue
            key = plan.target_name.lower()
            if key in seen_ci and plans[seen_ci[key]].target_name != plan.target_name:
                plan.status = RenamePlanStatus.CONFLICT
                plan.action = RenameAction.FAIL
                plan.message = "目标名称冲突（大小写）"
                plans[seen_ci[key]].status = RenamePlanStatus.CONFLICT
                plans[seen_ci[key]].action = RenameAction.FAIL
                plans[seen_ci[key]].message = "目标名称冲突（大小写）"
            else:
                seen_ci[key] = i
