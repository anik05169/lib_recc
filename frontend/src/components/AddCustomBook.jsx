// AddCustomBook.jsx

export default function AddCustomBook({ newBook, setNewBook, addCustomBook }) {
  return (
    <>
      <h3>Add Your Own Book</h3>

      <div className="add-book-form">
        <input
          placeholder="Book ID (number)"
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

        <textarea
          placeholder="Description"
          value={newBook.description || ""}
          onChange={(e) =>
            setNewBook({ ...newBook, description: e.target.value })
          }
        />

        {/* 🔥 ADD THIS INPUT */}
        <input
          placeholder="Image URL (optional)"
          value={newBook.image_url || ""}
          onChange={(e) =>
            setNewBook({ ...newBook, image_url: e.target.value })
          }
        />

        <button onClick={addCustomBook}>Add Book</button>
      </div>
    </>
  );
}
