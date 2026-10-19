# WebSocket chat endpoint

This adds a WebSocket transport for the existing LangGraph agent. The endpoint streams text chunks as the agent generates its answer; the Telegram bot continues to work as before.

## Configuration

Add these entries to your local `.env` (never commit the real token):

```dotenv
WS_API_TOKEN=replace-with-a-long-random-secret
WS_USER_ID=1
```

`WS_USER_ID` must be the internal primary key of the user row in PostgreSQL, not the Telegram ID. This demo intentionally binds the endpoint to one configured user instead of trusting a user ID supplied by a WebSocket client.

## Run

After the database has been initialized by the bot/migrations:

```bash
docker compose up --build ws-api
```

Health check: `http://localhost:8000/health`

WebSocket URL: `ws://localhost:8000/ws/chat`

## Message protocol

1. Connect to `/ws/chat`.
2. Send the first JSON frame with the token:

   ```json
   {"token":"replace-with-a-long-random-secret"}
   ```

3. Wait for `{"type":"ready"}`.
4. Send a message as a JSON frame:

   ```json
   {"message":"Добавь задачу купить молоко"}
   ```

5. The server sends text chunks as they arrive:

   ```json
   {"type":"token","text":"Задача "}
   {"type":"token","text":"добавлена"}
   {"type":"done"}
   ```

   Chunk boundaries are not guaranteed to match words. The client should append each `token.text` to the current answer and treat `done` as the end of that answer. An error is represented as `{"type":"error","message":"..."}`.

The server calls `app.agent.core.stream`, which uses LangGraph's `astream(..., stream_mode="messages")` to receive model message chunks. It streams only text chunks from the agent node, not tool-node output, and runs the existing conversation-memory maintenance after generation.

## Try it with a WebSocket client

Install `websocat`, then run:

```bash
websocat ws://localhost:8000/ws/chat
```

Paste the token JSON as the first line, then send message JSON lines. You should see several `token` frames followed by `done` (although a short answer may arrive in only one text chunk).

For local-only interview practice this is enough. Before exposing it publicly, add TLS (WSS), rate limiting, and a stronger identity/session model. The configured token is sent inside the WebSocket message, so do not use plain `ws://` over an untrusted network.
