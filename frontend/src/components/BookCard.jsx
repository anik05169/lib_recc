//BookCard.jsx

export default function BookCard({ book, children, showDescription }) {
  return (
    <li className="book-card">
      <img
        src={book.image_url || "/placeholder.jpg"}
        alt={book.title}
        className="book-cover"
        onError={(e) => {
          e.target.src = "/placeholder.jpg";
        }}
      />

      <div className="book-content">
        <strong>{book.title}</strong>

        {showDescription && (
          <p className="book-description">{book.description}</p>
        )}

        {children}
      </div>
    </li>
  );
}

