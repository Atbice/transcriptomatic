import asyncio
import json
from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Store connections per meeting_id
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, meeting_id: int):
        await websocket.accept()
        if meeting_id not in self.active_connections:
            self.active_connections[meeting_id] = []
        self.active_connections[meeting_id].append(websocket)
        print(f"WebSocket connected for meeting {meeting_id}. Total connections for meeting: {len(self.active_connections[meeting_id])}")

    def disconnect(self, websocket: WebSocket, meeting_id: int):
        if meeting_id in self.active_connections:
            # Use a loop to safely remove the websocket instance
            # as direct comparison might fail in some edge cases
            connections = self.active_connections[meeting_id]
            for i, conn in enumerate(connections):
                 if conn == websocket:
                     del connections[i]
                     break # Exit loop once removed

            print(f"WebSocket disconnected for meeting {meeting_id}. Remaining connections: {len(self.active_connections[meeting_id])}")
            if not self.active_connections[meeting_id]:
                del self.active_connections[meeting_id] # Clean up empty list

    async def broadcast_json(self, data: dict, meeting_id: int):
        logging.info(f"broadcast_json called for meeting {meeting_id}. Checking connections...") # Added log
        if meeting_id in self.active_connections:
            connections = self.active_connections[meeting_id]
            logging.info(f"Found {len(connections)} connection(s) for meeting {meeting_id}.") # Added log
            message = json.dumps(data)
            # Keep the print for now as it's useful for seeing the actual message
            print(f"Broadcasting to {len(connections)} connections for meeting {meeting_id}: {message[:200]}...") # Log truncated message
            # Create a list of tasks to send messages concurrently
            # Filter out potentially closed connections before sending
            active_conns = [conn for conn in self.active_connections[meeting_id] if conn.client_state.name == 'CONNECTED']
            tasks = [conn.send_text(message) for conn in active_conns]
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        print(f"Error sending to websocket {i} for meeting {meeting_id}: {result}")
                        # Optionally handle disconnection here if needed based on the exception type
            else:
                logging.warning(f"No active connections to broadcast to for meeting {meeting_id} after filtering.") # Changed to warning
        else:
            logging.warning(f"No connection list found for meeting_id {meeting_id}. Active meetings: {list(self.active_connections.keys())}") # Changed to warning and added active keys
            # Removed redundant and incorrectly indented print statement

# Global instance of the manager
manager = ConnectionManager()