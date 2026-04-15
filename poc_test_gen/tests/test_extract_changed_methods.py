import json

from extract_changed_methods import extract_methods_from_java, extract_changed_methods


def test_extract_methods_from_java(tmp_path):
    java_code = """package com.example;

public class LoginService {

    public String login(String userId, String password) {
        if (userId == null || password == null) {
            throw new IllegalArgumentException("userId/password is required");
        }
        return "SUCCESS";
    }

    public String healthCheck() {
        return "OK";
    }
}
"""
    file_path = tmp_path / "LoginService.java"
    file_path.write_text(java_code, encoding="utf-8")

    methods = extract_methods_from_java(str(file_path))

    assert len(methods) == 2
    assert methods[0].method_name == "login"
    assert methods[1].method_name == "healthCheck"


def test_extract_changed_methods(tmp_path):
    java_code = """package com.example;

public class LoginService {

    public String login(String userId, String password) {
        if (userId == null || password == null) {
            throw new IllegalArgumentException("userId/password is required");
        }
        return "SUCCESS";
    }

    public String healthCheck() {
        return "OK";
    }
}
"""
    file_path = tmp_path / "LoginService.java"
    file_path.write_text(java_code, encoding="utf-8")

    changed_files_json = tmp_path / "changed_files.json"
    changed_files_json.write_text(
        json.dumps(
            {
                "changed_files": [
                    {
                        "file_path": str(file_path),
                        "changed_line_ranges": [[4, 7]]
                    }
                ]
            }
        ),
        encoding="utf-8"
    )

    methods = extract_changed_methods(str(changed_files_json))

    assert len(methods) == 1
    assert methods[0].method_name == "login"
    assert "public String login" in methods[0].code