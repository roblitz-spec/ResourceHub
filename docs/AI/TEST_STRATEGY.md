# ResourceHub — Test Strategy

## Test Pyramid

```
         E2E (Preview==Rename, Undo Cycle)
        /──────────────────────────────────\
       /     Integration (Rule Combos)       \
      /──────────────────────────────────────\
     /         Unit (Single Rule, Handler)     \
    /──────────────────────────────────────────\
```

## Test Layers

| Layer | What | Blocking? |
|---|---|---|
| **Single Rule** | Each RuleStep type with default params | ✅ Blocker |
| **Two-Rule Combo** | 7 verified combinations | ✅ Blocker |
| **Three-Rule Combo** | 3 verified combinations | ✅ Blocker |
| **Preview==Rename** | preview_name → target_name → file on disk | ✅ Blocker |
| **Undo Cycle** | Rename→Undo, Rename→Undo→Rename→Undo | ✅ Blocker |
| **Boundary** | Unicode, emoji, long names, empty dirs, conflicts | ✅ Blocker |
| **Regression** | Full pytest suite (152 tests) | ✅ Blocker |

## Why This Strategy

- Single Rule tests catch handler bugs in isolation
- Combo tests verify pipeline ordering (Step A→B ≠ B→A)
- Preview==Rename tests ensure no drift between preview and actual rename
- Boundary tests catch platform-specific issues (Windows reserved names, Unicode)

## Release Gate

All layers must pass. Any failure = release blocked.
