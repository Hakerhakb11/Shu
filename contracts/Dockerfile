FROM swaggerapi/swagger-ui:v5.18.2

LABEL maintainer="Shu Team"
LABEL description="Interactive Swagger UI and static contracts server for Shu microservices"

# Copy all OpenAPI specs and event schemas into web root
COPY . /usr/share/nginx/html/contracts/

# Multi-spec dropdown configuration
ENV URLS="[ \
  { \"url\": \"/contracts/catalog/openapi.yaml\", \"name\": \"Catalog Service API\" }, \
  { \"url\": \"/contracts/auth/openapi.yaml\", \"name\": \"Auth Service API\" }, \
  { \"url\": \"/contracts/cart/openapi.yaml\", \"name\": \"Cart Service API\" } \
]"

ENV URLS_PRIMARY_NAME="Catalog Service API"
ENV DEEP_LINKING="true"
ENV DISPLAY_REQUEST_DURATION="true"
ENV DOC_EXPANSION="list"

EXPOSE 8080
