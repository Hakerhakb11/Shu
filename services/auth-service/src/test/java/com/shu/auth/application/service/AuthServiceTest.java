package com.shu.auth.application.service;

import com.shu.auth.application.dto.RegistrationCommand;
import com.shu.auth.application.port.out.PasswordHasher;
import com.shu.auth.application.port.out.TokenProvider;
import com.shu.auth.application.port.out.TokenRevocationPort;
import com.shu.auth.domain.exception.RegistrationException;
import com.shu.auth.domain.model.Role;
import com.shu.auth.domain.model.User;
import com.shu.auth.domain.repository.RefreshSessionRepository;
import com.shu.auth.domain.repository.UserRepository;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class AuthServiceTest {

    @Test
    void registerCreatesClient() {
        UserRepository users = Mockito.mock(UserRepository.class);
        RefreshSessionRepository sessions = Mockito.mock(RefreshSessionRepository.class);
        PasswordHasher passwords = Mockito.mock(PasswordHasher.class);
        TokenProvider tokens = Mockito.mock(TokenProvider.class);
        TokenRevocationPort revocations = Mockito.mock(TokenRevocationPort.class);
        Mockito.when(passwords.hash("secret123")).thenReturn("bcrypt-hash");
        Mockito.when(users.save(Mockito.any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));

        AuthService service = new AuthService(
                users,
                sessions,
                passwords,
                tokens,
                revocations,
                900,
                30);
        var result = service.register(new RegistrationCommand(
                " User@Example.com ",
                "secret123",
                Role.CLIENT));

        assertEquals("user@example.com", result.email());
        assertEquals(Role.CLIENT, result.role());
    }

    @Test
    void registerRejectsExistingEmail() {
        UserRepository users = Mockito.mock(UserRepository.class);
        Mockito.when(users.findByEmail("used@example.com")).thenReturn(Optional.of(
                new User(
                        UUID.randomUUID(),
                        "used@example.com",
                        "hash",
                        Role.CLIENT)));

        AuthService service = new AuthService(
                users,
                Mockito.mock(RefreshSessionRepository.class),
                Mockito.mock(PasswordHasher.class),
                Mockito.mock(TokenProvider.class),
                Mockito.mock(TokenRevocationPort.class),
                900,
                30);

        assertThrows(
                RegistrationException.class,
                () -> service.register(new RegistrationCommand(
                        "used@example.com",
                        "secret123",
                        Role.CLIENT)));
    }
}
