import BookCard from "./BookCard";
import { useState } from "react";

function RecommendList({ books, expandedRecId, setExpandedRecId }) {
  return (
    <ul className="recommend-list">
      {books.map((b) => (
        <li
          key={b.book_id}
          onClick={() =>
            setExpandedRecId(expandedRecId === b.book_id ? null : b.book_id)
          }
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              setExpandedRecId(expandedRecId === b.book_id ? null : b.book_id);
            }
          }}
          role="button"
          tabIndex={0}
        >
          <strong>{b.title}</strong>
          {expandedRecId === b.book_id && (
            <p className="recommend-description">{b.description}</p>
          )}
        </li>
      ))}
    </ul>
  );
}

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

  const handleRemove = (book) => {
    if (!window.confirm(`Remove "${book.title}" from your collection?`)) {
      return;
    }
    deleteFromLibrary(book.book_id);
  };

  return (
    <ul className="book-list">
      {books.map((book) => {
        const recPayload = recommendations[book.book_id];
        const catalogRecs = Array.isArray(recPayload)
          ? recPayload
          : recPayload?.catalog;
        const libraryRecs = Array.isArray(recPayload)
          ? []
          : recPayload?.library || [];
        const showLibrarySection =
          Array.isArray(libraryRecs) && libraryRecs.length >= 1;

        return (
          <BookCard
            key={book.book_id}
            book={book}
            showDescription={expandedBookId === book.book_id}
          >
            <div className="rating-row">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => openBookDetails(book)}
              >
                {expandedBookId === book.book_id ? "Hide similar" : "Find similar"}
              </button>

              <button
                type="button"
                className="btn-danger"
                onClick={() => handleRemove(book)}
                title="Remove from library"
              >
                Remove
              </button>

              <div className="rating-select-wrapper">
                {avgRatings[book.book_id] && (
                  <span className="rating-avg">
                    ★ {avgRatings[book.book_id]}
                  </span>
                )}
                <select
                  className="btn-secondary rating-select"
                  aria-label={`Rate ${book.title}`}
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
                      {r} {r === 1 ? "star" : "stars"}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {expandedBookId === book.book_id && (
              <div className="recommendation-box">
                {!recPayload ? (
                  <p>Loading recommendations…</p>
                ) : (
                  <>
                    <div className="recommendation-section">
                      <h4>Similar books</h4>
                      {!catalogRecs || catalogRecs.length === 0 ? (
                        <p>No similar books found in the catalog.</p>
                      ) : (
                        <RecommendList
                          books={catalogRecs}
                          expandedRecId={expandedRecId}
                          setExpandedRecId={setExpandedRecId}
                        />
                      )}
                    </div>

                    {showLibrarySection && (
                      <div className="recommendation-section">
                        <h4>Also in your library</h4>
                        <RecommendList
                          books={libraryRecs}
                          expandedRecId={expandedRecId}
                          setExpandedRecId={setExpandedRecId}
                        />
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </BookCard>
        );
      })}
    </ul>
  );
}
