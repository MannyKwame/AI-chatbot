# Gemini AI Chatbot

A full-stack AI chatbot built with **React, FastAPI, Google's Gemini API, and PostgreSQL**. The project demonstrates how to connect an LLM to a frontend and backend while saving conversations and messages in a database.

## Features

- **AI-powered chat** using Google's Gemini API.
- **Persistent conversations** stored in PostgreSQL.
- **Conversation history** restored after refreshing the browser.
- **Multiple conversations** with the ability to start a new chat and switch between saved chats.
- **Collapsible sidebar** for navigating conversations.
- **Markdown rendering** for readable AI responses, including headings, lists, and code blocks.
- **Backend-managed API key** so the Gemini key is not exposed in frontend code.
- **FastAPI endpoints** for sending messages and retrieving conversation history.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, JavaScript, CSS |
| Backend | Python, FastAPI |
| AI model API | Google Gemini API (`gemini-3.6-flash`) |
| Database | PostgreSQL |
| ORM / database access | SQLAlchemy |
| PostgreSQL driver | Psycopg |
| Frontend Markdown | `react-markdown`, `remark-gfm` |
| Environment configuration | `python-dotenv` |

## Architecture

```text
React + Vite frontend
        |
        | HTTP requests
        v
FastAPI backend
        |
        +------> Google Gemini API
        |
        v
SQLAlchemy + Psycopg
        |
        v
PostgreSQL database
  ├── conversations
  └── messages
```

The frontend sends the user's message and active `conversation_id` to FastAPI. The backend loads recent messages from PostgreSQL, sends the relevant conversation context to Gemini, saves the new user message and assistant response, and returns the reply and conversation ID. The frontend stores that ID in browser `localStorage` so it can restore the selected conversation after a refresh.

## Project Structure

The project is organised into a frontend and backend. Your backend files may look similar to this:

```text
LLM chatbot/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── ...
│   ├── package.json
│   └── ...
└── backend/
    ├── main.py
    ├── database.py
    ├── models.py
    ├── create_tables.py
    ├── test_db.py
    ├── .env                 # Do not commit
    └── ...
```

## Prerequisites

Install or prepare the following before running the project:

- Python 3.13 (or another version supported by your installed dependencies)
- Node.js and npm
- PostgreSQL
- `uv` for Python environment and dependency management
- A Google Gemini API key

## Setup

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd "LLM chatbot"
```

Replace `<YOUR_REPOSITORY_URL>` with your Git repository URL. If your repository name differs, change the directory command accordingly.

### 2. Configure PostgreSQL

Create a PostgreSQL database for the app. For example:

```sql
CREATE DATABASE chatbot_db;
```

Use your own PostgreSQL username and password in the connection string below.

### 3. Configure backend environment variables

Create a `.env` file inside the `backend/` directory:

```env
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql+psycopg://YOUR_USERNAME:YOUR_PASSWORD@localhost:5432/chatbot_db
```

Replace the placeholder values with your own credentials. If your password contains special characters, URL-encode those characters in the database URL.

**Security:** Never commit `.env` or expose your Gemini API key in frontend code. Add `.env` to `.gitignore`.

### 4. Install backend dependencies

Open a terminal in the `backend/` directory:

```bash
uv sync
```

If your project does not yet have a committed `uv.lock`, `uv sync` will resolve dependencies from `pyproject.toml`.

Make sure the backend dependencies include the packages used by the project, such as FastAPI, Uvicorn, Google GenAI, SQLAlchemy, Psycopg, and python-dotenv.

### 5. Create the database tables

From the `backend/` directory, run:

```bash
uv run python create_tables.py
```

This creates the `conversations` and `messages` tables defined in `models.py`.

### 6. Start the backend

From the `backend/` directory:

```bash
uv run uvicorn main:app --reload
```

The API should be available at:

- API base URL: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

### 7. Install and start the frontend

Open a second terminal in the `frontend/` directory:

```bash
npm install
npm run dev
```

Open the local URL printed by Vite, commonly `http://localhost:5173`.

The backend CORS configuration should allow the frontend origin you use. The current development configuration allows `http://localhost:5173`.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/chat` | Creates or continues a conversation and returns the AI reply and `conversation_id`. |
| `GET` | `/conversations` | Returns the saved conversation list. |
| `GET` | `/conversations/{conversation_id}` | Returns the messages for a specific conversation. |
| `POST` | `/test-db-write` | Creates test data to verify database writes. |

### Example: send a message

`POST /chat`

```json
{
  "message": "Explain retrieval-augmented generation.",
  "conversation_id": null
}
```

For a new conversation, use `null` as the ID. For an existing conversation, send the ID returned by the previous response.

Example response:

```json
{
  "reply": "Retrieval-augmented generation (RAG) combines information retrieval with text generation...",
  "conversation_id": 1
}
```

The actual reply and ID will vary.

## How Conversation Persistence Works

1. The user sends a message from React.
2. React sends the message and active `conversation_id` to FastAPI.
3. FastAPI creates a conversation if no ID was provided, or loads the requested existing conversation.
4. The backend retrieves recent messages from PostgreSQL to build Gemini's context.
5. The user's new message is saved in PostgreSQL.
6. Gemini generates a response using the supplied context.
7. The assistant's response is saved in PostgreSQL.
8. FastAPI returns the response and conversation ID.
9. React stores the conversation ID in `localStorage`.
10. On refresh or when selecting a saved chat, React retrieves the stored conversation history from FastAPI.

The backend currently sends up to the latest 20 saved messages as context to Gemini. This context limit does not mean older messages are automatically deleted from PostgreSQL.

## Current Limitations and Security Notes

This is a learning project and local development prototype, not a production-ready multi-user service.

- The app currently has no user authentication or conversation ownership checks. Do not expose it publicly with real or sensitive conversations until these are implemented.
- The conversation ID stored in `localStorage` identifies the active chat in that browser; it is not an authentication mechanism.
- The frontend uses a local backend URL. Update the API URL and CORS settings before deployment.
- The development server uses `--reload`; use an appropriate production deployment configuration when hosting the app.
- Add stronger error handling, request limits, authentication, authorisation, and database migration management before production use.
- Keep API keys and database credentials private.

## Learning Goals

This project was built to practise:

- Connecting a React frontend to a FastAPI backend.
- Calling an LLM API securely from the backend.
- Understanding conversation context and model inference.
- Modelling conversations and messages in a relational database.
- Saving and retrieving data with SQLAlchemy.
- Building REST endpoints with FastAPI.
- Persisting frontend state across browser refreshes.
- Supporting multiple conversations in a chat interface.

## Future Improvements

- User registration, login, and conversation ownership.
- Delete and rename conversation controls.
- Better conversation titles and timestamps.
- Streaming AI responses.
- Database migrations with Alembic.
- Automated tests for the API and database.
- Deployment with production environment variables and HTTPS.
- Optional document upload and retrieval-augmented generation (RAG).

## License

Choose a license before distributing or accepting contributions. If no license has been added, all rights remain with the copyright holder by default.
