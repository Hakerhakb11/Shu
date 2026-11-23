export type Role = 'CLIENT' | 'SELLER' | 'MODERATOR' | 'COURIER' | 'ADMIN';
export type RegisterRole = 'CLIENT' | 'SELLER';
export type BookStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'BLOCKED';
export type ModerationTargetStatus = 'APPROVED' | 'REJECTED' | 'BLOCKED';
export type UnavailableReason =
  | 'DELETED'
  | 'NOT_APPROVED'
  | 'OUT_OF_STOCK'
  | 'INSUFFICIENT_STOCK';

export interface AuthUser {
  id: string;
  role: Role;
  email?: string;
}

export interface RegisterResponse {
  id: string;
  email: string;
  role: Role;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  expiresIn?: number;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
}

export interface Characteristic {
  id?: number | null;
  name: string;
  value: string;
}

export interface BookListItem {
  id: number;
  title: string;
  author: string;
  price: number;
  category_id: number;
  seller_id: string;
  status: BookStatus;
  image_url: string | null;
  stock: number;
}

export interface BookDetail extends BookListItem {
  description: string;
  characteristics: Characteristic[];
  category: Category | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PaginatedBooks {
  items: BookListItem[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface BookCreatePayload {
  title: string;
  author: string;
  description: string;
  price: number;
  category_id: number;
  stock: number;
  image_url: string | null;
  characteristics: { name: string; value: string }[];
}

export type BookUpdatePayload = Partial<BookCreatePayload>;

export interface CartItem {
  item_id: number;
  quantity: number;
  available: boolean;
  unavailable_reason: UnavailableReason | null;
  message: string | null;
  title: string | null;
  author: string | null;
  price: number | null;
  stock: number | null;
  image_url: string | null;
  line_total: number;
}

export interface CartResponse {
  user_id: string;
  items: CartItem[];
  total_price: number;
  has_unavailable_items: boolean;
}

export interface CartItemQuantityResponse {
  item_id: number;
  quantity: number;
}