"""Admin dashboard routes — basic auth, metrics, conversation viewer, WebSocket live updates."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import get_settings
from app.dependencies import get_db
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBasic()

# Track connected WebSocket clients for live updates
_ws_clients: set[WebSocket] = set()


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin basic auth credentials."""
    settings = get_settings()
    if (
        credentials.username != settings.admin_username
        or credentials.password != settings.admin_password
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials.username


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    _: str = Depends(verify_admin),
    db=Depends(get_db),
):
    """Serve the admin dashboard HTML page."""
    settings = get_settings()
    conv_service = ConversationService(db)

    # Fetch metrics
    today_count = await conv_service.get_conversation_count(since_hours=24)
    week_count = await conv_service.get_conversation_count(since_hours=168)
    escalation_count = await conv_service.get_escalation_count(since_hours=24)
    channel_breakdown = await conv_service.get_channel_breakdown(since_hours=168)
    recent = await conv_service.get_recent_conversations(limit=20)

    metrics_json = json.dumps({
        "today": today_count,
        "week": week_count,
        "escalations": escalation_count,
        "channels": channel_breakdown,
    })
    recent_json = json.dumps(recent, default=str)

    return HTMLResponse(_DASHBOARD_HTML.format(
        client_name=settings.client_name,
        agent_name=settings.agent_name,
        metrics_json=metrics_json,
        recent_json=recent_json,
    ))


@router.get("/conversation/{conversation_id}", response_class=HTMLResponse)
async def conversation_detail(
    conversation_id: str,
    _: str = Depends(verify_admin),
    db=Depends(get_db),
):
    """Full debug view of a conversation — transcript + intent + tools + sentiment."""
    from sqlalchemy import select
    from app.models.conversation import Conversation
    from app.models.message import Message
    from app.models.lead import Lead

    settings = get_settings()

    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get messages
    msg_stmt = select(Message).where(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at)
    msg_result = await db.execute(msg_stmt)
    messages = msg_result.scalars().all()

    # Get lead data
    lead_stmt = select(Lead).where(Lead.conversation_id == conversation_id)
    lead_result = await db.execute(lead_stmt)
    lead = lead_result.scalar_one_or_none()

    messages_data = [
        {
            "direction": m.direction.value,
            "content": m.content,
            "intent": m.intent,
            "sentiment": m.sentiment,
            "tool_calls": m.tool_calls,
            "llm_model": m.llm_model,
            "token_count": m.token_count,
            "time": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]

    lead_data = None
    if lead:
        lead_data = {
            "score": lead.score,
            "status": lead.status.value,
            "budget": lead.budget_confirmed,
            "authority": lead.is_decision_maker,
            "need": lead.need_identified,
            "timeline": lead.timeline,
        }

    return HTMLResponse(_CONVERSATION_HTML.format(
        client_name=settings.client_name,
        conversation_id=conversation_id,
        channel=conv.channel.value,
        status=conv.status.value,
        mode=conv.mode.value,
        escalated=conv.escalated,
        messages_json=json.dumps(messages_data, default=str),
        lead_json=json.dumps(lead_data, default=str),
    ))


@router.websocket("/ws")
async def admin_ws(websocket: WebSocket, db=Depends(get_db)):
    """WebSocket for live dashboard updates."""
    await websocket.accept()
    _ws_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        _ws_clients.discard(websocket)


async def broadcast_update(data: dict[str, Any]):
    """Push update to all connected admin clients."""
    message = json.dumps(data, default=str)
    disconnected = set()
    for ws in _ws_clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)
    _ws_clients -= disconnected


