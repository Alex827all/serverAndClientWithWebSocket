import asyncio
import json
import websockets
import os

players = {}
next_id = 1

async def handler(websocket, path):
    global next_id
    player_id = next_id
    next_id += 1

    players[player_id] = {
        "x": 0,
        "y": 0,
        "color": f"hsl({(player_id*70)%360}, 70%, 50%)"
    }

    try:
        while True:
            data = await websocket.recv()
            message = json.loads(data)

            if message["type"] == "move":
                dx, dy = message["dx"], message["dy"]
                p = players[player_id]
                p["x"] = max(0, min(9, p["x"] + dx))
                p["y"] = max(0, min(9, p["y"] + dy))

            state = {"type": "state", "players": players}
            websockets_to_send = set(websocket.server.websockets)
            await asyncio.gather(*[
                ws.send(json.dumps(state))
                for ws in websockets_to_send
            ])
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        del players[player_id]
        state = {"type": "state", "players": players}
        websockets_to_send = set(websocket.server.websockets)
        await asyncio.gather(*[
            ws.send(json.dumps(state))
            for ws in websockets_to_send
        ])

async def main():
    port = int(os.environ.get("PORT", "8080"))
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"Server started on port {port}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
