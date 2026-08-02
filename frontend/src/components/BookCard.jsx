//BookCard.jsx

export default function BookCard({ book, children, inLibrary, showDescription = true }) {
  return (
    <li className="book-card">
      {inLibrary && (
        <span className="badge-in-library">In collection</span>
      )}

      <div className="book-card-main">
        <img
          src={book.image_url || "https://placehold.co/150x200?text=No+Image"}
          alt={book.title}
          className="book-cover"
          onError={(e) => {
            e.target.src = "https://placehold.co/150x200?text=No+Image";
          }}
        />

        <div className="book-content">
          <strong>{book.title}</strong>
          {showDescription && (
            <p className="book-description">
              {book.description || "No description available."}
            </p>
          )}
        </div>
      </div>

      <div className="book-card-actions">
        {children}
      </div>
    </li>
  );
}
