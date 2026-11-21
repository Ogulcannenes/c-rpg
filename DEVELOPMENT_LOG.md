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

## Phase 2 — Security hardening (2026-11-21)

### Learner-program sandbox (Windows, verified on this machine)

New `sandbox_windows.py`; `sandbox.py` is the platform-neutral facade (same `run_limited` API).

- Programs are created **suspended**; a Job Object is attached **before** the first instruction:
  1 process (no children), 512 MB memory, CPU-time cap, UI restrictions (clipboard, desktop,
  ExitWindows…), no crash dialogs, kill-on-close. If the job cannot be attached the process is
  terminated without ever running (fail closed → `phase: "sandbox_error"`).
- When available (it is here), programs run in an **AppContainer with no capabilities**: no
  network (loopback included, so no access to the local API), no access to user files, low
  integrity. Fallback is the Job Object alone, reported as `sandbox: "job"` and in `/api/health`.
- Minimal environment block: API keys and user variables are **not** inherited (they were before).
- Each run gets a fresh, empty working folder (deleted afterwards); workspace data files
  (`.txt/.csv/.json/...`, ≤2 MB) are copied in. Learner binaries are linked `-static`.
- Compiler, CMake and clang run inside a Job Object (2 GB/process, 3 GB/job, ≤32 processes);
  a timeout kills the whole tree. At most `MAX_PARALLEL_BUILDS` (2) compile/run jobs at once;
  others wait up to 60 s, then get `phase: "busy"`.
- Compile-time file access: `#include`/`__has_include` with absolute or `..` paths, computed
  includes, `#embed`, `#pragma GCC dependency` are rejected (line splices and `%:` digraphs
  handled). Inline asm is checked on the **expanded `-S` output** before assembling, so
  `.incbin`/`.include` hidden behind string concatenation or macros cannot read files — not
  even through assembler error messages. Builds are therefore C++→asm, check, asm→exe.
- Identical sources are compiled once (LRU cache of 24 builds) — several test inputs reuse
  one binary.

Measured with real programs (smoke test + `tests/test_sandbox_windows.py`):

| Attempt | AppContainer (default) | Job only (fallback) |
|---|---|---|
| read a file in the user profile | blocked | readable |
| write outside the run folder | blocked | possible |
| files in its own run folder (c14 tasks) | works | works |
| `system("cmd ...")` | blocked | blocked |
| read API keys from environment | none | none |
| connect to a loopback port | no connection | connects |
| infinite loop / crash / output flood / memory bomb | killed at 3 s / ~0.06 s, no dialog / 64 KB cap / `bad_alloc` at the cap | same |

**Known limitations:** the compiler itself runs as the user (only the policy checks above stop
compile-time reads); POSIX mode is for development only (rlimits + process group, no file or
network isolation); the AppContainer profile `CppAdventure.Sandbox` persists in the user
profile and should be removed by the uninstaller (Phase 11).

### Local API

- **Per-launch session:** `create_app_server()` makes a random token; the window opens
  `/__session?code=<one-time code>` which sets an `HttpOnly; SameSite=Strict` cookie
  (`cppadv_session_<port>`). Every `/api/*` request without it gets 401. Static files stay
  public; the token never appears in page content. `desktop.py` and `server.main()` use it.
  In-process test servers (`server.Handler` directly) have no auth by design.
- **Port race removed:** the server binds port 0 itself instead of probe-close-rebind.
- **PIN enforced everywhere:** a PIN-protected profile is locked until `/api/select` succeeds;
  selecting another profile locks the previous one; every endpoint with a `profile_id` returns
  403 `pin_required` while locked (exempt: select, create, update/delete/import, which verify
  the PIN themselves). The UI already falls back to the profile picker + cat PIN dialog.
- **Headers on every response:** CSP (`default-src 'self'`, no objects/frames/foreign
  connections; `script-src` still allows inline handlers until Phase 5 removes them),
  `nosniff`, `no-referrer`, `X-Frame-Options: DENY`, COOP.
- **XSS:** profile name was written unescaped into an `aria-label` (`cat-companion-ui.js`);
  now escaped at the sink. Names with control characters, `<`, `>` or backticks are rejected.
- **API keys:** stored with Windows DPAPI (`secret_store.py`, `<name>.dpapi`); legacy plaintext
  files are migrated on first read and the plaintext copy removed.
- **Import validation:** XP, streak, per-task/lab XP, rewards, scores and dates are clamped to
  real ranges; interview answers are rebuilt from known fields (no truncated JSON).

### Found during the browser check (pre-existing bug)

