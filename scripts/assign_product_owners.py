"""
Give every product an owner (the retail agent who may see it) -> scripts/assign_product_owners.py

  1. adds the column products.owner_user_id if it does not exist yet
  2. shows the roles and users that exist in your database
  3. assigns the products listed in ASSIGNMENTS below to those users
  4. prints the result

Run from the project root:   python -m scripts.assign_product_owners
Safe to run several times. Run it again after every  python -m scripts.load_data  because
reloading the products clears the owners.
"""

from sqlalchemy import create_engine, text

from app.core.config import settings

# Edit the emails so they match the users you create. product ids are the ones from your CSV.
ASSIGNMENTS = {
	"agent1@example.com": [101, 102, 103],
	"agent2@example.com": [104, 105],
}


def main():
	engine = create_engine(settings.database_url)

	with engine.begin() as conn:
		conn.execute(text(
			"ALTER TABLE products ADD COLUMN IF NOT EXISTS owner_user_id INTEGER "
			"REFERENCES users(user_id) ON DELETE SET NULL"))
		conn.execute(text(
			"CREATE INDEX IF NOT EXISTS ix_products_owner_user_id ON products (owner_user_id)"))
	print("Column products.owner_user_id is in place.")

	with engine.connect() as conn:
		roles = conn.execute(text("SELECT role_id, role_name FROM roles ORDER BY role_id")).all()
		users = conn.execute(text(
			"SELECT u.user_id, u.name, u.email, r.role_name FROM users u "
			"JOIN roles r ON r.role_id = u.role_id ORDER BY u.user_id")).all()

	print("\nRoles in the database:")
	for row in roles:
		print(f"  {row.role_id}  {row.role_name}")
	print("\nUsers in the database:")
	for row in users:
		print(f"  {row.user_id}  {row.email:<30} {row.name:<20} role: {row.role_name}")
	if not users:
		print("  (none yet)")

	user_ids = {row.email.lower(): row.user_id for row in users}
	missing = [email for email in ASSIGNMENTS if email.lower() not in user_ids]

	with engine.begin() as conn:
		for email, product_ids in ASSIGNMENTS.items():
			user_id = user_ids.get(email.lower())
			if user_id is None:
				continue
			for product_id in product_ids:
				conn.execute(text("UPDATE products SET owner_user_id = :u WHERE product_id = :p"),
				             {"u": user_id, "p": product_id})

	with engine.connect() as conn:
		rows = conn.execute(text(
			"SELECT p.product_id, p.product_name, u.email FROM products p "
			"LEFT JOIN users u ON u.user_id = p.owner_user_id ORDER BY p.product_id")).all()
	print("\nProduct owners:")
	for row in rows:
		print(f"  {row.product_id}  {row.product_name:<24} owner: {row.email or '(nobody yet)'}")

	if missing:
		print("\nThese users do not exist yet, so their products were NOT assigned:")
		for email in missing:
			print(f"  {email}")
		print("Create them in /docs with POST /auth/users, then run this script again.")


if __name__ == "__main__":
	main()
