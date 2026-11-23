import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { ApiError, cartApi, catalogApi } from '../api/client';
import { BookModal } from '../components/BookModal';
import { useAuth } from '../context/AuthContext';
import type { Category, PaginatedBooks } from '../types';

interface CatalogPageProps {
  onCartChanged: () => void;
  onRequireAuth: () => void;
}

export function CatalogPage({ onCartChanged, onRequireAuth }: CatalogPageProps) {
  const { user } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [data, setData] = useState<PaginatedBooks | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const [search, setSearch] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [page, setPage] = useState(1);

  const [selectedBookId, setSelectedBookId] = useState<number | null>(null);

  const loadBooks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await catalogApi.listItems({
        page,
        size: 12,
        search: search || undefined,
        category_id: categoryId ? Number(categoryId) : undefined,
        min_price: minPrice ? Number(minPrice) : undefined,
        max_price: maxPrice ? Number(maxPrice) : undefined,
      });
      setData(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось загрузить каталог');
    } finally {
      setLoading(false);
    }
  }, [page, search, categoryId, minPrice, maxPrice]);

  useEffect(() => {
    catalogApi.listCategories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    loadBooks();
  }, [loadBooks]);

  const handleFilterSubmit = (e: FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadBooks();
  };

  const handleResetFilters = () => {
    setSearch('');
    setCategoryId('');
    setMinPrice('');
    setMaxPrice('');
    setPage(1);
  };

  const handleAddToCart = async (bookId: number) => {
    if (!user) {
      onRequireAuth();
      return;
    }
    try {
      await cartApi.addItem(bookId, 1);
      onCartChanged();
      setToast('Книга добавлена в корзину');
      setTimeout(() => setToast(null), 2500);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось добавить товар в корзину');
    }
  };

  return (
    <section>
      <div className="page-header">
        <h1>Каталог книг</h1>
        {data && <span className="muted">Найдено: {data.total}</span>}
      </div>

      <form className="card filters-bar" onSubmit={handleFilterSubmit}>
        <input
          type="search"
          placeholder="Поиск по названию или автору..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <select
          value={categoryId}
          onChange={(e) => {
            setCategoryId(e.target.value);
            setPage(1);
          }}
        >
          <option value="">Все категории</option>
          {categories.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.name}
            </option>
          ))}
        </select>
        <input
          type="number"
          min={0}
          placeholder="Цена от"
          value={minPrice}
          onChange={(e) => {
            setMinPrice(e.target.value);
            setPage(1);
          }}
        />
        <input
          type="number"
          min={0}
          placeholder="Цена до"
          value={maxPrice}
          onChange={(e) => {
            setMaxPrice(e.target.value);
            setPage(1);
          }}
        />
        <button type="button" className="btn btn-secondary" onClick={handleResetFilters}>
          Сбросить
        </button>
      </form>

      {toast && <div className="alert alert-success">{toast}</div>}
      {error && <div className="alert alert-error">{error}</div>}
      {loading && <p className="muted">Загрузка книг...</p>}

      {!loading && data && data.items.length === 0 && (
        <div className="card empty-state">
          <p>Книг по заданным фильтрам пока нет.</p>
        </div>
      )}

      {!loading && data && data.items.length > 0 && (
        <>
          <div className="book-grid">
            {data.items.map((book) => (
              <article key={book.id} className="card book-card">
                <div className="book-cover" onClick={() => setSelectedBookId(book.id)}>
                  {book.image_url ? (
                    <img src={book.image_url} alt={book.title} />
                  ) : (
                    <div className="cover-placeholder">Нет обложки</div>
                  )}
                </div>

                <div className="book-body">
                  <h3 className="book-title" onClick={() => setSelectedBookId(book.id)}>
                    {book.title}
                  </h3>
                  <p className="book-author">{book.author}</p>
                  <div className="book-meta">
                    <span className="book-price">{book.price.toFixed(2)} ₽</span>
                    <span className="muted">Остаток: {book.stock}</span>
                  </div>
                </div>

                <div className="book-actions">
                  <button
                    className="btn btn-secondary"
                    onClick={() => setSelectedBookId(book.id)}
                  >
                    Подробнее
                  </button>
                  <button
                    className="btn btn-primary"
                    disabled={book.stock <= 0}
                    onClick={() => handleAddToCart(book.id)}
                  >
                    {book.stock > 0 ? 'В корзину' : 'Нет в наличии'}
                  </button>
                </div>
              </article>
            ))}
          </div>

          {data.pages > 1 && (
            <div className="pagination">
              <button
                className="btn btn-secondary"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Назад
              </button>
              <span>
                Страница {data.page} из {data.pages}
              </span>
              <button
                className="btn btn-secondary"
                disabled={page >= data.pages}
                onClick={() => setPage((p) => p + 1)}
              >
                Вперёд
              </button>
            </div>
          )}
        </>
      )}

      {selectedBookId !== null && (
        <BookModal
          bookId={selectedBookId}
          onClose={() => setSelectedBookId(null)}
          onAddToCart={handleAddToCart}
          canAddToCart={Boolean(user)}
        />
      )}
    </section>
  );
}