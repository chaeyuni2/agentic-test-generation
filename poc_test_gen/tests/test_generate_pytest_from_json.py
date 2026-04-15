import json
from pathlib import Path

from generate_pytest_from_json import (
    build_assertions,
    build_test_function,
    convert_json_to_pytest,
)


def test_build_assertions_simple():
    expected = {
        "result": "SUCCESS",
        "status": 200,
    }

    code = build_assertions(expected)

    assert "assert response['result'] == 'SUCCESS'" in code
    assert "assert response['status'] == 200" in code


def test_build_test_function_contains_test_name_and_payload():
    test_case = {
        "name": "login_success",
        "description": "Valid credentials return success",
        "inputs": {
            "userId": "admin",
            "password": "1234",
        },
        "expected": {
            "result": "SUCCESS",
        },
        "priority": "high",
    }

    function_code = build_test_function(test_case)

    assert "def test_login_success():" in function_code
    assert '"userId": "admin"' in function_code
    assert '"password": "1234"' in function_code
    assert "assert response['result'] == 'SUCCESS'" in function_code


def test_convert_json_to_pytest(tmp_path):
    scenario = {
        "source": {
            "file_path": "src/main/java/com/example/LoginService.java",
            "class_name": "LoginService",
            "method_name": "login",
        },
        "generated": {
            "class_name": "LoginService",
            "method_name": "login",
            "test_cases": [
                {
                    "name": "login_success",
                    "description": "Valid credentials return SUCCESS",
                    "inputs": {
                        "userId": "admin",
                        "password": "1234",
                    },
                    "expected": {
                        "result": "SUCCESS",
                    },
                    "priority": "high",
                }
            ],
        },
    }

    input_file = tmp_path / "LoginService_login.json"
    input_file.write_text(json.dumps(scenario, indent=2), encoding="utf-8")

    output_dir = tmp_path / "generated_tests"
    output_dir.mkdir()

    output_file = convert_json_to_pytest(input_file, output_dir)

    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8")
    assert "def test_login_success():" in content
    assert '"userId": "admin"' in content
    assert "assert response['result'] == 'SUCCESS'" in content