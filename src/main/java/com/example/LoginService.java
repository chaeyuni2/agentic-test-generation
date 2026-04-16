package com.example;

public class LoginService {

    public String login(String userId, String password) {
        if (userId == null || password == null) {
            throw new IllegalArgumentException("userId/password is required");
        }

        if (userId.isBlank() || password.isBlank()) {
            return "EMPTY_INPUT";
        }

        if ("locked".equals(userId)) {
            return "LOCKED_USER";
        }

        if (!"admin".equals(userId)) {
            return "USER_NOT_FOUND";
        }

        if (password.length() < 4) {
            return "WEAK_PASSWORD";
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