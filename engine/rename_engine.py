from __future__ import annotations

from typing import TYPE_CHECKING

from models.rename_plan import (
    RenameAction,
    RenamePlan,
    RenamePlanStatus,
)
from models.rename_result import RenameResult

if TYPE_CHECKING:
    from engine.operation_logger import OperationLogger


class RenameEngine:
    """重命名执行引擎 —— 仅基于 RenamePlan.action 执行，不重复决策。"""

    @staticmethod
    def rename(
        plans: list[RenamePlan],
        logger: OperationLogger | None = None,
    ) -> list[RenameResult]:
        results: list[RenameResult] = []

        def _emit(r: RenameResult) -> None:
            results.append(r)
            if logger is not None:
                logger.record(r)

        for plan in plans:
            if plan.action == RenameAction.SKIP:
                _emit(RenameResult(
                    source=plan.source, target=plan.target,
                    success=True, message=plan.message or "已跳过",
                ))
                continue

            if plan.action == RenameAction.FAIL:
                _emit(RenameResult(
                    source=plan.source, target=plan.target,
                    success=False, message=plan.message,
                ))
                continue

            # RENAME / OVERWRITE
            try:
                if plan.action == RenameAction.OVERWRITE and plan.target.exists():
                    plan.target.unlink()

                plan.source.rename(plan.target)
                plan.status = (
                    RenamePlanStatus.OVERWRITTEN
                    if plan.action == RenameAction.OVERWRITE
                    else RenamePlanStatus.SUCCESS
                )
                _emit(RenameResult(
                    source=plan.source, target=plan.target, success=True,
                ))
            except PermissionError:
                plan.status = RenamePlanStatus.FAILED
                plan.message = "权限不足"
                _emit(RenameResult(
                    source=plan.source, target=plan.target,
                    success=False, message="权限不足",
                ))
            except FileExistsError:
                plan.status = RenamePlanStatus.FAILED
                plan.message = "目标已存在"
                _emit(RenameResult(
                    source=plan.source, target=plan.target,
                    success=False, message="目标已存在",
                ))
            except OSError as exc:
                plan.status = RenamePlanStatus.FAILED
                plan.message = f"系统错误：{exc}"
                _emit(RenameResult(
                    source=plan.source, target=plan.target,
                    success=False, message=f"系统错误：{exc}",
                ))
            except Exception as exc:
                plan.status = RenamePlanStatus.FAILED
                plan.message = f"未知错误：{exc}"
                _emit(RenameResult(
                    source=plan.source, target=plan.target,
                    success=False, message=f"未知错误：{exc}",
                ))

        return results
