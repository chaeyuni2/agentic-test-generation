'''
최근 git diff 기준으로 어떤 Java 파일이 바뀌었고, 그 파일의 몇 번째 줄이 바뀌었는지 추출
'''
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

# 바뀐 파일 1개에 대한 정보
@dataclass
class ChangedFile:
    file_path: str
    changed_line_ranges: list[tuple[int, int]]

# python에서 git diff, git status 같은 Git 명령어 실행
def run_git_command(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Git command failed: git {' '.join(args)}\n"
            f"stdout:\n{exc.stdout}\n"
            f"stderr:\n{exc.stderr}"
        ) from exc

# git diff 결과에서 .java 파일명만 가져오기
def get_changed_java_files(base_ref: str, head_ref: str) -> list[str]:
    output = run_git_command(["diff", "--name-only", base_ref, head_ref])
    files = [line.strip() for line in output.splitlines() if line.strip()]
    return [f for f in files if f.endswith(".java") and Path(f).exists()]

# 변경된 line 정보 추출
def get_changed_line_ranges(file_path: str, base_ref: str, head_ref: str) -> list[tuple[int, int]]:
    diff_text = run_git_command(["diff", "-U0", base_ref, head_ref, "--", file_path])

    changed_ranges: list[tuple[int, int]] = []
    for line in diff_text.splitlines():
        if not line.startswith("@@"):
            continue

        # Example:
        # @@ -40,2 +40,4 @@
        match = re.search(r"\+(\d+)(?:,(\d+))?", line)
        if not match:
            continue

        start_line = int(match.group(1))
        count = int(match.group(2) or "1")

        if count == 0:
            # Pure deletion on new file side: no new lines to inspect
            continue

        end_line = start_line + count - 1
        changed_ranges.append((start_line, end_line))

    return merge_ranges(changed_ranges)

# diff가 잘게 쪼개져 나오는 경우 어떤 메서드와 겹치는 지 판단할 때 단순화하기 위해
def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []

    ranges = sorted(ranges, key=lambda x: x[0])
    merged: list[tuple[int, int]] = [ranges[0]]

    for start, end in ranges[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + 1:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def collect_changed_files(base_ref: str, head_ref: str) -> list[ChangedFile]:
    '''
    함수 오케스트레이션
    
    1. 변경된 .java 파일 목록 추출
    2. 각 파일마다 변경 줄 범위 추출
    3. ChangedFile 객체 리스트로 반환
    '''
    java_files = get_changed_java_files(base_ref, head_ref)
    changed: list[ChangedFile] = []

    for file_path in java_files:
        ranges = get_changed_line_ranges(file_path, base_ref, head_ref)
        if ranges:
            changed.append(ChangedFile(file_path=file_path, changed_line_ranges=ranges))

    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract changed Java files and changed line ranges.")
    parser.add_argument("--base-ref", default="HEAD~1", help="Base git ref to compare from.")
    parser.add_argument("--head-ref", default="HEAD", help="Head git ref to compare to.")
    parser.add_argument(
        "--output",
        default="outputs/changed_files.json",
        help="Path to save JSON output.",
    )
    args = parser.parse_args()

    changed_files = collect_changed_files(args.base_ref, args.head_ref)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "base_ref": args.base_ref,
        "head_ref": args.head_ref,
        "changed_files": [asdict(item) for item in changed_files],
    }

    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved changed file metadata to: {output_path}")


if __name__ == "__main__":
    main()