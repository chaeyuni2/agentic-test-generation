from __future__ import annotations

import argparse
import json
from pathlib import Path

from extract_changed_methods import extract_changed_methods
from llm_client import generate_test_scenarios


def sanitize_filename(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate JSON test scenarios for changed Java methods.")
    parser.add_argument(
        "--changed-files-json",
        default="outputs/changed_files.json",
        help="Path to changed files JSON.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/test_scenarios",
        help="Directory to save per-method scenario JSON files.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    methods = extract_changed_methods(args.changed_files_json)

    if not methods:
        print("No changed methods found.")
        return

    summary: list[dict] = []

    for method in methods:
        print(
            f"Generating scenarios for "
            f"{method.file_path}::{method.class_name}.{method.method_name} "
            f"({method.start_line}-{method.end_line})"
        )

        scenarios = generate_test_scenarios(
            class_name=method.class_name,
            method_name=method.method_name,
            code=method.code,
        )

        file_stem = sanitize_filename(
            f"{Path(method.file_path).stem}_{method.method_name}_{method.start_line}_{method.end_line}"
        )
        output_path = output_dir / f"{file_stem}.json"

        payload = {
            "source": {
                "file_path": method.file_path,
                "package_name": method.package_name,
                "class_name": method.class_name,
                "method_name": method.method_name,
                "start_line": method.start_line,
                "end_line": method.end_line,
                "signature_line": method.signature_line,
            },
            "generated": scenarios,
        }

        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        summary.append(
            {
                "file_path": method.file_path,
                "class_name": method.class_name,
                "method_name": method.method_name,
                "output_file": str(output_path),
            }
        )

    summary_path = output_dir / "_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved summary to: {summary_path}")


if __name__ == "__main__":
    main()