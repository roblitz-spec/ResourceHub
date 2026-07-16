# ResourceHub — AI Changelog

> For architecture decisions behind these changes, see [`DECISION_LOG.md`](DECISION_LOG.md).

## M11.1
- **Multiple Selection Support**: ExtendedSelection in QTableView, batch rename (file + directory + mixed)
- **Scanner API**: `scan(paths: list[Path])` — multi-path input with deduplication
- **Tests**: 176 PASS (+12 multi-select scenarios)

## M10 Phase 3A
- **Rule Dependency Analysis**: `RuleAnalysis` with `uses_index` / `uses_metadata`, PreviewEngine conditional context
- **MetadataProvider**: Lazy `os.stat()` caching
- **Documentation**: Architecture sync (timestamps → metadata, Directory unified pipeline)
- **Tests**: 164 PASS (+11 RuleAnalysis tests)

## M15 RC
- **AddSuffix Rule**: Independent `add_suffix` handler, no impact on `add_prefix`
- **Undo Validation**: Target missing + double undo edge cases covered
- **RC Regression Matrix**: 32 scenarios (single/2-combo/3-combo/E2E/undo/boundary)
- **AI Memory System**: `docs/AI/` created, 8 initial documents
- **QThread Lifecycle Fix**: RenameWorker moved to instance variable, `closeEvent` timeout
- **Tests**: 152 PASS

## M15
- **AddSuffix Rule**: New `add_suffix` handler + UI entry
- **UX Polish**: Button labels, step numbering, tooltips
- **Tests**: 150 PASS

## M14.2
- **Rule Manager UX**: Button labels ("新建规则"/"删除规则"), step numbering (①②③), tooltips

## M14.1
- **QThread Stabilization**: RenameWorker lifecycle fix

## M14
- **Date Rule**: `source`/`format`/`position`/`separator`, metadata from PreviewEngine context (MetadataProvider)
- **Number Rule Fix**: Folders no longer consume numbering index
- **Tests**: 144 PASS

## M13
- **Insert Rule**: `text` + `at_index`, clamp to bounds
- **Tests**: 131 PASS

## M12
- **Number Rule**: `start`/`step`/`padding`/`position`, pure-function via context
- **Tests**: 122 PASS

## M8-M11
- **Core Pipeline**: Scanner, PreviewEngine, RenamePlanEngine, RenameEngine
- **RuleEngine v1**: replace, remove_text, add_prefix, regex_replace, case, trim
- **UndoEngine**: Single-level undo via OperationLogger
- **Settings**: QSettings-based RenamePolicy
- **i18n**: zh_CN / en_US
- **Packaging**: PyInstaller build
