import { useState } from "react";
import BookCard from "../components/BookCard";

export default function LibraryView({
  books,
  loading,
  avgRatings,
  rateBook,
  setUserBooks,
  newBook,
  setNewBook,
  addCustomBook,
  expandedBookId,
  recommendations,
  openBookDetails,
}) {
  const [expandedRecId, setExpandedRecId] = useState(null);

  if (!books || books.length === 0) {
    return (
      <>
        <h2>My Library</h2>
        {loading && <p>Loading library...</p>}
        {!loading && <p>No books in your library yet. Add some from the catalog or create your own!</p>}
        
        {/* ADD CUSTOM BOOK */}
        <h3>Add Your Own Book</h3>
        <div className="add-book-form">
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
        </div>
      </>
    );
  }

  return (
    <>
      <h2>My Library</h2>

      {/* ADD CUSTOM BOOK */}
      <h3>Add Your Own Book</h3>
      <div className="add-book-form">
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
      </div>

      {loading && <p>Loading library...</p>}

      <ul className="book-list">
        {books.map((book) => (
          <BookCard
            key={book.book_id}
            book={book}
            showDescription={expandedBookId === book.book_id}
          >
            {avgRatings[book.book_id] && (
              <p>⭐ {avgRatings[book.book_id]}</p>
            )}

            <button onClick={() => openBookDetails(book)}>
              {expandedBookId === book.book_id
                ? "Hide Details"
                : "View Details"}
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

            {/* Recommendations for library books */}
            {expandedBookId === book.book_id && (
              <div className="recommendation-box">
                <h4>Related Books in Your Library</h4>

                {!recommendations[book.book_id] ? (
                  <p>Loading recommendations...</p>
                ) : recommendations[book.book_id].length === 0 ? (
                  <p>No related books found in your library.</p>
                ) : (
                  <ul className="recommend-list">
                    {recommendations[book.book_id].map((b) => (
                      <li
                        key={b.book_id}
                        style={{ cursor: "pointer" }}
                        onClick={() =>
                          setExpandedRecId(
                            expandedRecId === b.book_id
                              ? null
                              : b.book_id
                          )
                        }
                      >
                        <strong>{b.title}</strong>

                        {expandedRecId === b.book_id && (
                          <p className="recommend-description">
                            {b.description}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </BookCard>
        ))}
      </ul>
    </>
  );
}
