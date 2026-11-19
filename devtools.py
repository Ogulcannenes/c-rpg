"""Small, deterministic developer-tool learning labs for C++ Adventure.

Git and shell labs use virtual state: they never touch the host repository or run
arbitrary terminal input. The testing lab is intentionally delegated to the
existing bounded C++ runner in server.py.
"""
from __future__ import annotations

import re


MAX_TEXT = 4000
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,48}$")


def initial_state(module: str) -> dict:
    if module == "git":
        files = {"README.md": "# C++ Adventure\n"}
        return {"initialized": False, "branch": "main", "branches": {"main": None}, "branch_files": {"main": files}, "branch_bases": {"main": files}, "remote": {}, "files": files, "staged": [], "commits": [], "message": "", "last": ""}
    if module == "conflict":
        return {"started": False, "conflict": False, "left": "", "right": "", "resolved": "", "complete": False, "last": ""}
    if module == "cmake":
        return {"step": 0, "complete": False, "last": ""}
    if module == "terminal":
        return {"cwd": "/adventure", "dirs": ["/adventure"], "files": {"/adventure/README.txt": "C++ Adventure çalışma alanı"}, "history": [], "last": ""}
    if module == "testing":
        return {"code": "#include <iostream>\nint main(){ int n; std::cin >> n; std::cout << n * 2; }", "input": "21", "expected": "42", "last": "", "runs": 0, "passed": 0}
    raise ValueError("Unknown developer lab")


def _message(state: dict, text: str) -> dict:
    state["last"] = text
    return state


