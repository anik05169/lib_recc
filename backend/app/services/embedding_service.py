"""Sentence embedding encoder — used at index-sync time only (not on API hot path)."""

import os

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

_tokenizer = None
_model = None
_device = "cpu"


def book_text_from_record(book: dict) -> str:
    title = (book.get("title") or "").strip()
    desc = (book.get("description") or "").strip()
    return f"{title} {desc}".strip()


def get_embedding_model_name() -> str:
    return os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)


def _load_backend():
    global _tokenizer, _model, _device
    if _model is not None and _tokenizer is not None:
        return _tokenizer, _model, _device

    from transformers import AutoModel, AutoTokenizer
    import torch

    model_name = get_embedding_model_name()
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()

    _tokenizer = tokenizer
    _model = model
    _device = device
    return _tokenizer, _model, _device


def encode_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    tokenizer, model, device = _load_backend()

    import torch

    batch_size = 32
    all_embeddings: list[list[float]] = []
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            enc = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=256,
                return_tensors="pt",
            )
            enc = {k: v.to(device) for k, v in enc.items()}
            out = model(**enc).last_hidden_state
            mask = enc["attention_mask"].unsqueeze(-1).float()
            pooled = (out * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            all_embeddings.extend(pooled.cpu().numpy().tolist())
    return all_embeddings
