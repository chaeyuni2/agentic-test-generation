from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def sanitize_java_method_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_가-힣]", "_", value)
    if not value:
        value = "generated_test"
    if value[0].isdigit():
        value = f"test_{value}"
    return value


def parse_method_parameters(signature_line: str) -> list[tuple[str, str]]:
    """
    Example:
      public String login(String userId, String password) {
      -> [("String", "userId"), ("String", "password")]
    """
    match = re.search(r"\((.*)\)", signature_line)
    if not match:
        return []

    params_raw = match.group(1).strip()
    if not params_raw:
        return []

    results: list[tuple[str, str]] = []
    for param in params_raw.split(","):
        p = param.strip()
        parts = p.split()
        if len(parts) >= 2:
            param_name = parts[-1]
            param_type = " ".join(parts[:-1])
            results.append((param_type, param_name))
    return results


def java_literal(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    raise ValueError(f"Unsupported literal type for Java conversion: {type(value)}")


def build_argument_list(signature_line: str, inputs: dict[str, Any]) -> str:
    params = parse_method_parameters(signature_line)
    args: list[str] = []

    for _param_type, param_name in params:
        args.append(java_literal(inputs.get(param_name)))

    return ", ".join(args)


def extract_result_type(signature_line: str) -> str:
    """
    Example:
      public String login(String userId, String password) {
      -> String
    """
    line = signature_line.strip()
    line = line[:-1].strip() if line.endswith("{") else line
    before_paren = line.split("(", 1)[0].strip()
    parts = before_paren.split()
    if len(parts) >= 2:
        return parts[-2]
    return "String"


def junit_assertion_block(signature_line: str, class_name: str, method_name: str, test_case: dict) -> str:
    inputs = test_case.get("inputs", {})
    expected = test_case.get("expected", {})
    args = build_argument_list(signature_line, inputs)

    if "exception" in expected:
        exception_name = expected["exception"]
        return f"""assertThrows({exception_name}.class, () -> {{
            {class_name.lower_first()}.{method_name}({args});
        }});"""

    result_key = "result" if "result" in expected else "return" if "return" in expected else None
    return_type = extract_result_type(signature_line)

    if result_key:
        expected_value = java_literal(expected[result_key])
        return f"""{return_type} result = {class_name.lower_first()}.{method_name}({args});

        assertThat(result).isEqualTo({expected_value});"""

    return f"""// TODO: unsupported expected format
        {class_name.lower_first()}.{method_name}({args});"""


def class_var_name(class_name: str) -> str:
    if not class_name:
        return "target"
    return class_name[0].lower() + class_name[1:]


def build_test_method(signature_line: str, class_name: str, method_name: str, test_case: dict) -> str:
    raw_name = test_case.get("name", "generated_test")
    description = test_case.get("description", "")
    test_name = sanitize_java_method_name(raw_name)

    inputs = test_case.get("inputs", {})
    expected = test_case.get("expected", {})
    args = build_argument_list(signature_line, inputs)
    target_var = class_var_name(class_name)

    if "exception" in expected:
        exception_name = expected["exception"]
        body = f"""assertThrows({exception_name}.class, () -> {{
            {target_var}.{method_name}({args});
        }});"""
    else:
        result_key = "result" if "result" in expected else "return" if "return" in expected else None
        return_type = extract_result_type(signature_line)
        if result_key:
            expected_value = java_literal(expected[result_key])
            body = f"""{return_type} result = {target_var}.{method_name}({args});

        assertThat(result).isEqualTo({expected_value});"""
        else:
            body = f"""// TODO: unsupported expected format
        {target_var}.{method_name}({args});"""

    return f"""    @Test
    void {test_name}() {{
        // {description}
        {body}
    }}"""


def build_java_test_class(data: dict) -> str:
    source = data.get("source", {})
    generated = data.get("generated", {})

    package_name = source.get("package_name")
    class_name = source.get("class_name", "UnknownClass")
    method_name = source.get("method_name", "unknownMethod")
    signature_line = source.get("signature_line", "")
    test_cases = generated.get("test_cases", [])

    package_block = f"package {package_name};\n\n" if package_name else ""
    imports_block = """import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertThrows;
"""

    test_class_name = f"{class_name}GeneratedTest"
    target_var = class_var_name(class_name)

    methods_block = "\n\n".join(
        build_test_method(signature_line, class_name, method_name, tc) for tc in test_cases
    )

    return f"""{package_block}{imports_block}
class {test_class_name} {{

    private final {class_name} {target_var} = new {class_name}();

{methods_block}
}}
"""


def package_to_path(package_name: str | None) -> Path:
    if not package_name:
        return Path()
    return Path(*package_name.split("."))


def convert_json_to_junit(json_file: Path, output_root: Path) -> Path:
    data = json.loads(json_file.read_text(encoding="utf-8"))

    source = data.get("source", {})
    package_name = source.get("package_name")
    class_name = source.get("class_name", "UnknownClass")

    output_dir = output_root / package_to_path(package_name)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{class_name}GeneratedTest.java"
    output_file.write_text(build_java_test_class(data), encoding="utf-8")

    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate JUnit5 Java test files from scenario JSON.")
    parser.add_argument(
        "--input-dir",
        default="outputs/test_scenarios",
        help="Directory containing scenario JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        default="src/test/java",
        help="Directory to save generated JUnit test files.",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_root = Path(args.output_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    json_files = [p for p in input_dir.glob("*.json") if p.name != "_summary.json"]

    if not json_files:
        print("No scenario JSON files found.")
        return

    generated_files: list[str] = []

    for json_file in json_files:
        output_file = convert_json_to_junit(json_file, output_root)
        generated_files.append(str(output_file))
        print(f"Generated JUnit test file: {output_file}")

    summary_path = Path("outputs/generated_junit_summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps({"generated_junit_files": generated_files}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved JUnit generation summary to: {summary_path}")


if __name__ == "__main__":
    main()