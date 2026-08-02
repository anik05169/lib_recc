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

  const count = books?.length ?? 0;

  return (
    <>
      <div className="section-heading">
        <h2>My collection</h2>
        {!loading && (
          <p className="section-meta">
            {count === 0 ? "Empty shelf" : `${count} book${count === 1 ? "" : "s"}`}
          </p>
        )}
      </div>

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

      {loading && (
        <ul className="book-list library-toolbar">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={`skel-lib-${i}`} />
          ))}
        </ul>
      )}

      {!loading && books?.length === 0 && (
        <div className="empty-state">
          <p>
            Your collection is empty. Collect books from the catalog or ask the AI assistant for ideas.
          </p>
        </div>
      )}

      {!loading && books?.length > 0 && <UserLibrary {...props} />}
    </>
  );
}
