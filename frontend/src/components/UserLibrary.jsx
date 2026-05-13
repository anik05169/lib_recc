import BookCard from "./BookCard";
import { useState } from "react";

export default function UserLibrary({
  books,
  avgRatings,
  userRatings,
  rateBook,
  setUserBooks,
  expandedBookId,
  openBookDetails,
  recommendations,
  deleteFromLibrary,
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', width: '100%', flexWrap: 'wrap' }}>
            <button
              className="btn-secondary"
              onClick={() => openBookDetails(book)}
            >
              {expandedBookId === book.book_id ? "Hide Similar" : "Find Similar"}
            </button>

            <button
              className="btn-danger"
              onClick={() => deleteFromLibrary(book.book_id)}
              title="Remove from library"
            >
              Remove
            </button>

            <div className="rating-select-wrapper" style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
              {avgRatings[book.book_id] && (
                <span style={{ color: '#fbbf24', fontWeight: 'bold', fontSize: '0.85rem' }}>
                  ★ {avgRatings[book.book_id]}
                </span>
              )}
              <select
                className="btn-secondary"
                style={{ padding: '6px 12px', width: 'auto' }}
                value={userRatings?.[book.book_id] || book.currentRating || ""}
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
                    {r} {r === 1 ? 'Star' : 'Stars'}
                  </option>
                ))}
              </select>
            </div>
          </div>


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
