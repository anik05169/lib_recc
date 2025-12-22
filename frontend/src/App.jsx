import { useCallback, useEffect, useMemo, useState } from "react";
import "./App.css";

const USER_ID = 1;

function App() {
  const [view, setView] = useState("catalog"); // catalog | library
  const [catalogBooks, setCatalogBooks] = useState([]);
  const [userBooks, setUserBooks] = useState([]);
  const [searchQuery, setSearchQuery] = useState(""); // New: for search

  const [expandedBookId, setExpandedBookId] = useState(null);
  const [recommendations, setRecommendations] = useState({}); // keyed by book_id
  const [avgRatings, setAvgRatings] = useState({});

  const [newBook, setNewBook] = useState({
    book_id: "",
    title: "",
    description: "",
  });

  const [loading, setLoading] = useState({
    catalog: false,
    library: false,
    ratings: false,
    recommendations: {},
  }); // New: loading states

  const [error, setError] = useState(null); // New: error state

  /* ---------------- LOADERS ---------------- */

  useEffect(() => {
    loadCatalog();
    loadUserLibrary();
    loadAverageRatings();
  }, []);

  const loadCatalog = useCallback(async () => {
    setLoading(prev => ({ ...prev, catalog: true }));
    setError(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/books");
      if (!res.ok) throw new Error("Failed to load catalog");
      const data = await res.json();
      setCatalogBooks(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message);
      console.error(err);
    } finally {
      setLoading(prev => ({ ...prev, catalog: false }));
    }
  }, []);

  const loadUserLibrary = useCallback(async () => {
    setLoading(prev => ({ ...prev, library: true }));
    setError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/user/library/${USER_ID}`);
      if (!res.ok) throw new Error("Failed to load library");
      const data = await res.json();
      setUserBooks(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message);
      console.error(err);
    } finally {
      setLoading(prev => ({ ...prev, library: false }));
    }
  }, []);

  const loadAverageRatings = useCallback(async () => {
    setLoading(prev => ({ ...prev, ratings: true }));
    setError(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/ratings/average");
      if (!res.ok) throw new Error("Failed to load ratings");
      const data = await res.json();
      const map = {};
      data.forEach((r) => {
        map[r._id] = r.avg_rating.toFixed(1);
      });
      setAvgRatings(map);
    } catch (err) {
      setError(err.message);
      console.error(err);
    } finally {
      setLoading(prev => ({ ...prev, ratings: false }));
    }
  }, []);

  /* ---------------- ACTIONS ---------------- */

  const openBookDetails = useCallback(async (book) => {
    if (expandedBookId === book.book_id) {
      setExpandedBookId(null);
      return;
    }

    setExpandedBookId(book.book_id);
    setLoading(prev => ({ ...prev, recommendations: { ...prev.recommendations, [book.book_id]: true } }));
    setError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/recommend/${book.book_id}`);
      if (!res.ok) throw new Error("Failed to load recommendations");
      const data = await res.json();
      setRecommendations((prev) => ({
        ...prev,
        [book.book_id]: Array.isArray(data) ? data : [],
      }));
    } catch (err) {
      setError(err.message);
      console.error(err);
    } finally {
      setLoading(prev => ({ ...prev, recommendations: { ...prev.recommendations, [book.book_id]: false } }));
    }
  }, [expandedBookId]);

  const addFromCatalog = useCallback(async (book_id) => {
    setError(null);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/user/add-from-catalog?user_id=${USER_ID}&book_id=${book_id}`,
        { method: "POST" }
      );
      if (!res.ok) throw new Error("Failed to add book");
      await loadUserLibrary();
      alert("Book added to your library");
    } catch (err) {
      setError(err.message);
      alert("Error: " + err.message);
    }
  }, [loadUserLibrary]);

  const addCustomBook = useCallback(async () => {
    if (!newBook.book_id.trim() || isNaN(newBook.book_id) || !newBook.title.trim() || !newBook.description.trim()) {
      alert("Please fill all fields correctly. Book ID must be a number.");
      return;
    }

    setError(null);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/user/add-custom-book?user_id=${USER_ID}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            book_id: Number(newBook.book_id),
            title: newBook.title,
            description: newBook.description,
          }),
        }
      );
      if (!res.ok) throw new Error("Failed to add custom book");
      setNewBook({ book_id: "", title: "", description: "" });
      await loadCatalog();
      await loadUserLibrary();
      alert("Book added and model retrained");
    } catch (err) {
      setError(err.message);
      alert("Error: " + err.message);
    }
  }, [newBook, loadCatalog, loadUserLibrary]);

  const rateBook = useCallback(async (book_id, rating) => {
    if (!rating) return; // Prevent empty rating
    setError(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/rate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: USER_ID,
          book_id,
          rating,
        }),
      });
      if (!res.ok) throw new Error("Failed to rate book");
      await loadAverageRatings();
    } catch (err) {
      setError(err.message);
      alert("Error: " + err.message);
    }
  }, [loadAverageRatings]);

  // Filtered books for search
  const filteredCatalogBooks = useMemo(() => {
    return catalogBooks.filter(book =>
      book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      book.description.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [catalogBooks, searchQuery]);

  const filteredUserBooks = useMemo(() => {
    return userBooks.filter(book =>
      book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      book.description.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [userBooks, searchQuery]);

  /* ---------------- UI ---------------- */

  return (
    <div className="container">
      <h1>Personal Library</h1>

      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {/* NAV */}
      <button onClick={() => setView("catalog")}>Browse Catalog</button>
      <button onClick={() => setView("library")}>My Library</button>

      {/* SEARCH */}
      <input
        type="text"
        placeholder="Search books..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        style={{ margin: "10px 0", padding: "5px", width: "100%" }}
      />

      {/* ---------------- CATALOG ---------------- */}
      {view === "catalog" && (
        <>
          <h2>Catalog</h2>
          {loading.catalog && <p>Loading catalog...</p>}
          <ul className="book-list">
            {filteredCatalogBooks.map((book) => (
              <li key={book.book_id}>
                <strong>{book.title}</strong>
                <p>{book.description}</p>

                <button onClick={() => openBookDetails(book)}>
                  {expandedBookId === book.book_id
                    ? "Hide Details"
                    : "View Details"}
                </button>
                <button onClick={() => addFromCatalog(book.book_id)}>
                  Add to My Library
                </button>

                {/* INLINE DETAILS */}
                {expandedBookId === book.book_id && (
                  <div className="recommendation-box">
                    <h4>Related Books</h4>
                    {loading.recommendations[book.book_id] && <p>Loading recommendations...</p>}
                    {recommendations[book.book_id]?.length === 0 ? (
                      <p>No related books found.</p>
                    ) : (
                      <ul className="recommend-list">
                        {recommendations[book.book_id]?.map((b) => (
                          <li key={b.book_id}>
                            <strong>{b.title}</strong>
                            <p>{b.description}</p>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </>
      )}

      {/* ---------------- MY LIBRARY ---------------- */}
      {view === "library" && (
        <>
          <h2>My Library</h2>
          {loading.library && <p>Loading library...</p>}

          {/* ADD CUSTOM BOOK */}
          <h3>Add Your Own Book</h3>
          <input
            placeholder="Book ID (number)"
            value={newBook.book_id}
            onChange={(e) =>
              setNewBook({ ...newBook, book_id: e.target.value })
            }
          />
          <input
            placeholder="Title"
            value={newBook.title}
            onChange={(e) =>
              setNewBook({ ...newBook, title: e.target.value })
            }
          />
          <textarea
            placeholder="Description"
            value={newBook.description}
            onChange={(e) =>
              setNewBook({ ...newBook, description: e.target.value })
            }
          />
          <button onClick={addCustomBook}>Add Book</button>

          <ul className="book-list">
            {filteredUserBooks.map((book) => (
              <li key={book.book_id}>
                <strong>{book.title}</strong>
                <p>{book.description}</p>

                {avgRatings[book.book_id] && (
                  <p>⭐ {avgRatings[book.book_id]}</p>
                )}

                <select
                  value={book.currentRating || ""} // Track current rating
                  onChange={(e) => {
                    const rating = Number(e.target.value);
                    setUserBooks(prev => prev.map(b => b.book_id === book.book_id ? { ...b, currentRating: rating } : b));
                    rateBook(book.book_id, rating);
                  }}
                >
                  <option value="">Rate</option>
                  {[1, 2, 3, 4, 5].map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

export default App;