# ── Inline HTML Templates ──────────────────────────────────
# (Kept inline for simplicity in MVP — would move to Jinja2 templates in production)

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{client_name} — Admin Dashboard</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Inter',system-ui,sans-serif; background:#0f172a; color:#e2e8f0; }}
  .header {{ background:linear-gradient(135deg,#1e293b,#334155); padding:24px 32px; border-bottom:1px solid #334155; }}
  .header h1 {{ font-size:22px; color:#f8fafc; }} .header p {{ color:#94a3b8; font-size:13px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; padding:24px 32px; }}
  .card {{ background:#1e293b; border:1px solid #334155; border-radius:12px; padding:20px; }}
  .card .label {{ font-size:12px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px; }}
  .card .value {{ font-size:32px; font-weight:700; color:#f8fafc; margin-top:4px; }}
  .card.escalation .value {{ color:#f87171; }}
  .section {{ padding:16px 32px; }}
  .section h2 {{ font-size:16px; margin-bottom:12px; color:#cbd5e1; }}
  table {{ width:100%; border-collapse:collapse; background:#1e293b; border-radius:8px; overflow:hidden; }}
  th,td {{ padding:12px 16px; text-align:left; border-bottom:1px solid #334155; font-size:14px; }}
  th {{ background:#334155; color:#94a3b8; font-size:12px; text-transform:uppercase; }}
  td a {{ color:#60a5fa; text-decoration:none; }} td a:hover {{ text-decoration:underline; }}
  .badge {{ padding:2px 8px; border-radius:9999px; font-size:11px; font-weight:600; }}
  .badge.active {{ background:#065f46; color:#6ee7b7; }}
  .badge.escalated {{ background:#7f1d1d; color:#fca5a5; }}
  .badge.resolved {{ background:#1e3a5f; color:#93c5fd; }}
  .live-dot {{ display:inline-block; width:8px; height:8px; background:#22c55e; border-radius:50%; margin-right:8px; animation:pulse 2s infinite; }}
  @keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.4; }} }}
</style>
</head>
<body>
<div class="header">
  <h1><span class="live-dot"></span>{client_name} — AI Agent Dashboard</h1>
  <p>Agent: {agent_name} | <span id="liveClock"></span></p>
</div>
<div class="grid">
  <div class="card"><div class="label">Today</div><div class="value" id="metricToday">—</div></div>
  <div class="card"><div class="label">This Week</div><div class="value" id="metricWeek">—</div></div>
  <div class="card escalation"><div class="label">Escalations (24h)</div><div class="value" id="metricEsc">—</div></div>
  <div class="card"><div class="label">Active Now</div><div class="value" id="metricActive">—</div></div>
</div>
<div class="section">
  <h2>Recent Conversations</h2>
  <table><thead><tr><th>Time</th><th>Channel</th><th>Status</th><th>Mode</th><th>Messages</th><th></th></tr></thead>
  <tbody id="convTable"></tbody></table>
</div>
<script>
const metrics = {metrics_json};
const recent = {recent_json};
document.getElementById('metricToday').textContent = metrics.today;
document.getElementById('metricWeek').textContent = metrics.week;
document.getElementById('metricEsc').textContent = metrics.escalations;
document.getElementById('metricActive').textContent = recent.filter(c=>c.status==='active').length;
function renderTable(data) {{
  const tbody = document.getElementById('convTable');
  tbody.innerHTML = data.map(c => `<tr>
    <td>${{new Date(c.created_at).toLocaleString()}}</td>
    <td>${{c.channel}}</td>
    <td><span class="badge ${{c.status}}">${{c.status}}</span></td>
    <td>${{c.mode}}</td>
    <td>${{c.message_count}}</td>
    <td><a href="/admin/conversation/${{c.id}}">View</a></td>
  </tr>`).join('');
}}
renderTable(recent);
// Live clock
setInterval(()=>{{ document.getElementById('liveClock').textContent = new Date().toLocaleTimeString(); }}, 1000);
// WebSocket live updates
const ws = new WebSocket(`ws://${{location.host}}/admin/ws`);
ws.onmessage = (e) => {{
  const data = JSON.parse(e.data);
  if (data.metrics) {{
    document.getElementById('metricToday').textContent = data.metrics.today;
    document.getElementById('metricEsc').textContent = data.metrics.escalations;
  }}
  if (data.recent) renderTable(data.recent);
}};
</script>
</body></html>"""


_CONVERSATION_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Conversation — {conversation_id}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Inter',system-ui,sans-serif; background:#0f172a; color:#e2e8f0; padding:24px 32px; }}
  .back {{ color:#60a5fa; text-decoration:none; font-size:14px; }} .back:hover {{ text-decoration:underline; }}
  h1 {{ font-size:18px; margin:12px 0; color:#f8fafc; }}
  .meta {{ display:flex; gap:16px; margin-bottom:16px; font-size:13px; color:#94a3b8; }}
  .meta span {{ background:#1e293b; padding:4px 10px; border-radius:6px; }}
  .transcript {{ max-width:700px; }}
  .msg {{ margin-bottom:16px; padding:12px 16px; border-radius:12px; font-size:14px; line-height:1.5; }}
  .msg.inbound {{ background:#1e293b; border:1px solid #334155; margin-right:60px; }}
  .msg.outbound {{ background:#1e3a5f; border:1px solid #2563eb44; margin-left:60px; }}
  .msg .tools {{ font-size:12px; color:#94a3b8; margin-top:8px; background:#0f172a; padding:6px 10px; border-radius:6px; }}
  .msg .meta-line {{ font-size:11px; color:#64748b; margin-top:4px; }}
  .lead-card {{ background:#1e293b; border:1px solid #334155; border-radius:12px; padding:16px; margin-top:20px; max-width:300px; }}
  .lead-card h3 {{ font-size:14px; margin-bottom:8px; color:#cbd5e1; }}
  .lead-card .score {{ font-size:28px; font-weight:700; color:#f59e0b; }}
</style>
</head>
<body>
<a href="/admin/" class="back">← Back to Dashboard</a>
<h1>Conversation {conversation_id}</h1>
<div class="meta">
  <span>Channel: {channel}</span>
  <span>Status: {status}</span>
  <span>Mode: {mode}</span>
  <span>Escalated: {escalated}</span>
</div>
<div class="transcript" id="transcript"></div>
<div id="leadCard"></div>
<script>
const messages = {messages_json};
const lead = {lead_json};
const transcript = document.getElementById('transcript');
messages.forEach(m => {{
  let html = `<div class="msg ${{m.direction}}">`;
  html += `<div>${{m.content}}</div>`;
  if (m.intent) html += `<div class="meta-line">Intent: ${{m.intent}} | Sentiment: ${{m.sentiment || '—'}} | Model: ${{m.llm_model || '—'}} | Tokens: ${{m.token_count || '—'}}</div>`;
  if (m.tool_calls && m.tool_calls.length) {{
    html += `<div class="tools">🔧 Tools: ${{m.tool_calls.map(t => t.name || JSON.stringify(t)).join(', ')}}</div>`;
  }}
  html += `<div class="meta-line">${{m.time ? new Date(m.time).toLocaleString() : ''}}</div>`;
  html += `</div>`;
  transcript.innerHTML += html;
}});
if (lead) {{
  document.getElementById('leadCard').innerHTML = `
    <div class="lead-card">
      <h3>Lead Score</h3>
      <div class="score">${{lead.score}}/100</div>
      <div style="font-size:13px;margin-top:8px;">
        Status: ${{lead.status}}<br>
        Budget: ${{lead.budget ? '✅' : '❌'}} | Authority: ${{lead.authority ? '✅' : '❌'}} | Need: ${{lead.need ? '✅' : '❌'}}<br>
        Timeline: ${{lead.timeline || '—'}}
      </div>
    </div>`;
}}
</script>
</body></html>"""
