'''
변경된 줄이 포함된 Java 메서드 전체 추출
'''
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

# Java 메서드 선언을 찾기 위한 정규식 -> PoC용
METHOD_DECLARATION_RE = re.compile(
    r"""
    ^\s*
    (?:
        public|protected|private
    )?
    \s*
    (?:
        static\s+
    )?
    (?:
        final\s+
    )?
    (?:
        synchronized\s+
    )?
    (?:
        abstract\s+
    )?
    (?:
        native\s+
    )?
    [\w\<\>\[\],\s?\.]+      # return type
    \s+
    (?P<name>[A-Za-z_]\w*)   # method name
    \s*
    \(
        [^;{}]*              # params
    \)
    \s*
    (?:
        throws\s+[^{]+
    )?
    \{
    \s*$
    """,
    re.VERBOSE,
)


CLASS_RE = re.compile(r"\bclass\s+([A-Za-z_]\w*)\b")
PACKAGE_RE = re.compile(r"^\s*package\s+([\w\.]+)\s*;", re.MULTILINE)


@dataclass
class JavaMethod:
    file_path: str
    package_name: str | None
    class_name: str | None
    method_name: str
    start_line: int
    end_line: int
    signature_line: str
    code: str


def load_changed_files(json_path: str) -> list[dict]:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    return data.get("changed_files", [])


def find_package_name(content: str) -> str | None:
    match = PACKAGE_RE.search(content)
    return match.group(1) if match else None


def find_class_name(lines: list[str]) -> str | None:
    for line in lines:
        match = CLASS_RE.search(line)
        if match:
            return match.group(1)
    return None

# 한 줄에 있는 '{'와 '}'의 개수 추출 (메서드 범위 추적)
def count_braces(line: str) -> tuple[int, int]:
    open_count = line.count("{")
    close_count = line.count("}")
    return open_count, close_count


def extract_methods_from_java(file_path: str) -> list[JavaMethod]:
    '''
    중괄호 균형으로 메서드 블록 범위 찾는 방식

    1. Java 파일을 줄 단위로 읽음
    2. 메서드 선언처럼 보이는 줄을 찾음
    3. 그 줄부터 시작해서 { } 개수를 추적
    4. 균형이 0이 되면 메서드 끝이라고 판단
    5. 그 범위를 코드로 저장
    '''
    path = Path(file_path)
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    package_name = find_package_name(content)
    class_name = find_class_name(lines)

    methods: list[JavaMethod] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip annotations above methods, but allow them to be included in method block later.
        if METHOD_DECLARATION_RE.match(line):
            method_name = METHOD_DECLARATION_RE.match(line).group("name")  # type: ignore[union-attr]
            start_idx = i
            brace_balance = 0
            started = False

            while i < len(lines):
                open_count, close_count = count_braces(lines[i])
                brace_balance += open_count
                brace_balance -= close_count

                if open_count > 0:
                    started = True

                if started and brace_balance == 0:
                    end_idx = i
                    code = "\n".join(lines[start_idx:end_idx + 1])
                    methods.append(
                        JavaMethod(
                            file_path=file_path,
                            package_name=package_name,
                            class_name=class_name,
                            method_name=method_name,
                            start_line=start_idx + 1,
                            end_line=end_idx + 1,
                            signature_line=lines[start_idx].strip(),
                            code=code,
                        )
                    )
                    break
                i += 1

        i += 1

    return methods

# 메서드 범위와 변경 줄 범위가 겹치는 지 확인
def overlaps(method_start: int, method_end: int, changed_ranges: Iterable[tuple[int, int]]) -> bool:
    for start, end in changed_ranges:
        if not (method_end < start or method_start > end):
            return True
    return False

# 수정된 메서드 목록 추출
def extract_changed_methods(changed_files_json: str) -> list[JavaMethod]:
    changed_files = load_changed_files(changed_files_json)
    matched_methods: list[JavaMethod] = []

    for item in changed_files:
        file_path = item["file_path"]
        changed_ranges = [tuple(r) for r in item["changed_line_ranges"]]

        methods = extract_methods_from_java(file_path)
        for method in methods:
            if overlaps(method.start_line, method.end_line, changed_ranges):
                matched_methods.append(method)

    return matched_methods


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract changed Java methods from changed files JSON.")
    parser.add_argument(
        "--changed-files-json",
        default="outputs/changed_files.json",
        help="Path to changed files JSON.",
    )
    parser.add_argument(
        "--output",
        default="outputs/changed_methods.json",
        help="Path to save extracted changed methods.",
    )
    args = parser.parse_args()

    methods = extract_changed_methods(args.changed_files_json)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "methods": [asdict(m) for m in methods],
    }

    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved changed methods to: {output_path}")


if __name__ == "__main__":
    main()