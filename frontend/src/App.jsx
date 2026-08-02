import { useEffect, useState, useCallback, useRef } from "react";
import CatalogView from "./views/CatalogView";
import LibraryView from "./views/LibraryView";
import Login from "./components/Login";
import Register from "./components/Register";
import { API_BASE_URL, isApiConfigured, PLACEHOLDER_IMAGE_URL } from "./api";
import "./App.css";

const BASE_URL = API_BASE_URL;

function App() {
  /* ---------------- AUTH STATE ---------------- */
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [authView, setAuthView] = useState("login"); // "login" or "register"
  const [checkingAuth, setCheckingAuth] = useState(true);

  /* ---------------- APP STATE ---------------- */
  const [view, setView] = useState("catalog");
  const [catalogBooks, setCatalogBooks] = useState([]);
  const [userBooks, setUserBooks] = useState([]);
  const [userBookIds, setUserBookIds] = useState(new Set());
  const [userRatings, setUserRatings] = useState({});
  const [expandedBookId, setExpandedBookId] = useState(null);
  const [expandedLibraryBookId, setExpandedLibraryBookId] = useState(null);
  const [recommendations, setRecommendations] = useState({});
  const [libraryRecommendations, setLibraryRecommendations] = useState({});
  const [avgRatings, setAvgRatings] = useState({});
  const [loading, setLoading] = useState({ catalog: false, library: false });
  const [searchQuery, setSearchQuery] = useState("");
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });

  /* ---------------- TOAST SYSTEM ---------------- */
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message, type = "info") => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  // NEW BOOK (for My Library) — no book_id needed (auto-generated)
  const [newBook, setNewBook] = useState({
    title: "",
    description: "",
  });

  /* ---------------- AUTH HELPERS ---------------- */
  const getAuthHeaders = useCallback(() => {
    const storedToken = localStorage.getItem("token");
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${storedToken || token}`,
    };
  }, [token]);

  const catalogAbortRef = useRef(null);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
    setView("catalog");
    setCatalogBooks([]);
    setUserBooks([]);
    setUserBookIds(new Set());
    setUserRatings({});
  }, []);

  const checkAuth = useCallback(async () => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      setCheckingAuth(false);
      return;
    }
    try {
      const res = await fetch(`${BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${storedToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setToken(storedToken);
        setUser(data);
      } else {
        localStorage.removeItem("token");
      }
    } catch {
      localStorage.removeItem("token");
    } finally {
      setCheckingAuth(false);
    }
  }, []);

  const loadCatalog = useCallback(
    async (search = "", page = 1) => {
      if (catalogAbortRef.current) {
        catalogAbortRef.current.abort();
      }
      const controller = new AbortController();
      catalogAbortRef.current = controller;

      setLoading((p) => ({ ...p, catalog: true }));
      try {
        const params = new URLSearchParams({ page: String(page), limit: "50" });
        if (search) params.set("search", search);
        const res = await fetch(`${BASE_URL}/books?${params}`, {
          signal: controller.signal,
        });
        if (!res.ok) {
          showToast("Failed to load catalog", "error");
          return;
        }
        const data = await res.json();
        if (Array.isArray(data)) {
          setCatalogBooks(data);
          setPagination({ page: 1, pages: 1, total: data.length });
        } else {
          setCatalogBooks(data.books || []);
          setPagination({ page: data.page || 1, pages: data.pages || 1, total: data.total || 0 });
        }
      } catch (err) {
        if (err.name === "AbortError") return;
        console.error("Failed to load catalog:", err);
        showToast("Failed to load catalog", "error");
      } finally {
        if (!controller.signal.aborted) {
          setLoading((p) => ({ ...p, catalog: false }));
        }
      }
    },
    [showToast]
  );

  const loadUserLibrary = useCallback(async () => {
    setLoading((p) => ({ ...p, library: true }));
    try {
      const res = await fetch(`${BASE_URL}/user/library`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setUserBooks(data);
        setUserBookIds(new Set(data.map((b) => b.book_id)));
      } else if (res.status === 401) {
        handleLogout();
      }
    } catch (err) {
      console.error("Failed to load library:", err);
      showToast("Failed to load library", "error");
    } finally {
      setLoading((p) => ({ ...p, library: false }));
    }
  }, [getAuthHeaders, handleLogout, showToast]);

  const loadAverageRatings = useCallback(async () => {
    try {
      const res = await fetch(`${BASE_URL}/ratings/average`);
      if (!res.ok) return;
      const data = await res.json();
      if (!Array.isArray(data)) return;
      const map = {};
      data.forEach((r) => {
        map[r._id] = r.avg_rating.toFixed(1);
      });
      setAvgRatings(map);
    } catch (err) {
      console.error("Failed to load ratings:", err);
    }
  }, []);

  const loadUserRatings = useCallback(async () => {
    try {
      const res = await fetch(`${BASE_URL}/ratings/mine`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        const map = {};
        data.forEach((r) => { map[r.book_id] = r.rating; });
        setUserRatings(map);
      } else if (res.status === 401) {
        handleLogout();
      }
    } catch (err) {
      console.error("Failed to load user ratings:", err);
    }
  }, [getAuthHeaders, handleLogout]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const handleLogin = async (newToken) => {
    setToken(newToken);
    setAuthView("login");
    try {
      const res = await fetch(`${BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${newToken}` },
      });
      if (res.ok) setUser(await res.json());
    } catch {
      /* profile loads on next checkAuth if needed */
    }
  };

  const handleRegister = async (newToken) => {
    setToken(newToken);
    setAuthView("login");
    try {
      const res = await fetch(`${BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${newToken}` },
      });
      if (res.ok) setUser(await res.json());
    } catch {
      /* ignore */
    }
  };

  /* ---------------- LOADERS ---------------- */
  useEffect(() => {
    if (token) {
      loadCatalog();
      loadUserLibrary();
      loadAverageRatings();
      loadUserRatings();
    }
  }, [token, loadCatalog, loadUserLibrary, loadAverageRatings, loadUserRatings]);

  /* ---------------- ACTIONS ---------------- */
  const handleSearch = useCallback((query) => {
    setSearchQuery(query);
    loadCatalog(query, 1);
  }, [loadCatalog]);

  const handlePageChange = useCallback((page) => {
    loadCatalog(searchQuery, page);
  }, [loadCatalog, searchQuery]);

  // Open catalog book + fetch recommendations
  const openBookDetails = useCallback(
    async (book) => {
      if (expandedBookId === book.book_id) {
        setExpandedBookId(null);
        return;
      }
      setExpandedBookId(book.book_id);
      try {
        const res = await fetch(`${BASE_URL}/recommend/${book.book_id}`);
        if (!res.ok) {
          setRecommendations((prev) => ({ ...prev, [book.book_id]: [] }));
          return;
        }
        const data = await res.json();
        setRecommendations((prev) => ({
          ...prev,
          [book.book_id]: Array.isArray(data) ? data : [],
        }));
      } catch (err) {
        console.error("Failed to load recommendations:", err);
        setRecommendations((prev) => ({ ...prev, [book.book_id]: [] }));
      }
    },
    [expandedBookId]
  );

  // Open library book + fetch catalog + in-library similar books
  const openLibraryBookDetails = useCallback(
    async (book) => {
      if (expandedLibraryBookId === book.book_id) {
        setExpandedLibraryBookId(null);
        return;
      }
      setExpandedLibraryBookId(book.book_id);
      // Clear cache so UI shows loading while refetching
      setLibraryRecommendations((prev) => {
        const next = { ...prev };
        delete next[book.book_id];
        return next;
      });
      try {
        const res = await fetch(`${BASE_URL}/user/recommend/${book.book_id}`, {
          headers: getAuthHeaders(),
        });
        if (res.ok) {
          const data = await res.json();
          const payload = Array.isArray(data)
            ? { catalog: data, library: [] }
            : {
                catalog: Array.isArray(data?.catalog) ? data.catalog : [],
                library: Array.isArray(data?.library) ? data.library : [],
              };
          setLibraryRecommendations((prev) => ({
            ...prev,
            [book.book_id]: payload,
          }));
        } else if (res.status === 401) {
          handleLogout();
        } else {
          setLibraryRecommendations((prev) => ({
            ...prev,
            [book.book_id]: { catalog: [], library: [] },
          }));
        }
      } catch (err) {
        console.error("Failed to load library recommendations:", err);
        setLibraryRecommendations((prev) => ({
          ...prev,
          [book.book_id]: { catalog: [], library: [] },
        }));
      }
    },
    [expandedLibraryBookId, getAuthHeaders, handleLogout]
  );

  // Add catalog book to user library
  const addFromCatalog = async (book_id) => {
    try {
      const res = await fetch(
        `${BASE_URL}/user/add-from-catalog?book_id=${book_id}`,
        { method: "POST", headers: getAuthHeaders() }
      );
      if (res.ok) {
        loadUserLibrary();
        showToast("Book added to your collection!", "success");
      } else if (res.status === 401) {
        handleLogout();
      } else {
        const err = await res.json().catch(() => ({}));
        showToast(err.detail || "Failed to add book", "error");
      }
    } catch (err) {
      console.error("Failed to add book:", err);
      showToast("Failed to add book", "error");
    }
  };

  // Rate book
  const rateBook = async (book_id, rating) => {
    try {
      const res = await fetch(`${BASE_URL}/ratings`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ book_id, rating }),
      });
      if (res.ok) {
        loadAverageRatings();
        setUserRatings((prev) => ({ ...prev, [book_id]: rating }));
        showToast(`Rated ${rating} star${rating > 1 ? "s" : ""}`, "success");
      } else if (res.status === 401) {
        handleLogout();
      } else {
        const err = await res.json().catch(() => ({}));
        showToast(err.detail || "Failed to save rating", "error");
      }
    } catch (err) {
      console.error("Failed to rate book:", err);
      showToast("Failed to save rating", "error");
    }
  };

  // Delete from library
  const deleteFromLibrary = async (book_id) => {
    try {
      const res = await fetch(`${BASE_URL}/user/library/${book_id}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        loadUserLibrary();
        loadAverageRatings();
        showToast("Book removed from library", "info");
      } else if (res.status === 401) {
        handleLogout();
      } else {
        const err = await res.json().catch(() => ({}));
        showToast(err.detail || "Failed to remove book", "error");
      }
    } catch (err) {
      console.error("Failed to delete book:", err);
      showToast("Failed to remove book", "error");
    }
  };

  // Add custom book
  const addCustomBook = async (bookToUse = null) => {
    const data = bookToUse || newBook;

    if (!data.title?.trim() || !data.description?.trim()) {
      showToast("Title and description are required", "warning");
      return;
    }

    try {
      const res = await fetch(`${BASE_URL}/user/add-custom-book`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          title: data.title,
          description: data.description,
          image_url: data.image_url || PLACEHOLDER_IMAGE_URL,
        }),
      });

      if (!res.ok) {
        if (res.status === 401) {
          handleLogout();
          return;
        }
        const err = await res.json();
        showToast(err.detail || "Failed to add book", "error");
        return;
      }

      // reset
      setNewBook({ title: "", description: "", image_url: "" });
      loadUserLibrary();
      showToast("Custom book added!", "success");
    } catch (err) {
      console.error("Failed to add custom book:", err);
      showToast("Failed to add custom book", "error");
    }
  };

  /* ---------------- UI ---------------- */

  if (checkingAuth) {
    return (
      <div className="status-screen">
        <div className="status-panel">
          <h1>Library AI</h1>
          <p>Opening your library…</p>
          <div className="loading-dots" aria-hidden="true">
            <span /><span /><span />
          </div>
        </div>
      </div>
    );
  }

  if (!isApiConfigured) {
    return (
      <div className="status-screen">
        <div className="status-panel">
          <h1>Configuration required</h1>
          <p>
            Set <code>VITE_API_BASE_URL</code> in <code>frontend/.env</code> (see{" "}
            <code>frontend/.env.example</code>).
          </p>
        </div>
      </div>
    );
  }

  if (!token) {
    return authView === "login" ? (
      <Login onLogin={handleLogin} switchToRegister={() => setAuthView("register")} />
    ) : (
      <Register onRegister={handleRegister} switchToLogin={() => setAuthView("login")} />
    );
  }

  return (
    <div className="app-shell">
      <div className="container">
        <header className="header-section">
          <div className="brand-block">
            <div className="brand-mark">
              <span className="brand-mark-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" strokeLinecap="round" />
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </span>
              <h1>Library AI</h1>
            </div>
            <p className="header-tagline">Catalog, collection, and recommendations in one place.</p>
            {user?.name && (
              <p className="header-greeting">
                Welcome, <strong>{user.name}</strong>
              </p>
            )}
          </div>
          <div className="header-actions">
            <button onClick={handleLogout} className="btn-logout btn-secondary" type="button">
              Log out
            </button>
          </div>
        </header>

        <nav className="nav-tabs" aria-label="Primary">
          <button
            type="button"
            className={view === "catalog" ? "active" : ""}
            aria-current={view === "catalog" ? "page" : undefined}
            onClick={() => setView("catalog")}
          >
            Explore Catalog
          </button>
          <button
            type="button"
            className={view === "library" ? "active" : ""}
            aria-current={view === "library" ? "page" : undefined}
            onClick={() => setView("library")}
          >
            My Collection
          </button>
        </nav>

        <main className="content-area">
          {view === "catalog" && (
            <CatalogView
              books={catalogBooks}
              loading={loading.catalog}
              expandedBookId={expandedBookId}
              recommendations={recommendations}
              openBookDetails={openBookDetails}
              addFromCatalog={addFromCatalog}
              userBookIds={userBookIds}
              searchQuery={searchQuery}
              onSearch={handleSearch}
              pagination={pagination}
              onPageChange={handlePageChange}
            />
          )}

          {view === "library" && (
            <LibraryView
              books={userBooks}
              loading={loading.library}
              avgRatings={avgRatings}
              userRatings={userRatings}
              rateBook={rateBook}
              setUserBooks={setUserBooks}
              newBook={newBook}
              setNewBook={setNewBook}
              addCustomBook={addCustomBook}
              expandedBookId={expandedLibraryBookId}
              recommendations={libraryRecommendations}
              openBookDetails={openLibraryBookDetails}
              deleteFromLibrary={deleteFromLibrary}
              showToast={showToast}
              getAuthHeaders={getAuthHeaders}
            />
          )}
        </main>

        {toasts.length > 0 && (
          <div className="toast-container" role="status" aria-live="polite">
            {toasts.map((t) => (
              <div key={t.id} className={`toast ${t.type}`}>
                {t.message}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
