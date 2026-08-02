export default function AddCustomBook({ newBook, setNewBook, addCustomBook }) {
  return (
    <div className="add-custom-section">
      <h3>Personal entry</h3>
      <p className="section-lead">
        Add a book that is not in the catalog. It stays private to your collection.
      </p>

      <div className="add-book-form">
        <div className="add-book-fields">
          <input
            placeholder="Title"
            value={newBook.title || ""}
            onChange={(e) =>
              setNewBook({ ...newBook, title: e.target.value })
            }
            aria-label="Book title"
          />

          <input
            placeholder="Image URL (optional)"
            value={newBook.image_url || ""}
            onChange={(e) =>
              setNewBook({ ...newBook, image_url: e.target.value })
            }
            aria-label="Cover image URL"
          />
        </div>

        <div className="add-book-fields">
          <textarea
            placeholder="What is this book about?"
            value={newBook.description || ""}
            onChange={(e) =>
              setNewBook({ ...newBook, description: e.target.value })
            }
            aria-label="Book description"
          />
          <button type="button" onClick={() => addCustomBook()}>
            Add to my collection
          </button>
        </div>
      </div>
    </div>
  );
}
