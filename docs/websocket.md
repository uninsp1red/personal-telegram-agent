# WebSocket chat endpoint

This adds a small WebSocket transport for the existing LangGraph agent. It is a separate API process; the Telegram bot continues to work as before.

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
4. Send messages as JSON frames:

   ```json
   {"message":"Добавь задачу купить молоко"}
   ```

5. The server invokes the same `app.agent.core.invoke` function used by the Telegram bot and returns:

   ```json
   {"type":"response","message":"..."}
   ```

Invalid frames return a JSON error. Invalid authentication closes the connection with code 1008. Server-side processing errors are logged and return a generic error to the client.

## Try it with a WebSocket client

Install `websocat`, then run:

```bash
websocat ws://localhost:8000/ws/chat
```

Paste the token JSON as the first line, then send message JSON lines.

For local-only interview practice this is enough. Before exposing it publicly, add TLS (WSS), rate limiting, and a stronger identity/session model. The configured token is sent inside the WebSocket message, so do not use plain `ws://` over an untrusted network.
