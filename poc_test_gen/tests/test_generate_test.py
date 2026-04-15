import json

import generate_tests


def test_sanitize_filename():
    assert generate_tests.sanitize_filename("LoginService.login(10-20)") == "LoginService_login_10-20_"


def test_generate_tests_flow_with_fake_llm(tmp_path, monkeypatch):
    changed_files_json = tmp_path / "changed_files.json"
    java_file = tmp_path / "LoginService.java"

    java_file.write_text(
        """package com.example;

public class LoginService {

    public String login(String userId, String password) {
        return "SUCCESS";
    }
}
""",
        encoding="utf-8"
    )

    changed_files_json.write_text(
        json.dumps(
            {
                "changed_files": [
                    {
                        "file_path": str(java_file),
                        "changed_line_ranges": [[4, 6]]
                    }
                ]
            }
        ),
        encoding="utf-8"
    )

    def fake_generate_test_scenarios(class_name, method_name, code):
        return {
            "class_name": class_name,
            "method_name": method_name,
            "test_cases": [
                {
                    "name": "success_login",
                    "description": "returns success",
                    "inputs": {"userId": "admin", "password": "1234"},
                    "expected": {"result": "SUCCESS"},
                    "priority": "high"
                }
            ]
        }

    monkeypatch.setattr(generate_tests, "generate_test_scenarios", fake_generate_test_scenarios)

    methods = generate_tests.extract_changed_methods(str(changed_files_json))
    assert len(methods) == 1

    output_dir = tmp_path / "test_scenarios"
    output_dir.mkdir()

    method = methods[0]
    scenarios = fake_generate_test_scenarios(method.class_name, method.method_name, method.code)

    output_file = output_dir / "sample.json"
    payload = {
        "source": {
            "file_path": method.file_path,
            "class_name": method.class_name,
            "method_name": method.method_name,
        },
        "generated": scenarios,
    }
    output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    saved = json.loads(output_file.read_text(encoding="utf-8"))
    assert saved["generated"]["method_name"] == "login"
    assert saved["generated"]["test_cases"][0]["name"] == "success_login"