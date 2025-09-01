"""
Python WebSocket Speech Recognition Client Example

This example demonstrates how to connect to the FastAPI speech recognition 
WebSocket endpoint and stream audio for real-time transcription.

Requirements:
    pip install websockets pyaudio

Usage:
    python speech_client_example.py
"""

import asyncio
import json
import base64
import pyaudio
import websockets
import threading
import queue
from typing import Optional

class SpeechWebSocketClient:
    def __init__(self, websocket_url: str = "ws://localhost:8000/speech/stream"):
        self.websocket_url = websocket_url
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.audio_thread = None
        
        # Audio configuration
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.audio_interface = pyaudio.PyAudio()

    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            print(f"✅ Connected to {self.websocket_url}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False

    async def configure_language(self, language: str = "en-US"):
        """Configure the speech recognition language"""
        if not self.websocket:
            print("❌ Not connected to WebSocket")
            return False
            
        config_message = {
            "type": "config",
            "language": language
        }
        
        try:
            await self.websocket.send(json.dumps(config_message))
            print(f"🔧 Sent language configuration: {language}")
            return True
        except Exception as e:
            print(f"❌ Failed to send config: {e}")
            return False

    async def start_recognition(self):
        """Start speech recognition"""
        if not self.websocket:
            print("❌ Not connected to WebSocket")
            return False
            
        start_message = {"type": "start"}
        
        try:
            await self.websocket.send(json.dumps(start_message))
            print("🎤 Started speech recognition")
            return True
        except Exception as e:
            print(f"❌ Failed to start recognition: {e}")
            return False

    async def stop_recognition(self):
        """Stop speech recognition"""
        if not self.websocket:
            print("❌ Not connected to WebSocket")
            return False
            
        stop_message = {"type": "stop"}
        
        try:
            await self.websocket.send(json.dumps(stop_message))
            print("🛑 Stopped speech recognition")
            return True
        except Exception as e:
            print(f"❌ Failed to stop recognition: {e}")
            return False

    def start_audio_capture(self):
        """Start capturing audio from microphone"""
        def audio_capture_thread():
            stream = self.audio_interface.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            print("🎙️ Started audio capture")
            
            while self.is_recording:
                try:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    self.audio_queue.put(data)
                except Exception as e:
                    print(f"❌ Audio capture error: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            print("🛑 Audio capture stopped")
        
        self.is_recording = True
        self.audio_thread = threading.Thread(target=audio_capture_thread)
        self.audio_thread.start()

    def stop_audio_capture(self):
        """Stop capturing audio from microphone"""
        self.is_recording = False
        if self.audio_thread:
            self.audio_thread.join()

    async def send_audio_data(self):
        """Send captured audio data to WebSocket"""
        while self.is_recording and self.websocket:
            try:
                if not self.audio_queue.empty():
                    audio_data = self.audio_queue.get_nowait()
                    
                    # Encode audio data to base64
                    base64_data = base64.b64encode(audio_data).decode('utf-8')
                    
                    audio_message = {
                        "type": "audio",
                        "data": base64_data
                    }
                    
                    await self.websocket.send(json.dumps(audio_message))
                    
                await asyncio.sleep(0.01)  # Small delay
            except queue.Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"❌ Error sending audio data: {e}")
                break

    async def listen_for_results(self):
        """Listen for recognition results from WebSocket"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("📡 WebSocket connection closed")
        except Exception as e:
            print(f"❌ Error receiving messages: {e}")

    async def handle_message(self, data):
        """Handle incoming WebSocket messages"""
        msg_type = data.get("type", "")
        
        if msg_type == "config_success":
            print(f"✅ {data.get('message', 'Configuration successful')}")
        elif msg_type == "start_success":
            print(f"✅ {data.get('message', 'Recognition started')}")
        elif msg_type == "stop_success":
            print(f"✅ {data.get('message', 'Recognition stopped')}")
        elif msg_type == "error":
            print(f"❌ Error: {data.get('message', 'Unknown error')}")
        elif "finish" in data:
            # Handle recognition results
            finish = data.get("finish", False)
            text = data.get("text", "")
            confidence = data.get("confidence")
            
            if finish:
                conf_str = f" (confidence: {confidence:.2f})" if confidence else ""
                print(f"✅ Final: {text}{conf_str}")
            else:
                print(f"🔄 Interim: {text}")
        else:
            print(f"📨 Received: {data}")

    async def close(self):
        """Close the WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            print("📡 WebSocket connection closed")

    def cleanup(self):
        """Cleanup audio resources"""
        self.stop_audio_capture()
        if self.audio_interface:
            self.audio_interface.terminate()

async def main():
    """Main demo function"""
    print("🎙️ Speech Recognition WebSocket Client Demo")
    print("=" * 50)
    
    client = SpeechWebSocketClient()
    
    try:
        # Connect to WebSocket
        if not await client.connect():
            return
        
        # Configure language
        if not await client.configure_language("en-US"):
            return
        
        # Start listening for results
        results_task = asyncio.create_task(client.listen_for_results())
        
        # Wait a moment for configuration
        await asyncio.sleep(1)
        
        # Start recognition
        if not await client.start_recognition():
            return
        
        # Start audio capture and sending
        client.start_audio_capture()
        audio_task = asyncio.create_task(client.send_audio_data())
        
        print("\n🎤 Speak now! Press Ctrl+C to stop...")
        print("=" * 50)
        
        # Let it run for a while or until interrupted
        try:
            await asyncio.gather(results_task, audio_task)
        except KeyboardInterrupt:
            print("\n⏹️  Stopping...")
        
        # Stop recognition
        await client.stop_recognition()
        
        # Wait a moment for final results
        await asyncio.sleep(1)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        # Cleanup
        client.cleanup()
        await client.close()
        print("🏁 Demo completed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
