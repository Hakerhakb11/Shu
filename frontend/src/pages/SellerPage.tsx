import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { ApiError, catalogApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { BookDetail, BookListItem, Category } from '../types';

interface CharDraft {
  name: string;
  value: string;
}

export function SellerPage() {
  const { user } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [publishedBooks, setPublishedBooks] = useState<BookListItem[]>([]);
  const [recentCreated, setRecentCreated] = useState<BookDetail[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [stock, setStock] = useState('1');
  const [categoryId, setCategoryId] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [chars, setChars] = useState<CharDraft[]>([{ name: 'Переплёт', value: 'Твёрдый' }]);

  const [newCatName, setNewCatName] = useState('');
  const [newCatSlug, setNewCatSlug] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [cats, page] = await Promise.all([
        catalogApi.listCategories(),
        catalogApi.listItems({ page: 1, size: 100 }),
      ]);
      setCategories(cats);
      if (!categoryId && cats.length > 0) {
        setCategoryId(String(cats[0].id));
      }
      setPublishedBooks(page.items.filter((item) => item.seller_id === user?.id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось загрузить данные продавца');
    }
  }, [categoryId, user?.id]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const resetForm = () => {
    setEditingId(null);
    setTitle('');
    setAuthor('');
    setDescription('');
    setPrice('');
    setStock('1');
    setImageUrl('');
    setChars([{ name: 'Переплёт', value: 'Твёрдый' }]);
  };

  const handleSubmitBook = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSubmitting(true);

    const cleanChars = chars
      .map((c) => ({ name: c.name.trim(), value: c.value.trim() }))
      .filter((c) => c.name && c.value);

    const payload = {
      title: title.trim(),
      author: author.trim(),
      description: description.trim(),
      price: Number(price),
      category_id: Number(categoryId),
      stock: Number(stock),
      image_url: imageUrl.trim() || null,
      characteristics: cleanChars,
    };

    try {
      if (editingId !== null) {
        const updated = await catalogApi.updateItem(editingId, payload);
        setSuccess(`Книга «${updated.title}» обновлена`);
        setRecentCreated((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
      } else {
        const created = await catalogApi.createItem(payload);
        setSuccess(`Книга «${created.title}» создана и отправлена на модерацию (PENDING)`);
        setRecentCreated((prev) => [created, ...prev]);
      }
      resetForm();
      await loadData();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось сохранить книгу');
    } finally {
      setSubmitting(false);
    }
  };

  const handleStartEdit = async (bookId: number) => {
    setError(null);
    try {
      const detail = await catalogApi.getItem(bookId);
      setEditingId(detail.id);
      setTitle(detail.title);
      setAuthor(detail.author);
      setDescription(detail.description);
      setPrice(String(detail.price));
      setStock(String(detail.stock));
      setCategoryId(String(detail.category_id));
      setImageUrl(detail.image_url ?? '');
      setChars(
        detail.characteristics.length > 0
          ? detail.characteristics.map((c) => ({ name: c.name, value: c.value }))
          : [{ name: '', value: '' }]
      );
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось открыть книгу на редактирование');
    }
  };

  const handleDelete = async (bookId: number) => {
    setError(null);
    try {
      await catalogApi.deleteItem(bookId);
      setRecentCreated((prev) => prev.filter((b) => b.id !== bookId));
      await loadData();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось удалить книгу');
    }
  };

  const handleCreateCategory = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const created = await catalogApi.createCategory({
        name: newCatName.trim(),
        slug: newCatSlug.trim().toLowerCase(),
      });
      setCategories((prev) => [...prev, created]);
      setCategoryId(String(created.id));
      setNewCatName('');
      setNewCatSlug('');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось создать категорию');
    }
  };

  return (
    <section className="stack-lg">
      <h1>Кабинет продавца</h1>
      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="two-col">
        <div className="card">
          <h2>{editingId ? `Редактирование книги #${editingId}` : 'Добавить новую книгу'}</h2>
          <form onSubmit={handleSubmitBook} className="form">
            <label>
              Название
              <input required value={title} onChange={(e) => setTitle(e.target.value)} />
            </label>
            <label>
              Автор
              <input required value={author} onChange={(e) => setAuthor(e.target.value)} />
            </label>
            <label>
              Категория
              <select
                required
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
              >
                <option value="" disabled>
                  Выберите категорию
                </option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </label>
            <div className="form-row">
              <label>
                Цена (₽)
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                />
              </label>
              <label>
                Остаток (шт.)
                <input
                  type="number"
                  min="0"
                  required
                  value={stock}
                  onChange={(e) => setStock(e.target.value)}
                />
              </label>
            </div>
            <label>
              URL обложки (необязательно)
              <input
                type="url"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                placeholder="https://example.com/cover.jpg"
              />
            </label>
            <label>
              Описание
              <textarea
                rows={3}
                required
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </label>

            <div>
              <div className="inline-between">
                <span className="label-text">Характеристики</span>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setChars((prev) => [...prev, { name: '', value: '' }])}
                >
                  + Добавить
                </button>
              </div>
              {chars.map((ch, idx) => (
                <div key={idx} className="char-edit-row">
                  <input
                    placeholder="Название (ISBN)"
                    value={ch.name}
                    onChange={(e) =>
                      setChars((prev) =>
                        prev.map((item, i) => (i === idx ? { ...item, name: e.target.value } : item))
                      )
                    }
                  />
                  <input
                    placeholder="Значение"
                    value={ch.value}
                    onChange={(e) =>
                      setChars((prev) =>
                        prev.map((item, i) =>
                          i === idx ? { ...item, value: e.target.value } : item
                        )
                      )
                    }
                  />
                  <button
                    type="button"
                    className="btn btn-danger-outline btn-sm"
                    onClick={() => setChars((prev) => prev.filter((_, i) => i !== idx))}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? 'Сохранение...' : editingId ? 'Сохранить изменения' : 'Отправить на модерацию'}
              </button>
              {editingId && (
                <button type="button" className="btn btn-secondary" onClick={resetForm}>
                  Отмена
                </button>
              )}
            </div>
          </form>
        </div>

        <div className="stack">
          <div className="card">
            <h3>Создать категорию</h3>
            <form onSubmit={handleCreateCategory} className="form">
              <label>
                Название
                <input
                  required
                  minLength={2}
                  value={newCatName}
                  onChange={(e) => setNewCatName(e.target.value)}
                  placeholder="Научная фантастика"
                />
              </label>
              <label>
                Slug (латиница)
                <input
                  required
                  minLength={2}
                  value={newCatSlug}
                  onChange={(e) => setNewCatSlug(e.target.value)}
                  placeholder="sci-fi"
                />
              </label>
              <button type="submit" className="btn btn-secondary">
                Создать категорию
              </button>
            </form>
          </div>

          {recentCreated.length > 0 && (
            <div className="card">
              <h3>Отправлено на модерацию в этой сессии</h3>
              <ul className="simple-list">
                {recentCreated.map((book) => (
                  <li key={book.id} className="inline-between">
                    <span>
                      <strong>{book.title}</strong> — {book.price.toFixed(2)} ₽{' '}
                      <span className="badge">{book.status}</span>
                    </span>
                    <button
                      className="btn btn-danger-outline btn-sm"
                      onClick={() => handleDelete(book.id)}
                    >
                      Удалить
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="card">
            <h3>Мои опубликованные книги ({publishedBooks.length})</h3>
            {publishedBooks.length === 0 ? (
              <p className="muted">Одобренных книг пока нет.</p>
            ) : (
              <ul className="simple-list">
                {publishedBooks.map((book) => (
                  <li key={book.id} className="inline-between">
                    <div>
                      <strong>{book.title}</strong>
                      <div className="muted">
                        {book.author} · {book.price.toFixed(2)} ₽ · Остаток: {book.stock}
                      </div>
                    </div>
                    <div className="inline-gap">
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleStartEdit(book.id)}
                      >
                        Править
                      </button>
                      <button
                        className="btn btn-danger-outline btn-sm"
                        onClick={() => handleDelete(book.id)}
                      >
                        Удалить
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}