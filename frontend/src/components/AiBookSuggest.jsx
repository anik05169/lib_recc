import { useState } from "react";
import { API_BASE_URL } from "../api";
import BookCard from "./BookCard";

/* ------------------ Helpers ------------------ */

// Fetch book cover from Google Books (free)
async function fetchBookImage(title, author) {
  try {
    const apiKey = import.meta.env.VITE_GOOGLE_BOOKS_API_KEY;
    const query = encodeURIComponent(`${title} ${author}`);
    const url = `https://www.googleapis.com/books/v1/volumes?q=${query}&maxResults=1${apiKey ? `&key=${apiKey}` : ""}`;

    const res = await fetch(url);

    if (!res.ok) {
      if (res.status === 429) {
        console.warn("Google Books API rate limit hit (429). Consider adding an API key.");
      }
      return "https://via.placeholder.com/150x200?text=No+Image";
    }

    const data = await res.json();
    return (
      data.items?.[0]?.volumeInfo?.imageLinks?.thumbnail ||
      "https://via.placeholder.com/150x200?text=No+Image"
    );
  } catch (error) {
    console.error("Error fetching book image:", error);
    return "https://via.placeholder.com/150x200?text=No+Image";
  }
}

/* ------------------ Component ------------------ */

export default function AiBookSuggest({ setNewBook, addCustomBook }) {
  const [aiQuery, setAiQuery] = useState("");
  const [aiSuggestions, setAiSuggestions] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);

  const handleAddToLibrary = (book) => {
    const bookData = {
      book_id: Date.now() % 1000000,
      title: book.title,
      description: book.description,
      image_url: book.image_url || "/placeholder.jpg",
    };
    setNewBook(bookData);
    addCustomBook(bookData);
  };



  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

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
      const recommendations = data.recommendations || [];
      const enriched = [];

      // Fetch images sequentially with a delay to avoid 429 rate limiting
      for (let i = 0; i < recommendations.length; i++) {
        const book = recommendations[i];
        const imageUrl = await fetchBookImage(book.title, book.author);

        enriched.push({
          ...book,
          book_id: `${Date.now()}-${i}`,
          image_url: imageUrl,
        });

        // Add a small delay between requests if there are more to fetch
        if (i < recommendations.length - 1) {
          await sleep(500); // 500ms delay to be safe
        }
      }

      setAiSuggestions(enriched);
    } catch (err) {
      console.error("AI suggestion error:", err);
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <>
      <div className="ai-suggest-box">
        <h3>AI Assistant Suggestions</h3>
        <textarea
          placeholder="I'm looking for a gripping sci-fi novel about time travel..."
          value={aiQuery}
          onChange={(e) => setAiQuery(e.target.value)}
        />

        <button onClick={getAiSuggestions} disabled={aiLoading}>
          {aiLoading ? "Consulting AI..." : "Get Recommendations"}
        </button>
      </div>

      {aiSuggestions.length > 0 && (
        <div className="ai-results">
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
                >
                  Add to Collection
                </button>
              </BookCard>
            ))}
          </ul>
        </div>
      )}


    </>
  );
}
