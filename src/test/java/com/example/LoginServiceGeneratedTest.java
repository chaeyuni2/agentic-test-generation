package com.example;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertThrows;

class LoginServiceGeneratedTest {

    private final LoginService loginService = new LoginService();

    @Test
    void null_userid_throws_exception() {
        // Verify that passing null as userId throws IllegalArgumentException
        assertThrows(IllegalArgumentException.class, () -> {
            loginService.login(null, "any");
        });
    }

    @Test
    void null_password_throws_exception() {
        // Verify that passing null as password throws IllegalArgumentException
        assertThrows(IllegalArgumentException.class, () -> {
            loginService.login("admin", null);
        });
    }

    @Test
    void locked_user_returns_locked_user() {
        // Verify that userId 'locked' returns 'LOCKED_USER' status
        String result = loginService.login("locked", "any");

        assertThat(result).isEqualTo("LOCKED_USER");
    }

    @Test
    void non_admin_user_returns_user_not_found() {
        // Verify that any userId other than 'admin' or 'locked' returns 'USER_NOT_FOUND'
        String result = loginService.login("user123", "1234");

        assertThat(result).isEqualTo("USER_NOT_FOUND");
    }

    @Test
    void admin_wrong_password_returns_invalid_password() {
        // Verify that userId 'admin' with incorrect password returns 'INVALID_PASSWORD'
        String result = loginService.login("admin", "wrongpass");

        assertThat(result).isEqualTo("INVALID_PASSWORD");
    }

    @Test
    void admin_correct_password_returns_success() {
        // Verify that userId 'admin' with correct password returns 'SUCCESS'
        String result = loginService.login("admin", "1234");

        assertThat(result).isEqualTo("SUCCESS");
    }

    @Test
    void empty_userid_returns_user_not_found() {
        // Verify that empty string userId returns 'USER_NOT_FOUND'
        String result = loginService.login("", "1234");

        assertThat(result).isEqualTo("USER_NOT_FOUND");
    }

    @Test
    void empty_password_for_admin_returns_invalid_password() {
        // Verify that empty password for userId 'admin' returns 'INVALID_PASSWORD'
        String result = loginService.login("admin", "");

        assertThat(result).isEqualTo("INVALID_PASSWORD");
    }
}
