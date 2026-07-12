# ResourceHub — Review Guidelines

> For the Reviewer (ChatGPT / User) when evaluating AI Developer output.

## Review Checklist

### Architecture
- [ ] Does the change respect module boundaries?
- [ ] Does it introduce unnecessary coupling?
- [ ] Are new handlers registered without modifying existing ones?

### Compatibility
- [ ] Will existing `rules.json` files still load?
- [ ] Are parameter names unchanged?
- [ ] Is the context contract preserved?
- [ ] Does it affect frozen modules?

### Testing
- [ ] Are new tests added for the change?
- [ ] Do all 152 existing tests still pass?
- [ ] Are boundary cases covered?
- [ ] Is the regression matrix (single/2-combo/3-combo/E2E/undo) verified?

### UX
- [ ] Does it match existing interaction patterns?
- [ ] Are labels in Chinese (zh_CN default)?
- [ ] Is button placement consistent?

### Release
- [ ] Does it affect the current Milestone timeline?
- [ ] Is it a Blocker, Minor, or Deferred item?

## Decision Options

| Verdict | Meaning |
|---|---|
| **Approve** | Proceed to implementation |
| **Reject** | Do not implement; provide reason |
| **Request Assessment** | Need more design analysis before deciding |
| **Defer** | Move to future Milestone |