The language refresh in `app.js` rewrites every `[data-i]` element; onboarding, lab theater,
advanced C++ and project steps used `data-i` as a numeric index, so their content (e.g. the
character cards) was replaced by `0…6`. Index attributes renamed to `data-idx`; regression test
added. Verified in Chrome: cards keep names and images after a language refresh.

Browser check (throwaway DB, real `create_app_server`): session cookie works and is not
readable from JavaScript; Monaco loads under the CSP with no violations; `/api/run` through the
UI session ran in the AppContainer (`sandbox: "appcontainer"`). Only console error:
pre-existing missing `favicon.ico`.

**Files:** `sandbox.py` (rewritten), `sandbox_windows.py`, `secret_store.py` (new), `server.py`,
`desktop.py`, `project_workshop.py`, `advanced_cpp.py`, `concept_checker.py`,
`web/cat-companion-ui.js`, `web/onboarding.js`, `web/lab-theater.js`, `web/advanced-cpp-ui.js`,
`web/app.js`; tests `test_sandbox_windows.py`, `test_phase2_security.py` (new),
`test_phase1_regressions.py`, `test_claude_ai.py` (expects DPAPI instead of plaintext).

**Results (Phase 2):** full suite three consecutive runs: 212 OK / 213 OK / 213 OK (~206–223 s; the
213th test is the `data-idx` regression added during run 1). Suite time dropped from ~228 s
despite more tests, thanks to the compile cache.

## Phase 3 — Database migrations and data integrity (2026-11-21)

- New `db_migrations.py`: schema version in `PRAGMA user_version`; each migration plus its
  version bump runs in one `BEGIN IMMEDIATE` transaction, so an interrupted upgrade rolls back
  and is retried on the next start. Migrations shipped:
  1. baseline schema (the 22 existing tables; safe on old databases: `IF NOT EXISTS` + column adds
     + old single-item appearance → slot model),
  2. indexes on `learning_events(profile_id, task_id, correct)`, `learning_events(profile_id, created_at)`,
     `review_schedule(profile_id, due_at)`, `study_sessions(profile_id, day)`,
  3. one-time learning-event backfill — this used to run on **every** startup (O(completions × curriculum)).
- Before upgrading a database that already has profiles, a verified copy is written to
  `<data>/backups/adventure-before-schema-vN-from-vM-<timestamp>.db` (SQLite online backup +
  `integrity_check`). Backups are never deleted by the app.
- A database written by a **newer** app version is refused (startup stops) instead of being
  modified — protects data when someone runs an older build.
- `PRAGMA journal_mode=WAL` is set once by the migration runner (persistent) instead of on every
  connection.
- Save format **v2**: export now includes `ai_usage`; import accepts v1 and v2 (v1 simply has no
  `ai_usage`) and rejects unknown versions. `admin_bonus` (test-panel level XP) is intentionally
  neither exported nor imported.
- `POST /api/backup/database`: verified copy of the whole database (all profiles) in `<data>/backups`.

**Verified on real data:** a temporary copy of the installed app's database (from the Phase 0
backup: schema v0, 7 profiles, 106 completions) upgraded to v3 with identical row counts in every
table, `integrity_check = ok`, and the pre-upgrade backup created. The live database was not touched
(it will be upgraded, with its own automatic backup, the next time the app starts).

**Tests:** `tests/test_db_migrations.py` (8): fresh DB; pre-versioning DB with realistic progress
(profiles, Cyrillic names, completions, quiz history, owned + equipped item); idempotent second run
(no duplicate backfill, no second backup); interrupted migration (rollback, version unchanged,
retry succeeds); newer-version DB left byte-identical; read-only copy of the local dev database;
save v2 round trip incl. `ai_usage` and v1 compatibility; whole-database backup.

### Restoring a backup (manual)

