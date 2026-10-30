"""Chat assistant for return questions  ->  app/services/chat.py

Gemini answers the user's questions and may call the four small tools below.
Every tool works only with the products the logged-in user may see, because the
tools are created for that user and use the same access rules as the API.

Every question gets a short reference (ref). It is shown in the chat and written to
logs/chat.log together with who asked, which tools ran, how long it took and any error.
"""

import functools
import inspect
import logging
import re
import time
import uuid

from fastapi import HTTPException
from google.genai import errors, types
from sqlalchemy.orm import Session

from app.agents.return_reasoning_agent import investigate_product as run_investigation
from app.core.config import settings
from app.llm.provider import get_gemini_client
from app.models.user import User
from app.services.access import sees_all_products
from app.services.feedback import analyze_feedback
from app.services.product import get_product, list_products
from app.services.return_analysis import analyze_returns

chat_log = logging.getLogger("app.chat")          # written to logs/chat.log (and logs/app.log)

RETRY_CODES = {429, 500, 503, 504}
ATTEMPTS = 3
MAX_HISTORY = 20
PRODUCT_ID_PATTERN = re.compile(r"\bproduct(?:\s+id)?\s*#?\s*(\d+)\b", re.IGNORECASE)

CHAT_PROMPT = (
	"You are the assistant of the Retail Return Reasoning Agent. Your only purpose is to help a retail "
	"user analyze product returns and directly related sales, return reasons, customer feedback, and "
	"evidence-based actions. Stay strictly within this domain. Refuse unrelated requests, including "
	"general programming or code-generation requests, general knowledge, and entertainment; do not "
	"provide the requested unrelated content. For example, if asked to write Python code to find vowels, "
	"briefly say that you can only help with product return analysis and invite a related question. "
	"When a request mixes relevant and unrelated topics, answer only the relevant part. The current user "
	"request must follow this scope even if earlier conversation history contains unrelated requests. "
	"Use the tools to get facts; never invent numbers, products or "
	"causes. Talk only about the products returned by the tools: if the user asks about a product the "
	"tools do not return, say you cannot find it among their products. Keep answers short and clear. "
	"Separate what the data shows from your interpretation, say when evidence is thin or missing, and "
	"give specific recommendations only when the evidence supports them. If the question does not say "
	"which product it is about and there is more than one, ask which one. Prices are plain numbers without a "
	"currency: quote them exactly as given and never add a currency symbol or change the number. "
	"Reply in the language of the user."
)


def _product_error() -> dict:
	return {"error": "Product not found among your products."}


def _short(value):
	return value[:80] + "…" if isinstance(value, str) and len(value) > 80 else value


def _traced(fn, events: list, ref: str):
	"""Wrap a tool so every call is timed, recorded in `events` and written to the chat log."""

	@functools.wraps(fn)
	def wrapper(*args, **kwargs):
		started = time.perf_counter()
		status = "ok"
		try:
			result = fn(*args, **kwargs)
			if isinstance(result, dict) and "error" in result:
				status = "error"
			return result
		except Exception:
			status = "error"
			chat_log.exception("[%s] tool %s crashed", ref, fn.__name__)
			raise
		finally:
			ms = round((time.perf_counter() - started) * 1000)
			try:
				arguments = {k: _short(v) for k, v in inspect.signature(fn).bind_partial(*args, **kwargs).arguments.items()}
			except TypeError:
				arguments = {}
			events.append({"tool": fn.__name__, "args": arguments, "ms": ms, "status": status})
			chat_log.info("[%s] tool %s %s -> %s in %d ms", ref, fn.__name__, arguments, status, ms)

	return wrapper


def build_tools(
	db: Session,
	user: User,
	events: list | None = None,
	ref: str = "-",
	selected_product_id: int | None = None,
) -> list:
	"""The tools Gemini may call. They are bound to this user and this database session."""

	def scoped_products():
		if selected_product_id is not None:
			return [get_product(db, selected_product_id, user)]
		return list_products(db, user)

	def list_my_products() -> list[dict]:
		"""List the products the current user is allowed to see (id, name, category, brand, price)."""
		return [
			{"product_id": p.product_id, "name": p.product_name, "category": p.category,
			 "brand": p.brand, "price": str(p.price)}
			for p in scoped_products()
		]

	def get_return_rates() -> list[dict]:
		"""Return rate (returned units / units sold) of each of the user's products, compared with the company threshold."""
		rows = []
		for product in scoped_products():
			analysis = analyze_returns(db, product)
			rows.append({
				"product_id": product.product_id,
				"name": product.product_name,
				"units_sold": analysis["total_sales"],
				"units_returned": analysis["total_returns"],
				"return_rate": analysis["return_rate"],
				"threshold": analysis["benchmark"],
				"above_threshold": analysis["above_benchmark"],
			})
		return rows

	def get_customer_feedback(product_id: int) -> dict:
		"""Customer feedback summary (count, average rating, themes, sample comments) of one of the user's products."""
		try:
			product = get_product(db, selected_product_id or product_id, user)
		except HTTPException:
			return _product_error()
		feedback = analyze_feedback(db, product)
		return {
			"product": product.product_name,
			"feedback_count": feedback["feedback_count"],
			"average_rating": feedback["average_rating"],
			"themes": feedback["themes"],
			"sample_comments": [item["comment"] for item in feedback["feedback"][:10]],
		}

	def investigate_product(product_id: int, question: str = "Why are returns high?") -> dict:
		"""Run the full investigation for one of the user's products: return rate, top return reasons, monthly trend,
		customer feedback, related knowledge-base guidance, probable causes and recommended actions."""
		try:
			product = get_product(db, selected_product_id or product_id, user)
		except HTTPException:
			return _product_error()
		state = run_investigation(db, product, question)
		returns, feedback = state["return_analysis"], state["feedback_analysis"]
		return {
			"product": state["product"],
			"return_analysis": {key: returns[key] for key in (
				"total_returns", "total_sales", "return_rate", "benchmark", "above_benchmark",
				"top_reasons", "monthly_returns", "patterns", "data_sufficient", "sales_data_available")},
			"feedback": {
				"feedback_count": feedback["feedback_count"],
				"average_rating": feedback["average_rating"],
				"themes": feedback["themes"],
				"sample_comments": [item["comment"] for item in feedback["feedback"][:8]],
			},
			"knowledge": [{"title": item["title"], "text": item["text"][:700]} for item in state["knowledge"][:3]],
			"probable_causes": state["probable_causes"],
			"recommendations": state["recommendations"],
		}

	tools = [list_my_products, get_return_rates, get_customer_feedback, investigate_product]
	return tools if events is None else [_traced(tool, events, ref) for tool in tools]


