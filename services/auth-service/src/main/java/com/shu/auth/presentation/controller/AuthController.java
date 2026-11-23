package com.shu.auth.presentation.controller;

import com.shu.auth.application.dto.AuthTokens;
import com.shu.auth.application.dto.LoginCommand;
import com.shu.auth.application.dto.RegisteredUser;
import com.shu.auth.application.dto.RegistrationCommand;
import com.shu.auth.application.port.in.AuthUseCase;
import com.shu.auth.presentation.dto.*;
import com.shu.auth.presentation.mapper.AuthPresentationMapper;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/auth")
public class AuthController {
    private final AuthUseCase auth;
    private final boolean cookieSecure;

    public AuthController(AuthUseCase auth,
                          @Value("${app.auth.cookie-secure:false}") boolean cookieSecure) {
        this.auth = auth;
        this.cookieSecure = cookieSecure;
    }

    @PostMapping("/register")
    public ResponseEntity<RegisterResponse> register(@Valid @RequestBody RegisterRequest request) {
        RegisteredUser user = auth.register(new RegistrationCommand(
                request.email(),
                request.password(),
                request.role()));
        return ResponseEntity.status(HttpStatus.CREATED).body(AuthPresentationMapper.toResponse(user));
    }

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@Valid @RequestBody LoginRequest request, HttpServletResponse response) {
        AuthTokens tokens = auth.login(new LoginCommand(request.email(), request.password()));
        response.addHeader(HttpHeaders.SET_COOKIE, refreshCookie(tokens.refreshToken(), tokens.expiresIn()).toString());
        return ResponseEntity.ok(new LoginResponse(
                tokens.accessToken(),
                "Bearer",
                tokens.expiresIn()));
    }

    @PostMapping("/refresh")
    public ResponseEntity<RefreshResponse> refresh(@CookieValue(name = "refreshToken", required = false) String refreshToken,
                                                    HttpServletResponse response) {
        AuthTokens tokens = auth.refresh(refreshToken);
        response.addHeader(HttpHeaders.SET_COOKIE, refreshCookie(tokens.refreshToken(), tokens.expiresIn()).toString());
        return ResponseEntity.ok(new RefreshResponse(
                tokens.accessToken(),
                "Bearer"));
    }

    @PostMapping("/logout")
    public ResponseEntity<Void> logout(@CookieValue(name = "refreshToken", required = false) String refreshToken,
                                       @RequestHeader(name = HttpHeaders.AUTHORIZATION, required = false) String authorization,
                                       HttpServletResponse response) {
        String accessToken = authorization != null && authorization.startsWith("Bearer ")
                ? authorization.substring(7) : null;
        auth.logout(refreshToken, accessToken);
        response.addHeader(HttpHeaders.SET_COOKIE, ResponseCookie.from("refreshToken", "")
                .httpOnly(true).secure(cookieSecure).sameSite("Strict").path("/auth").maxAge(0).build().toString());
        return ResponseEntity.ok().build();
    }

    private ResponseCookie refreshCookie(String value, long expiresIn) {
        return ResponseCookie.from("refreshToken", value)
                .httpOnly(true)
                .secure(cookieSecure)
                .sameSite("Strict")
                .path("/auth")
                .maxAge(30L * 24 * 60 * 60)
                .build();
    }
}
