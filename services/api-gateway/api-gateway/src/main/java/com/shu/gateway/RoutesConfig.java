package com.shu.gateway;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Маршрутизация по префиксу пути. Путь передаётся сервису без изменений:
 * в контрактах пути уже содержат префикс (/auth/..., /catalog/..., /cart/...).
 */
@Configuration
public class RoutesConfig {

    @Bean
    RouteLocator routes(RouteLocatorBuilder builder,
                        @Value("${services.auth-url}") String authUrl,
                        @Value("${services.catalog-url}") String catalogUrl,
                        @Value("${services.cart-url}") String cartUrl) {
        return builder.routes()
                .route("auth",    r -> r.path("/auth/**").uri(authUrl))
                .route("catalog", r -> r.path("/catalog/**").uri(catalogUrl))
                .route("cart",    r -> r.path("/cart/**").uri(cartUrl))
                .build();
    }
}
