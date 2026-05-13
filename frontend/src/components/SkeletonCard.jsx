export default function SkeletonCard() {
  return (
    <li className="book-card skeleton-card">
      <div className="book-card-main">
        <div className="skeleton skeleton-cover" />
        <div className="book-content">
          <div className="skeleton skeleton-title" />
          <div className="skeleton skeleton-text" />
          <div className="skeleton skeleton-text short" />
        </div>
      </div>
      <div className="book-card-actions">
        <div className="skeleton skeleton-btn" />
        <div className="skeleton skeleton-btn" />
      </div>
    </li>
  );
}
