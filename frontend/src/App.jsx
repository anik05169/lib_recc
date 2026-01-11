import { useEffect, useState, useCallback } from "react";
import CatalogView from "./views/CatalogView";
import LibraryView from "./views/LibraryView";
import Login from "./components/Login";
import Register from "./components/Register";
import { API_BASE_URL } from "./config";
import "./App.css";

function App() {
  /* ---------------- AUTH STATE ---------------- */
  const [token, setToken] = useState(null);
  const [authView, setAuthView] = useState("login"); // "login" or "register"
  const [checkingAuth, setCheckingAuth] = useState(true);

  /* ---------------- APP STATE ---------------- */
  const [view, setView] = useState("catalog");
  const [catalogBooks, setCatalogBooks] = useState([]);
  const [userBooks, setUserBooks] = useState([]);
  const [expandedBookId, setExpandedBookId] = useState(null);
  const [expandedLibraryBookId, setExpandedLibraryBookId] = useState(null);
  const [recommendations, setRecommendations] = useState({});
  const [libraryRecommendations, setLibraryRecommendations] = useState({});
  const [avgRatings, setAvgRatings] = useState({});
  const [loading, setLoading] = useState({
    catalog: false,
    library: false,
  });

  // NEW BOOK (for My Library)
  const [newBook, setNewBook] = useState({
    book_id: "",
    title: "",
    description: "",
  });

  /* ---------------- AUTH HELPERS ---------------- */
  const getAuthHeaders = () => {
    const storedToken = localStorage.getItem("token");
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${storedToken || token}`,
    };
  };

  const checkAuth = async () => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      setCheckingAuth(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/auth/me`, {
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

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setView("catalog");
  };

  /* ---------------- LOADERS ---------------- */
  useEffect(() => {
    if (token) {
      loadCatalog();
      loadUserLibrary();
      loadAverageRatings();
    }
  }, [token]);

  const loadCatalog = async () => {
    setLoading((p) => ({ ...p, catalog: true }));
    try {
      const res = await fetch(`${API_BASE_URL}/books`);
      const data = await res.json();
      setCatalogBooks(data);
    } catch (err) {
      console.error("Failed to load catalog:", err);
    } finally {
      setLoading((p) => ({ ...p, catalog: false }));
    }
  };

  const loadUserLibrary = async () => {
    setLoading((p) => ({ ...p, library: true }));
    try {
      const res = await fetch(`${API_BASE_URL}/user/library`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setUserBooks(data);
      } else if (res.status === 401) {
        handleLogout();
      }
    } catch (err) {
      console.error("Failed to load library:", err);
    } finally {
      setLoading((p) => ({ ...p, library: false }));
    }
  };

  const loadAverageRatings = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/ratings/average`);
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

  /* ---------------- ACTIONS ---------------- */

  // Open catalog book + fetch recommendations
  const openBookDetails = useCallback(
    async (book) => {
      if (expandedBookId === book.book_id) {
        setExpandedBookId(null);
        return;
      }

      setExpandedBookId(book.book_id);

      try {
        const res = await fetch(
          `${API_BASE_URL}/recommend/${book.book_id}`
        );
        const data = await res.json();

        setRecommendations((prev) => ({
          ...prev,
          [book.book_id]: data,
        }));
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
        const res = await fetch(
          `${API_BASE_URL}/user/recommend/${book.book_id}`,
          {
            headers: getAuthHeaders(),
          }
        );
        if (res.ok) {
          const data = await res.json();

          setLibraryRecommendations((prev) => ({
            ...prev,
            [book.book_id]: data,
          }));
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
        `${API_BASE_URL}/user/add-from-catalog?book_id=${book_id}`,
        {
          method: "POST",
          headers: getAuthHeaders(),
        }
      );
      if (res.ok) {
        loadUserLibrary();
      } else if (res.status === 401) {
        handleLogout();
      }
    } catch (err) {
      console.error("Failed to add book:", err);
    }
  };

  // Rate book
  const rateBook = async (book_id, rating) => {
    try {
      const res = await fetch(`${API_BASE_URL}/rate`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          book_id,
          rating,
        }),
      });
      if (res.ok) {
        loadAverageRatings();
      } else if (res.status === 401) {
        handleLogout();
      }
    } catch (err) {
      console.error("Failed to rate book:", err);
    }
  };

  // Add custom book
const addCustomBook = async () => {
  const bookId = Number(newBook.book_id);

  if (
    !bookId ||
    !newBook.title?.trim() ||
    !newBook.description?.trim()
  ) {
    alert("Book ID must be a number and all fields are required");
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/user/add-custom-book`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        book_id: bookId,
        title: newBook.title,
        description: newBook.description,
        image_url: newBook.image_url || "/placeholder.jpg", // 🔥 FIX
      }),
    });

    if (!res.ok) {
      if (res.status === 401) {
        handleLogout();
        return;
      }
      const err = await res.json();
      console.error(err);
      alert("Backend rejected request");
      return;
    }

    // reset (keep image_url out)
    setNewBook({
      book_id: "",
      title: "",
      description: "",
      image_url: "",
    });

    loadCatalog();
    loadUserLibrary();
  } catch (err) {
    console.error("Failed to add custom book:", err);
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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h1>Personal Library</h1>
        <button onClick={handleLogout} style={{ padding: "8px 16px", cursor: "pointer" }}>
          Logout
        </button>
      </div>

      <button onClick={() => setView("catalog")}>Catalog</button>
      <button onClick={() => setView("library")}>My Library</button>

      {view === "catalog" && (
        <CatalogView
          books={catalogBooks}
          loading={loading.catalog}
          expandedBookId={expandedBookId}
          recommendations={recommendations}
          openBookDetails={openBookDetails}
          addFromCatalog={addFromCatalog}
        />
      )}

      {view === "library" && (
        <LibraryView
          books={userBooks}
          loading={loading.library}
          avgRatings={avgRatings}
          rateBook={rateBook}
          setUserBooks={setUserBooks}
          newBook={newBook}
          setNewBook={setNewBook}
          addCustomBook={addCustomBook}
          expandedBookId={expandedLibraryBookId}
          recommendations={libraryRecommendations}
          openBookDetails={openLibraryBookDetails}
        />
      )}
    </div>
  );
}

export default App;

