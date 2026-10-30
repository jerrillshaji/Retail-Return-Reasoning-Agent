from types import SimpleNamespace
from unittest.mock import Mock

from app.models.roles import Role
from app.models.user import User
from app.services import chat as chat_service


def test_chat_requests_include_strict_product_return_scope(db, monkeypatch):
    role = Role(role_name="administrator")
    db.add(role)
    db.flush()
    user = User(name="Admin", email="admin@example.com", password_hash="hash", role=role)
    db.add(user)
    db.commit()

    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(
        text="I can only help with product return analysis."
    )
    monkeypatch.setattr(chat_service, "get_gemini_client", lambda: client)

    chat_service.answer_question(
        db,
        user,
        "Generate me Python code to find vowels in a string",
        [],
    )

    config = client.models.generate_content.call_args.kwargs["config"]
    assert "Your only purpose is to help a retail user analyze product returns" in config.system_instruction
    assert "general programming or code-generation requests" in config.system_instruction
    assert "do not provide the requested unrelated content" in config.system_instruction
