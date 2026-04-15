from llm_client import build_prompt


def test_build_prompt_contains_method_info():
    code = 'public String login(String userId, String password) { return "SUCCESS"; }'

    prompt = build_prompt(
        class_name="LoginService",
        method_name="login",
        code=code,
    )

    assert "LoginService" in prompt
    assert "login" in prompt
    assert code in prompt
    assert "Return ONLY valid JSON" in prompt
    assert '"class_name": "LoginService"' in prompt
    assert '"method_name": "login"' in prompt


def test_build_prompt_uses_unknown_class_when_class_name_is_none():
    prompt = build_prompt(
        class_name=None,
        method_name="healthCheck",
        code='public String healthCheck() { return "OK"; }',
    )

    assert "UnknownClass" in prompt
    assert "healthCheck" in prompt