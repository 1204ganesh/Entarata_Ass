import json
import os
import textwrap
from typing import Any, Optional

import httpx
from app.models import Annotation, Complexity


SYSTEM_PROMPT = """You are a careful code explainer.
Explain only behavior that is directly visible in the provided snippet.
Do not infer business purpose from names alone.
Do not invent runtime behavior, inputs, outputs, libraries, network calls, database calls, or side effects.

Return strict JSON with exactly these top-level keys:
{
  "explanation": "2 to 4 plain-English sentences",
  "optimizedCode": "string or null",
  "optimizationSummary": "string or null"
}

If behavior cannot be determined from the code, say that in the explanation.
Keep optimizedCode as a plain string, not an object."""


async def explain_with_provider(
    language: str,
    code: str,
    annotations: list[Annotation],
    complexity: Complexity,
    include_optimization: bool,
) -> tuple[dict[str, Any], str]:
    provider = os.getenv("LLM_PROVIDER", "local").lower().strip()

    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        return await _call_openai(language, code, annotations, complexity, include_optimization), "openai"

    if provider == "mistral" and os.getenv("MISTRAL_API_KEY"):
        return await _call_mistral(language, code, annotations, complexity, include_optimization), "mistral"

    return explain_locally(language, code, annotations, complexity, include_optimization), "local"


def explain_locally(
    language: str,
    code: str,
    annotations: list[Annotation],
    complexity: Complexity,
    include_optimization: bool,
) -> dict[str, Any]:
    return _local_response(language, code, annotations, complexity, include_optimization)


async def _call_openai(
    language: str,
    code: str,
    annotations: list[Annotation],
    complexity: Complexity,
    include_optimization: bool,
) -> dict[str, Any]:
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    payload = {
        "model": model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(language, code, annotations, complexity, include_optimization)},
        ],
    }
    headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return _safe_json(content)


async def _call_mistral(
    language: str,
    code: str,
    annotations: list[Annotation],
    complexity: Complexity,
    include_optimization: bool,
) -> dict[str, Any]:
    model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
    payload = {
        "model": model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(language, code, annotations, complexity, include_optimization)},
        ],
    }
    headers = {"Authorization": f"Bearer {os.environ['MISTRAL_API_KEY']}"}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post("https://api.mistral.ai/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return _safe_json(content)


def _user_prompt(
    language: str,
    code: str,
    annotations: list[Annotation],
    complexity: Complexity,
    include_optimization: bool,
) -> str:
    annotation_text = "\n".join(
        f"- line {item.line}: {item.kind} {item.name} ({item.detail})" for item in annotations
    ) or "- no key structures detected"
    optimization_instruction = (
        "Suggest an optimized version only if there is a clear, behavior-preserving improvement. "
        "Otherwise return the original code as optimizedCode and explain that no safe optimization is obvious. "
        "optimizedCode must be a string, not an object."
        if include_optimization
        else "Set optimizedCode and optimizationSummary to null."
    )
    return textwrap.dedent(
        f"""
        Language: {language}
        Static annotations:
        {annotation_text}

        Complexity estimate:
        time={complexity.time}, space={complexity.space}, confidence={complexity.confidence}, reason={complexity.reason}

        {optimization_instruction}

        Return only JSON in this exact shape:
        {{
          "explanation": "2 to 4 plain-English sentences",
          "optimizedCode": "string or null",
          "optimizationSummary": "string or null"
        }}

        Code:
        ```{language}
        {code}
        ```
        """
    ).strip()


def _safe_json(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        first = content.find("{")
        last = content.rfind("}")
        if first == -1 or last == -1:
            raise
        parsed = json.loads(content[first : last + 1])

    explanation = _string_or_explanation(parsed)
    if not explanation:
        raise ValueError("LLM response did not include an explanation.")

    return {
        "explanation": explanation,
        "optimizedCode": _string_or_code(parsed.get("optimizedCode")),
        "optimizationSummary": _string_or_summary(parsed.get("optimizationSummary")),
    }


def _string_or_explanation(parsed: dict[str, Any]) -> str:
    for key in ("explanation", "summary", "description", "plainEnglishExplanation", "plain_english_explanation"):
        value = parsed.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            for nested_key in ("text", "summary", "explanation", "description"):
                nested_value = value.get(nested_key)
                if isinstance(nested_value, str) and nested_value.strip():
                    return nested_value.strip()

    for value in parsed.values():
        if isinstance(value, str) and len(value.strip()) > 20:
            return value.strip()

    return ""


def _string_or_code(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("code", "optimizedCode", "optimized_code"):
            if isinstance(value.get(key), str):
                return value[key]
    return str(value)


def _string_or_summary(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("summary", "text", "optimizationSummary", "reason"):
            if isinstance(value.get(key), str):
                return value[key]
    return str(value)


def _local_response(
    language: str,
    code: str,
    annotations: list[Annotation],
    complexity: Complexity,
    include_optimization: bool,
) -> dict[str, Any]:
    functions = [item.name for item in annotations if item.kind == "function"]
    loops = [item for item in annotations if item.kind == "loop"]
    branches = [item for item in annotations if item.kind == "conditional"]
    returns = [item for item in annotations if item.kind == "return"]

    parts: list[str] = []
    if functions:
        parts.append(f"This {language} snippet defines {len(functions)} function(s): {', '.join(functions[:3])}.")
    else:
        parts.append(f"This {language} snippet runs a short block of code without a detected top-level function.")

    if loops and branches:
        parts.append("It repeats work with a loop and uses conditional logic to choose between paths.")
    elif loops:
        parts.append("It repeats work with a loop, so its behavior depends on the size of the input being iterated.")
    elif branches:
        parts.append("It uses conditional logic to choose between paths.")
    else:
        parts.append("No loop or branch was detected, so the control flow appears straightforward.")

    if returns:
        parts.append("The snippet returns a value from at least one code path.")
    parts.append(f"The estimated complexity is {complexity.time} time and {complexity.space} space.")

    return {
        "explanation": " ".join(parts[:4]),
        "optimizedCode": code if include_optimization else None,
        "optimizationSummary": "No LLM key is configured, so the fallback keeps the original code unchanged."
        if include_optimization
        else None,
    }
