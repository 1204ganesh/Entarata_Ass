import ast
import re
from app.models import Annotation, Complexity


def analyze_code(language: str, code: str) -> tuple[list[Annotation], Complexity]:
    if language == "python":
        annotations = _analyze_python(code)
    else:
        annotations = _analyze_javascript(code)
    return annotations, _estimate_complexity(code, annotations)


def _analyze_python(code: str) -> list[Annotation]:
    annotations: list[Annotation] = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return _line_scan(code)

    for node in ast.walk(tree):
        line = getattr(node, "lineno", None)
        if not line:
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            annotations.append(
                Annotation(kind="function", line=line, name=node.name, detail="Defines a reusable function.")
            )
        elif isinstance(node, ast.ClassDef):
            annotations.append(
                Annotation(kind="class", line=line, name=node.name, detail="Defines a class with related behavior.")
            )
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            annotations.append(
                Annotation(kind="import", line=line, name="import", detail="Loads external module functionality.")
            )
        elif isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
            annotations.append(
                Annotation(kind="loop", line=line, name="loop", detail="Repeats a block of logic.")
            )
        elif isinstance(node, ast.If):
            annotations.append(
                Annotation(kind="conditional", line=line, name="if", detail="Branches based on a condition.")
            )
        elif isinstance(node, ast.Return):
            annotations.append(
                Annotation(kind="return", line=line, name="return", detail="Produces a value from a function.")
            )
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            annotations.append(
                Annotation(kind="assignment", line=line, name="assignment", detail="Stores or updates a value.")
            )

    return _dedupe_annotations(annotations)


def _analyze_javascript(code: str) -> list[Annotation]:
    annotations: list[Annotation] = []
    function_patterns = [
        re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\("),
        re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"),
        re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?[A-Za-z_$][\w$]*\s*=>"),
    ]

    for index, raw_line in enumerate(code.splitlines(), start=1):
        line = raw_line.strip()
        for pattern in function_patterns:
            match = pattern.search(line)
            if match:
                annotations.append(
                    Annotation(kind="function", line=index, name=match.group(1), detail="Defines a reusable function.")
                )
                break
        if re.search(r"\bclass\s+([A-Za-z_$][\w$]*)", line):
            name = re.search(r"\bclass\s+([A-Za-z_$][\w$]*)", line).group(1)
            annotations.append(Annotation(kind="class", line=index, name=name, detail="Defines a class."))
        if re.search(r"\b(import|require)\b", line):
            annotations.append(Annotation(kind="import", line=index, name="import", detail="Loads external functionality."))
        if re.search(r"\b(for|while)\s*\(", line):
            annotations.append(Annotation(kind="loop", line=index, name="loop", detail="Repeats a block of logic."))
        if re.search(r"\bif\s*\(", line):
            annotations.append(Annotation(kind="conditional", line=index, name="if", detail="Branches based on a condition."))
        if re.search(r"\breturn\b", line):
            annotations.append(Annotation(kind="return", line=index, name="return", detail="Returns a value."))
        if re.search(r"\b(const|let|var)\s+[A-Za-z_$][\w$]*\s*=", line) or re.search(r"[A-Za-z_$][\w$]*\s*=", line):
            annotations.append(Annotation(kind="assignment", line=index, name="assignment", detail="Stores or updates a value."))

    return _dedupe_annotations(annotations)


def _line_scan(code: str) -> list[Annotation]:
    annotations: list[Annotation] = []
    for index, raw_line in enumerate(code.splitlines(), start=1):
        line = raw_line.strip()
        if line.startswith("def "):
            name = line.split("def ", 1)[1].split("(", 1)[0].strip()
            annotations.append(Annotation(kind="function", line=index, name=name, detail="Defines a function."))
        elif line.startswith("class "):
            name = line.split("class ", 1)[1].split("(", 1)[0].split(":", 1)[0].strip()
            annotations.append(Annotation(kind="class", line=index, name=name, detail="Defines a class."))
        elif line.startswith(("for ", "while ")):
            annotations.append(Annotation(kind="loop", line=index, name="loop", detail="Repeats a block of logic."))
        elif line.startswith("if "):
            annotations.append(Annotation(kind="conditional", line=index, name="if", detail="Branches based on a condition."))
        elif line.startswith("return"):
            annotations.append(Annotation(kind="return", line=index, name="return", detail="Returns a value."))
    return _dedupe_annotations(annotations)


def _estimate_complexity(code: str, annotations: list[Annotation]) -> Complexity:
    loop_lines = [item.line for item in annotations if item.kind == "loop"]
    nested_loop_hint = _has_nested_loop(code)
    recursion_hint = _has_recursion_hint(code)

    if recursion_hint:
        return Complexity(
            time="Likely recursive; depends on branching and base case",
            space="O(depth) call stack",
            confidence="low",
            reason="A function appears to call itself, but exact complexity requires more semantic analysis.",
        )

    if nested_loop_hint:
        return Complexity(
            time="O(n^2)",
            space="O(1) to O(n)",
            confidence="medium",
            reason="Nested loops were detected, which often implies quadratic time.",
        )

    if loop_lines:
        return Complexity(
            time="O(n)",
            space="O(1) to O(n)",
            confidence="medium",
            reason="At least one loop was detected; growing collections may increase space usage.",
        )

    return Complexity(
        time="O(1)",
        space="O(1)",
        confidence="medium",
        reason="No loops, recursion, or growing collections were detected.",
    )


def _has_nested_loop(code: str) -> bool:
    loop_stack: list[int] = []
    for raw_line in code.splitlines():
        stripped = raw_line.lstrip()
        indent = len(raw_line) - len(stripped)
        if re.match(r"(for|while)\b", stripped) or re.search(r"\b(for|while)\s*\(", stripped):
            while loop_stack and loop_stack[-1] >= indent:
                loop_stack.pop()
            if loop_stack:
                return True
            loop_stack.append(indent)
    return False


def _has_recursion_hint(code: str) -> bool:
    python_funcs = re.findall(r"\bdef\s+([A-Za-z_]\w*)\s*\(", code)
    js_funcs = re.findall(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", code)
    for name in python_funcs + js_funcs:
        if len(re.findall(rf"\b{name}\s*\(", code)) > 1:
            return True
    return False


def _dedupe_annotations(annotations: list[Annotation]) -> list[Annotation]:
    seen: set[tuple[str, int, str]] = set()
    result: list[Annotation] = []
    for item in sorted(annotations, key=lambda value: (value.line, value.kind, value.name)):
        key = (item.kind, item.line, item.name)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

