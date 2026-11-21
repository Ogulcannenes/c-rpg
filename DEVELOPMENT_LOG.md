# C++ Adventure — Development Log

Modernization work on branch `modernization`. Each phase lists what changed, why,
which tests ran, and what is still open. Test results are copied from real runs only.
(`DEVAM.md` holds the older Turkish progress notes and is kept unchanged.)

## Rollback

- Full backup (source, `.git`, every SQLite database, installed-app data; SHA-256 manifest):
  `C:\Users\user\CppAdventure-backups\phase0-2026-11-21\` — verify with `SHA256SUMS.txt`.
- Git: commit `02501de` is the exact pre-modernization state. `main` is untouched.
- Restore a database: stop the app, copy the `.db` file from the backup over the live one
  (`%LOCALAPPDATA%\CppAdventure\data\adventure.db` for the installed app).

## Phase 0 — Repository protection (2026-11-21)

- Git refused to run: `.git` is owned by the `CodexSandboxOffline` Windows account
  ("dubious ownership"). No config was changed; commands use
  `git -c safe.directory="<exact repo path>"`. Permanent fix (user's choice):
  `git config --global --add safe.directory "C:/Users/user/OneDrive/Desktop/adel1/C++ Adventure"`.
- Backup created and verified: 305 files, 5 databases (`PRAGMA integrity_check` = ok), 0 hash mismatches.
  No API keys exist on disk (`%LOCALAPPDATA%\CppAdventure\secrets` absent), so none were copied.
- `02501de` — checkpoint of all previously untracked/modified work (server.py imports
  `sandbox.py`, `lesson_extra.py`, `lesson_scenes.py`, `task_clarity.py`, `workshop_projects.py`,
  which were untracked, so `HEAD` could not run before).
- `95359ce` — `.gitattributes` (LF for sources, CRLF for `.bat`/`.ps1`, binaries marked) and
  extended `.gitignore` (SQLite WAL/SHM, dev-mode runtime folders, local Claude files).
  Renormalization verified as line-ending-only with `git diff --cached --ignore-cr-at-eol`.

## Phase 1 — Test baseline and critical bug fixes (2026-11-21)

**Baseline (before any change):** `python -m unittest discover -s tests` → 167 tests, OK
(two clean runs). One earlier run exited 1 with an unrecorded failure; a flaky test may exist —
tracked below. Command used: `C:\msys64\ucrt64\bin\python.exe -B -m unittest discover -s tests`.

Every bug below was first reproduced by a failing test in `tests/test_phase1_regressions.py`
(13 tests, all red before the fix).

| # | Bug (verified) | Root cause | Fix |
|---|---|---|---|
| 1 | Unknown POST routes and `/api/vscode`, `/api/vscode/read` returned 500 | `/api/submit` success `return` indented at route level (old `server.py:1787`), so every later route hit `UnboundLocalError` | Indent the `return` into the submit branch |
| 2 | `GET /api/export?profile_id=bad` dropped the connection | `do_GET` had no error handling | `do_GET` wraps `_route_get` with the `do_POST` policy (400/500 JSON) |
| 3 | Negative `Content-Length` hung a handler thread; list bodies caused 500 | `read_json` trusted the header and the JSON type | Digits-only length check; body must be a JSON object (400 otherwise) |
| 4 | Restoring any realistic save failed ("İstek çok büyük.") | Every POST capped at 30 KB | `POST_BODY_LIMITS`: `/api/import` 8 MB, plugin install unchanged, others 30 KB |
| 5 | Import overwrote PIN-protected profiles without the PIN | No PIN check on `/api/import` | PIN verified before any write; UI uses the existing `CatPinDialog` |
| 6 | Profile update saved name/avatar then returned 400 for a bad PIN | Early `return` inside `with db()` commits | Validate the new PIN before the first write |
| 7 | Daily bonus credited but reported as 0 | Response used `daily_bonus if inserted else 0` | Report the bonus actually credited |
| 8 | Arena/project/shop/secret-quest rewards and interview answers could double-apply under concurrent requests | Read-then-write without a write lock (SQLite defers locking until the first write) | `db(immediate=True)` → `BEGIN IMMEDIATE` on those paths; interview answer re-checked under the lock |
| 9 | XP/level admin panel enabled in shipped builds | Default `CPP_ADVENTURE_ADMIN` = on | Opt-in: only `CPP_ADVENTURE_ADMIN=1` enables it (`admin_enabled_from_env`) |
| 10 | Claude tutor always failed (HTTP 400) and silently fell back | `temperature: 0.3` is rejected by `claude-haiku-5-5`; thinking could consume the 450-token budget | Removed sampling params; `thinking: disabled` + `output_config.effort: low`; `refusal`/empty replies return an error → offline hint |
| 11 | Restored saves lost a Claude/Groq tutor selection | Import allow-list missed `claude`, `groq` | Added both |

Also: a non-object `save` in `/api/import` now returns 400 instead of 500; `state()` exposes
`pin_protected` (boolean only) so the UI knows when to ask for a PIN.

**Test changes:** `tests/test_admin_panel.py` now enables the panel explicitly in `setUpClass`
(and restores it), because the panel is opt-in.

**Files changed:** `server.py`, `web/app.js`, `web/admin-panel.js` (comment), `README.md`
(admin section), `tests/test_admin_panel.py`, `tests/test_phase1_regressions.py` (new).

**Results:** targeted run (`test_phase1_regressions`, `test_admin_panel`, `test_claude_ai`): 22 tests, OK.
Full suite after the fixes, three consecutive runs: 180 tests OK / 180 OK / 180 OK (~228 s each).
No flaky failure reappeared.

**Open after Phase 1:**
- Possible flaky test from the first baseline run (failure not captured).
- PIN is still checked only on select/update/delete/import; all other endpoints trust the
  client's `profile_id`. Replaced in Phase 2 by a per-launch API token plus per-profile sessions.
