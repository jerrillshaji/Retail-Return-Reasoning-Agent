from datetime import date
from decimal import Decimal

from app.agents.tools.product_tools import product_summary
from app.models.customer import Customer
from app.models.product import Product
from app.models.roles import Role
from app.models.sale import Sale
from app.models.user import User
from app.services.chat import answer_question, build_tools


def make_user(db, email):
    role = Role(role_name=f"role-{email}")
    db.add(role)
    db.flush()
    user = User(name="Test User", email=email, password_hash="hash", role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_selected_product_context_prevents_same_name_substitution(db):
    user = make_user(db, "owner@example.com")
    first = Product(
        product_name="Bluetooth Speaker S2",
        category="Electronics",
        brand="SoundMax",
        price=Decimal("3299.00"),
        owner_user_id=user.user_id,
    )
    second = Product(
        product_name="Bluetooth Speaker S2",
        category="Electronics",
        brand="SoundMax",
        price=Decimal("3299.00"),
        owner_user_id=user.user_id,
    )
    customer = Customer(name="Test Customer", email="chat-context@example.com")
    db.add_all([first, second, customer])
    db.flush()
    db.add(Sale(
        product_id=first.product_id,
        customer_id=customer.customer_id,
        sale_date=date(2026, 9, 1),
        quantity=40,
        unit_price=Decimal("3299.00"),
    ))
    db.commit()

    tools = {tool.__name__: tool for tool in build_tools(db, user, selected_product_id=second.product_id)}

    products = tools["list_my_products"]()
    rates = tools["get_return_rates"]()

    assert [item["product_id"] for item in products] == [second.product_id]
    assert len(rates) == 1
    assert rates[0]["product_id"] == second.product_id
    assert rates[0]["units_sold"] == 0
    assert rates[0]["return_rate"] is None
    assert product_summary(second)["product_id"] != product_summary(first)["product_id"]


def test_inaccessible_explicit_product_id_is_not_replaced_by_same_name(db):
    user = make_user(db, "signed-in@example.com")
    other_owner = make_user(db, "other-owner@example.com")
    product = Product(
        product_name="Bluetooth Speaker S2",
        category="Electronics",
        brand="SoundMax",
        price=Decimal("3299.00"),
        owner_user_id=other_owner.user_id,
    )
    db.add(product)
    db.commit()

    result = answer_question(
        db,
        user,
        f"Why are returns high for product ID {product.product_id}?",
        [],
    )

    assert "can't find product ID" in result["reply"]
    assert "won't substitute" in result["reply"]
    assert result["events"] == []
