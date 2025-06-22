#!/usr/bin/env python3
"""
WebSocket Client Test Script
Interactive testing of all WebSocket endpoints
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime
from typing import Optional

class WebSocketTester:
    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        
    async def connect(self, endpoint: str):
        """Connect to WebSocket endpoint"""
        uri = f"{self.base_url}{endpoint}"
        print(f"🔌 Connecting to: {uri}")
        
        try:
            self.websocket = await websockets.connect(uri)
            print(f"✅ Connected to {endpoint}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected")
    
    async def send_message(self, message: dict):
        """Send message to WebSocket"""
        if not self.websocket:
            print("❌ Not connected")
            return
            
        try:
            await self.websocket.send(json.dumps(message))
            print(f"📤 Sent: {json.dumps(message, indent=2)}")
        except Exception as e:
            print(f"❌ Send error: {e}")
    
    async def receive_messages(self):
        """Receive messages from WebSocket"""
        if not self.websocket:
            print("❌ Not connected")
            return
            
        print("📥 Listening for messages (Ctrl+C to stop)...")
        try:
            while self.running:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=1.0
                    )
                    data = json.loads(message)
                    print(f"\n📨 Received: {json.dumps(data, indent=2)}")
                except asyncio.TimeoutError:
                    continue
                except websockets.ConnectionClosed:
                    print("❌ Connection closed by server")
                    break
        except KeyboardInterrupt:
            print("\n⏹️ Stopped listening")
    
    async def test_main_websocket(self):
        """Test main WebSocket endpoint"""
        print("\n🧪 Testing Main WebSocket (/ws)")
        print("-" * 40)
        
        if await self.connect("/ws"):
            # Test ping
            await self.send_message({
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            })
            
            # Test subscription
            await self.send_message({
                "type": "subscribe",
                "channels": ["trades", "orders", "positions"],
                "timestamp": datetime.now().isoformat()
            })
            
            # Listen for messages
            self.running = True
            await self.receive_messages()
            await self.disconnect()
    
    async def test_options_websocket(self):
        """Test options data WebSocket"""
        print("\n🧪 Testing Options WebSocket (/api/v1/truedata/options/stream)")
        print("-" * 40)
        
        if await self.connect("/api/v1/truedata/options/stream"):
            # Listen for messages
            self.running = True
            
            # Start receiving in background
            receive_task = asyncio.create_task(self.receive_messages())
            
            # Wait a bit for initial messages
            await asyncio.sleep(5)
            
            # Send subscription request
            await self.send_message({
                "type": "subscribe",
                "symbols": ["NIFTY", "BANKNIFTY"],
                "timestamp": datetime.now().isoformat()
            })
            
            # Wait for more messages
            await asyncio.sleep(10)
            
            self.running = False
            await receive_task
            await self.disconnect()
    
    async def interactive_test(self):
        """Interactive WebSocket testing"""
        print("\n🎮 Interactive WebSocket Test Mode")
        print("=" * 50)
        
        endpoints = {
            "1": ("/ws", "Main WebSocket"),
            "2": ("/api/v1/truedata/options/stream", "Options Data Stream"),
        }
        
        print("\nAvailable endpoints:")
        for key, (endpoint, desc) in endpoints.items():
            print(f"  {key}. {desc} ({endpoint})")
        
        choice = input("\nSelect endpoint (1-2): ")
        
        if choice not in endpoints:
            print("❌ Invalid choice")
            return
            
        endpoint, desc = endpoints[choice]
        
        if await self.connect(endpoint):
            print("\n📝 Commands:")
            print("  - Type JSON message to send")
            print("  - Type 'listen' to receive messages")
            print("  - Type 'quit' to disconnect")
            
            while True:
                command = input("\n> ").strip()
                
                if command.lower() == 'quit':
                    break
                elif command.lower() == 'listen':
                    self.running = True
                    await self.receive_messages()
                else:
                    try:
                        # Try to parse as JSON
                        message = json.loads(command)
                        await self.send_message(message)
                    except json.JSONDecodeError:
                        # Send as simple message
                        await self.send_message({
                            "type": "message",
                            "data": command,
                            "timestamp": datetime.now().isoformat()
                        })
            
            await self.disconnect()

async def main():
    """Main test runner"""
    tester = WebSocketTester()
    
    print("🔍 WebSocket Test Client")
    print("=" * 50)
    print("\nTest modes:")
    print("  1. Automated tests")
    print("  2. Interactive mode")
    
    mode = input("\nSelect mode (1-2): ")
    
    if mode == "1":
        # Run automated tests
        await tester.test_main_websocket()
        await tester.test_options_websocket()
    elif mode == "2":
        # Run interactive mode
        await tester.interactive_test()
    else:
        print("❌ Invalid mode")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!") 