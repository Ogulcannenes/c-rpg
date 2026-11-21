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

### Phase 7 follow-up (deferred items)

- Hints: text is no longer in `/api/state` (only `hint_count`). `POST /api/hint {task_id, level, lang}`
  reveals one level at a time, in order (409 `hint_order` otherwise), and records it in the new
  `hint_reveals` table (migration 4, `ON DELETE CASCADE`). `/api/submit` applies the 10 % penalty if
  the server revealed a hint, whatever the client sends. Profile import clears the table too.
- Interview: all 7 choice questions stored the correct option first, so "always pick A" scored 100 %.
  Options are now shuffled per session (deterministic, `interview_option_order`) and graded by
  mapping the shown index back.
- Predict tasks no longer ship `starter` (it equals the answer).
- Shop rebalancing: still not done.

## Phase 8 — Modern C++ curriculum (2026-11-21)

- New self-contained module `modern_cpp.py` adds four chapters (24 chapters / 192 tasks total),
  wired into `curriculum.py` before `task_clarity`. The old index-aligned tables stay at 20.
  - c21 Move semantics and the Rule of Five (prereqs c17, c12)
  - c22 optional / variant / string_view (c09, c19)
  - c23 Concepts and Ranges, C++20 (c19, c13)
  - c24 Concurrency: real `std::thread`, `std::mutex`, `std::atomic`, `std::jthread` (c21, c19)
- Each chapter: TR + RU lesson, 5 guide sections with code, 8 missions in the usual order. Code
  missions have 3–4 hidden tests and a new structural concept rule (`move_semantics`,
  `rule_of_five`, `vocabulary_types`, `string_view_parse`, `constrained_template`,
  `custom_concept`, `ranges_pipeline`, `thread_join`, `shared_counter`). `#include <thread>` alone
  does not count as using threads; an unsynchronised counter fails `shared_counter`.
- Verified in the real sandbox (static C++20, Windows): threads/mutex/atomic, optional/variant,
  concepts/ranges, jthread/async all compile and run.
- `tests/test_modern_cpp.py`: reference solutions for all 16 code missions pass every hidden test
  and concept check; no starter passes as-is; all 8 predictions match real program output; TR
  slots contain no Cyrillic and RU prompts are Russian; quiz answers are among the offered options.
- Four new world-map zones (TR/RU); fixed `rpg-ui.js` zone fallback (`[a,b]||x` was always truthy).
- Count-based assertions in older tests updated (20→24 chapters, 160→192 tasks). Each new chapter also
  got an animated walkthrough scene (`lesson_scenes.py`, section 2) and its own map icon (`ch-21`…`ch-24`).
- Full suite: **262 tests OK** (265 s).
- Browser check: skill tree draws 24 nodes / 39 edges with correct prerequisites; dashboard shows
  0/192 tasks, 0/24 chapters; hint buttons fetch text from the server in order.
- Not done: C++23 topics (`std::expected`, `std::print`) — the bundled GCC must be checked first;
  multi-file projects.

## Phase 9 — Free online AI tutor (2026-11-21)

User requirement: the AI must be free and online-only, with no local model. Choice: **Groq free plan**
(no credit card; answers HTTP 429 instead of charging; already integrated). Gemini's free model
list changed several times in 2026, so it was not added as a second provider.

- New `ai_tutor.py`:
  - Groq request, a 3-level hint policy and a system prompt that names the answer language
    explicitly (Turkish/Russian).
  - Learner code and input go inside `<learner_code>`/`<program_input>` tags and are declared
    untrusted. The code cannot close its own tag (escaped).
  - Error taxonomy (`unconfigured`, `rate_limited`, `auth`, `network`, `server`, `bad_response`,
    `disabled`) with TR/RU messages. `ask_groq` never raises.
  - Model fallback `gpt-oss-120b → gpt-oss-20b` on 429 and on 400/404 (retired model).
  - `check_key` verifies a key through the free model list, with no tokens spent.
- Removed: Ollama (local), OpenAI and Claude (paid). This covers the code paths, settings options,
  key rows, locale strings, `/api/ai/claude-key` and `tests/test_claude_ai.py`. Migration 5 moves
  profiles that used them to `groq`; import maps them the same way. Old `ai_usage` history rows
  are kept. A saved Claude key file is left on disk untouched (user data) and is no longer read.
- Endpoints:
  - `/api/ai/diagnose` takes `hint_level` 1–3. Consent is still required for every request.
  - Hidden tests, the profile id and the name are never sent. Only the visible example output is.
  - Usage records tokens/requests with cost 0.
  - New `POST /api/ai/check`; `/api/ai/key` takes `verify`.
