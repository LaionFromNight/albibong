import asyncio
import json
import queue
import threading

import websockets

from albibong.classes.logger import Logger

logger = Logger(__name__, stdout=True, log_to_file=False)


class WebsocketServer(threading.Thread):
    def __init__(self, name, in_queue) -> None:
        super().__init__()
        self.name = name
        self.in_queue = in_queue
        self.stop_event = threading.Event()
        self.connections = set()

    async def handler(self, websocket):
        from albibong.classes.world_data import get_world_data

        self.connections.add(websocket)
        try:
            world_data = get_world_data()
            me = world_data.me
            event_init_world = {
                "type": "init_world",
                "payload": {
                    "me": {
                        "username": me.username,
                        "guild": me.guild,
                        "alliance": me.alliance,
                    },
                    "world": {
                        "map": (
                            world_data.current_map.name
                            if world_data.current_map
                            else "zone in to other map to initialize"
                        ),
                        "isInDungeon": world_data.is_in_dungeon,
                    },
                },
            }
            await websocket.send(json.dumps(event_init_world))
            async for _message in websocket:
                # Radar UI is read-only for now, so backend no longer handles control events.
                continue
        finally:
            self.connections.remove(websocket)

    async def main(self):
        async with websockets.serve(self.handler, "", 8081):
            while True:
                if self.stop_event.is_set():
                    return

                while not self.in_queue.empty():
                    if self.stop_event.is_set():
                        return

                    event = self.in_queue.get()
                    if len(self.connections) > 0:
                        # logger.info(f"broadcast {event}")
                        websockets.broadcast(self.connections, json.dumps(event))
                        await asyncio.sleep(0)

                await asyncio.sleep(0)

    def run(self):
        logger.info(f"Thread {self.name} started")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.main())

    def stop(self):
        logger.info(f"Thread {self.name} stopped")
        self.stop_event.set()


event_queue = queue.Queue()
ws_server = WebsocketServer(name="ws_server", in_queue=event_queue)


def send_event(event):
    event_queue.put(event)


def get_ws_server():
    return ws_server
