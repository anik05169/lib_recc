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
  const skipInitialSearch = useRef(true);

  useEffect(() => {
    if (skipInitialSearch.current) {
      skipInitialSearch.current = false;
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      onSearch(localSearch);
    }, 400);
    return () => clearTimeout(debounceRef.current);
  }, [localSearch, onSearch]);

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

  const totalLabel =
    typeof pagination.total === "number"
      ? `${pagination.total.toLocaleString()} book${pagination.total === 1 ? "" : "s"}`
      : null;

  return (
    <>
      <div className="section-heading">
        <h2>Catalog</h2>
        {totalLabel && !loading && (
          <p className="section-meta">{totalLabel}</p>
        )}
      </div>

      <div className="search-bar-wrapper">
        <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <circle cx="11" cy="11" r="7" />
          <path d="M20 20l-3.5-3.5" strokeLinecap="round" />
        </svg>
        <label htmlFor="catalog-search" className="visually-hidden">
          Search catalog
        </label>
        <input
          type="search"
          placeholder="Search by title or description…"
          value={localSearch}
          onChange={(e) => setLocalSearch(e.target.value)}
          id="catalog-search"
          autoComplete="off"
        />
      </div>

      {loading && (!books || books.length === 0) && (
        <ul className="book-list">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={`skel-${i}`} />
          ))}
        </ul>
      )}

      {loading && books && books.length > 0 && (
        <p className="catalog-updating">Updating results…</p>
      )}

      {!loading && (!books || books.length === 0) && (
        <div className="empty-state">
          <p>
            {searchQuery
              ? `No books found for “${searchQuery}”. Try a different search.`
              : "No books in the catalog yet."}
          </p>
        </div>
      )}

      {books && books.length > 0 && (
        <ul className="book-list">
          {books.map((book) => (
            <BookCard
              key={book.book_id}
              book={book}
              showDescription={expandedBookId === book.book_id}
              inLibrary={userBookIds?.has(book.book_id)}
            >
              <button
                type="button"
                className="btn-secondary"
                onClick={() => openBookDetails(book)}
              >
                {expandedBookId === book.book_id
                  ? "Hide recommendations"
                  : "Similar books"}
              </button>

              <button
                type="button"
                onClick={() => addFromCatalog(book.book_id)}
                disabled={userBookIds?.has(book.book_id)}
              >
                {userBookIds?.has(book.book_id) ? "Collected" : "Collect book"}
              </button>

              {expandedBookId === book.book_id && (
                <div className="recommendation-box">
                  <h4>Related books</h4>

                  {!recommendations[book.book_id] ? (
                    <p>Loading recommendations…</p>
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
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault();
                              setExpandedRecId(
                                expandedRecId === b.book_id ? null : b.book_id
                              );
                            }
                          }}
                          role="button"
                          tabIndex={0}
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

      {pagination.pages > 1 && (
        <div className="pagination" aria-label="Catalog pages">
          <button
            type="button"
            className="btn-secondary"
            disabled={pagination.page <= 1}
            onClick={() => onPageChange(pagination.page - 1)}
          >
            Prev
          </button>

          {getPageNumbers().map((p) => (
            <button
              type="button"
              key={p}
              className={p === pagination.page ? "active-page" : "btn-secondary"}
              aria-current={p === pagination.page ? "page" : undefined}
              onClick={() => onPageChange(p)}
            >
              {p}
            </button>
          ))}

          <span className="pagination-info">
            of {pagination.pages}
            {typeof pagination.total === "number" && (
              <> · {pagination.total.toLocaleString()} total</>
            )}
          </span>

          <button
            type="button"
            className="btn-secondary"
            disabled={pagination.page >= pagination.pages}
            onClick={() => onPageChange(pagination.page + 1)}
          >
            Next
          </button>
        </div>
      )}
    </>
  );
}
