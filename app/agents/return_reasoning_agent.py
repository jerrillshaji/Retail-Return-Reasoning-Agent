"""Return investigation workflow built with LangGraph.

The workflow is a small graph. Each box ("node") does one job and writes its result
into the shared state; the arrows ("edges") decide what runs next:

    START -> load_returns -> load_feedback --+--> retrieve_knowledge --+--> find_causes -> END
                                             |                         |
                                             +--> no_knowledge --------+
                                (decision: is there anything to look up in the knowledge base?)
"""

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agents.state import InvestigationState
from app.agents.tools.analysis_tool import identify_causes
from app.agents.tools.feedback_tools import get_feedback_evidence
from app.agents.tools.product_tools import product_summary
from app.agents.tools.return_tools import get_return_evidence
from app.models.product import Product
from app.rag.retriever import retrieve


def build_graph(db: Session, product: Product):
	"""Create the workflow for one product (db and product are used by the nodes below)."""

	def load_returns(state: InvestigationState) -> dict:
		return {"return_analysis": get_return_evidence(db, product)}

	def load_feedback(state: InvestigationState) -> dict:
		return {"feedback_analysis": get_feedback_evidence(db, product)}

	def route_after_data(state: InvestigationState) -> str:
		"""Decision: only search the knowledge base when there is something to search for."""
		has_reasons = bool(state["return_analysis"]["top_reasons"])
		has_themes = bool(state["feedback_analysis"]["themes"])
		return "retrieve_knowledge" if (has_reasons or has_themes) else "no_knowledge"

	def retrieve_knowledge(state: InvestigationState) -> dict:
		reasons = " ".join(item["reason"] for item in state["return_analysis"]["top_reasons"])
		themes = " ".join(item["theme"] for item in state["feedback_analysis"]["themes"])
		search_text = f"{state['query']} {reasons} {themes} {product.category}"
		return {"knowledge": retrieve(db, search_text)}

	def no_knowledge(state: InvestigationState) -> dict:
		return {"knowledge": []}

	def find_causes(state: InvestigationState) -> dict:
		causes, evidence, recommendations = identify_causes(
			state["return_analysis"], state["feedback_analysis"]
		)
		return {"probable_causes": causes, "evidence": evidence, "recommendations": recommendations}

	builder = StateGraph(InvestigationState)
	builder.add_node("load_returns", load_returns)
	builder.add_node("load_feedback", load_feedback)
	builder.add_node("retrieve_knowledge", retrieve_knowledge)
	builder.add_node("no_knowledge", no_knowledge)
	builder.add_node("find_causes", find_causes)

	builder.add_edge(START, "load_returns")
	builder.add_edge("load_returns", "load_feedback")
	builder.add_conditional_edges(
		"load_feedback",
		route_after_data,
		{"retrieve_knowledge": "retrieve_knowledge", "no_knowledge": "no_knowledge"},
	)
	builder.add_edge("retrieve_knowledge", "find_causes")
	builder.add_edge("no_knowledge", "find_causes")
	builder.add_edge("find_causes", END)
	return builder.compile()


def investigate_product(db: Session, product: Product, query: str) -> InvestigationState:
	graph = build_graph(db, product)
	return graph.invoke({"product": product_summary(product), "query": query})