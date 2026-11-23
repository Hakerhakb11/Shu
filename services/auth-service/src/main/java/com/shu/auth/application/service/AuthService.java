package com.shu.auth.application.service;

import com.shu.auth.application.dto.*;
import com.shu.auth.application.port.in.AuthUseCase;
import com.shu.auth.application.port.out.PasswordHasher;
import com.shu.auth.application.port.out.TokenProvider;
import com.shu.auth.application.port.out.TokenRevocationPort;
import com.shu.auth.domain.exception.AuthenticationException;
import com.shu.auth.domain.exception.RegistrationException;
import com.shu.auth.domain.model.RefreshSession;
import com.shu.auth.domain.model.Role;
import com.shu.auth.domain.model.User;
import com.shu.auth.domain.repository.RefreshSessionRepository;
import com.shu.auth.domain.repository.UserRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.HexFormat;
import java.util.UUID;

@Service
public class AuthService implements AuthUseCase {
    private final UserRepository users;
    private final RefreshSessionRepository sessions;
    private final PasswordHasher passwords;
    private final TokenProvider tokens;
    private final TokenRevocationPort revocations;
    private final long accessTtlSeconds;
    private final long refreshTtlDays;

    public AuthService(UserRepository users, RefreshSessionRepository sessions, PasswordHasher passwords,
            TokenProvider tokens, TokenRevocationPort revocations,
            @Value("${app.auth.access-token-ttl-seconds:900}") long accessTtlSeconds,
            @Value("${app.auth.refresh-token-ttl-days:30}") long refreshTtlDays) {
        this.users = users;
        this.sessions = sessions;
        this.passwords = passwords;
        this.tokens = tokens;
        this.revocations = revocations;
        this.accessTtlSeconds = accessTtlSeconds;
        this.refreshTtlDays = refreshTtlDays;
    }

    @Override
    @Transactional
    public RegisteredUser register(RegistrationCommand command) {
        String email = command.email().trim().toLowerCase();
        if (email.isBlank() || command.password().length() < 6) {
            throw new RegistrationException("Неверные данные регистрации");
        }
        if (command.role() != Role.CLIENT && command.role() != Role.SELLER) {
            throw new RegistrationException("Регистрация доступна только для ролей CLIENT и SELLER");
        }
        if (users.findByEmail(email).isPresent()) {
            throw new RegistrationException("Пользователь с таким email уже существует");
        }
        User user = new User(
                UUID.randomUUID(),
                email,
                passwords.hash(command.password()),
                command.role());
        User saved = users.save(user);
        return new RegisteredUser(
                saved.id(),
                saved.email(),
                saved.role());
    }

    @Override
    @Transactional
    public AuthTokens login(LoginCommand command) {
        String email = command.email().trim().toLowerCase();
        User user = users.findByEmail(email)
                .orElseThrow(() -> new AuthenticationException("Неверный email или пароль"));
        if (!passwords.matches(command.password(), user.passwordHash())) {
            throw new AuthenticationException("Неверный email или пароль");
        }
        return issueTokens(user);
    }

    @Override
    @Transactional
    public AuthTokens refresh(String refreshToken) {
        if (refreshToken == null || refreshToken.isBlank())
            throw new AuthenticationException("Refresh-токен отсутствует");
        String hash = hashRefreshToken(refreshToken);
        RefreshSession session = sessions.findActiveByHash(hash)
                .orElseThrow(() -> new AuthenticationException("Refresh-токен недействителен или истек"));
        if (session.expiresAt().isBefore(Instant.now()))
            throw new AuthenticationException("Refresh-токен недействителен или истек");
        User user = users.findById(session.userId())
                .orElseThrow(() -> new AuthenticationException("Пользователь не найден"));
        sessions.revoke(hash);
        return issueTokens(user);
    }

    @Override
    @Transactional
    public void logout(String refreshToken, String accessToken) {
        if (refreshToken != null && !refreshToken.isBlank())
            sessions.revoke(hashRefreshToken(refreshToken));
        if (accessToken != null && !accessToken.isBlank()) {
            try {
                TokenProvider.ParsedAccessToken parsed = tokens.parseAccessToken(accessToken);
                revocations.revokeAccessToken(parsed.jti(), parsed.expiresAt());
            } catch (RuntimeException ignored) {
                // Невалидный access-токен не должен раскрывать детали.
            }
        }
    }

    private AuthTokens issueTokens(User user) {
        String refreshToken = tokens.createRefreshToken();
        String refreshHash = hashRefreshToken(refreshToken);
        Instant expiresAt = Instant.now().plus(refreshTtlDays, ChronoUnit.DAYS);
        sessions.save(new RefreshSession(
                UUID.randomUUID(),
                user.id(),
                refreshHash,
                expiresAt,
                false));
        return new AuthTokens(
                tokens.createAccessToken(user),
                refreshToken,
                accessTtlSeconds);
    }

    public static String hashRefreshToken(String token) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(token.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception exception) {
            throw new IllegalStateException("Не удалось хэшировать refresh-токен", exception);
        }
    }
}
