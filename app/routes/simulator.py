"""Simulator route — browser-based chat UI for testing the agent without real APIs."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.channels.simulator import SimulatorAdapter
from app.config import get_settings
from app.dependencies import get_db, get_redis
from app.services.orchestrator import Orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBasic()


def _check_simulator(credentials: HTTPBasicCredentials = Depends(security)):
    settings = get_settings()
    if not settings.simulator_enabled:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Simulator disabled")
    if credentials.username != settings.admin_username or credentials.password != settings.admin_password:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return True


@router.get("/simulator", response_class=HTMLResponse)
async def simulator_page(_=Depends(_check_simulator)):
    """Serve the simulator chat UI."""
    settings = get_settings()
    return HTMLResponse(_SIMULATOR_HTML.format(
        agent_name=settings.agent_name,
        client_name=settings.client_name,
    ))


@router.websocket("/simulator/ws")
async def simulator_ws(websocket: WebSocket, db=Depends(get_db), redis=Depends(get_redis)):
    """WebSocket endpoint for real-time simulator chat."""
    settings = get_settings()
    if not settings.simulator_enabled:
        await websocket.close()
        return

    await websocket.accept()
    adapter = SimulatorAdapter()

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            nlp_message = await adapter.parse_inbound(payload)
            if not nlp_message:
                continue

            orchestrator = Orchestrator(db, redis)
            response = await orchestrator.process_message(nlp_message)

            await websocket.send_text(json.dumps({
                "text": response.text,
                "debug": response.debug,
            }, default=str))
    except WebSocketDisconnect:
        logger.info("Simulator client disconnected")
    except Exception as e:
        logger.exception("Simulator error: %s", e)


_SIMULATOR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{agent_name} — Chat Simulator</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Inter',system-ui,sans-serif; background:#0f172a; color:#e2e8f0; height:100vh; display:flex; }}
  .chat-panel {{ flex:1; display:flex; flex-direction:column; max-width:600px; border-right:1px solid #334155; }}
  .debug-panel {{ flex:1; overflow-y:auto; padding:16px; background:#0a0f1a; font-size:13px; }}
  .debug-panel h3 {{ color:#94a3b8; font-size:12px; text-transform:uppercase; margin:12px 0 6px; }}
  .debug-panel pre {{ background:#1e293b; padding:8px; border-radius:6px; overflow-x:auto; font-size:12px; color:#a5f3fc; white-space:pre-wrap; }}
  .chat-header {{ background:linear-gradient(135deg,#1e293b,#334155); padding:16px 20px; }}
  .chat-header h1 {{ font-size:18px; color:#f8fafc; }}
  .chat-header p {{ font-size:12px; color:#94a3b8; }}
  .messages {{ flex:1; overflow-y:auto; padding:16px; }}
  .msg {{ max-width:80%; margin-bottom:12px; padding:10px 14px; border-radius:12px; font-size:14px; line-height:1.5; }}
  .msg.user {{ background:#1e3a5f; margin-left:auto; color:#e0f2fe; border-bottom-right-radius:4px; }}
  .msg.agent {{ background:#1e293b; border:1px solid #334155; border-bottom-left-radius:4px; }}
  .input-bar {{ display:flex; padding:12px 16px; background:#1e293b; border-top:1px solid #334155; }}
  .input-bar input {{ flex:1; background:#0f172a; border:1px solid #334155; border-radius:8px; padding:10px 14px; color:#f8fafc; font-size:14px; outline:none; }}
  .input-bar input:focus {{ border-color:#3b82f6; }}
  .input-bar button {{ background:#2563eb; color:#fff; border:none; border-radius:8px; padding:10px 20px; margin-left:8px; cursor:pointer; font-size:14px; }}
  .input-bar button:hover {{ background:#1d4ed8; }}
  .typing {{ color:#94a3b8; font-size:13px; padding:4px 16px; }}
</style>
</head>
<body>
<div class="chat-panel">
  <div class="chat-header">
    <h1>💬 {agent_name}</h1>
    <p>{client_name} — Simulator Mode</p>
  </div>
  <div class="messages" id="messages"></div>
  <div class="typing" id="typing"></div>
  <div class="input-bar">
    <input type="text" id="input" placeholder="Type a message..." autocomplete="off">
    <button onclick="sendMessage()">Send</button>
  </div>
</div>
<div class="debug-panel" id="debugPanel">
  <h2 style="color:#f8fafc;font-size:16px;margin-bottom:12px;">🔍 Debug Panel</h2>
  <p style="color:#64748b;font-size:13px;">Send a message to see debug info here.</p>
</div>
<script>
const ws = new WebSocket(`ws://${{location.host}}/simulator/ws`);
const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('input');
const typingEl = document.getElementById('typing');
const debugEl = document.getElementById('debugPanel');

inputEl.addEventListener('keypress', e => {{ if(e.key==='Enter') sendMessage(); }});

function sendMessage() {{
  const text = inputEl.value.trim();
  if(!text) return;
  addMsg(text, 'user');
  ws.send(JSON.stringify({{ text, user_id: 'simulator_user' }}));
  inputEl.value = '';
  typingEl.textContent = '{agent_name} is typing...';
}}

ws.onmessage = (e) => {{
  typingEl.textContent = '';
  const data = JSON.parse(e.data);
  addMsg(data.text, 'agent');
  renderDebug(data.debug);
}};

function addMsg(text, type) {{
  const div = document.createElement('div');
  div.className = `msg ${{type}}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}}

function renderDebug(debug) {{
  if(!debug) return;
  let html = '<h2 style="color:#f8fafc;font-size:16px;margin-bottom:12px;">🔍 Debug Panel</h2>';
  if(debug.intent) html += `<h3>Intent</h3><pre>${{JSON.stringify(debug.intent, null, 2)}}</pre>`;
  if(debug.identity) html += `<h3>Identity</h3><pre>${{JSON.stringify(debug.identity, null, 2)}}</pre>`;
  if(debug.rag_results) html += `<h3>RAG Results</h3><pre>${{JSON.stringify(debug.rag_results, null, 2)}}</pre>`;
  if(debug.tool_calls) html += `<h3>Tool Calls</h3><pre>${{JSON.stringify(debug.tool_calls, null, 2)}}</pre>`;
  if(debug.lead_score !== undefined) html += `<h3>Lead Score</h3><pre>${{debug.lead_score}}/100</pre>`;
  if(debug.tokens) html += `<h3>Tokens</h3><pre>${{JSON.stringify(debug.tokens, null, 2)}}</pre>`;
  if(debug.response_time_ms) html += `<h3>Response Time</h3><pre>${{debug.response_time_ms}}ms</pre>`;
  if(debug.escalated) html += `<h3 style="color:#f87171">⚠️ ESCALATED</h3><pre>${{debug.escalation_reason}}</pre>`;
  html += `<h3>LLM Model</h3><pre>${{debug.llm_model || '—'}}</pre>`;
  debugEl.innerHTML = html;
}}
</script>
</body></html>"""
