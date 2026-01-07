import AiBookSuggest from "../components/AiBookSuggest";
import AddCustomBook from "../components/AddCustomBook";
import UserLibrary from "../components/UserLibrary";

export default function LibraryView(props) {
  const {
    books,
    loading,
    newBook,
    setNewBook,
    addCustomBook,
  } = props;

  return (
    <>
      <h2>My Library</h2>

      <AiBookSuggest />

      <AddCustomBook
        newBook={newBook}
        setNewBook={setNewBook}
        addCustomBook={addCustomBook}
      />

      {loading && <p>Loading library...</p>}

      {books?.length > 0 && <UserLibrary {...props} />}
    </>
  );
}
