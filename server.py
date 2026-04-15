import asyncio
import json
import websockets
from datetime import datetime

# Menyimpan semua client yang terhubung
connected_clients = set()

async def handler(websocket):
    """Handle WebSocket connection (tanpa parameter path)"""
    # Register client
    connected_clients.add(websocket)
    print(f"✅ Client connected. Total clients: {len(connected_clients)}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                print(f"📨 Received: {data.get('type', 'unknown')}")
                
                # Handle different message types
                if data.get('type') == 'ping':
                    await websocket.send(json.dumps({
                        'type': 'pong', 
                        'timestamp': str(datetime.now())
                    }))
                elif data.get('type') == 'get_stats':
                    # Kirim statistik jika diminta
                    await websocket.send(json.dumps({
                        'type': 'stats',
                        'clients': len(connected_clients),
                        'timestamp': str(datetime.now())
                    }))
                    
            except json.JSONDecodeError:
                print(f"⚠️ Received non-JSON message: {message}")
                
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected normally")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"❌ Client disconnected. Total clients: {len(connected_clients)}")

async def broadcast(data):
    """Broadcast data to all connected clients"""
    if connected_clients:
        message = json.dumps(data)
        # Gunakan asyncio.gather untuk mengirim ke semua client
        await asyncio.gather(*[client.send(message) for client in connected_clients], return_exceptions=True)

async def main():
    # Start WebSocket server
    async with websockets.serve(handler, "localhost", 8765):
        print("="*50)
        print("🔌 WebSocket Server Running")
        print("📍 ws://localhost:8765")
        print("="*50)
        print("\nWaiting for connections...\n")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")