from langchain_ollama import OllamaLLM, OllamaEmbeddings

from langchain_community.vectorstores import FAISS

llm = OllamaLLM(model="phi3:mini")
embeddings = OllamaEmbeddings(model="phi3:mini")

def suggest_books_from_description(
    user_description: str,
    books: list,
    k: int = 3
):
    """
    user_description: text entered by user
    books: [{title, description}]
    """

    texts = [b["description"] for b in books]
    vector_db = FAISS.from_texts(texts, embeddings)

    docs = vector_db.similarity_search(user_description, k=k)

    results = []
    for doc in docs:
        for book in books:
            if book["description"] == doc.page_content:
                results.append(book)
                break

    return results
