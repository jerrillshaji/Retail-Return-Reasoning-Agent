# Retail Return Reasoning Agent

A small FastAPI application for recording product sales, returns, and customer feedback, then producing evidence-first return investigations. PostgreSQL is the default database. Deterministic analysis and keyword knowledge search work locally without API credentials. Gemini report explanations are optional.

## 1. Prepare Python

Install Python 3.11 or newer. In VS Code, open the existing `Project` folder, then open **Terminal > New Terminal** and run these commands from the project root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell prevents activation, run this once in that terminal, then activate the environment again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 2. Configure `.env`

The `.env` file is in the project root, beside `requirements.txt`. It is ignored by Git. Change `SECRET_KEY`, `INITIAL_ADMIN_EMAIL`, and `INITIAL_ADMIN_PASSWORD` before using the app with real data. A strong `SECRET_KEY` can be generated with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

`DATABASE_URL` defaults to a local PostgreSQL instance. Install PostgreSQL, create the application database and user as described below, and replace the example password in `.env`. Tables are created automatically at first startup. If you already have records in the previous SQLite database, they are not copied automatically; export/import them separately before switching.

### Set up PostgreSQL on Windows

1. Install PostgreSQL using the official Windows installer from `https://www.postgresql.org/download/windows/`. Keep the default port `5432`; remember the password you choose for the PostgreSQL superuser `postgres`.
2. Open **SQL Shell (psql)** from the Start menu. Accept the default server, database, port, and username by pressing Enter, then enter the `postgres` password when prompted.
3. Create a dedicated app login and database by running these SQL statements. The example password is `1234` to match the current `.env` connection URL:

```sql
CREATE USER retail_agent WITH PASSWORD '1234';
CREATE DATABASE retail_agent_db OWNER retail_agent;
```

4. Open the project `.env` and change the password in `DATABASE_URL` to the same value. The URL format is `postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE`. If your password contains URL-reserved characters such as `@`, `:`, `/`, or `#`, percent-encode them in the URL.
5. In the project terminal, activate `.venv` and install the added PostgreSQL driver and requirements:

```powershell
pip install -r requirements.txt
```

6. Start the API. On first startup, it creates the tables and initial administrator in PostgreSQL. Check `http://127.0.0.1:8000/health`.

### Load the supplied dummy CSV into the approved schema

The ORM models now match the revised design used by `scripts/load_data.py`. If the database was previously created by the old app models, those tables must be rebuilt because SQLAlchemy `create_all()` does not rename or alter existing columns. Stop the API, make sure `data/retail_return_reasoning_agent_dummy_data.csv` exists, then run:

```powershell
python -m scripts.load_data --reset
```

This command **drops and recreates the 16 application tables, including saved conversations and messages**, then reloads the dummy CSV. Back up any data you need first. Start the API after it succeeds; startup seeds the role lookup rows and initial administrator. For later data refreshes, use `python -m scripts.load_data` without `--reset`; that reloads the ten CSV data tables but leaves roles, users, and chat history intact.

Gemini is optional. Without an API key, report statistics/recommendations use simple local rules and knowledge retrieval falls back to keyword overlap. With a key and an indexed Chroma collection, investigations use semantic search over return-handling guidance. To create that index, run `python -m scripts.ingest_knowledge` from the project root; it embeds the Markdown files in `data/knowledge/` with `gemini-embedding-001`, stores vectors in the local `data/chroma_db` collection, and stores document text/metadata in the configured SQL database. **Re-running this script rebuilds the Chroma collection and deletes the existing SQL knowledge documents and chunks**, so back up knowledge data first. Documents added through `POST /knowledge/documents` remain searchable through the SQL keyword fallback until they are added to Chroma. API use may be subject to provider quotas or charges. The approved SQL schema stores an embedding reference rather than embedding vectors; the vectors are stored in Chroma.

### `.env` settings

