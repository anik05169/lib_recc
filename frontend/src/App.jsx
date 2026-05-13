import { useEffect, useState, useCallback } from "react";
import CatalogView from "./views/CatalogView";
import LibraryView from "./views/LibraryView";
import Login from "./components/Login";
import Register from "./components/Register";
import { API_BASE_URL } from "./api";
import "./App.css";

const BASE_URL = API_BASE_URL.replace(/\/$/, "");

function App() {
  /* ---------------- AUTH STATE ---------------- */
  const [token, setToken] = useState(null);
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

  const handleLogout = useCallback(() => {
    localStorage.removeItem("token");
    setToken(null);
    setView("catalog");
    setCatalogBooks([]);
    setUserBooks([]);
    setUserBookIds(new Set());
    setUserRatings({});
  }, []);

  const checkAuth = async () => {
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
        setToken(storedToken);
      } else {
        localStorage.removeItem("token");
      }
    } catch (err) {
      localStorage.removeItem("token");
    } finally {
      setCheckingAuth(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const handleLogin = (newToken) => {
    setToken(newToken);
    setAuthView("login");
  };

  const handleRegister = (newToken) => {
    setToken(newToken);
    setAuthView("login");
  };

  /* ---------------- LOADERS ---------------- */
  useEffect(() => {
    if (token) {
      loadCatalog();
      loadUserLibrary();
      loadAverageRatings();
      loadUserRatings();
    }
  }, [token]);

  const loadCatalog = async (search = searchQuery, page = 1) => {
    setLoading((p) => ({ ...p, catalog: true }));
    try {
      const params = new URLSearchParams({ page: String(page), limit: "50" });
      if (search) params.set("search", search);
      const res = await fetch(`${BASE_URL}/books?${params}`);
      const data = await res.json();
      // Support both old (array) and new (paginated) response formats
      if (Array.isArray(data)) {
        setCatalogBooks(data);
        setPagination({ page: 1, pages: 1, total: data.length });
      } else {
        setCatalogBooks(data.books || []);
        setPagination({ page: data.page || 1, pages: data.pages || 1, total: data.total || 0 });
      }
    } catch (err) {
      console.error("Failed to load catalog:", err);
      showToast("Failed to load catalog", "error");
    } finally {
      setLoading((p) => ({ ...p, catalog: false }));
    }
  };

  const loadUserLibrary = async () => {
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
  };

  const loadAverageRatings = async () => {
    try {
      const res = await fetch(`${BASE_URL}/ratings/average`);
      const data = await res.json();
      const map = {};
      data.forEach((r) => {
        map[r._id] = r.avg_rating.toFixed(1);
      });
      setAvgRatings(map);
    } catch (err) {
      console.error("Failed to load ratings:", err);
    }
  };

  const loadUserRatings = async () => {
    try {
      const res = await fetch(`${BASE_URL}/ratings/mine`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        const map = {};
        data.forEach((r) => { map[r.book_id] = r.rating; });
        setUserRatings(map);
      }
    } catch (err) {
      console.error("Failed to load user ratings:", err);
    }
  };

  /* ---------------- ACTIONS ---------------- */
  const handleSearch = (query) => {
    setSearchQuery(query);
    loadCatalog(query, 1);
  };

  const handlePageChange = (page) => {
    loadCatalog(searchQuery, page);
  };

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
        const data = await res.json();
        setRecommendations((prev) => ({ ...prev, [book.book_id]: data }));
      } catch (err) {
        console.error("Failed to load recommendations:", err);
      }
    },
    [expandedBookId]
  );

  // Open library book + fetch user-specific recommendations
  const openLibraryBookDetails = useCallback(
    async (book) => {
      if (expandedLibraryBookId === book.book_id) {
        setExpandedLibraryBookId(null);
        return;
      }
      setExpandedLibraryBookId(book.book_id);
      try {
        const res = await fetch(`${BASE_URL}/user/recommend/${book.book_id}`, {
          headers: getAuthHeaders(),
        });
        if (res.ok) {
          const data = await res.json();
          setLibraryRecommendations((prev) => ({ ...prev, [book.book_id]: data }));
        } else if (res.status === 401) {
          handleLogout();
        }
      } catch (err) {
        console.error("Failed to load library recommendations:", err);
      }
    },
    [expandedLibraryBookId]
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
          image_url: data.image_url || "/placeholder.jpg",
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
      <div className="container">
        <p>Loading...</p>
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
    <div className="container">
      <header className="header-section">
        <h1>Library AI</h1>
        <button onClick={handleLogout} className="btn-logout btn-secondary">
          Logout
        </button>
      </header>

      <div className="nav-tabs">
        <button
          className={view === "catalog" ? "active" : ""}
          onClick={() => setView("catalog")}
        >
          Explore Catalog
        </button>
        <button
          className={view === "library" ? "active" : ""}
          onClick={() => setView("library")}
        >
          My Collection
        </button>
      </div>

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

      {/* Toast notifications */}
      {toasts.length > 0 && (
        <div className="toast-container">
          {toasts.map((t) => (
            <div key={t.id} className={`toast ${t.type}`}>
              {t.message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;
