# Releases

Version history for this repository (6 releases).

## v0.2.3: cass-memory v0.2.3
**Published:** 2026-01-07

**Full Changelog**: https://github.com/Dicklesworthstone/cass_memory_system/compare/v0.2.2...v0.2.3

[View on GitHub](https://github.com/Dicklesworthstone/cass_memory_system/releases/tag/v0.2.3)

---

## v0.2.2: cass-memory v0.2.2
**Published:** 2026-01-05

## Installer Improvements & Bug Fixes

This patch release focuses on improving the installation experience with more robust version detection and proper concurrent install protection.

### 🐛 Bug Fixes

#### Redirect-Based Version Resolution
The installer now uses GitHub's redirect behavior instead of the API to detect the latest version:
- **No rate limiting**: API calls are limited to 60/hour for unauthenticated users; redirects have no limit
- **No JSON parsing**: Eliminates cross-platform issues with grep/sed differences between GNU and BSD
- **Simpler failures**: Only fails if GitHub is completely down

The mechanism works by following `https://github.com/owner/repo/releases/latest` → `https://github.com/owner/repo/releases/tag/v0.2.2` and extracting the version from the final URL.

#### Fixed Concurrent Install Protection  
The lock file path was incorrectly using PID expansion (`$`), causing each installer process to create its own unique lock file. This defeated the purpose of preventing concurrent installations. The fix uses a static path `/tmp/cass-memory-install.lock`.

### 📝 Documentation

- Moved installation comment outside the code block in README for better formatting

### ⬆️ Upgrade

```bash
# Quick upgrade (recommended)
curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/cass_memory_system/main/install.sh | bash -s -- --easy-mode --verify

# Specific version
install.sh --version v0.2.2 --verify

# From source
install.sh --from-source --verify
```

### 📦 Checksums

SHA256 checksums are available as `.sha256` files alongside each binary. Verify with:
```bash
sha256sum -c cass-memory-linux-x64.sha256
```

---

**Full Changelog**: https://github.com/Dicklesworthstone/cass_memory_system/compare/v0.2.1...v0.2.2

**Full Changelog**: https://github.com/Dicklesworthstone/cass_memory_system/compare/v0.2.1...v0.2.2

[View on GitHub](https://github.com/Dicklesworthstone/cass_memory_system/releases/tag/v0.2.2)

---

## v0.2.1: cass-memory v0.2.1
**Published:** 2026-01-03

## What's Changed

### Bug Fixes

- **fix(cass):** Resolve `timeline.groups.flatMap` error - fixes session discovery in `cm reflect` (#7, #9)
  - cass timeline uses `--since Nd` format instead of `--days N`
  - Properly handle cass timeline returning groups as object instead of array
- **fix(cass):** Improve Codex CLI session parsing (#6)
  - Handle nested `payload.content` format
  - Fallback to direct JSONL parsing when cass returns >50% UNKNOWN entries
- **fix(cass):** Add size limit for fallback session parsing to prevent OOM
- **fix(privacy):** Add file locking for concurrent config access
- **fix(robustness):** Add signal handlers and model loading locks
- **fix(undo):** Add missing imports for utils functions

### Performance

- **perf(curate):** Optimize duplicate detection with pre-computed token sets
- **perf(audit,trauma):** Optimize batch operations

### Features

- **feat(serve):** Return richer delta info in MCP dry-run responses
- **feat(onboard):** `mark-done` now also updates reflection processed log

### Testing

- Improved test coverage across multiple modules:
  - `reflect`: 61% → 82%
  - `serve`: 52% → 68%
  - `context`: 52% → 86%
  - `playbook`: 63% → 81%
  - `top`: 60% → 100%
- Added 31 integration tests for onboard command
- Added comprehensive E2E tests for CLI commands

### Other

- Removed dead code from curate.ts and semantic.ts
- Various test improvements and cleanups

## Upgrade Notes

This release fixes critical issues with `cm reflect` session discovery. Users on v0.2.0 experiencing "timeline.groups.flatMap" errors should upgrade.

**Full Changelog**: https://github.com/Dicklesworthstone/cass_memory_system/compare/v0.2.0...v0.2.1

[View on GitHub](https://github.com/Dicklesworthstone/cass_memory_system/releases/tag/v0.2.1)

---

## v0.2.0: cass-memory v0.2.0
**Published:** 2025-12-16

**Full Changelog**: https://github.com/Dicklesworthstone/cass_memory_system/compare/v0.1.1...v0.2.0

[View on GitHub](https://github.com/Dicklesworthstone/cass_memory_system/releases/tag/v0.2.0)

---

## v0.1.1: cass-memory v0.1.1
**Published:** 2025-12-15

**Full Changelog**: https://github.com/Dicklesworthstone/cass_memory_system/compare/v0.1.0...v0.1.1

[View on GitHub](https://github.com/Dicklesworthstone/cass_memory_system/releases/tag/v0.1.1)

---

## v0.1.0: cass-memory v0.1.0
**Published:** 2025-12-15

**Full Changelog**: https://github.com/Dicklesworthstone/cass_memory_system/commits/v0.1.0

[View on GitHub](https://github.com/Dicklesworthstone/cass_memory_system/releases/tag/v0.1.0)

---

