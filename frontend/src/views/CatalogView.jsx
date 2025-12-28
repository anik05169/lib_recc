import { useState } from "react";
import BookCard from "../components/BookCard";

export default function CatalogView({
  books,
  loading,
  expandedBookId,
  recommendations,
  openBookDetails,
  addFromCatalog,
}) {
  // Hooks MUST be first
  const [expandedRecId, setExpandedRecId] = useState(null);

  if (!books || books.length === 0) return <p>No books found.</p>;

  return (
    <>
      <h2>Catalog</h2>
      {loading && <p>Loading catalog...</p>}

      <ul className="book-list">
        {books.map((book) => (
          <BookCard
            key={book.book_id}
            book={book}
            showDescription={expandedBookId === book.book_id}
          >
            <button onClick={() => openBookDetails(book)}>
              {expandedBookId === book.book_id
                ? "Hide Details"
                : "View Details"}
            </button>

            <button onClick={() => addFromCatalog(book.book_id)}>
              Add to My Library
            </button>

            {/* ✅ Recommendations MUST be inside this book */}
            {expandedBookId === book.book_id && (
              <div className="recommendation-box">
                <h4>Related Books</h4>

                {!recommendations[book.book_id] ? (
                  <p>Loading recommendations...</p>
                ) : recommendations[book.book_id].length === 0 ? (
                  <p>No related books found.</p>
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