1. Close C++ Adventure.
2. Copy the chosen file from `%LOCALAPPDATA%\CppAdventure\backups\` (or from
   `C:\Users\user\CppAdventure-backups\phase0-2026-11-21\localappdata-CppAdventure\data\`) to
   `%LOCALAPPDATA%\CppAdventure\data\adventure.db`, after moving the current file aside.
3. Delete `adventure.db-wal` / `adventure.db-shm` next to it only if they belong to the file you replaced.
4. Start the app; any needed migration runs automatically (with its own backup first).

**Results (Phase 3):** run 1: 221 OK; run 2: 1 failure — caused by my own mid-run Phase 4 edit
(route tables were written with single quotes and `test_lesson_scenes` greps `server.py` for
`"/api/lesson-scenes"`), not by Phase 3 code; run 3 (with the quote fix): 228 OK.

## Phase 4 — Backend architecture (2026-11-21)

Scope decision: `server.py` stays the composition root that owns configuration (`DB_PATH`,
`DATA_ROOT`, `SECRETS_DIR`, `COMPILER`), because 12 test modules patch those module globals; moving
them would silently point tests at the real database. AI provider extraction is done in Phase 9,
where that code is rewritten anyway.

- **Route tables:** the ~70-branch `if path == ...` chains in `do_GET`/`do_POST` were split
  mechanically (AST-based script, dry-run first) into one `Handler` method per endpoint
  (`_get_*`, `_post_*`) plus `GET_ROUTES` / `POST_ROUTES`. The dry run caught that a naive split
  would have deleted the session/PIN checks (they sat between the `/__session` branch and the API
  branches); the script refuses to transform when non-route statements are inside the chain.
  Dispatch order is unchanged: host/origin checks → `/__session` → session cookie → PIN lock →
  route. Unknown `/api/*` GETs now answer JSON 404 instead of the static-file HTML 404.
- **`content_index.py`:** O(1) `task()`, `chapter_of()`, `boss_of()` replace 10 linear
  `next(... CURRICULUM ...)` scans (some raised `StopIteration` for unknown ids). Invariants checked
  at import: unique ids, every chapter ends with its boss, prerequisites exist.
- A daily quest that points at removed content is moved to a valid task instead of making
  `/api/state` fail for that profile (Code Reviewer finding #2).
- Repeated `__import__("urllib.parse"...)`/`__import__("collections")` replaced by normal imports.
- **Strict CSP:** the only inline script (Monaco bootstrap) moved to `web/monaco-boot.js`, the only
  inline handler (`onclick="renderSettings()"`) replaced by a listener, so `script-src` is now
  `'self'` only. (The audit's "63 inline onclick handlers" were `.onclick =` property assignments
  in JS, which CSP does not restrict.) `MonacoReady` now always settles (resolves `null` on load
  failure, error kept in `window.MonacoLoadError`).
- Verified in Chrome with a throwaway DB: no CSP violations; Monaco editor and its web worker load;
  the settings button works.

**Known remaining structure debt:** `server.py` is still ~2,300 lines (route bodies keep inline SQL);
services/repositories split is incremental work for later phases.

**Results (Phase 4):** full suite three consecutive runs: 230 OK / 230 OK / 230 OK (~207–215 s).

## Phase 5 — Frontend architecture (2026-11-21)

- New `web/core.js`, loaded before every app script, owns the extension points. `app.js` calls
  `App.install([...])` once for `api, setView, renderSidebar, renderHome, renderJournal, renderMap,
  boot, selectProfile, renderLessonIntro, renderWorkshop, renderLabBoard`; feature modules only
  register `App.before(name, fn)` / `App.after(name, fn)`. After-hooks of async functions run after
  the promise resolves and are awaited in order; a throwing hook is logged and never breaks the call.
- Converted the 11 global reassignments in `motion.js`, `onboarding.js`, `learning-ui.js`,
  `stats-ui.js`, `study-tracker.js`, `lesson-scenes.js`, `project-workshop.js`, `lab-theater.js`.
- Fixed a latent race: several modules installed their wrappers inside `DOMContentLoaded`, after
  `app.js`'s own listener had already started `boot()` (the browser runs a microtask checkpoint
  between listeners), so the first render could miss them. Hooks are now registered at script load.
  The onboarding module's full replacements (`renderProfiles`, `profileForm`) also moved to load time.
- `App.esc` is the shared HTML/attribute escaper (modules still have local copies; consolidated
  during the Phase 6 UI rewrite).
- Tests (`tests/test_architecture.py`): every hook targets an installed extension point; no module
  reassigns one; `core.js` loads before `app.js` and all feature modules; `core.js` semantics run in
  Node (before/after order, async after-hooks, failing hook isolation, idempotent install, escaping).
- Browser check (Chrome, throwaway DB): all 11 extension points installed; adaptive home panel,
  map entry animation + 20 chapter cards, journal insights, and the multi-file workshop (exactly one
  instance via real nav click) render; no console errors.

**Results (Phase 5):** full suite 233 OK / 233 OK. A third run (and a later single re-run) was stopped by
Claude Code because the machine ran critically low on memory — not a test failure; not re-run yet.

## Phase 6 (part 1) — Design system and dashboard (2026-11-21)

- `web/theme.css` (loaded last): design tokens for colour, spacing, radii, type, elevation, a
  single z-index scale and motion; shared focus ring (`:focus-visible`); `.visually-hidden`;
  primary button now white on `#6b4fe0` (5.5:1; the audit measured 2.81:1 before); global
  `prefers-reduced-motion` rule. Palette contrast was computed before use (muted text 8.0:1,
  subtle 5.5:1, accent ink 9.0:1).
- `web/dashboard.js`: new home view — continue card (current chapter, next task, chapter progress,
  primary CTA), player card (level, XP-to-next-level bar, total XP, streak), daily quest, overall
  progress ring, companion, review queue, recent achievements, and the chapter list as real
  `<button>`s (the old `<article onclick>` chapter cards were not keyboard-reachable). Numbers use
  `Intl.NumberFormat`, counts use `Intl.PluralRules` (Russian one/few/many). Text lives in
  `locales.json` → `modules.dashboard` (tr + ru, same keys). `app.js renderHome()` delegates to it;
  the `learning-ui.js` adaptive panel still attaches via the kept `.section-head`.
- Removed the duplicate `cat-companion-ui.css` link, keeping the later (effective) position so the
  cascade is unchanged.
- Tests: `tests/test_dashboard_ui.py` (load order, no duplicate stylesheet, delegation, every copy
  key in both languages, Russian plural forms, buttons + escaping, theme tokens/focus/motion).
- Later the same day (1.9 GB free): full suite **239 tests OK** (204 s). Browser check at
  1440×900 with a throwaway DB; fixed the companion card overflow and card-header alignment
  (`01ca488`).

## Phase 6 (part 2) — Skill tree, lesson editor, offline editor (2026-11-21)

- `web/skill-tree.js`: the knowledge map now opens with a skill tree computed from each chapter's
  real `prerequisites` (longest-path layering + one barycentre pass; 20 nodes, 31 edges today).
  Nodes are `<button>`s with a full `aria-label` (status, progress, prerequisites); locked nodes
  explain which chapters are still missing; edges to/from the hovered or focused node light up.
  New chapters appear automatically. Copy: `locales.json` → `modules.skillTree` (tr + ru).
- Knowledge-map card titles are now real buttons (`.map-open`) — the cards were mouse-only.
- Lesson view: single column below 1100 px, editor toolbar wraps, button text 12 px (was 9 px).
- `web/monaco-boot.js`: if Monaco cannot load, `MonacoReady` resolves with a `<textarea>` stand-in
  implementing the API subset the app uses (create/getValue/setValue/onDidChangeModelContent/
  addCommand incl. Ctrl+S/deltaDecorations/Range/registerCompletionItemProvider/dispose), so
  code tasks, the workshop, arena and interviews stay usable. Verified in the browser by blocking
  the loader: a code task was written, compiled, accepted and auto-advanced.
- Success flow: after the 850 ms auto-advance, focus moves to the new task title (`#task-title`);
  `#task-result` is `role=status aria-live=polite`, `#console` is `role=log aria-live=polite`.
- Tests: `tests/test_skill_tree.py` (Node layout test on the real curriculum: every edge points
  forward, no overlaps, inside bounds), `tests/test_editor_fallback.py` (Node + fake DOM).

## Phase 7 — Game economy and server authority (2026-11-21)

- `state()` returns `PUBLIC_CURRICULUM`: answers, expected outputs, hidden tests and concept rules
  no longer reach the browser (before, every answer was readable in DevTools). Code/fix/boss tasks
  carry one worked example plus `test_count`. Grading is unchanged (server-side).
- Level vs. money: `profile.lifetime_xp` (drives the level, never decreases) and
  `profile.balance` (spendable, the shop deducts from it) are reported separately; the dashboard
  shows both. Levels were already derived from completions, so purchases never cost a level —
  now that is explicit and tested.
- Arena: `GET /api/arena` records when the server showed the challenge; a submission's time is
  `max(server-observed, compile time, claimed)`, so `solve_ms: 1` can no longer top the fastest list.
- Study time: a pulse may grow a session at most by the wall-clock time since its last pulse
  + 45 s (first pulse ≤ 120 s). `test_core` used an impossible 30→90 s jump in 0 s; it now uses
  30→70 s, and a new test proves an instant 11-hour jump is capped.
- Static files: `Cache-Control: no-cache` (revalidate) for app files, one day for `/vendor/`;
  before, no header was sent and WebView2 could keep showing an old version after an update.
- Tests: `tests/test_phase7_economy.py` (no secrets in state, quiz still graded, purchase keeps
  level, arena floor, cache headers). Full suite: **252 tests OK** (210 s).
- **Not done in Phase 7 (deferred):** server-side hint tracking (hints are still client-side and
  give no reward penalty), shuffling interview options, shop rebalancing; workshop projects still
  send their test cases (they are shown to the learner by design).
