from __future__ import annotations

import argparse
import json
import pprint
from pathlib import Path


def sanitize_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in value)


def format_python_value(value, indent: int = 4) -> str:
    return pprint.pformat(value, width=100, sort_dicts=False)


def build_assertions(expected: dict, response_var: str = "response") -> str:
    if not expected:
        return f"    assert {response_var} is not None"

    if "exception" in expected:
        return "\n".join([
            "    assert status_code == 422",
            f"    assert 'detail' in {response_var}",
        ])

    lines: list[str] = []

    normalized_expected = {}
    for key, value in expected.items():
        normalized_key = "result" if key == "return" else key
        normalized_expected[normalized_key] = value

    for key, value in normalized_expected.items():
        if isinstance(value, (dict, list)):
            expected_py = format_python_value(value, indent=8)
            lines.append(f"    assert {response_var}[{key!r}] == {expected_py}")
        else:
            lines.append(f"    assert {response_var}[{key!r}] == {value!r}")

    return "\n".join(lines)


def build_test_function(test_case: dict) -> str:
    raw_name = test_case.get("name", "unnamed_test")
    test_name = sanitize_name(raw_name)
    if not test_name.startswith("test_"):
        test_name = f"test_{test_name}"

    description = test_case.get("description", "")
    inputs = test_case.get("inputs", {})
    expected = test_case.get("expected", {})
    priority = test_case.get("priority", "medium")

    payload_code = format_python_value(inputs, indent=8)
    assertions = build_assertions(expected)

    return f'''def {test_name}():
    """
    {description}
    priority: {priority}
    """
    payload = {payload_code}

    raw_response = requests.post(
        "http://localhost:8000/login",
        json=payload,
        timeout=10,
    )
    status_code = raw_response.status_code
    response = raw_response.json()

{assertions}
'''


def build_pytest_file_content(source: dict, generated: dict) -> str:
    class_name = generated.get("class_name", source.get("class_name", "UnknownClass"))
    method_name = generated.get("method_name", source.get("method_name", "unknown_method"))
    test_cases = generated.get("test_cases", [])

    function_blocks = "\n\n".join(build_test_function(tc) for tc in test_cases)

    return f'''"""
Auto-generated pytest skeleton from LLM test scenario JSON.

Source:
- file_path: {source.get("file_path")}
- class_name: {class_name}
- method_name: {method_name}
"""

import pytest
import requests


{function_blocks}
'''


def convert_json_to_pytest(json_file: Path, output_dir: Path) -> Path:
    data = json.loads(json_file.read_text(encoding="utf-8"))

    source = data.get("source", {})
    generated = data.get("generated", {})

    class_name = generated.get("class_name", source.get("class_name", "UnknownClass"))
    method_name = generated.get("method_name", source.get("method_name", "unknown_method"))

    file_name = f"test_{sanitize_name(class_name)}_{sanitize_name(method_name)}.py"
    output_path = output_dir / file_name

    content = build_pytest_file_content(source=source, generated=generated)
    output_path.write_text(content, encoding="utf-8")

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate pytest files from LLM scenario JSON files.")
    parser.add_argument(
        "--input-dir",
        default="outputs/test_scenarios",
        help="Directory containing scenario JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/generated_pytests",
        help="Directory to save generated pytest files.",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    json_files = [
        p for p in input_dir.glob("*.json")
        if p.name != "_summary.json"
    ]

    if not json_files:
        print("No scenario JSON files found.")
        return

    generated_files: list[str] = []

    for json_file in json_files:
        output_path = convert_json_to_pytest(json_file=json_file, output_dir=output_dir)
        generated_files.append(str(output_path))
        print(f"Generated pytest file: {output_path}")

    summary_path = output_dir / "_summary.json"
    summary_path.write_text(
        json.dumps({"generated_pytest_files": generated_files}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved pytest generation summary to: {summary_path}")


if __name__ == "__main__":
    main()