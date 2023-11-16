import asyncio
import logging
import websockets
import pyperclip
from typing import Any, Dict

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class WSClipboardClient:
    def __init__(self, uri: str):
        self.uri = uri
        self.last_clipboard_content = ""

    async def clipboard_monitor(self, websocket: websockets.WebSocketClientProtocol):
        while True:
            try:
                current_clipboard_content = pyperclip.paste()
            except pyperclip.PyperclipException as e:
                logging.error(f"Error getting clipboard content: {e}")
                await asyncio.sleep(1)
                continue

            if current_clipboard_content != self.last_clipboard_content:
                self.last_clipboard_content = current_clipboard_content
                logging.info("New content copied on client, sending to server.")
                await websocket.send(current_clipboard_content)
            await asyncio.sleep(1)

    async def listen_server(self, websocket: websockets.WebSocketClientProtocol):
        async for message in websocket:
            logging.info("Received new content from server, updating client clipboard.")
            pyperclip.copy(message)
            self.last_clipboard_content = message

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    await asyncio.gather(
                        self.clipboard_monitor(websocket),
                        self.listen_server(websocket)
                    )
            except websockets.ConnectionClosed:
                logging.info("Connection to server lost, retrying...")
                await asyncio.sleep(5)

if __name__ == "__main__":
    client = WSClipboardClient("ws://10.0.0.147:8081")
    asyncio.run(client.connect())
