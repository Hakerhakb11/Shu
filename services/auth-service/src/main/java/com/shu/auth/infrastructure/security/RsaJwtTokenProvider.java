package com.shu.auth.infrastructure.security;

import com.shu.auth.application.port.out.TokenProvider;
import com.shu.auth.domain.model.User;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.security.KeyFactory;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.time.Instant;
import java.util.Base64;
import java.util.Date;
import java.util.UUID;

@Component
public class RsaJwtTokenProvider implements TokenProvider {
    private final PrivateKey privateKey;
    private final PublicKey publicKey;
    private final long accessTtlSeconds;

    public RsaJwtTokenProvider(
            @Value("${app.auth.jwt.private-key-pem:}") String privateKeyPem,
            @Value("${app.auth.jwt.public-key-pem:}") String publicKeyPem,
            @Value("${app.auth.access-token-ttl-seconds:900}") long accessTtlSeconds) {
        this.accessTtlSeconds = accessTtlSeconds;
        KeyPair pair;
        if (privateKeyPem == null || privateKeyPem.isBlank()) {
            pair = generateKeyPair();
        } else {
            pair = new KeyPair(parsePublicKey(publicKeyPem), parsePrivateKey(privateKeyPem));
        }
        this.privateKey = pair.getPrivate();
        this.publicKey = pair.getPublic();
    }

    @Override
    public String createAccessToken(User user) {
        Instant now = Instant.now();
        Instant expires = now.plusSeconds(accessTtlSeconds);
        return Jwts.builder()
                .subject(user.id().toString())
                .id(UUID.randomUUID().toString())
                .claim("role", user.role().name())
                .issuedAt(Date.from(now))
                .expiration(Date.from(expires))
                .signWith(privateKey)
                .compact();
    }

    @Override
    public String createRefreshToken() {
        return UUID.randomUUID().toString().replace("-", "") + UUID.randomUUID().toString().replace("-", "");
    }

    @Override
    public ParsedAccessToken parseAccessToken(String token) {
        Claims claims = Jwts.parser().verifyWith(publicKey).build().parseSignedClaims(token).getPayload();
        return new ParsedAccessToken(
                claims.getSubject(),
                claims.getId(),
                claims.getExpiration().toInstant());
    }

    private static KeyPair generateKeyPair() {
        try {
            KeyPairGenerator generator = KeyPairGenerator.getInstance("RSA");
            generator.initialize(2048);
            return generator.generateKeyPair();
        } catch (Exception exception) {
            throw new IllegalStateException("Не удалось создать RSA-ключи", exception);
        }
    }

    private static PrivateKey parsePrivateKey(String pem) {
        try {
            byte[] bytes = decodePem(pem);
            return KeyFactory.getInstance("RSA").generatePrivate(new PKCS8EncodedKeySpec(bytes));
        } catch (Exception exception) {
            throw new IllegalStateException("Некорректный RSA private key", exception);
        }
    }

    private static PublicKey parsePublicKey(String pem) {
        if (pem == null || pem.isBlank()) throw new IllegalStateException("Для private key требуется public-key-pem");
        try {
            byte[] bytes = decodePem(pem);
            return KeyFactory.getInstance("RSA").generatePublic(new X509EncodedKeySpec(bytes));
        } catch (Exception exception) {
            throw new IllegalStateException("Некорректный RSA public key", exception);
        }
    }

    private static byte[] decodePem(String pem) {
        String base64 = pem.replace("-----BEGIN PRIVATE KEY-----", "")
                .replace("-----END PRIVATE KEY-----", "")
                .replace("-----BEGIN PUBLIC KEY-----", "")
                .replace("-----END PUBLIC KEY-----", "")
                .replaceAll("\\s", "");
        return Base64.getDecoder().decode(base64);
    }
}
