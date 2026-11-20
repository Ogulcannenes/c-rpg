"""Task-specific C++ concept checks using Clang's function AST when available.

The checker inspects only the student's main function AST (not the full standard
library AST), so comments, string literals, and unused keyword mentions cannot
satisfy a lesson criterion. A structural lexer fallback keeps G++-only installs
usable; real compilation and the task's test cases remain mandatory either way.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess


RULES = {
    "output_main": {"tr": "main içinde gerçek std::cout çıktısı üret", "ru": "Выведи результат через std::cout внутри main"},
    "typed_variables": {"tr": "int ve std::string değişkenlerini tanımla ve çıktıda kullan", "ru": "Создай int и std::string и используй их при выводе"},
    "input_output": {"tr": "std::cin ile okunan değeri std::cout ile kullan", "ru": "Используй значение из std::cin в выводе std::cout"},
    "input_arithmetic": {"tr": "Girdiden okunan değerlerle aritmetik işlem yapıp sonucu yazdır", "ru": "Выполни вычисление с введёнными значениями и выведи результат"},
    "input_branch": {"tr": "Girdiye bağlı if/else dallarında farklı sonuçlar üret", "ru": "Выбери результат через if/else на основе ввода"},
    "input_loop": {"tr": "Girdi değerini kullanan döngüyle sonucu hesapla", "ru": "Вычисли результат циклом, использующим введённое значение"},
    "function_output": {"tr": "Kendi değer döndüren fonksiyonunu çağır ve sonucunu kullan", "ru": "Вызови собственную функцию с возвращаемым значением и используй результат"},
    "vector_iteration": {"tr": "std::vector içindeki elemanları döngüyle işle ve sonucu kullan", "ru": "Обработай элементы std::vector в цикле и используй результат"},
    "string_output": {"tr": "std::string değerini çıktı üretmek için kullan", "ru": "Используй значение std::string при выводе"},
    "reference_alias": {"tr": "Bir değişkene referans ver ve referans üzerinden değiştir", "ru": "Создай ссылку на переменную и измени её через ссылку"},
    "struct_member": {"tr": "Kendi struct nesnenin alanını okuyup çıktıda kullan", "ru": "Прочитай поле собственного struct-объекта и выведи его"},
    "class_method": {"tr": "Kendi class nesnenin metodunu çağır ve sonucunu kullan", "ru": "Вызови метод собственного class-объекта и используй результат"},
    "stl_sort": {"tr": "std::sort ile bir koleksiyonu sırala ve sıralı veriyi kullan", "ru": "Отсортируй коллекцию через std::sort и используй результат"},
    "file_exception": {"tr": "Dosyaya gerçekten yazıp oku ve hatayı try/catch ile yönet", "ru": "Запиши и прочитай файл, обработай ошибку через try/catch"},
    "integrated_project": {"tr": "Fonksiyon, koşul, döngü, değişken ve çıktıyı birlikte kullan", "ru": "Объедини функцию, условие, цикл, переменную и вывод"},
    'pointer_dynamic': {'tr': 'new/new[] ile bellek ayır, işaretçiyi kullan ve delete/delete[] ile serbest bırak', 'ru': 'Выдели память через new/new[], используй указатель и освободи через delete/delete[]'},
    'smart_pointer': {'tr': 'std::unique_ptr veya std::shared_ptr kullan; elle new/delete yazma', 'ru': 'Используй std::unique_ptr или std::shared_ptr; не пиши new/delete вручную'},
    'raii_scope': {'tr': 'Kurucusu ve yıkıcısı olan bir sınıfı blok kapsamında kullan (RAII)', 'ru': 'Используй класс с конструктором и деструктором в блоке (RAII)'},
    'virtual_dispatch': {'tr': 'virtual metot, override ve taban sınıf işaretçisi/referansıyla çağrı kullan', 'ru': 'Используй virtual-метод, override и вызов через указатель или ссылку на базовый класс'},
    'template_function': {'tr': 'template ile genel bir fonksiyon yaz ve en az iki farklı türle çağır', 'ru': 'Напиши обобщённую функцию через template и вызови её минимум с двумя типами'},
    'lambda_capture': {'tr': 'Yakalama listesi ([...]) olan bir lambda kullan', 'ru': 'Используй лямбду со списком захвата ([...])'},
    'map_set': {'tr': 'std::map veya std::set (ya da unordered sürümleri) kullan ve sonucu yazdır', 'ru': 'Используй std::map или std::set (или unordered-версии) и выведи результат'},
}


# Rules checked only with the token-based structural checker (no clang AST needed).
TOKEN_ONLY_RULES = {'pointer_dynamic', 'smart_pointer', 'raii_scope', 'virtual_dispatch', 'template_function', 'lambda_capture', 'map_set'}


def _walk(node):
    if isinstance(node, dict):
        yield node
        for child in node.get("inner", []):
            yield from _walk(child)


def _referenced(node):
    return [n.get("referencedDecl", {}) for n in _walk(node) if n.get("kind") == "DeclRefExpr"]


def _names(node):
    return {r.get("name", "") for r in _referenced(node) if r.get("name")}


def _ids(node):
    return {r.get("id") for r in _referenced(node) if r.get("id")}


def _operators(node, spelling):
    result = []
    for n in _walk(node):
        if n.get("kind") == "CXXOperatorCallExpr" and any(r.get("name") == spelling for r in _referenced(n)):
            result.append(n)
    return result


def _outputs(main):
    return [n for n in _operators(main, "operator<<") if "cout" in _names(n)]


def _inputs(main):
    return [n for n in _operators(main, "operator>>") if "cin" in _names(n)]


def _used_ids(main):
    return _ids(main)


def _main_ast(source):
    clang = shutil.which("clang++") or shutil.which("clang")
    if not clang:
        return None
    command = [clang, "-std=c++20", "-Xclang", "-ast-dump=json", "-Xclang", "-ast-dump-filter=main", "-fsyntax-only", "-x", "c++", "-"]
    try:
        result = subprocess.run(command, input=source, capture_output=True, text=True, timeout=8, encoding="utf-8", errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode or not result.stdout or len(result.stdout) > 6_000_000:
            return None
        decoder, offset, main = json.JSONDecoder(), 0, None
        while offset < len(result.stdout):
            while offset < len(result.stdout) and result.stdout[offset].isspace():
                offset += 1
            if offset >= len(result.stdout):
                break
            item, offset = decoder.raw_decode(result.stdout, offset)
            loc = item.get("loc", {})
            if item.get("kind") == "FunctionDecl" and item.get("name") == "main" and loc.get("file") == "<stdin>":
                main = item
                break
        return main
    except (OSError, subprocess.TimeoutExpired, ValueError, json.JSONDecodeError):
        return None


def _tokens(source):
    """Tokenize C++ enough for a structural fallback; discard comments/literals."""
    out, i, n = [], 0, len(source)
    operators = ("<<=", ">>=", "->", "::", "<<", ">>", "++", "--", "+=", "-=", "*=", "/=", "<=", ">=", "==", "!=", "&&", "||")
    while i < n:
        if source.startswith("//", i):
            end = source.find("\n", i + 2)
            i = n if end < 0 else end + 1
            continue
        if source.startswith("/*", i):
            end = source.find("*/", i + 2)
            i = n if end < 0 else end + 2
            continue
        if source[i] in "\"'":
            q, i = source[i], i + 1
            while i < n:
                if source[i] == "\\":
                    i += 2
                elif source[i] == q:
                    i += 1
                    break
                else:
                    i += 1
            out.append("<literal>")
            continue
        if source[i].isspace():
            i += 1
            continue
        if source[i].isalpha() or source[i] == "_":
            j = i + 1
            while j < n and (source[j].isalnum() or source[j] == "_"):
                j += 1
            out.append(source[i:j])
            i = j
            continue
        op = next((x for x in operators if source.startswith(x, i)), None)
        if op:
            out.append(op)
            i += len(op)
        else:
            out.append(source[i])
            i += 1
    return out


def _fallback(source, rule):
    t = _tokens(source)
    def has(*pattern):
        width = len(pattern)
        return any(t[i:i + width] == list(pattern) for i in range(len(t) - width + 1))

    def is_id(value):
        return bool(re.fullmatch(r"[A-Za-z_]\w*", value)) and value not in {"std", "int", "double", "float", "char", "bool", "string", "if", "else", "for", "while", "do", "return", "const", "auto"}

    def variable_after(type_tokens):
        names = set()
        width = len(type_tokens)
        for i in range(len(t) - width):
            if t[i:i + width] == type_tokens and is_id(t[i + width]):
                names.add(t[i + width])
        return names

    def stream_positions(stream, operator):
        return [i for i in range(len(t) - 1) if t[i] == stream and t[i + 1] == operator]

    def output_uses(names):
        for i in stream_positions("cout", "<<"):
            end = next((j for j in range(i + 2, len(t)) if t[j] == ";"), len(t))
            if names & set(t[i + 2:end]):
                return True
        return False

    cout = has("cout", "<<") or has("std", "::", "cout", "<<")
    cin = has("cin", ">>") or has("std", "::", "cin", ">>")
    ints = variable_after(["int"])
    strings = variable_after(["std", "::", "string"]) | variable_after(["string"])
    input_names = set()
    for i, token in enumerate(t[:-1]):
        if token == "cin" and t[i + 1] == ">>":
            if i + 2 < len(t) and is_id(t[i + 2]):
                input_names.add(t[i + 2])

    if rule == "output_main":
        return has("int", "main", "(") and cout
    if rule == "typed_variables":
        return bool(ints & set(t) and strings & set(t) and output_uses(ints) and output_uses(strings))
    if rule == "input_output":
        return cin and cout and bool(input_names & set(t)) and output_uses(input_names)
    if rule == "input_arithmetic":
        operators = {"+", "-", "*", "/", "%"}
        return cin and cout and bool(input_names & set(t)) and bool(operators & set(t)) and output_uses(input_names)
    if rule == "input_branch":
        return cin and "if" in t and "else" in t and cout and bool(input_names & set(t)) and len(stream_positions("cout", "<<")) >= 2
    if rule == "input_loop":
        return cin and bool({"for", "while", "do"} & set(t)) and cout and bool(input_names & set(t))
    if rule == "function_output":
        calls = {t[i] for i in range(len(t) - 1) if is_id(t[i]) and t[i + 1] == "("}
        definitions = {t[i + 1] for i in range(len(t) - 3) if t[i] in {"int", "double", "float", "bool", "string"} and is_id(t[i + 1]) and t[i + 2] == "("}
        return cout and bool(calls & definitions) and "return" in t
    if rule == "vector_iteration":
        vectors = variable_after(["std", "::", "vector", "<", "int", ">"])
        return bool(vectors and {"for", "while"} & set(t) and cout)
    if rule == "string_output":
        return bool(strings and cout and output_uses(strings))
    if rule == "reference_alias":
        aliases = set()
        originals = set()
        for i in range(len(t) - 4):
            if t[i] in {"int", "double", "float", "char", "bool"} and t[i + 1] == "&" and is_id(t[i + 2]) and t[i + 3] == "=" and is_id(t[i + 4]):
                aliases.add(t[i + 2]); originals.add(t[i + 4])
        mutated = any((t[i] in aliases and t[i + 1] in {"++", "--", "+=", "-=", "="}) or (t[i] in {"++", "--"} and t[i + 1] in aliases) for i in range(len(t) - 1))
        return bool(aliases and originals and mutated and output_uses(originals))
    if rule == "struct_member":
        declared = {t[i + 1] for i in range(len(t) - 2) if t[i] == "struct" and is_id(t[i + 1]) and t[i + 2] == "{"}
        objects = {t[i + 1] for i in range(len(t) - 1) if t[i] in declared and is_id(t[i + 1])}
        return cout and any(t[i] in objects and t[i + 1] == "." and is_id(t[i + 2]) for i in range(len(t) - 2))
    if rule == "class_method":
        declared = {t[i + 1] for i in range(len(t) - 2) if t[i] == "class" and is_id(t[i + 1]) and t[i + 2] == "{"}
        objects = {t[i + 1] for i in range(len(t) - 1) if t[i] in declared and is_id(t[i + 1])}
        return cout and any(t[i] in objects and t[i + 1] == "." and is_id(t[i + 2]) and t[i + 3] == "(" for i in range(max(0, len(t) - 3)))
    if rule == "stl_sort":
        return has("std", "::", "sort", "(") and any("vector" in t[i:i + 3] for i in range(len(t) - 2)) and cout
    if rule == "file_exception":
        return bool({"ifstream", "ofstream", "fstream"} & set(t)) and "try" in t and "catch" in t and bool({"<<", ">>"} & set(t)) and cout
    if rule == "pointer_dynamic":
        pointers = {t[i + 2] for i in range(len(t) - 2) if t[i] in {"int", "double", "float", "char"} and t[i + 1] == "*" and is_id(t[i + 2])}
        uses = sum(token in pointers for token in t)
        return bool(pointers and "new" in t and "delete" in t and uses >= 4 and cout)
    if rule == "smart_pointer":
        smart = {"unique_ptr", "shared_ptr", "make_unique", "make_shared"}
        return bool(smart & set(t) and "new" not in t and "delete" not in t and cout)
    if rule == "raii_scope":
        destructor = any(t[i] == "~" and is_id(t[i + 1]) and t[i + 2] == "(" for i in range(len(t) - 2))
        return bool(destructor and ({"struct", "class"} & set(t)) and cout)
    if rule == "virtual_dispatch":
        return bool("virtual" in t and "override" in t and "public" in t and cout and ("->" in t or "&" in t))
    if rule == "template_function":
        names = set()
        for i, token in enumerate(t):
            if token == "template" and i + 1 < len(t) and t[i + 1] == "<":
                depth, j = 0, i + 1
                while j < len(t):
                    if t[j] == "<":
                        depth += 1
                    elif t[j] == ">":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                k = j + 1
                while k + 1 < len(t) and t[k + 1] != "(":
                    k += 1
                if k + 1 < len(t) and is_id(t[k]):
                    names.add(t[k])
        calls = sum(1 for i in range(len(t) - 1) if t[i] in names and t[i + 1] == "(")
        return bool(names and calls >= 3 and cout)
    if rule == "lambda_capture":
        for i in range(1, len(t) - 2):
            if t[i] == "[" and t[i - 1] in {"=", ",", "("} and t[i + 1] != "]":
                j = i + 1
                while j < len(t) and t[j] != "]":
                    j += 1
                if j + 1 < len(t) and t[j + 1] in {"(", "{"}:
                    return bool(cout)
        return False
    if rule == "map_set":
        containers = {"map", "unordered_map", "set", "unordered_set"}
        declared = any(t[i] in containers and t[i + 1] == "<" for i in range(len(t) - 1))
        return bool(declared and cout)
    if rule == "integrated_project":
        calls = {t[i] for i in range(len(t) - 1) if is_id(t[i]) and t[i + 1] == "("}
        definitions = {t[i + 1] for i in range(len(t) - 3) if t[i] in {"int", "double", "float", "bool", "string"} and is_id(t[i + 1]) and t[i + 2] == "("}
        return bool(strings and "if" in t and {"for", "while"} & set(t) and calls & definitions and cout and "return" in t)
    return False


def _check_ast(main, rule):
    nodes = list(_walk(main))
    outputs, inputs = _outputs(main), _inputs(main)
    vars_ = [n for n in nodes if n.get("kind") == "VarDecl"]
    used = _used_ids(main)
    input_ids = set().union(*(_ids(n) for n in inputs)) if inputs else set()
    binary_ops = {n.get("opcode") for n in nodes if n.get("kind") in ("BinaryOperator", "CompoundAssignOperator")}
    loops = [n for n in nodes if n.get("kind") in ("ForStmt", "CXXForRangeStmt", "WhileStmt", "DoStmt")]
    if rule == "output_main":
        return bool(outputs)
    if rule == "typed_variables":
        output_ids = set().union(*(_ids(o) for o in outputs)) if outputs else set()
        has_int = any(n.get("type", {}).get("qualType", "").split()[0:1] == ["int"] and n.get("id") in output_ids for n in vars_)
        has_string = any("string" in n.get("type", {}).get("qualType", "") and n.get("id") in output_ids for n in vars_)
        return has_int and has_string
    if rule == "input_output":
        return bool(input_ids and any(input_ids & _ids(o) for o in outputs))
    if rule == "input_arithmetic":
        return bool(input_ids and {"+", "-", "*", "/", "%"} & binary_ops and any(input_ids & _ids(o) and any(op in {x.get("opcode") for x in _walk(o) if x.get("kind") == "BinaryOperator"} for op in ("+", "-", "*", "/", "%")) for o in outputs))
    if rule == "input_branch":
        for node in nodes:
            if node.get("kind") != "IfStmt":
                continue
            children = node.get("inner", [])
            if len(children) < 3 or not (input_ids & _ids(children[0])):
                continue
            if any("cout" in _names(o) for o in _outputs(children[1])) and any("cout" in _names(o) for o in _outputs(children[2])):
                return True
        return False
    if rule == "input_loop":
        return any(input_ids & _ids(loop) and (any(_ids(o) & _ids(loop) for o in outputs) or {"+=", "++", "--"} & {x.get("opcode") for x in _walk(loop) if x.get("kind") in ("BinaryOperator", "CompoundAssignOperator", "UnaryOperator")}) for loop in loops)
    if rule == "function_output":
        candidates = {r.get("name") for o in outputs for r in _referenced(o) if r.get("kind") == "FunctionDecl" and r.get("name") not in ("main", "operator<<")}
        return bool(candidates)
    if rule == "vector_iteration":
        containers = {v.get("id") for v in vars_ if "vector<" in v.get("type", {}).get("qualType", "")}
        return bool(containers and any(containers & _ids(loop) for loop in loops) and outputs)
    if rule == "string_output":
        strings = {v.get("id") for v in vars_ if "string" in v.get("type", {}).get("qualType", "")}
        return bool(strings and any(strings & _ids(o) for o in outputs))
    if rule == "reference_alias":
        refs = [v for v in vars_ if v.get("type", {}).get("qualType", "").rstrip().endswith("&")]
        for v in refs:
            init_ids = set().union(*(_ids(x) for x in v.get("inner", []))) if v.get("inner") else set()
            if not init_ids:
                continue
            alias_uses = [x for x in nodes if x.get("kind") in ("UnaryOperator", "BinaryOperator", "CompoundAssignOperator") and v.get("id") in _ids(x)]
            if alias_uses and any(init_ids & _ids(o) for o in outputs):
                return True
        return False
    if rule == "struct_member":
        return any(any(x.get("kind") == "MemberExpr" and x.get("referencedMemberDecl") for x in _walk(o)) for o in outputs)
    if rule == "class_method":
        return any(x.get("kind") == "CXXMemberCallExpr" for o in outputs for x in _walk(o))
    if rule == "stl_sort":
        sort_calls = [x for x in nodes if x.get("kind") == "CallExpr" and "sort" in _names(x)]
        containers = {v.get("id") for v in vars_ if "vector<" in v.get("type", {}).get("qualType", "")}
        if any(containers & _ids(call) and any(containers & _ids(o) for o in outputs) for call in sort_calls):
            return True
        return any(containers & _ids(call) and any(containers & _ids(loop) and any(any(o.get("kind") == "CXXOperatorCallExpr" and "cout" in _names(o) for o in _walk(loop)) for _ in (0,)) for loop in loops) for call in sort_calls)
    if rule == "file_exception":
        files = [v for v in vars_ if any(stream in v.get("type", {}).get("qualType", "") for stream in ("ifstream", "ofstream", "fstream"))]
        has_try = any(n.get("kind") == "CXXTryStmt" for n in nodes)
        has_catch = any(n.get("kind") == "CXXCatchStmt" for n in nodes)
        file_ids = {v.get("id") for v in files}
        file_use = any(file_ids & _ids(n) for n in nodes if n.get("kind") in ("CXXOperatorCallExpr", "CXXMemberCallExpr"))
        return bool(files and has_try and has_catch and file_use and outputs)
    if rule == "integrated_project":
        has_string = any("string" in v.get("type", {}).get("qualType", "") for v in vars_)
        has_function = bool({r.get("name") for o in outputs for r in _referenced(o) if r.get("kind") == "FunctionDecl" and r.get("name") not in ("main", "operator<<")})
        has_if = any(n.get("kind") == "IfStmt" for n in nodes)
        return has_string and has_function and has_if and loops and outputs
    return False


def check_cpp_concept(source: str, rule: str, language: str = "tr"):
    if rule not in RULES:
        return {"passed": False, "rule": rule, "method": "unavailable", "label": "", "message": "Bu görev için kavram denetimi tanımlanmamış." if language == "tr" else "Для задания не настроена проверка концепции."}
    main = None if rule in TOKEN_ONLY_RULES else _main_ast(source)
    passed = _check_ast(main, rule) if main else _fallback(source, rule)
    return {"passed": bool(passed), "rule": rule, "method": "clang-ast" if main else "structural-fallback", "label": RULES[rule].get(language, RULES[rule]["tr"]), "message": "" if passed else ("Kod derlenip çıktıyı üretse de bu görevde istenen C++ yapısı doğru ve anlamlı biçimde kullanılmıyor." if language == "tr" else "Код компилируется и выдаёт результат, но требуемая конструкция C++ не используется корректно и осмысленно.")}
