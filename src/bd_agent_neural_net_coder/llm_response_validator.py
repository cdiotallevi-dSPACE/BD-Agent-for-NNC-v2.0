from __future__ import annotations

import json


def strip_json_wrapper(value: str) -> str:
    text = value.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return text


def detect_truncation(raw: str, metadata: dict, maximum_tokens: int) -> dict:
    text = strip_json_wrapper(raw)
    done_reason = str(metadata.get("done_reason") or "").lower()
    generated = metadata.get("eval_count")
    if done_reason in {"length", "max_tokens", "token_limit"}:
        return {"status": "truncated", "failure_code": "llm_output_truncated", "reason": "runtime_done_reason", "configured_max_output_tokens": maximum_tokens}
    in_string = escaped = False
    depth = 0
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
    incomplete = not text or in_string or depth != 0 or not text.rstrip().endswith("}")
    if incomplete and isinstance(generated, int) and generated >= maximum_tokens:
        return {"status": "truncated", "failure_code": "llm_output_truncated", "reason": "token_limit_with_incomplete_json", "configured_max_output_tokens": maximum_tokens}
    return {"status": "not_confirmed", "failure_code": None}


def parse_json_without_repair(raw: str) -> dict:
    value = json.loads(strip_json_wrapper(raw))
    if not isinstance(value, dict):
        raise json.JSONDecodeError("top-level value must be an object", raw, 0)
    return value
