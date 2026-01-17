import { useState } from "react";
import { API_BASE_URL } from "../api";
import BookCard from "./BookCard";

/* ------------------ Helpers ------------------ */

// Fetch book cover from Google Books (free)
async function fetchBookImage(title, author) {
  try {
    const query = encodeURIComponent(`${title} ${author}`);
    const res = await fetch(
      `https://www.googleapis.com/books/v1/volumes?q=${query}&maxResults=1`
    );
    const data = await res.json();

    return (
      data.items?.[0]?.volumeInfo?.imageLinks?.thumbnail ||
      "/placeholder.jpg"
    );
  } catch {
    return "/placeholder.jpg";
  }
}

/* ------------------ Component ------------------ */

export default function AiBookSuggest({ setNewBook, addCustomBook }) {
  const [aiQuery, setAiQuery] = useState("");
  const [aiSuggestions, setAiSuggestions] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);

  const handleAddToLibrary = (book) => {
    setNewBook({
      book_id: Date.now() % 1000000,
      title: book.title,
      description: book.description,
      image_url: book.image_url || "/placeholder.jpg",
    });

    addCustomBook(); // 🔥 reuse existing logic
  };



  const getAiSuggestions = async () => {
    if (!aiQuery.trim()) return;

    setAiLoading(true);
    setAiSuggestions([]);

    try {
      const res = await fetch(`${API_BASE_URL.replace(/\/$/, "")}/books/ai-suggest-new`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: aiQuery }),
      });

      const data = await res.json();

      // 🔥 ADD IMAGE + ID TO EACH BOOK
      const enriched = await Promise.all(
        (data.recommendations || []).map(async (book, idx) => ({
          ...book,
          book_id: `${Date.now()}-${idx}`,
          image_url: await fetchBookImage(book.title, book.author),
        }))
      );

      setAiSuggestions(enriched);
    } catch (err) {
      console.error("AI suggestion error:", err);
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <>
      <h3>AI Book Suggestions</h3>

      <div className="ai-suggest-box">
        <textarea
          placeholder="Describe the kind of book you want (e.g. football biography, beginner AI, fantasy)..."
          value={aiQuery}
          onChange={(e) => setAiQuery(e.target.value)}
        />

        <button onClick={getAiSuggestions} disabled={aiLoading}>
          {aiLoading ? "Thinking..." : "Suggest Books"}
        </button>
      </div>

      {aiSuggestions.length > 0 && (
        <>
          <h4>AI Suggested Books</h4>

          <ul className="book-list">
            {aiSuggestions.map((book) => (
              <BookCard
                key={book.book_id}
                book={book}
                showDescription
              >
                <button
                  onClick={() => handleAddToLibrary(book)}
                  style={{
                    marginTop: "6px",
                    padding: "8px",
                    width: "100%",
                    background: "#4f8cff",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer",
                  }}
                >
                  ➕ Add to My Library
                </button>
              </BookCard>
            ))}
          </ul>
        </>
      )}

    </>
  );
}