def apply(module: str, state: dict, action: str, data: dict, compiler: str | None = None, cmake_available: bool | None = None) -> dict:
    if module == "git":
        if action == "init":
            state["initialized"] = True
            return _message(state, "Initialized empty teaching repository on main.")
        if not state.get("initialized"):
            return _message(state, "Run git init first.")
        if action == "write":
            name, content = str(data.get("name", "")), str(data.get("content", ""))
            if not SAFE_NAME.fullmatch(name) or not content or len(content) > MAX_TEXT:
                return _message(state, "Use a simple file name and 1–4000 characters of content.")
            state["files"][name] = content
            return _message(state, f"Working tree changed: {name}")
        if action == "add":
            name = str(data.get("name", ""))
            if name == "*": state["staged"] = sorted(state["files"])
            elif name in state["files"]: state["staged"] = sorted(set(state["staged"] + [name]))
            else: return _message(state, "That file does not exist in the virtual workspace.")
            return _message(state, f"Staged {len(state['staged'])} file(s).")
        if action == "commit":
            message = str(data.get("message", "")).strip()[:120]
            if not state["staged"] or not message: return _message(state, "Stage a file and enter a commit message first.")
            commit = {"id": f"{len(state['commits']) + 1:03}", "branch": state["branch"], "message": message, "files": list(state["staged"])}
            state["commits"].append(commit); state["branches"][state["branch"]] = commit["id"]; state["branch_files"][state["branch"]] = dict(state["files"]); state["staged"] = []
            return _message(state, f"Commit {commit['id']} created on {state['branch']}.")
        if action == "branch":
            name = str(data.get("name", ""))
            if not SAFE_NAME.fullmatch(name) or name in state["branches"]: return _message(state, "Choose a new branch name using letters, digits, dot, dash, or underscore.")
            state["branches"][name] = state["branches"].get(state["branch"]); state["branch_files"][name] = dict(state["files"]); state["branch_bases"][name] = dict(state["files"]); state["branch"] = name
            return _message(state, f"Created and switched to {name}.")
        if action == "checkout":
            name = str(data.get("name", ""))
            if name not in state["branches"]: return _message(state, "Branch not found.")
            state["branch"] = name; state["files"] = dict(state["branch_files"].get(name, {})); state["staged"] = []
            return _message(state, f"Switched to {name}.")
        if action == "merge":
            target = str(data.get("name", "")); current = state["branch"]
            if target not in state["branches"] or target == current: return _message(state, "Choose another existing branch to merge.")
            if state["staged"] or state["files"] != state["branch_files"].get(current, {}): return _message(state, "Commit or discard working-tree changes before merging.")
            base = state["branch_bases"].get(target, {})
            ours = dict(state["files"]); theirs = dict(state["branch_files"].get(target, {})); merged = dict(ours)
            conflicts = []
            for file in set(base) | set(ours) | set(theirs):
                b, o, t = base.get(file), ours.get(file), theirs.get(file)
                ours_changed, theirs_changed = o != b, t != b
                if ours_changed and theirs_changed and o != t: conflicts.append(file)
                elif theirs_changed:
                    if t is None: merged.pop(file, None)
                    else: merged[file] = t
            if conflicts: return _message(state, "Merge conflict in " + ", ".join(sorted(conflicts)) + ". Resolve it in the Conflict lab, then retry.")
            state["files"] = merged; state["branch_files"][current] = dict(merged)
            commit = {"id": f"{len(state['commits']) + 1:03}", "branch": current, "message": f"Merge {target} into {current}", "files": sorted(set(ours) | set(theirs))}
            state["commits"].append(commit); state["branches"][current] = commit["id"]
            return _message(state, f"Merged {target} into {current} as commit {commit['id']}.")
        if action == "push":
            branch = state["branch"]; state["remote"][branch] = {"head": state["branches"].get(branch), "files": dict(state["files"])}
            return _message(state, f"Pushed {branch} to the simulated remote. No network connection was used.")
        if action == "pull":
            branch = state["branch"]; remote = state["remote"].get(branch)
            if not remote: return _message(state, "No simulated remote update exists for this branch.")
            state["files"] = dict(remote["files"]); state["branch_files"][branch] = dict(remote["files"]); state["branches"][branch] = remote["head"]
            return _message(state, f"Pulled simulated {branch} remote state. No network connection was used.")
        if action == "status":
            changed = sorted(set(state["files"]) - set(state["staged"]))
            return _message(state, f"On branch {state['branch']} · staged: {len(state['staged'])} · unstaged: {len(changed)}")
        return _message(state, "Unknown Git lab action.")

    if module == "conflict":
        if action == "start":
            state.update(started=True, conflict=True, left="The hero has 100 HP.", right="The hero has 120 HP.", resolved="", complete=False)
            return _message(state, "Both branches changed the same line. Choose the final value to resolve the conflict.")
        if action == "resolve" and state.get("conflict"):
            result = str(data.get("resolved", "")).strip()
            if result not in (state["left"], state["right"]): return _message(state, "Use one of the branch versions shown above.")
            state.update(resolved=result, conflict=False, complete=True)
            return _message(state, "Conflict resolved and merge verified.")
        return _message(state, "Start the conflict scenario first.")

    if module == "cmake":
        if action == "step":
            requested = int(data.get("step", -1))
            if requested == state["step"] + 1 and requested <= 4:
                state["step"] = requested
                state["complete"] = requested == 4
                return _message(state, ["","Create CMakeLists.txt.","Declare the minimum CMake version and project.","Add the C++ executable target.","Configure, build, then run the executable."][requested])
            return _message(state, "Complete the CMake steps in order.")
        if action == "reset": return initial_state("cmake")
        if action == "status": return _message(state, f"CMake executable: {'detected' if (cmake_available if cmake_available is not None else compiler == 'cmake') else 'not detected'} · lesson progress {state['step']}/4. This lab does not execute arbitrary CMakeLists.txt files.")
        return _message(state, "Unknown CMake lab action.")

    if module == "terminal":
        command = str(data.get("command", "")).strip()
        if len(command) > 240: return _message(state, "Command is too long (240 character limit).")
        history = state.setdefault("history", [])
        parts = command.split()
        if not parts: return _message(state, "Enter a command, or type help.")
        op = parts[0].lower()
        if op == "help": output = "Allowed: help, pwd, ls, mkdir NAME, touch NAME, cat NAME, cd PATH, echo TEXT > NAME, clear, git status, cmake --version, g++ --version"
        elif op == "pwd": output = state["cwd"]
        elif op == "ls":
            prefix = state["cwd"].rstrip("/") + "/"
            output = "  ".join(sorted([p[len(prefix):] for p in state["dirs"] if p.startswith(prefix) and p != state["cwd"]] + [p[len(prefix):] for p in state["files"] if p.startswith(prefix)])) or "(empty)"
        elif op == "mkdir" and len(parts) == 2 and SAFE_NAME.fullmatch(parts[1]):
            path = state["cwd"].rstrip("/") + "/" + parts[1]
            if path in state["dirs"]: output = "Directory already exists."
            else: state["dirs"].append(path); output = f"Created {parts[1]}"
        elif op == "touch" and len(parts) == 2 and SAFE_NAME.fullmatch(parts[1]):
            path = state["cwd"].rstrip("/") + "/" + parts[1]; state["files"].setdefault(path, ""); output = f"Created {parts[1]}"
        elif op == "cat" and len(parts) == 2:
            path = state["cwd"].rstrip("/") + "/" + parts[1]; output = state["files"].get(path, "File not found.")
        elif op == "cd" and len(parts) == 2:
            target = parts[1]
            path = "/adventure" if target == ".." and state["cwd"] == "/adventure" else (state["cwd"].rsplit("/", 1)[0] or "/adventure" if target == ".." else target if target.startswith("/") else state["cwd"].rstrip("/") + "/" + target)
            if path in state["dirs"]: state["cwd"] = path; output = path
            else: output = "Directory not found."
        elif op == "echo" and ">" in parts:
            i = parts.index(">")
            if i + 1 >= len(parts) or not SAFE_NAME.fullmatch(parts[i + 1]): output = "Use: echo TEXT > safe-file-name"
            else:
                path = state["cwd"].rstrip("/") + "/" + parts[i + 1]; text = " ".join(parts[1:i])[:MAX_TEXT]; state["files"][path] = text; output = f"Wrote {len(text)} characters."
        elif command == "git status": output = "On branch main\nNothing to commit (simulated workspace)."
        elif command == "cmake --version": output = "CMake lesson simulator · no host command was executed."
        elif command == "g++ --version": output = "Compiler is available." if compiler else "G++ was not detected."
        elif op == "clear": history.clear(); output = "Terminal cleared."
        else: output = "Blocked: this teaching terminal accepts only allowlisted virtual commands. No operating-system command ran."
        if op != "clear": history.append({"command": command, "output": output}); history[:] = history[-30:]
        return _message(state, output)

    if module == "testing":
        if action == "save":
            code, expected, stdin = data.get("code", ""), data.get("expected", ""), data.get("input", "")
            if not isinstance(code, str) or len(code) > 20_000 or len(str(expected)) > 2000 or len(str(stdin)) > 2000:
                return _message(state, "Input exceeds the local lab limits.")
            state.update(code=code, expected=str(expected), input=str(stdin))
            return _message(state, "Test case saved locally.")
        return _message(state, "Run the saved case with the real G++ runner.")
    raise ValueError("Unknown developer lab")
