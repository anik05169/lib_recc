//BookCard.jsx

export default function BookCard({ book, children, showDescription }) {
  return (
    <li className="book-card">
      <div className="book-card-main">
        <img
          src={book.image_url || "https://via.placeholder.com/150x200?text=No+Image"}
          alt={book.title}
          className="book-cover"
          onError={(e) => {
            e.target.src = "https://via.placeholder.com/150x200?text=No+Image";
          }}
        />

        <div className="book-content">
          <strong>{book.title}</strong>
          <p className="book-description">
            {book.description || "No description available."}
          </p>
        </div>
      </div>

      <div className="book-card-actions">
        {children}
      </div>
    </li>
  );
}
