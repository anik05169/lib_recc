import { useState } from "react";
import { getApiBaseUrl, PLACEHOLDER_IMAGE_URL } from "../api";
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
        console.warn("Google Books API rate limit hit (429).");
        return { error: 429, url: "https://placehold.co/150x200?text=No+Image" };
      }
      return { error: res.status, url: "https://placehold.co/150x200?text=No+Image" };
    }

    const data = await res.json();
    const thumbnail = data.items?.[0]?.volumeInfo?.imageLinks?.thumbnail;
    return { error: null, url: thumbnail || "https://placehold.co/150x200?text=No+Image" };
  } catch (error) {
    console.error("Error fetching book image:", error);
    return { error: "fetch_error", url: "https://placehold.co/150x200?text=No+Image" };
  }
}

/* ------------------ Component ------------------ */

export default function AiBookSuggest({ setNewBook, addCustomBook, showToast, getAuthHeaders }) {
  const [aiQuery, setAiQuery] = useState("");
  const [aiSuggestions, setAiSuggestions] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);

  const handleAddToLibrary = (book) => {
    const bookData = {
      title: book.title,
      description: book.description,
      image_url: book.image_url || PLACEHOLDER_IMAGE_URL,
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
      const res = await fetch(`${getApiBaseUrl()}/books/ai-suggest-new`, {
        method: "POST",
        headers: getAuthHeaders ? getAuthHeaders() : { "Content-Type": "application/json" },
        body: JSON.stringify({ description: aiQuery }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : Array.isArray(data.detail)
              ? data.detail.map((d) => d.msg || JSON.stringify(d)).join("; ")
              : null;

        if (res.status === 401) {
          showToast?.("Please log in to use AI suggestions", "warning");
          return;
        }
        if (res.status === 503) {
          showToast?.(detail || "AI suggestions are not configured", "warning");
          return;
        }
        showToast?.(detail || `AI request failed (${res.status})`, "error");
        return;
      }

      const data = await res.json();
      const recommendations = data.recommendations || [];
      const enriched = [];

      // Fetch images sequentially with a delay to avoid 429 rate limiting
      let isRateLimited = false;
      for (let i = 0; i < recommendations.length; i++) {
        const book = recommendations[i];
        let imageUrl = "https://placehold.co/150x200?text=No+Image";

        if (!isRateLimited) {
          const result = await fetchBookImage(book.title, book.author);
          imageUrl = result.url;
          if (result.error === 429) {
            isRateLimited = true;
          }
        }

        enriched.push({
          ...book,
          book_id: `${Date.now()}-${i}`,
          image_url: imageUrl,
        });

        // Delay to avoid rate limiting
        if (!isRateLimited && i < recommendations.length - 1) {
          await sleep(1000);
        }
      }

      setAiSuggestions(enriched);
      if (enriched.length > 0) {
        showToast?.(`Found ${enriched.length} AI recommendations!`, "success");
      }
    } catch (err) {
      console.error("AI suggestion error:", err);
      showToast?.(
        err?.message ? `AI suggestion failed: ${err.message}` : "AI suggestion failed. Try again later.",
        "error"
      );
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <>
      <div className="ai-suggest-box">
        <h3>AI suggestions</h3>
        <p className="section-lead">
          Describe a mood, genre, or theme — get fresh titles to add privately.
        </p>
        <textarea
          placeholder="I'm looking for a gripping sci-fi novel about time travel…"
          value={aiQuery}
          onChange={(e) => setAiQuery(e.target.value)}
          aria-label="Describe books you want"
        />

        <button type="button" onClick={getAiSuggestions} disabled={aiLoading}>
          {aiLoading ? "Finding books…" : "Get recommendations"}
        </button>
      </div>

      {aiSuggestions.length > 0 && (
        <div className="ai-results">
          <h4>Suggested for you</h4>

          <ul className="book-list">
            {aiSuggestions.map((book) => (
              <BookCard
                key={book.book_id}
                book={book}
                showDescription
              >
                <button type="button" onClick={() => handleAddToLibrary(book)}>
                  Add to collection
                </button>
              </BookCard>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}
