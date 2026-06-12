from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "dashboard": set(),
            "agent": set(),
            "all": set()
        }
    
    async def connect(self, websocket: WebSocket, channel: str = "all"):
        await websocket.accept()
        self.active_connections[channel].add(websocket)
        self.active_connections["all"].add(websocket)
        logger.info(f"WebSocket connected to {channel}. Total: {len(self.active_connections['all'])}")
    
    def disconnect(self, websocket: WebSocket, channel: str = "all"):
        self.active_connections[channel].discard(websocket)
        self.active_connections["all"].discard(websocket)
    
    async def broadcast(self, message: dict, channel: str = "all"):
        dead_connections = set()
        for connection in self.active_connections.get(channel, set()):
            try:
                await connection.send_json(message)
            except:
                dead_connections.add(connection)
        
        for conn in dead_connections:
            self.active_connections[channel].discard(conn)
            self.active_connections["all"].discard(conn)

manager = ConnectionManager()

@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await manager.connect(websocket, "dashboard")
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast({
                "type": "dashboard_update",
                "data": json.loads(data) if data else {}
            }, "dashboard")
    except WebSocketDisconnect:
        manager.disconnect(websocket, "dashboard")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, "dashboard")

@router.websocket("/ws/agent/{agent_id}")
async def agent_websocket(websocket: WebSocket, agent_id: str):
    await manager.connect(websocket, "agent")
    try:
        await websocket.send_json({
            "type": "connected",
            "agent_id": agent_id,
            "message": "Connected to CrossSell IQ real-time feed"
        })
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "agent")
    except Exception as e:
        logger.error(f"Agent WebSocket error: {e}")
        manager.disconnect(websocket, "agent")

async def broadcast_prediction_update(prediction: dict):
    await manager.broadcast({
        "type": "new_prediction",
        "data": prediction
    }, "dashboard")

async def broadcast_agent_alert(agent_id: str, alert: dict):
    await manager.broadcast({
        "type": "agent_alert",
        "agent_id": agent_id,
        "data": alert
    }, "agent")
