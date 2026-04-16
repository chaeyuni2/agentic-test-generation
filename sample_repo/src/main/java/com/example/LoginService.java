package com.example;
// trigger github actions test
public class LoginService {

    public String login(String userId, String password) {
        if (userId == null || password == null) {
            throw new IllegalArgumentException("userId/password is required");
        }

        if ("locked".equals(userId)) {
            return "LOCKED_USER";
        }

        if (!"admin".equals(userId)) {
            return "USER_NOT_FOUND";
        }

        if (!"1234".equals(password)) {
            return "INVALID_PASSWORD";
        }

        return "SUCCESS";
    }

    public String healthCheck() {
        return "OK";
    }
}