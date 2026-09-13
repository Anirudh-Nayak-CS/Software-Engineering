from collections.abc import Sequence

from models.documents import Chunk
from infrastructure.config import Settings, settings


class KeywordRetriever:
    def __init__(self, chunks: Sequence[Chunk], retrieval_count: int):
        from rank_bm25 import BM25Okapi

        self.chunks = list(chunks)
        self.retrieval_count = retrieval_count
        tokenized_documents = [
            chunk.text.lower().split()
            for chunk in self.chunks
        ]
        self.index = BM25Okapi(tokenized_documents)

    def invoke(self, query: str) -> list:
        query_tokens = query.lower().split()
        scores = self.index.get_scores(query_tokens)
        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )
        return [
            self.chunks[index]
            for index in ranked_indices[: self.retrieval_count]
        ]


def build_retriever(documents: Sequence, app_settings: Settings = settings):
    """Build a lightweight local BM25 retriever."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=app_settings.chunk_size,
        chunk_overlap=app_settings.chunk_overlap,
    )
    chunks: list[Chunk] = []
    chunk_id = 1
    for document in documents:
        for text in splitter.split_text(document.text):
            chunks.append(
                Chunk(
                    text=text,
                    source=document.name,
                    chunk_id=chunk_id,
                    page=document.page,
                )
            )
            chunk_id += 1
    return KeywordRetriever(chunks, app_settings.retrieval_count)


def format_retrieved_documents(documents: Sequence) -> str:
    """Format retrieved evidence with the metadata needed for source citations."""
    sections: list[str] = []
    for document in documents:
        source = getattr(document, "source", "Unknown source")
        page = getattr(document, "page", "Unknown page")
        sections.append(
            f"[Source: {source}, Page {page}]\n{document.text}"
        )
    return "\n\n---\n\n".join(sections)
