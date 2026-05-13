// LibraryView.jsx

import AiBookSuggest from "../components/AiBookSuggest";
import AddCustomBook from "../components/AddCustomBook";
import UserLibrary from "../components/UserLibrary";
import SkeletonCard from "../components/SkeletonCard";

export default function LibraryView(props) {
  const {
    books,
    loading,
    newBook,
    setNewBook,
    addCustomBook,
    showToast,
    getAuthHeaders,
  } = props;

  return (
    <>
      <h2>My Library</h2>

      <AiBookSuggest
        setNewBook={setNewBook}
        addCustomBook={addCustomBook}
        showToast={showToast}
        getAuthHeaders={getAuthHeaders}
      />

      <AddCustomBook
        newBook={newBook}
        setNewBook={setNewBook}
        addCustomBook={addCustomBook}
      />

      {/* Skeleton loaders */}
      {loading && (
        <ul className="book-list" style={{ marginTop: "2rem" }}>
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={`skel-lib-${i}`} />
          ))}
        </ul>
      )}

      {!loading && books?.length === 0 && (
        <p style={{ color: "var(--text-muted)", textAlign: "center", padding: "3rem" }}>
          Your library is empty. Add books from the catalog or use the AI assistant!
        </p>
      )}

      {!loading && books?.length > 0 && <UserLibrary {...props} />}
    </>
  );
}
