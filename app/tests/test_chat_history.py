from fastapi import HTTPException

from app.models.chat_conversation import ChatConversation
from app.models.chat_message import ChatMessageRecord
from app.models.roles import Role
from app.models.user import User
from app.services.chat_history import (
    create_conversation,
    delete_conversation,
    get_conversation_detail,
    list_conversations,
    load_recent_history,
    save_assistant_message,
    save_user_message,
)


def make_user(db, email):
    role = Role(role_name=f"role-{email}")
    db.add(role)
    db.flush()
    user = User(name="Test User", email=email, password_hash="hash", role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_conversations_are_private_to_the_owner(db):
    owner = make_user(db, "owner@example.com")
    another_user = make_user(db, "other@example.com")
    conversation = create_conversation(db, owner)

    assert [item.conversation_id for item in list_conversations(db, owner)] == [conversation.conversation_id]
    assert list_conversations(db, another_user) == []
    try:
        get_conversation_detail(db, another_user, conversation.conversation_id)
    except HTTPException as error:
        assert error.status_code == 404
    else:
        raise AssertionError("A user must not be able to open another user's conversation")


def test_messages_persist_in_order_and_supply_recent_history(db):
    user = make_user(db, "chat@example.com")
    conversation = create_conversation(db, user)

    save_user_message(db, conversation, "Why are returns high?")
    save_assistant_message(db, conversation, "The return rate is 20%.", {
        "ref": "abc12345",
        "model": "gemini-test",
        "duration_ms": 120,
    })

    db.expire_all()
    saved = get_conversation_detail(db, user, conversation.conversation_id)

    assert saved.title == "Why are returns high?"
    assert [message.role for message in saved.messages] == ["user", "assistant"]
    assert load_recent_history(db, saved) == [
        {"role": "user", "content": "Why are returns high?"},
        {"role": "assistant", "content": "The return rate is 20%."},
    ]
    assert saved.messages[1].ref == "abc12345"
    assert saved.messages[1].model == "gemini-test"


def test_deleting_conversation_deletes_its_messages(db):
    user = make_user(db, "delete@example.com")
    conversation = create_conversation(db, user)
    save_user_message(db, conversation, "Delete this chat")

    delete_conversation(db, user, conversation.conversation_id)

    assert db.query(ChatConversation).filter_by(conversation_id=conversation.conversation_id).count() == 0
    assert db.query(ChatMessageRecord).filter_by(conversation_id=conversation.conversation_id).count() == 0
