// AddCustomBook.jsx

export default function AddCustomBook({ newBook, setNewBook, addCustomBook }) {
  return (
    <div className="add-custom-section" style={{ marginTop: '3rem', borderTop: '1px solid var(--border)', paddingTop: '2rem' }}>
      <h3 style={{ marginBottom: '1.5rem' }}>Personal Entry</h3>

      <div className="add-book-form" style={{ display: 'grid', gridTemplateColumns: 'minmax(200px, 1fr) 2fr', gap: '1.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <input
            placeholder="Book ID"
            type="number"
            value={newBook.book_id || ""}
            onChange={(e) =>
              setNewBook({ ...newBook, book_id: e.target.value })
            }
          />

          <input
            placeholder="Title"
            value={newBook.title || ""}
            onChange={(e) =>
              setNewBook({ ...newBook, title: e.target.value })
            }
          />

          <input
            placeholder="Image URL (optional)"
            value={newBook.image_url || ""}
            onChange={(e) =>
              setNewBook({ ...newBook, image_url: e.target.value })
            }
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <textarea
            style={{ flex: 1, minHeight: '130px' }}
            placeholder="What is this book about?"
            value={newBook.description || ""}
            onChange={(e) =>
              setNewBook({ ...newBook, description: e.target.value })
            }
          />
          <button onClick={addCustomBook} style={{ width: '100%' }}>
            Add to My Collection
          </button>
        </div>
      </div>
    </div>

  );
}
