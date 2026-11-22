package com.shu.auth.application.port.out;

import com.shu.auth.domain.model.User;
import java.time.Instant;

public interface TokenProvider {
    String createAccessToken(User user);
    String createRefreshToken();
    ParsedAccessToken parseAccessToken(String token);
    record ParsedAccessToken(
            String subject,
            String jti,
            Instant expiresAt) {
    }
}
