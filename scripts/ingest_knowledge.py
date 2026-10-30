"""
Load the knowledge documents (RAG) -> scripts/ingest_knowledge.py

What it does, in simple words:
  1. Reads every .md file in  data/knowledge/
  2. Cuts each file into small chunks of text
  3. Turns each chunk into numbers ("embedding") with the Gemini API
  4. Saves the numbers in a local search index (Chroma, folder data/chroma_db)
  5. Saves the documents and chunks in your Postgres tables
     knowledge_documents and knowledge_chunks (from the approved design)

Run from the project root:   python -m scripts.ingest_knowledge
Safe to run again: it clears the old knowledge data first.
"""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import create_engine, text

from app.core.config import settings

KNOWLEDGE_DIR = Path("data/knowledge")
CHROMA_DIR = "data/chroma_db"
COLLECTION = "return_knowledge"
EMBEDDING_MODEL = "gemini-embedding-001"     # change here if Google renames it
CHUNK_SIZE = getattr(settings, "chunk_size", 700)
CHUNK_OVERLAP = getattr(settings, "chunk_overlap", 100)


def get_api_key() -> str:
    """Find the Gemini key, whatever name it has in your settings or .env file."""
    load_dotenv()                                   # makes .env values visible as environment variables
    for attr in ("gemini_api_key", "google_api_key"):
        value = getattr(settings, attr, None)
        if value:
            return value
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        if os.environ.get(name):
            return os.environ[name]
    raise SystemExit("No Gemini API key found. Add  GEMINI_API_KEY=...  to your .env file.")


def main():
    files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    if not files:
        raise SystemExit(f"No .md files found in {KNOWLEDGE_DIR}. Copy the knowledge files there first.")

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=get_api_key())
    engine = create_engine(settings.database_url)
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    # start from an empty search index
    try:
        Chroma(collection_name=COLLECTION, persist_directory=CHROMA_DIR,
               embedding_function=embeddings).delete_collection()
    except Exception:
        pass                                         # nothing to delete the first time
    store = Chroma(collection_name=COLLECTION, persist_directory=CHROMA_DIR,
                   embedding_function=embeddings)

    total_chunks = 0
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM knowledge_documents"))   # chunks are deleted with them (CASCADE)

        for path in files:
            content = path.read_text(encoding="utf-8")
            doc_id = conn.execute(text("""
                INSERT INTO knowledge_documents (document_name, source, document_type, uploaded_at)
                VALUES (:name, :source, :type, :now) RETURNING document_id
            """), {"name": path.stem, "source": str(path).replace("\\", "/"),
                   "type": "return_handling_guide", "now": datetime.now()}).scalar_one()

            chunks = splitter.split_text(content)
            ids = [f"doc{doc_id}-chunk{i}" for i in range(len(chunks))]
            for i, chunk in enumerate(chunks):
                conn.execute(text("""
                    INSERT INTO knowledge_chunks (document_id, chunk_text, chunk_index, embedding_reference)
                    VALUES (:doc, :chunk, :idx, :ref)
                """), {"doc": doc_id, "chunk": chunk, "idx": i, "ref": ids[i]})

            store.add_texts(texts=chunks, ids=ids,
                            metadatas=[{"document_id": doc_id, "document_name": path.stem,
                                        "chunk_index": i} for i in range(len(chunks))])
            total_chunks += len(chunks)
            print(f"  {path.name:<40} {len(chunks):>2} chunks")

    print(f"\nDone: {len(files)} documents, {total_chunks} chunks.")

    # quick test of the search
    question = "earbuds battery drains quickly and the case will not charge"
    print(f"\nTest search: {question!r}")
    for r in store.similarity_search(question, k=3):
        print(f"  -> {r.metadata['document_name']} (chunk {r.metadata['chunk_index']})")


if __name__ == "__main__":
    main()
