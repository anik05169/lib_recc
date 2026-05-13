# Personal Library & Recommendation System

This project is a comprehensive library catalog and book recommendation platform. It features user authentication, personal libraries, global and personalized content-based recommender systems, and an AI-powered librarian that suggests books based on natural language prompts.

## 🚀 Features Focus

### 1. Robust Authentication & User Management
- **JWT-Based Auth:** Secure login and registration using JSON Web Tokens.
- **Password Hashing:** Passwords are encrypted utilizing `bcrypt` via `passlib`.
- **Personalized State:** Every user maintains their private collection of books separate from the global library catalog.

### 2. Dual Recommender System 
- **Global Catalog Recommender:** Suggests books similar to a selected book from the main catalog.
- **User-Specific Recommender:** Users can add custom, private books to their own vault. The system trains a bespoke recommendation model strictly around a user's local dataset. 
- *How it works:* Uses **TF-IDF** (Term Frequency-Inverse Document Frequency) vectorization on book descriptions and computes similarities utilizing **Cosine Similarity**. The implementation handles these computations without relying heavily on massive ML dependencies, keeping the application lightweight.

### 3. AI Book Assistant (LLM Integration via HuggingFace)
- Users can naturally describe what they want to read (e.g., *"recommend me a mystery novel set in the 1920s"*).
- The system connects with the HuggingFace API, explicitly querying the **Meta-Llama-3-8B-Instruct** model.
- The prompt engineering guarantees the LLM responds in a strict, predictable JSON format representing exactly 3 real book propositions.

### 4. Dynamic Library & Rating System
- **Add from Catalog / Add Custom:** Users expand their libraries using standard references or their distinct items.
- **Rating system:** Users can rate books (1-5), and data feeds an aggregate rating pipeline.

---

## 🛠️ Technology Stack & Architecture

### Backend Stack (Core Focus)

The backend is structurally decoupled and follows modern Python standards. It acts as the backbone for both the API delivery and Machine Learning logic.

* **FastAPI:** 
   * *Why:* Selected for its blazing fast execution speed (ASGI), its intuitive and developer-friendly declaration of endpoints, and the automatic interactive API documentation it generates out of the box (Swagger UI).
* **MongoDB (via `pymongo`):** 
   * *Why:* The unstructured nature of books (some might have varying identifiers, null image references, or specific user metadata) perfectly fits NoSQL document schemas. Features like Upsert are seamlessly integrated.
* **Pydantic:** 
   * *Why:* For meticulous data validation. Models define schemas for incoming API requests (e.g. `UserLogin`, `Book`, `Rating`), strictly typing inputs and sanitizing payloads before they interface with business logic.
* **HuggingFace Inference API Pipeline:** 
   * *Why:* Instead of hosting resource-thirsty LLMs locally, leveraging the inference API maintains the application's lightweight architecture while still offering sophisticated LLaMA-based natural language recommendations.
* **Pandas:** 
   * *Why:* Integrated within the recommender logic for swift matrix manipulation and dataset handling of books traversing between MongoDB constraints and the similarity matrices.
* **Uvicorn / Gunicorn:** 
   * *Why:* Uvicorn handles asynchronous requests exceptionally well, while Gunicorn acts as the robust process manager backing it up for potential production deployments.

### Frontend Stack

* **React 19:** View layer chosen for its component-based composition, effectively isolating behaviors (like `AiBookSuggest` vs `UserLibrary`).
* **Vite:** Next-generation frontend tooling offering unparalleled Hot Module Replacement speed compared to CRA or Webpack setups.
* **Axios:** Streamlined promise-based HTTP client to establish secure, token-authenticated requests back up to the FastAPI backend.

---

## 📂 Backend Architecture Highlights
```
backend/
├── app/
│   ├── core/         # Security, JWT configuration, and Auth middlewares
│   ├── db/           # MongoDB connection and configurations
│   ├── models/       # Pydantic schemas enforcing types and payloads 
│   ├── routes/       # FastAPI endpoint routing (auth, books, users, ratings)
│   ├── services/     # Business logic: TF-IDF Recommender, HuggingFace wrapper
│   └── main.py       # API bootstrap and startup events (training models)
├── requirements.txt
└── .env              # Stores MonogURI, JWT Secret, and HF API keys
```

## ⚙️ Getting Started

### Backend
1. Traverse into `/backend`
2. Create virtual environment: `python -m venv venv` and activate it.
3. Install dependencies: `pip install -r requirements.txt`
4. Setup `.env` (Requires `MONGODB_URI`, `HF_API_KEY`, etc.)
5. Run server: `uvicorn app.main:app --reload`

### Frontend
1. Traverse into `/frontend`
2. Install dependencies: `npm install`
3. Start development server: `npm run dev`
