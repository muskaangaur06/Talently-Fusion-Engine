"""Runtime embedding + FAISS search service, loaded once as a process-global singleton.

Uses ONNX Runtime with a standalone tokenizer instead of sentence-transformers/torch.
Importing sentence-transformers pulls in the full PyTorch framework (~250MB+ baseline
RAM) even for pure CPU inference on a small model; the transformers library's own
AutoTokenizer also imports torch internally. This pipeline avoids torch entirely by
using onnxruntime for inference and the standalone `tokenizers` library for tokenizing,
cutting baseline RAM from ~390MB to ~150MB - the difference between fitting and not
fitting inside Render's 512MB free-tier limit for this dataset size.

Output is verified numerically identical (cosine similarity 1.0) to the
sentence-transformers all-MiniLM-L6-v2 output used to originally build the FAISS index.
"""
import os
import threading

import numpy as np

MODEL_DIR = os.environ.get(
    "ONNX_MODEL_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "models", "all-MiniLM-L6-v2-onnx")
)
MODEL_DIR = os.path.abspath(MODEL_DIR)
EMBEDDING_DIM = 384
MAX_SEQ_LENGTH = 256
FAISS_INDEX_PATH = os.path.abspath(
    os.environ.get("FAISS_INDEX_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "data", "jobs.faiss"))
)

_lock = threading.Lock()
_session = None
_tokenizer = None
_index = None
_index_mtime = None


def _get_session():
    global _session
    if _session is None:
        with _lock:
            if _session is None:
                import onnxruntime as ort

                onnx_path = os.path.join(MODEL_DIR, "model.onnx")
                options = ort.SessionOptions()
                options.intra_op_num_threads = 1
                options.inter_op_num_threads = 1
                _session = ort.InferenceSession(onnx_path, sess_options=options, providers=["CPUExecutionProvider"])
    return _session


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        with _lock:
            if _tokenizer is None:
                from tokenizers import Tokenizer

                tok = Tokenizer.from_file(os.path.join(MODEL_DIR, "tokenizer.json"))
                tok.enable_padding()
                tok.enable_truncation(max_length=MAX_SEQ_LENGTH)
                _tokenizer = tok
    return _tokenizer


def get_index():
    """Loads (or hot-reloads on mtime change) the FAISS index from disk."""
    global _index, _index_mtime
    if not os.path.exists(FAISS_INDEX_PATH):
        return None
    import faiss

    mtime = os.path.getmtime(FAISS_INDEX_PATH)
    if _index is None or mtime != _index_mtime:
        with _lock:
            _index = faiss.read_index(FAISS_INDEX_PATH)
            _index_mtime = mtime
    return _index


def _mean_pool_and_normalize(token_embeddings: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
    mask = attention_mask[..., None].astype(np.float32)
    summed = (token_embeddings * mask).sum(axis=1)
    counts = np.clip(mask.sum(axis=1), 1e-9, None)
    pooled = summed / counts
    norms = np.linalg.norm(pooled, axis=1, keepdims=True)
    norms[norms == 0] = 1e-9
    return (pooled / norms).astype(np.float32)


def embed_texts(texts: list) -> np.ndarray:
    if not texts:
        return np.zeros((0, EMBEDDING_DIM), dtype=np.float32)

    tokenizer = _get_tokenizer()
    session = _get_session()

    encodings = tokenizer.encode_batch(texts)
    input_ids = np.array([e.ids for e in encodings], dtype=np.int64)
    attention_mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
    token_type_ids = np.zeros_like(input_ids)

    outputs = session.run(
        None, {"input_ids": input_ids, "attention_mask": attention_mask, "token_type_ids": token_type_ids}
    )
    token_embeddings = outputs[0]
    return _mean_pool_and_normalize(token_embeddings, attention_mask)


def embed_text(text: str) -> np.ndarray:
    return embed_texts([text])


def vector_search(query_text: str, top_k: int = 50):
    """Returns list of (faiss_index, distance) tuples ordered by ascending L2 distance."""
    index = get_index()
    if index is None or index.ntotal == 0:
        return []
    query_vec = embed_text(query_text)
    distances, indices = index.search(query_vec, min(top_k, index.ntotal))
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        results.append((int(idx), float(dist)))
    return results


def reconstruct_vectors(faiss_indices: list) -> np.ndarray:
    """Fetches precomputed vectors straight out of the FlatL2 index by their internal position,
    avoiding a live re-encode of job text at request time."""
    index = get_index()
    if index is None:
        return np.zeros((len(faiss_indices), EMBEDDING_DIM), dtype=np.float32)
    return np.array([index.reconstruct(i) for i in faiss_indices], dtype=np.float32)


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    a = vec_a.flatten()
    b = vec_b.flatten()
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
