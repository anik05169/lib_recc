import { useState, useEffect, useRef } from "react";
import BookCard from "../components/BookCard";
import SkeletonCard from "../components/SkeletonCard";

export default function CatalogView({
  books,
  loading,
  expandedBookId,
  recommendations,
  openBookDetails,
  addFromCatalog,
  userBookIds,
  searchQuery,
  onSearch,
  pagination,
  onPageChange,
}) {
  const [expandedRecId, setExpandedRecId] = useState(null);
  const [localSearch, setLocalSearch] = useState(searchQuery || "");
  const debounceRef = useRef(null);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      onSearch(localSearch);
    }, 400);
    return () => clearTimeout(debounceRef.current);
  }, [localSearch]);

  // Generate page numbers for pagination
  const getPageNumbers = () => {
    const pages = [];
    const total = pagination.pages;
    const current = pagination.page;
    const delta = 2;
    for (let i = Math.max(1, current - delta); i <= Math.min(total, current + delta); i++) {
      pages.push(i);
    }
    return pages;
  };

  return (
    <>
      <h2>Catalog</h2>

      {/* Search Bar */}
      <div className="search-bar-wrapper">
        <span className="search-icon">🔍</span>
        <input
          type="text"
          placeholder="Search books by title or description..."
          value={localSearch}
          onChange={(e) => setLocalSearch(e.target.value)}
          id="catalog-search"
        />
      </div>

      {/* Skeleton loaders while loading */}
      {loading && (
        <ul className="book-list">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={`skel-${i}`} />
          ))}
        </ul>
      )}

      {/* No results */}
      {!loading && (!books || books.length === 0) && (
        <p style={{ color: "var(--text-muted)", textAlign: "center", padding: "3rem" }}>
          {searchQuery ? `No books found for "${searchQuery}"` : "No books in catalog yet."}
        </p>
      )}

      {/* Book grid */}
      {!loading && books && books.length > 0 && (
        <ul className="book-list">
          {books.map((book) => (
            <BookCard
              key={book.book_id}
              book={book}
              showDescription={expandedBookId === book.book_id}
              inLibrary={userBookIds?.has(book.book_id)}
            >
              <button
                className="btn-secondary"
                onClick={() => openBookDetails(book)}
              >
                {expandedBookId === book.book_id
                  ? "Hide Recommendations"
                  : "Similar Books"}
              </button>

              <button
                onClick={() => addFromCatalog(book.book_id)}
                disabled={userBookIds?.has(book.book_id)}
              >
                {userBookIds?.has(book.book_id) ? "Collected ✓" : "Collect Book"}
              </button>

              {/* Recommendations inside this book card */}
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
                              expandedRecId === b.book_id ? null : b.book_id
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
      )}

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="pagination">
          <button
            className="btn-secondary"
            disabled={pagination.page <= 1}
            onClick={() => onPageChange(pagination.page - 1)}
          >
            ‹ Prev
          </button>

          {getPageNumbers().map((p) => (
            <button
              key={p}
              className={p === pagination.page ? "active-page" : "btn-secondary"}
              onClick={() => onPageChange(p)}
            >
              {p}
            </button>
          ))}

          <span className="pagination-info">
            of {pagination.pages}
          </span>

          <button
            className="btn-secondary"
            disabled={pagination.page >= pagination.pages}
            onClick={() => onPageChange(pagination.page + 1)}
          >
            Next ›
          </button>
        </div>
      )}
    </>
  );
}
