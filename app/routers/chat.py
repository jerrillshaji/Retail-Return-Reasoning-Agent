"""Chat endpoints  ->  app/routers/chat.py"""

from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.file_logging import read_log_tail
from app.database.session import get_db
from app.models.user import User
from app.routers.auth import get_current_user, require_roles
from app.schemas.chat import (
	ChatLogResponse,
	ChatRequest,
	ChatResponse,
	ConversationCreate,
	ConversationDetail,
	ConversationSummary,
)
from app.services.chat import answer_question
from app.services.chat_history import (
	create_conversation,
	delete_conversation,
	get_conversation_detail,
	get_owned_conversation,
	list_conversations,
	load_recent_history,
	save_assistant_message,
	save_user_message,
	serialize_conversation,
)

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(require_roles("administrator", "retail_manager", "analyst", "quality_user"))])


@router.post("", response_model=ChatResponse)
def chat(data: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ChatResponse:
	conversation = get_owned_conversation(db, user, data.conversation_id)
	history = load_recent_history(db, conversation)
	save_user_message(db, conversation, data.message)
	answer = answer_question(db, user, data.message, history, data.selected_product_id)
	save_assistant_message(db, conversation, answer["reply"], answer)
	return ChatResponse(conversation_id=conversation.conversation_id, **answer)


@router.post("/conversations", response_model=ConversationDetail, status_code=status.HTTP_201_CREATED)
def new_conversation(
	data: ConversationCreate,
	db: Session = Depends(get_db),
	user: User = Depends(get_current_user),
) -> ConversationDetail:
	conversation = create_conversation(db, user, data.title)
	return ConversationDetail(**serialize_conversation(conversation), messages=[])


@router.get("/conversations", response_model=list[ConversationSummary])
def conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
	return [serialize_conversation(item) for item in list_conversations(db, user)]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def conversation_detail(
	conversation_id: int,
	db: Session = Depends(get_db),
	user: User = Depends(get_current_user),
) -> dict:
	conversation = get_conversation_detail(db, user, conversation_id)
	return {
		**serialize_conversation(conversation),
		"messages": [
			{
				"message_id": message.message_id,
				"role": message.role,
				"content": message.content,
				"created_at": message.created_at,
				"ref": message.ref,
				"model": message.model,
				"duration_ms": message.duration_ms,
			}
			for message in conversation.messages
		],
	}


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_conversation(
	conversation_id: int,
	db: Session = Depends(get_db),
	user: User = Depends(get_current_user),
) -> Response:
	delete_conversation(db, user, conversation_id)
	return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/logs", response_model=ChatLogResponse, dependencies=[Depends(require_roles("administrator"))])
def chat_logs(source: Literal["chat", "app"] = "chat", lines: int = Query(default=100, ge=1, le=500)) -> ChatLogResponse:
	"""The most recent lines of the server log files. Administrators only."""
	return ChatLogResponse(source=source, lines=read_log_tail(source, lines))