- UI:
  - Settings offer Groq (free) / offline / off; key check button; "Ücretsiz" instead of cost.
  - The diagnosis card shows the hint level, a "Daha ayrıntılı ipucu" button and the model name.
  - Fixed `chapterIcon` capping at 20, which hid the c21–c24 icons.
- Tests: `tests/test_phase9_ai_tutor.py` (13 tests; no real network): provider policy, prompt
  framing, tag escape, error codes, fallback, key check, endpoint flows, migration.
  Full suite: **270 tests OK** (257 s).
- Not verified: a real request to Groq (no key on this machine; the user creates a free key at
  console.groq.com/keys). Free-plan limits are set per account and can change; see the Groq console.

## Phase 10 — Accessibility, Turkish/Russian, performance (2026-11-21)

- Accessibility:
  - Skip link ("İçeriğe geç" / "Перейти к содержимому") as the first element; `<main id="main-content" tabindex="-1">`.
  - The active nav item gets `aria-current="page"`.
  - New `App.trapFocus` in `core.js`: Tab and Shift+Tab wrap inside the dialog, Escape closes it, and focus returns to the opener. The save dialog uses it; the onboarding wizard got the same Tab trap. The PIN dialog already had one.
  - Bug fixed: Escape inside a dialog also ran the app's global Escape handler and jumped to the profile screen.
- Turkish/Russian:
  - `pairs.advanced-cpp.001` had Russian text in the Turkish slot ("Модель готова." → "Model hazır.").
  - Quiz grading folds `ё`→`е`.
  - The class lab built a C++ variable from `name.lower()`, so "Işık Pati" produced invalid code. New `visual_labs.cpp_identifier` (Turkish→ASCII, keyword/digit safe) and `cpp_string` (escapes quotes).
  - Server errors: new `error_catalog.py` gives each of the 44 Turkish-only messages an `error_code` and Russian text. Bilingual "TR / RU" messages are split. `send_json` adds `error_tr`/`error_ru`; `api()` in `app.js` shows the current language.
- Performance (measured, no change): `/api/state` builds in ~11 ms and is 247 KB (55 KB gzipped), mostly the public curriculum. It is acceptable over loopback; caching the curriculum separately is a possible later step.
- Tests: `tests/test_phase10_a11y_i18n.py` (8 tests). It includes a Node run of the real `trapFocus` and a guard that every new Turkish-only server error needs a catalog entry. `test_architecture` now also checks the split fields.
- Full suite: 278 tests. 277 passed on the full run; the one exact-match test was then updated and passes.
- Screen-reader testing with NVDA/JAWS was not done; the checks are structural and keyboard-level.

## Phase 11 — Windows packaging (2026-11-21)

- Evaluation:
  - Inno Setup 6 was chosen for the real installer: per-user, no admin rights, TR/RU wizard, uninstaller, AppMutex.
  - MSIX was not chosen. It needs a signing certificate to install outside developer mode, and it virtualises `%LOCALAPPDATA%`, which would hide the existing profiles.
  - Inno Setup is **not installed on this machine**, so the `.iss` was written but **not compiled here**. `build-windows.bat` uses ISCC when present and otherwise falls back to the previous self-extracting setup.
- `desktop.py`:
  - Single instance through the named mutex `Local\CppAdventure.SingleInstance`; a second launch focuses the running window and exits.
  - WebView2 runtime check (HKLM/WOW6432Node/HKCU `pv`) with a TR/RU message and download link.
  - `--remove-sandbox-profile` for the uninstaller (`DeleteAppContainerProfile`; the profile holds only temporary runs).
  - `main()` returns exit codes.
- `server.find_compiler`: `CPP_ADVENTURE_COMPILER` → PATH → `C:\msys64\{ucrt64,mingw64,clang64}` and similar. An MSYS2 folder found this way is put on PATH so cc1plus finds its DLLs.
- Legacy DB pointer: the source must be absolute and start with the SQLite header. It is opened read-only (`mode=ro`) and whitespace is trimmed.
- Build:
  - `CppAdventure.spec`: `upx=False`, version resource from `APP_VERSION` (bumped to **0.5.0**), and tkinter/unittest/pydoc excluded.
  - `requirements-desktop.txt` pins the direct dependencies; `requirements-desktop.lock.txt` holds exact transitive versions, and `setup-desktop.bat` installs from it.
  - `installer/app_version.py`.
