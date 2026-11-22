package com.shu.auth.application.port.in;

import com.shu.auth.application.dto.*;

public interface AuthUseCase {
    RegisteredUser register(RegistrationCommand command);
    AuthTokens login(LoginCommand command);
    AuthTokens refresh(String refreshToken);
    void logout(String refreshToken, String accessToken);
}
