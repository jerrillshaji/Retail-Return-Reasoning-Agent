"""
Finds out WHICH part of the chat is slow  ->  scripts/check_chat.py
Run from the project root:   python -m scripts.check_chat
It prints how many seconds each step takes. If a step runs for more than 2 minutes, press Ctrl+C
and tell me which step it was. It changes nothing in your database.
"""

import time

from sqlalchemy import select

from app.core.config import settings
from app.database.session import SessionLocal
from app.llm.provider import get_gemini_client
from app.models.user import User
from app.services.chat import answer_question, build_tools


def timed(label, fn):
	print(f"... {label}", flush=True)
	start = time.time()
	try:
		result = fn()
		print(f"    done in {time.time() - start:.1f}s", flush=True)
		return result
	except Exception as exc:
		print(f"    FAILED after {time.time() - start:.1f}s -> {type(exc).__name__}: {str(exc)[:300]}", flush=True)


def main():
	with SessionLocal() as db:
		user = db.scalar(select(User).order_by(User.user_id))      # the first user (the administrator)
		tools = {fn.__name__: fn for fn in build_tools(db, user)}

		print("PART 1: the database and project code (no Gemini)")
		timed("list_my_products", tools["list_my_products"])
		timed("get_return_rates", tools["get_return_rates"])
		timed("investigate_product for product 101 (search + analysis)", lambda: tools["investigate_product"](101))

		print(f"\nPART 2: one plain Gemini call, model = {settings.gemini_chat_model}")
		client = get_gemini_client()
		if client is None:
			print("    no Gemini key found")
		else:
			text = timed("plain question", lambda: client.models.generate_content(
				model=settings.gemini_chat_model, contents="Say hello in five words").text)
			print("    answer:", text)

		print("\nPART 3: the real chat with a simple question")
		reply = timed("chat: How many products do I have?", lambda: answer_question(db, user, "How many products do I have?", []))
		print("    reply:", (reply or "")[:200])


if __name__ == "__main__":
	main()
