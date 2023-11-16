import asyncio
import logging
import websockets
import pyperclip
from typing import Any, Dict

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class WSClipboardServer:
    def __init__(self, port: int):
        self.port = port
        self.clients = set()
        self.last_clipboard_content = ""

    async def register(self, websocket: websockets.WebSocketServerProtocol):
        self.clients.add(websocket)
        logging.info(f"Client connected: {len(self.clients)} total clients")

    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        self.clients.remove(websocket)
        logging.info(f"Client disconnected: {len(self.clients)} total clients")

    async def notify_clients(self, message: str):
        if self.clients:
            tasks = [asyncio.create_task(self.send_to_client(client, message)) for client in self.clients]
            await asyncio.gather(*tasks)

    async def send_to_client(self, client, message):
        try:
            await client.send(message)
        except websockets.exceptions.WebSocketException as e:
            logging.error(f"Error sending message to a client: {e}")

    async def clipboard_monitor(self):
        while True:
            try:
                current_clipboard_content = pyperclip.paste()
            except pyperclip.PyperclipException as e:
                logging.error(f"Error getting clipboard content: {e}")
                await asyncio.sleep(1)
                continue

            if current_clipboard_content != self.last_clipboard_content:
                self.last_clipboard_content = current_clipboard_content
                logging.info("New content copied on server, sending to clients.")
                await self.notify_clients(current_clipboard_content)

            await asyncio.sleep(1)

    async def handler(self, websocket: websockets.WebSocketServerProtocol, path: str):
        await self.register(websocket)
        try:
            async for message in websocket:
                logging.info("Received new content from client, updating server clipboard.")
                pyperclip.copy(message)
                self.last_clipboard_content = message
        finally:
            await self.unregister(websocket)

    async def run_server(self):
        async with websockets.serve(self.handler, "0.0.0.0", self.port):
            await asyncio.gather(
                self.clipboard_monitor(),
                asyncio.Future()  # Run forever
            )

if __name__ == "__main__":
    server = WSClipboardServer(8081)
    asyncio.run(server.run_server())
