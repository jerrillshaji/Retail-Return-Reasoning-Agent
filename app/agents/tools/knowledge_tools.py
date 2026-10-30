"""
Search tool for the agent -> app/agents/tools/knowledge_tools.py

Lets the agent look up return-handling guidance (causes of returns and recommended
actions) from the knowledge documents loaded by scripts/ingest_knowledge.py.
It still has to be added to the agent's tool list (next step).
"""

from langchain_core.tools import tool

from app.rag.vector_store import get_vectorstore


@tool
def search_return_knowledge(question: str) -> str:
    """Search the return-handling knowledge base for likely causes of a kind of return
    (battery, charging, defects, damage, listing mismatch, compatibility) and for
    recommended corrective actions. Use it after you know the main return reasons."""
    results = get_vectorstore().similarity_search(question, k=3)
    if not results:
        return "No relevant knowledge found."
    return "\n\n".join(f"[{r.metadata.get('document_name')}]\n{r.page_content}" for r in results)