- `APP_NAME`: API title displayed by FastAPI.
- `DATABASE_URL`: PostgreSQL connection string; format is `postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE`.
- `SECRET_KEY`: signs login tokens; replace it with a long random value before use.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: lifetime of login tokens.
- `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD`: first administrator credentials, created only when the database has no matching user.
- `RETURN_RATE_THRESHOLD`: return-rate benchmark as a decimal; `0.10` means 10%.
- `GEMINI_API_KEY`: optional Google Gemini API key for report wording.
- `GEMINI_CHAT_MODEL`: Gemini model used when a key is set.
- `GEMINI_EMBEDDING_MODEL`: Gemini embedding model for the optional embedding helper; the knowledge ingestion script currently uses `gemini-embedding-001`.
- `CHUNK_SIZE` and `CHUNK_OVERLAP`: knowledge document chunk sizes in words.

## 3. Run the API

From the project root with `.venv` active:

```powershell
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation. Health check: `http://127.0.0.1:8000/health`.

The first startup creates the administrator specified by `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD`. Users can create a standard retail-manager account from the login page; passwords are stored as Argon2 hashes. Sign in at `POST /auth/login`; use the returned bearer token via **Authorize** in Swagger. Change the starter password with `POST /auth/change-password`. Use `POST /auth/users` with an administrator token to create users with other roles.

## 4. Add data and investigate

Use Swagger or an HTTP client in this order:

1. `POST /products` with `{"product_name":"Example jacket","category":"Clothing","brand":"Example","price":49.99,"description":"Waterproof jacket"}`. The database assigns `product_id`.
2. `POST /customers` with `{"name":"Example customer","email":"customer@example.com"}`. The database assigns `customer_id`.
3. `POST /sales` with `{"product_id":1,"customer_id":1,"quantity":100,"unit_price":49.99,"sale_date":"2026-09-01"}`. Use the IDs returned by the previous steps; repeat for additional sales periods if available.
4. `POST /returns` with `{"sale_id":1,"return_reason_id":1,"returned_quantity":1,"return_date":"2026-09-12","return_status":"Received","refund_amount":49.99}`. `return_reason_id` may be omitted or null when the reason table has no matching row.
5. `POST /products/1/feedback` with `{"sale_id":1,"rating":2,"feedback_text":"The sleeves are too short","feedback_date":"2026-09-12"}`. Use the actual `product_id` and `sale_id` values.
6. Optionally, `POST /knowledge/documents` with `{"title":"Sizing guide","source":"sizing-guide.md","text":"...document text..."}`.
7. `POST /investigate` with `{"product_id":1,"query":"Why are customers returning this jacket?"}`. The API saves and returns the report.

A return rate is only calculated when sales units are available; the configured threshold defaults to 10%. Findings are evidence summaries, not proof of causality. Without enough data, the report calls that out. The initial knowledge upload endpoint accepts document text; PDF parsing and bulk CSV import are not implemented in this first version.

## Saved chat history

After login, the sidebar lists the signed-in user's conversations. **New** starts a saved conversation, selecting one reopens its messages, and **Delete** permanently removes that conversation and its messages. Chat messages and conversation ownership are stored in PostgreSQL. The backend loads the latest 20 saved messages as Gemini context; history sent by the browser is not trusted. New chat tables are created automatically at API startup. A `--reset` data reload deletes chat history too; an ordinary CSV reload preserves it.

The chat assistant is limited to product return analysis and directly related sales, return reasons, customer feedback, and evidence-based actions. It should decline unrelated requests such as general programming questions.

## Run tests

After installing dependencies and activating `.venv`, run `pytest` from the project root.

## API overview

- `POST /auth/signup`, `POST /auth/login`, `POST /auth/change-password`, `POST /auth/users`
- `POST /products`, `GET /products`, `GET /products/{product_id}`, `GET /products/{product_id}/return-analysis`
- `DELETE /products/{product_id}` (administrator only; returns `204` when deleted and `409` when related history prevents deletion)
- `PATCH /products/{product_id}/owner` (administrator only; body: `{"email":"user@example.com"}`)
- `POST /customers`, `POST /sales`, `POST /returns`, `GET /return-reasons`, `GET /products/{product_id}/returns`
- `POST /products/{product_id}/feedback`, `GET /products/{product_id}/feedback`
- `POST /knowledge/documents`, `POST /knowledge/search`
- `GET /chat/conversations`, `POST /chat/conversations`, `GET /chat/conversations/{conversation_id}`, `DELETE /chat/conversations/{conversation_id}`, `POST /chat`
- `POST /investigate`, `GET /investigate/{product_id}/report`