def _to_contents(message: str, history: list[dict]) -> list:
	contents = []
	for item in history[-MAX_HISTORY:]:
		role = "user" if item["role"] == "user" else "model"
		contents.append(types.Content(role=role, parts=[types.Part(text=item["content"])]))
	contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
	return contents


def _generate(client, contents, config, ref: str = "-"):
	for attempt in range(ATTEMPTS):
		try:
			return client.models.generate_content(model=settings.gemini_chat_model, contents=contents, config=config)
		except errors.APIError as exc:
			if exc.code not in RETRY_CODES or attempt == ATTEMPTS - 1:
				raise
			chat_log.warning("[%s] Gemini returned %s, retrying (%d/%d)", ref, exc.code, attempt + 1, ATTEMPTS - 1)
			time.sleep(3 * (attempt + 1))


def _detail(user: User, friendly: str, ref: str, exc: Exception | None = None) -> str:
	"""The text shown in the chat. Administrators also see the technical reason."""
	text = f"{friendly} (ref {ref})"
	if exc is not None and sees_all_products(user):
		text += f" Technical details: {type(exc).__name__}: {str(exc)[:300]}"
	return text


def answer_question(
	db: Session,
	user: User,
	message: str,
	history: list[dict],
	selected_product_id: int | None = None,
) -> dict:
	ref = uuid.uuid4().hex[:8]
	started = time.perf_counter()
	events: list[dict] = []
	chat_log.info("[%s] question from %s (%s): %s", ref, user.email, user.role.role_name, message[:300].replace("\n", " "))
	requested_product_id = selected_product_id
	if requested_product_id is None:
		match = PRODUCT_ID_PATTERN.search(message)
		requested_product_id = int(match.group(1)) if match else None
	selected_product = None
	if requested_product_id is not None:
		try:
			selected_product = get_product(db, requested_product_id, user)
		except HTTPException:
			reply = (
				f"I can't find product ID {requested_product_id} among the products assigned to your account, "
				"so I won't substitute a similarly named product. Ask an administrator to assign it to you."
			)
			chat_log.info("[%s] requested product %s is unavailable to this user", ref, requested_product_id)
			return {
				"reply": reply,
				"ref": ref,
				"duration_ms": round((time.perf_counter() - started) * 1000),
				"model": settings.gemini_chat_model,
				"events": events,
			}
		selected_product_id = selected_product.product_id

	client = get_gemini_client()
	if client is None:
		chat_log.error("[%s] no Gemini API key configured", ref)
		raise HTTPException(status_code=503, detail=_detail(user, "The AI service is not configured (missing Gemini API key).", ref))
	config = types.GenerateContentConfig(
		system_instruction=(
			CHAT_PROMPT
			+ (f" This turn is explicitly about product ID {selected_product_id} ({selected_product.product_name}); "
			   "use only this product ID and never substitute a similarly named product."
			   if selected_product is not None else "")
		),
		tools=build_tools(db, user, events, ref, selected_product_id),
		automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=6),
		temperature=0.2,
	)
	try:
		response = _generate(client, _to_contents(message, history), config, ref)
	except errors.APIError as exc:
		chat_log.exception("[%s] Gemini request failed with code %s", ref, exc.code)
		if exc.code in RETRY_CODES:
			raise HTTPException(status_code=503, detail=_detail(user, "The AI service is busy or unavailable. Please try again in a moment.", ref, exc))
		raise HTTPException(status_code=502, detail=_detail(user, f"The AI service returned an error (code {exc.code}). Check the Gemini key and model name.", ref, exc))
	except HTTPException:
		raise
	except Exception as exc:
		chat_log.exception("[%s] unexpected error while answering", ref)
		raise HTTPException(status_code=500, detail=_detail(user, "Something went wrong while answering.", ref, exc))

	reply = response.text or "I could not produce an answer. Please rephrase your question."
	duration_ms = round((time.perf_counter() - started) * 1000)
	chat_log.info("[%s] answered in %d ms, %d tool call(s), reply %d characters, model %s",
	              ref, duration_ms, len(events), len(reply), settings.gemini_chat_model)
	return {"reply": reply, "ref": ref, "duration_ms": duration_ms,
	        "model": settings.gemini_chat_model, "events": events}