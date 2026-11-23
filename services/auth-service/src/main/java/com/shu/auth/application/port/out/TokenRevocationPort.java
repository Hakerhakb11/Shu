package com.shu.auth.application.port.out;

import java.time.Instant;

public interface TokenRevocationPort {
    void revokeAccessToken(String jti, Instant expiresAt);
}
