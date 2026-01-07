import BookCard from "./BookCard";
import { useState } from "react";

export default function UserLibrary({
  books,
  avgRatings,
  rateBook,
  setUserBooks,
  expandedBookId,
  openBookDetails,
  recommendations,
}) {
  const [expandedRecId, setExpandedRecId] = useState(null);

  return (
    <ul className="book-list">
      {books.map((book) => (
        <BookCard
          key={book.book_id}
          book={book}
          showDescription={expandedBookId === book.book_id}
        >
          {avgRatings[book.book_id] && <p>⭐ {avgRatings[book.book_id]}</p>}

          <button onClick={() => openBookDetails(book)}>
            {expandedBookId === book.book_id ? "Hide Details" : "View Details"}
          </button>

          <select
            value={book.currentRating || ""}
            onChange={(e) => {
              const rating = Number(e.target.value);
              setUserBooks((prev) =>
                prev.map((b) =>
                  b.book_id === book.book_id
                    ? { ...b, currentRating: rating }
                    : b
                )
              );
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

          {expandedBookId === book.book_id && (
            <div className="recommendation-box">
              <h4>Related Books in Your Library</h4>

              {!recommendations[book.book_id] ? (
                <p>Loading recommendations...</p>
              ) : recommendations[book.book_id].length === 0 ? (
                <p>No related books found.</p>
              ) : (
                <ul className="recommend-list">
                  {recommendations[book.book_id].map((b) => (
                    <li
                      key={b.book_id}
                      onClick={() =>
                        setExpandedRecId(
                          expandedRecId === b.book_id ? null : b.book_id
                        )
                      }
                    >
                      <strong>{b.title}</strong>
                      {expandedRecId === b.book_id && <p>{b.description}</p>}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </BookCard>
      ))}
    </ul>
  );
}