- `start-desktop.bat` no longer cascades through stale `dist-stage*` builds. The old folders were not deleted.
- Verified on this Windows 11 machine:
  - A PyInstaller build to a scratch folder succeeded (66.8 MB). The exe reports FileVersion 0.5.0.
  - Launched with a throwaway `LOCALAPPDATA`, the window opened. A second launch exited in 0.5 s and the log shows "focusing the running window". The window then closed normally.
  - With MSYS2 removed from PATH, a program compiled and printed the right output.
- Not verified:
  - The Inno installer itself (no ISCC).
  - Uninstall.
  - Code signing: no certificate, so files are unsigned and SmartScreen may warn.
  - The project's `dist\` was not rebuilt.
- Tests: `tests/test_phase11_desktop.py` (17 tests). Full suite: **293 tests OK** (256 s).

## Phase 12 — Regression, docs, report (2026-11-21)

- Full regression after Phase 11, three consecutive runs: **293 OK / 293 OK / 293 OK** (256 s, 259 s, 253 s).
- `docs/FINAL_REPORT.md`: Turkish final report (summary table, per-phase results, verified and
  not-verified lists, next steps for the user, rollback). It is linked from the README.
  Screenshots are in `docs/screenshots/` (before/after).
- Still open: quest/boss screen redesign; locked-achievement contrast; shop rebalance; C++23 topics;
  multi-file missions; splitting `server.py` into services. Also not done yet: compiling and
  testing the Inno installer (needs ISCC), code signing (needs a certificate), a real Groq request
  (needs the user's free key) and a screen-reader pass.

## UI/UX + accessibility + technical audit (2026-11-21)

Full report with scores, measurements and before/after screenshots: `docs/UX_AUDIT.md`.

- Method: real running app (throwaway DB) at 980/1440/1920 px, all 15 sections plus lesson,
  quiz, code, boss, settings and profiles; in-page measurement scripts. Four independent read-only
  reviewers (UI Designer, UX Architect, Accessibility Auditor, Code Reviewer), checked by Reality
  Checker, which also re-scored each fix round. The app has no colour-theme system, so "15 themes"
  was scored as cohesion of the 15 sidebar sections.
- Scores: visual 71.8 → 76.2 → 78.4, technical 68 → 73 → 77, total 69.5 → 74.3 → 77.6.
  Seven of nine visual criteria are still 76–79, so the phase is **not** marked successful.
  Round 3 (profile picker focus/title, editor 14px, inline greys, career empty states) was not
  re-scored independently.
- Main fixes:
  - Wrong "previous boss" lock note.
  - Global Escape → profiles.
  - Empty lesson card.
  - Sticky Run/Submit.
  - No text under 11px; off-token greys and opacity fading replaced with tokens (0 measurable AA failures).
  - setView focus/title/scroll, including settings and profiles.
  - Text size 100–150% with Ctrl+Plus/Minus/0, and a reduce-motion switch honoured by all JS modules.
  - Monaco ariaLabel ×5; toast ≥4 s.
  - Narrower but non-wrapping sidebar at ≤1100px; 4×2 task tabs.
  - Remaining English labels translated.
  - Server:
    - hidden-test input/expected no longer revealed;
    - import backs up first and validates all lists;
    - 500s are logged, generic message plus incident id;
    - single-file backups with as_uri paths.
  - Tests isolate DATA_ROOT.
- Deliberately not done: backup pruning (owner's rule: never delete backups); the 78 stale files
  in the repo's git-ignored backups/ folder were left in place.
- Tests: new tests/test_ux_audit_fixes.py (8); suite 301 OK after rounds 1 and 2.

## Task outputs in English, new README, SCORES.md (2026-11-21)

- The owner asked that what a program must print in the practice tasks be English, not Turkish.
  - 27 tasks changed their expected output, starter, prompt, hint and reference solution together, for example "Merhaba" → "Hello", "Gecti/Tekrar" → "Passed/Retry", "Miyav" → "Meow", "yok" → "none".
  - Prompts stay Turkish/Russian. Recomputed outputs: `map` order "bee 1, bird 1, cat 2"; "Mira Star 9"; "paws8"; "cat 3".
  - New test `EnglishTaskOutputTests`: every expected output of code/fix/boss/predict tasks is ASCII and contains no Turkish word.
  - Workshop projects and lesson animations were not changed.
- README rewritten from scratch as a general application README: features, requirements, MSYS2 G++ setup, setup/uninstall, data and backups, AI key, building, tests, security, troubleshooting and environment variables.
- New `SCORES.md`: quality scores per criterion and round, technical sub-scores, measured indicators, test-suite results per phase and test counts per file.
- Full suite: **302 tests OK**.
