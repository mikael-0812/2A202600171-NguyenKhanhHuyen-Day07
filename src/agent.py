from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        context_chunks = [item["content"] for item in results]
        context = "\n\n".join(f"[{idx + 1}] {chunk}" for idx, chunk in enumerate(context_chunks))

        prompt = (
            "You are a knowledge base assistant. Answer the question using the provided context. "
            "If the context is insufficient, say so clearly.\n\n"
            f"Context:\n{context if context else 'No relevant context found.'}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
