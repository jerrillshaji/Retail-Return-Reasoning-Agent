"""Chroma vector store and vector similarity helpers."""

import math
import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings

CHROMA_DIR = "data/chroma_db"
COLLECTION = "return_knowledge"
EMBEDDING_MODEL = "gemini-embedding-001"


def get_embedding_api_key() -> str:
	load_dotenv()
	for attr in ("gemini_api_key", "google_api_key"):
		value = getattr(settings, attr, None)
		if value:
			return value
	return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")


def get_vectorstore() -> Chroma:
	embeddings = GoogleGenerativeAIEmbeddings(
		model=EMBEDDING_MODEL,
		google_api_key=get_embedding_api_key(),
	)
	return Chroma(
		collection_name=COLLECTION,
		persist_directory=CHROMA_DIR,
		embedding_function=embeddings,
	)


def cosine_similarity(left: list[float], right: list[float]) -> float:
	if len(left) != len(right):
		return 0.0
	left_norm = math.sqrt(sum(value * value for value in left))
	right_norm = math.sqrt(sum(value * value for value in right))
	if not left_norm or not right_norm:
		return 0.0
	return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)
