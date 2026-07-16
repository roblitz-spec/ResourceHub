# ResourceHub — Development Constitution

## Core Principles

1. **Stability First** — Release quality matters more than feature count
2. **Compatibility First** — Existing `rules.json` must load without error
3. **Extension over Modification** — New features add handlers, don't change existing ones
4. **Feature Freeze is Hard** — Once a Milestone closes, only Bug Fixes are allowed
5. **Rule Single Responsibility** — Each RuleStep type does one transformation
6. **Tests Required** — Every behavioral change must have a test
7. **Assessment Required** — Architecture, Pipeline, or Serialization changes need prior design review
8. **Manual QA Required** — Automated tests are not sufficient for release
9. **AI Stays in Scope** — Don't expand the task beyond the user's explicit request
10. **Documents are Source of Truth** — `docs/AI/` is the long-term memory for AI collaborators
11. **Network Filesystem by Default** — All directory scanning code must assume it may run on SMB/NAS/WebDAV/FUSE. Local SSD testing alone is insufficient.

## Performance Design Principles

1. **Hot Path Awareness** — Directory scanning is a hot path. Every filesystem API in a loop body is a candidate for network round trips.

2. **Avoid Canonicalization** — `Path.resolve()` / `realpath()` traverse every path component with `lstat()`. On network filesystems, this is catastrophic. Use paths as-is unless canonical form is a business requirement.

3. **Single Query, Multiple Uses** — Avoid sequential `exists()` → `is_dir()` → `stat()` on the same path. Each call is an independent stat. Use one `stat()` and check `st_mode`.

4. **Reuse DirEntry Data** — `os.scandir()` returns `DirEntry` objects with cached attributes. `entry.is_dir()` uses `d_type` (no stat). `entry.name` / `entry.path` are pure memory reads.

5. **Preserve API Contract** — Performance optimizations must not change: API signatures, return values, sort order, or business logic. Speed gains must be transparent to consumers.

6. **Regression Protection** — Any performance fix that removes or changes filesystem API usage must include a CI-level regression test that asserts the problematic API is NOT called.

## When Rules Can Be Broken

- Major version bump (M→N where N ≥ next major)
- Explicit user directive to refactor a frozen module
- Security vulnerability requiring immediate fix
