import type {
  AuthUser,
  BookCreatePayload,
  BookDetail,
  BookUpdatePayload,
  CartItemQuantityResponse,
  CartResponse,
  Category,
  LoginResponse,
  ModerationTargetStatus,
  PaginatedBooks,
  RegisterResponse,
  RegisterRole,
  Role,
} from '../types';

export class ApiError extends Error {
  status: number;
  errorCode?: string;

  constructor(message: string, status: number, errorCode?: string) {
    super(message);
    this.status = status;
    this.errorCode = errorCode;
  }
}

let currentAccessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;
let tokenListener: ((token: string | null) => void) | null = null;

export function setAccessToken(token: string | null): void {
  currentAccessToken = token;
  tokenListener?.(token);
}

export function getAccessToken(): string | null {
  return currentAccessToken;
}

export function subscribeTokenChanges(listener: (token: string | null) => void): () => void {
  tokenListener = listener;
  return () => {
    tokenListener = null;
  };
}

export function decodeUserFromJwt(token: string, email?: string): AuthUser | null {
  try {
    const [, payloadPart] = token.split('.');
    if (!payloadPart) return null;
    const base64 = payloadPart.replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=');
    const json = decodeURIComponent(
      atob(padded)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    const claims = JSON.parse(json) as { sub?: string; role?: string | string[] };
    if (!claims.sub) return null;
    const rawRole = Array.isArray(claims.role) ? claims.role[0] : claims.role;
    const role = (rawRole || 'CLIENT') as Role;
    return { id: String(claims.sub), role, email };
  } catch {
    return null;
  }
}

async function parseErrorMessage(response: Response): Promise<{ message: string; code?: string }> {
  try {
    const data = await response.json();
    if (typeof data?.detail === 'string') {
      return { message: data.detail, code: data.error_code };
    }
    if (Array.isArray(data?.detail) && data.detail.length > 0) {
      const first = data.detail[0];
      const field = Array.isArray(first?.loc) ? first.loc.join('.') : '';
      return { message: field ? `${field}: ${first.msg}` : String(first.msg) };
    }
    if (typeof data?.message === 'string') {
      return { message: data.message, code: data.code || data.error_code };
    }
  } catch {
    // Тело ответа не является JSON
  }
  return { message: `Ошибка сервера (HTTP ${response.status})` };
}

export async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const response = await fetch('/auth/refresh', {
        method: 'POST',
        credentials: 'include',
      });
      if (!response.ok) {
        setAccessToken(null);
        return null;
      }
      const data = (await response.json()) as LoginResponse;
      if (data.accessToken) {
        setAccessToken(data.accessToken);
        return data.accessToken;
      }
      setAccessToken(null);
      return null;
    } catch {
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
  skipRefresh?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { skipAuth = false, skipRefresh = false, headers: rawHeaders, ...rest } = options;

  const buildHeaders = (token: string | null): Headers => {
    const headers = new Headers(rawHeaders);
    if (rest.body && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
    if (!skipAuth && token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  };

  let response = await fetch(path, {
    ...rest,
    headers: buildHeaders(currentAccessToken),
    credentials: 'include',
  });

  if (response.status === 401 && !skipRefresh && !path.startsWith('/auth/')) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      response = await fetch(path, {
        ...rest,
        headers: buildHeaders(newToken),
        credentials: 'include',
      });
    }
  }

  if (!response.ok) {
    const { message, code } = await parseErrorMessage(response);
    throw new ApiError(message, response.status, code);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

export const authApi = {
  register(email: string, password: string, role: RegisterRole): Promise<RegisterResponse> {
    return request<RegisterResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, role }),
      skipAuth: true,
      skipRefresh: true,
    });
  },

  login(email: string, password: string): Promise<LoginResponse> {
    return request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
      skipAuth: true,
      skipRefresh: true,
    });
  },

  logout(): Promise<void> {
    return request<void>('/auth/logout', {
      method: 'POST',
      skipRefresh: true,
    });
  },
};

export interface CatalogQuery {
  page?: number;
  size?: number;
  category_id?: number;
  min_price?: number;
  max_price?: number;
  search?: string;
}

export const catalogApi = {
  listItems(query: CatalogQuery = {}): Promise<PaginatedBooks> {
    const params = new URLSearchParams();
    if (query.page) params.set('page', String(query.page));
    if (query.size) params.set('size', String(query.size));
    if (query.category_id) params.set('category_id', String(query.category_id));
    if (query.min_price !== undefined) params.set('min_price', String(query.min_price));
    if (query.max_price !== undefined) params.set('max_price', String(query.max_price));
    if (query.search?.trim()) params.set('search', query.search.trim());
    const qs = params.toString();
    return request<PaginatedBooks>(`/catalog/items${qs ? `?${qs}` : ''}`, { skipAuth: true });
  },

  getItem(itemId: number): Promise<BookDetail> {
    return request<BookDetail>(`/catalog/items/${itemId}`, { skipAuth: true });
  },

  createItem(payload: BookCreatePayload): Promise<BookDetail> {
    return request<BookDetail>('/catalog/items', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  updateItem(itemId: number, payload: BookUpdatePayload): Promise<BookDetail> {
    return request<BookDetail>(`/catalog/items/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  deleteItem(itemId: number): Promise<void> {
    return request<void>(`/catalog/items/${itemId}`, { method: 'DELETE' });
  },

  listCategories(): Promise<Category[]> {
    return request<Category[]>('/catalog/categories', { skipAuth: true });
  },

  createCategory(payload: { name: string; slug: string; description?: string | null }): Promise<Category> {
    return request<Category>('/catalog/categories', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  listModerationItems(page = 1, size = 20): Promise<PaginatedBooks> {
    return request<PaginatedBooks>(`/catalog/moderation/items?page=${page}&size=${size}`);
  },

  updateItemStatus(itemId: number, status: ModerationTargetStatus): Promise<BookDetail> {
    return request<BookDetail>(`/catalog/items/${itemId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },
};

export const cartApi = {
  getCart(): Promise<CartResponse> {
    return request<CartResponse>('/cart');
  },

  addItem(item_id: number, quantity = 1): Promise<CartItemQuantityResponse> {
    return request<CartItemQuantityResponse>('/cart/items', {
      method: 'POST',
      body: JSON.stringify({ item_id, quantity }),
    });
  },

  removeItem(itemId: number, quantity?: number): Promise<CartItemQuantityResponse> {
    const qs = quantity ? `?quantity=${quantity}` : '';
    return request<CartItemQuantityResponse>(`/cart/items/${itemId}${qs}`, {
      method: 'DELETE',
    });
  },

  clearCart(): Promise<void> {
    return request<void>('/cart', { method: 'DELETE' });
  },
};