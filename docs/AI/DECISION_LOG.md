# ResourceHub — Decision Log (ADR)

## ADR-001: Prefix / Suffix Design

- **Milestone**: M15
- **Status**: Accepted
- **Decision**: Keep `add_prefix` and `add_suffix` as independent RuleStep types.
- **Reason**: Backward compatibility — existing `rules.json` with `add_prefix` must load without migration. Avoids modifying frozen Rule structure post Feature Freeze.
- **Alternatives Considered**: Unify into single Rule with `position` parameter. Rejected due to migration risk.

## ADR-002: Undo Design

- **Milestone**: M15
- **Status**: Accepted
- **Decision**: Maintain single-level Undo only.
- **Reason**: Satisfies current requirements. Multi-level Undo adds session management complexity (stack, redo, history UI) without proven user demand.
- **Alternatives Considered**: Multi-level Undo stack. Deferred to future Milestone.

## ADR-003: Feature Freeze Policy

- **Milestone**: M15 RC
- **Status**: Accepted
- **Decision**: Freeze core pipeline modules (RuleEngine, RenameEngine, PreviewEngine, RenamePlanEngine, FileTableModel) after M15 RC.
- **Reason**: Reduce regression risk. Prioritize release stability over continued iteration.
- **Alternatives Considered**: Allow continuous modification. Rejected — risk of destabilizing 152-test baseline.

## ADR-004: RuleEngine Pure Function Contract

- **Milestone**: M12 (Number Rule design)
- **Status**: Accepted
- **Decision**: RuleEngine handlers must be pure functions. State (like numbering index) is passed via `context` dict from PreviewEngine.
- **Reason**: Testability, predictability, thread safety. Avoids global counters that break between Preview and Rename cycles.
- **Alternatives Considered**: Module-level counters with `reset()`. Rejected — violates stateless principle.

## ADR-005: Context Contract

- **Milestone**: M14 (Date Rule)
- **Status**: Accepted
- **Decision**: Context fields (`index`, `timestamps.modified`, `timestamps.created`) are frozen. New fields can be added but existing ones cannot be renamed or re-typed.
- **Reason**: Rule handlers depend on these fields. Renaming breaks existing Rule configurations.
