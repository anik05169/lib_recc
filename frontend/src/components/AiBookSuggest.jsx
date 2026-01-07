import { useState } from "react";
import BookCard from "./BookCard";

export default function AiBookSuggest() {
  const [aiQuery, setAiQuery] = useState("");
  const [aiSuggestions, setAiSuggestions] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  const getAiSuggestions = async () => {
    if (!aiQuery.trim()) return;

    setAiLoading(true);
    setAiSuggestions(null);

    try {
      const res = await fetch("http://localhost:8000/books/ai-suggest-new", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: aiQuery }),
      });

      const data = await res.json();
      setAiSuggestions(data.recommendations);
    } catch (err) {
      console.error("AI suggestion error:", err);
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <>
      <h3>AI Book Suggestions</h3>

      <div className="ai-suggest-box">
        <textarea
          placeholder="Describe the kind of book you want..."
          value={aiQuery}
          onChange={(e) => setAiQuery(e.target.value)}
        />

        <button onClick={getAiSuggestions} disabled={aiLoading}>
          {aiLoading ? "Thinking..." : "Suggest Books"}
        </button>
      </div>

      {aiSuggestions && (
        <>
          <h4>AI Suggested Books</h4>

          {Array.isArray(aiSuggestions) ? (
            <div className="book-list">
              {aiSuggestions.map((book, idx) => (
                <BookCard key={idx} book={book} />
              ))}
            </div>
          ) : (
            <pre style={{ whiteSpace: "pre-wrap", marginTop: 10 }}>
              {aiSuggestions}
            </pre>
          )}
        </>
      )}
    </>
  );
}
