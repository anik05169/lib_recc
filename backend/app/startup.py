from app.db.mongo import get_mongo_db
from app.db.ratings_util import get_avg_ratings_map
from app.services import pinecone_store
from app.services.recommender import set_ratings_map, train_model
from pymongo.errors import ConfigurationError, ServerSelectionTimeoutError


def train_recommender_on_startup():
    """Load ratings cache and sync catalog vectors to Pinecone on startup."""
    try:
        db = get_mongo_db()
        books = list(db.books.find({}, {"_id": 0}))

        ratings_map = get_avg_ratings_map(db)
        set_ratings_map(ratings_map)

        if not books:
            print("No books found. Pinecone catalog not synced.")
            return

        synced = train_model(books, ratings_map)
        print(f"Startup: ratings cached; {synced} catalog vectors synced to Pinecone")
        if synced == 0:
            if pinecone_store.warm_namespace_cache(pinecone_store.CATALOG_NAMESPACE):
                count = pinecone_store.get_namespace_vector_count(pinecone_store.CATALOG_NAMESPACE)
                print(f"Startup: Pinecone catalog cache warmed ({count} vectors)")
            else:
                print(
                    "Hint: SKIP_EMBEDDING_SYNC is set or sync returned 0. "
                    "Run scripts/sync_pinecone_index.py to populate Pinecone."
                )
    except ServerSelectionTimeoutError:
        print("Could not connect to MongoDB. Recommender not initialized.")
        print("Hint: Check if your IP address is whitelisted in MongoDB Atlas.")
    except ConfigurationError as e:
        print("MongoDB configuration error. Recommender not initialized.")
        print(f"Details: {e}")
    except Exception as e:
        print(f"Error during recommender startup: {e}")
