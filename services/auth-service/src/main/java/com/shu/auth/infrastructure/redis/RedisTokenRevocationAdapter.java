package com.shu.auth.infrastructure.redis;

import com.shu.auth.application.port.out.TokenRevocationPort;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import java.time.Duration;
import java.time.Instant;

@Component
public class RedisTokenRevocationAdapter implements TokenRevocationPort {
    private final StringRedisTemplate redis;

    public RedisTokenRevocationAdapter(StringRedisTemplate redis) { this.redis = redis; }

    @Override
    public void revokeAccessToken(String jti, Instant expiresAt) {
        long seconds = Math.max(1, Duration.between(Instant.now(), expiresAt).getSeconds());
        redis.opsForValue().set("auth:blacklist:" + jti, "revoked", Duration.ofSeconds(seconds));
    }
}
