# websocket_server.py

import asyncio
import websockets
import json
import logging
from typing import Dict, Set, Any, Optional
from datetime import datetime
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketNotificationServer:
    """WebSocket server for real-time notifications in SSTDMS."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.user_sessions: Dict[int, Set[str]] = {}  # user_id -> set of connection_ids
        self.connection_info: Dict[str, Dict[str, Any]] = {}  # connection_id -> user info
        
    async def register_client(self, websocket: websockets.WebSocketServerProtocol, user_id: int, username: str) -> str:
        """Register a new client connection."""
        connection_id = str(uuid.uuid4())
        
        self.clients[connection_id] = websocket
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(connection_id)
        
        self.connection_info[connection_id] = {
            "user_id": user_id,
            "username": username,
            "connected_at": datetime.now().isoformat(),
            "last_ping": datetime.now().isoformat()
        }
        
        logger.info(f"Client registered: {username} (ID: {user_id}, Connection: {connection_id})")
        
        # Send welcome message
        await self.send_to_connection(connection_id, {
            "type": "connection_established",
            "message": "WebSocket connection established successfully",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat()
        })
        
        return connection_id
    
    async def unregister_client(self, connection_id: str):
        """Unregister a client connection."""
        if connection_id in self.clients:
            user_info = self.connection_info.get(connection_id, {})
            user_id = user_info.get("user_id")
            username = user_info.get("username", "Unknown")
            
            # Remove from clients
            del self.clients[connection_id]
            
            # Remove from user sessions
            if user_id and user_id in self.user_sessions:
                self.user_sessions[user_id].discard(connection_id)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
            
            # Remove connection info
            if connection_id in self.connection_info:
                del self.connection_info[connection_id]
            
            logger.info(f"Client unregistered: {username} (Connection: {connection_id})")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send message to a specific connection."""
        if connection_id not in self.clients:
            logger.warning(f"Connection {connection_id} not found")
            return False
        
        try:
            websocket = self.clients[connection_id]
            await websocket.send(json.dumps(message))
            return True
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"Connection {connection_id} is closed, removing from clients")
            await self.unregister_client(connection_id)
            return False
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {str(e)}")
            return False
    
    async def send_to_user(self, user_id: int, message: Dict[str, Any]) -> int:
        """Send message to all connections of a specific user."""
        if user_id not in self.user_sessions:
            logger.warning(f"User {user_id} has no active connections")
            return 0
        
        sent_count = 0
        connections_to_remove = []
        
        for connection_id in self.user_sessions[user_id].copy():
            success = await self.send_to_connection(connection_id, message)
            if success:
                sent_count += 1
            else:
                connections_to_remove.append(connection_id)
        
        # Clean up failed connections
        for connection_id in connections_to_remove:
            await self.unregister_client(connection_id)
        
        return sent_count
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """Broadcast message to all connected clients."""
        sent_count = 0
        connections_to_remove = []
        
        for connection_id in list(self.clients.keys()):
            success = await self.send_to_connection(connection_id, message)
            if success:
                sent_count += 1
            else:
                connections_to_remove.append(connection_id)
        
        # Clean up failed connections
        for connection_id in connections_to_remove:
            await self.unregister_client(connection_id)
        
        return sent_count
    
    async def send_notification(self, user_id: int, notification_type: str, title: str, message: str, data: Dict[str, Any] = None) -> int:
        """Send a structured notification to a user."""
        notification = {
            "type": "notification",
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        }
        
        return await self.send_to_user(user_id, notification)
    
    async def handle_client_message(self, connection_id: str, message: Dict[str, Any]):
        """Handle incoming messages from clients."""
        message_type = message.get("type")
        
        if message_type == "ping":
            # Update last ping time
            if connection_id in self.connection_info:
                self.connection_info[connection_id]["last_ping"] = datetime.now().isoformat()
            
            # Send pong response
            await self.send_to_connection(connection_id, {
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            })
        
        elif message_type == "subscribe":
            # Handle subscription to specific notification types
            subscription_type = message.get("subscription_type")
            logger.info(f"Connection {connection_id} subscribed to {subscription_type}")
            
            await self.send_to_connection(connection_id, {
                "type": "subscription_confirmed",
                "subscription_type": subscription_type,
                "timestamp": datetime.now().isoformat()
            })
        
        elif message_type == "get_status":
            # Send connection status
            user_info = self.connection_info.get(connection_id, {})
            await self.send_to_connection(connection_id, {
                "type": "status",
                "connection_info": user_info,
                "total_connections": len(self.clients),
                "timestamp": datetime.now().isoformat()
            })
        
        else:
            logger.warning(f"Unknown message type from {connection_id}: {message_type}")
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle a client connection."""
        connection_id = None
        
        try:
            # Wait for authentication message
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)
            
            if auth_data.get("type") != "authenticate":
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Authentication required"
                }))
                return
            
            user_id = auth_data.get("user_id")
            username = auth_data.get("username")
            session_token = auth_data.get("session_token")
            
            # TODO: Validate session_token with your session handler
            # For now, we'll accept any authentication
            if not user_id or not username:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid authentication data"
                }))
                return
            
            # Register the client
            connection_id = await self.register_client(websocket, user_id, username)
            
            # Listen for messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_client_message(connection_id, data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {connection_id}: {message}")
                except Exception as e:
                    logger.error(f"Error handling message from {connection_id}: {str(e)}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"Error in client handler: {str(e)}")
        finally:
            if connection_id:
                await self.unregister_client(connection_id)
    
    async def start_server(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            "total_connections": len(self.clients),
            "total_users": len(self.user_sessions),
            "connections_per_user": {
                user_id: len(connections) 
                for user_id, connections in self.user_sessions.items()
            },
            "server_info": {
                "host": self.host,
                "port": self.port,
                "started_at": datetime.now().isoformat()
            }
        }

# Global server instance
notification_server = WebSocketNotificationServer()

# Convenience functions for external use
async def send_user_notification(user_id: int, notification_type: str, title: str, message: str, data: Dict[str, Any] = None) -> int:
    """Send notification to a specific user."""
    return await notification_server.send_notification(user_id, notification_type, title, message, data)

async def broadcast_system_notification(title: str, message: str, data: Dict[str, Any] = None) -> int:
    """Broadcast system notification to all users."""
    notification = {
        "type": "system_notification",
        "title": title,
        "message": message,
        "data": data or {},
        "timestamp": datetime.now().isoformat(),
        "id": str(uuid.uuid4())
    }
    return await notification_server.broadcast_to_all(notification)

# Example usage and testing
if __name__ == "__main__":
    async def test_notifications():
        """Test function to send sample notifications."""
        await asyncio.sleep(5)  # Wait for server to start
        
        # Send test notifications
        await send_user_notification(
            user_id=1,
            notification_type="project_update",
            title="프로젝트 업데이트",
            message="프로젝트 'ABC'에 새로운 문서가 업로드되었습니다.",
            data={"project_id": 123, "document_name": "설계도.pdf"}
        )
        
        await broadcast_system_notification(
            title="시스템 공지",
            message="시스템 점검이 예정되어 있습니다.",
            data={"maintenance_time": "2025-08-01 02:00:00"}
        )
    
    # Start server and test
    async def main():
        # Start test notifications in background
        asyncio.create_task(test_notifications())
        
        # Start the server
        await notification_server.start_server()
    
    asyncio.run(main())

