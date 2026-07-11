from __future__ import annotations

from models.enums import ItemType
from models.file_item import FileItem
from models.validation_result import ValidationResult

_FORBIDDEN_CHARS = set('< > : " / \\ | ? *'.split())


class Validator:
    """重命名前校验 —— 只检查 preview_name 的合法性。"""

    @staticmethod
    def validate(items: list[FileItem]) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        seen: dict[str, int] = {}  # preview_name → 首次出现索引

        for item in items:
            if item.item_type == ItemType.DIRECTORY:
                results.append(ValidationResult(file_path=item.full_path, is_valid=True))
                continue

            name = item.preview_name
            if name is None or name.strip() == "":
                results.append(ValidationResult(
                    file_path=item.full_path, is_valid=False, message="名称不能为空",
                ))
                continue

            if any(c in name for c in _FORBIDDEN_CHARS):
                results.append(ValidationResult(
                    file_path=item.full_path, is_valid=False, message="包含非法字符",
                ))
                continue

            if len(name) > 255:
                results.append(ValidationResult(
                    file_path=item.full_path, is_valid=False, message="名称过长",
                ))
                continue

            if name in seen:
                results.append(ValidationResult(
                    file_path=item.full_path, is_valid=False, message="目标名称重复",
                ))
                results[seen[name]].is_valid = False
                results[seen[name]].message = "目标名称重复"
            else:
                seen[name] = len(results)
                results.append(ValidationResult(file_path=item.full_path, is_valid=True))

        return results
