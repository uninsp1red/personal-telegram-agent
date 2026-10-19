import hmac
import json
import logging
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.agent.core import invoke as invoke_agent

logger = logging.getLogger(__name__)
app = FastAPI(title="Personal Telegram Agent WebSocket API")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/chat")
async def chat(websocket: WebSocket) -> None:
    """Authenticated, single-user WebSocket bridge to the existing LangGraph agent.

    First client frame: {"token": "..."}
    Later client frames: {"message": "..."}
    Server frames: {"type": "ready"} / {"type": "response", "message": "..."}.
    """
    await websocket.accept()

    expected_token = os.getenv("WS_API_TOKEN")
    configured_user_id = os.getenv("WS_USER_ID")
    if not expected_token or not configured_user_id:
        logger.error("WS_API_TOKEN and WS_USER_ID must be configured")
        await websocket.close(code=1011, reason="WebSocket API is not configured")
        return

    try:
        user_id = int(configured_user_id)
    except ValueError:
        logger.error("WS_USER_ID must be an integer database user ID")
        await websocket.close(code=1011, reason="WebSocket API is not configured")
        return

    try:
        auth_frame = await websocket.receive_json()
    except (json.JSONDecodeError, WebSocketDisconnect):
        await websocket.close(code=1008, reason="Expected authentication JSON")
        return

    supplied_token = auth_frame.get("token") if isinstance(auth_frame, dict) else None
    if not isinstance(supplied_token, str) or not hmac.compare_digest(
        supplied_token, expected_token
    ):
        await websocket.close(code=1008, reason="Invalid token")
        return

    await websocket.send_json({"type": "ready"})

    try:
        while True:
            payload = await websocket.receive_json()
            message = payload.get("message") if isinstance(payload, dict) else None

            if not isinstance(message, str) or not message.strip():
                await websocket.send_json({
                    "type": "error",
                    "message": "Each frame must contain a non-empty string field 'message'.",
                })
                continue

            try:
                reply = await invoke_agent(user_id=user_id, message=message.strip())
                await websocket.send_json({"type": "response", "message": reply})
            except Exception:
                logger.exception("Agent invocation failed over WebSocket")
                await websocket.send_json({
                    "type": "error",
                    "message": "Agent processing failed. Check server logs.",
                })
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
