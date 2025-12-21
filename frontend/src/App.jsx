import { useEffect, useState } from "react";
import { getBooks, trainModel, recommendBooks } from "./api";
import "./App.css";

function App() {
  const [books, setBooks] = useState([]);
  const [search, setSearch] = useState("");
  const [selectedBook, setSelectedBook] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [training, setTraining] = useState(false);

  const [newBook, setNewBook] = useState({
    book_id: "",
    title: "",
    description: "",
  });

  // Load books on page load
  useEffect(() => {
    loadBooks();
  }, []);

  const loadBooks = async () => {
    const res = await getBooks();
    setBooks(res.data);
  };

  // Train model
  const handleTrain = async () => {
    setTraining(true);
    await trainModel();
    setTraining(false);
    alert("Model trained successfully");
  };

  // Get recommendations
  const handleRecommend = async (book) => {
    setSelectedBook(book);
    const res = await recommendBooks(book.book_id);
    setRecommendations(res.data);
  };

  // Add book + retrain
  const handleAddBook = async () => {
    if (!newBook.book_id || !newBook.title || !newBook.description) {
      alert("Please fill all fields");
      return;
    }

    await fetch("http://127.0.0.1:8000/add-book", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        book_id: Number(newBook.book_id),
        title: newBook.title,
        description: newBook.description,
      }),
    });

    alert("Book added. Retraining model...");
    await trainModel();
    await loadBooks();

    setNewBook({ book_id: "", title: "", description: "" });
  };

  // Search filter
  const filteredBooks = books.filter(
    (book) =>
      book.title.toLowerCase().includes(search.toLowerCase()) ||
      book.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="container">
      <h1>Library Recommendation System</h1>

      {/* TRAIN */}
      <button onClick={handleTrain} disabled={training}>
        {training ? "Training..." : "Train Model"}
      </button>

      {/* ADD BOOK */}
      <h2>Add a Book</h2>
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
      <button onClick={handleAddBook}>Add Book & Retrain</button>

      {/* RECOMMENDATIONS AT TOP */}
      {selectedBook && (
        <div className="recommendation-box">
          <h2>Recommended for "{selectedBook.title}"</h2>
          <ul className="recommend-list">
            {recommendations.map((rec) => (
              <li key={rec.book_id}>
                <strong>{rec.title}</strong>
                <p>{rec.description}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* SEARCH */}
      <input
        className="search"
        type="text"
        placeholder="Search books..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {/* BOOK LIST */}
      <h2>Books</h2>
      <ul className="book-list">
        {filteredBooks.map((book) => (
          <li
            key={book.book_id}
            onClick={() => handleRecommend(book)}
          >
            <strong>{book.title}</strong>
            <p>{book.description}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
