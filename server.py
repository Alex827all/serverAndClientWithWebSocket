import asyncio
import json
import websockets
import random  # <--- добавлено

players = {}
next_id = 1
connected = set()


async def handler(websocket):
  global next_id
  connected.add(websocket)

  player_id = next_id
  next_id += 1

  players[player_id] = {
      "x": random.randint(0, 9),  # случайная X
      "y": random.randint(0, 9),  # случайная Y
      "color": f"hsl({(player_id * 70) % 360}, 70%, 50%)"
  }

  await websocket.send(json.dumps({"type": "init", "player_id": player_id}))
  print(f"Sent init to player {player_id}")

  try:
    async for message in websocket:
      data = json.loads(message)

      if data.get("type") == "move":
        dx = int(data.get("dx", 0))
        dy = int(data.get("dy", 0))
        p = players[player_id]
        p["x"] = max(0, min(9, p["x"] + dx))
        p["y"] = max(0, min(9, p["y"] + dy))

      elif data.get("type") == "teleport":
        new_x = int(data.get("x", 0))
        new_y = int(data.get("y", 0))
        p = players[player_id]
        p["x"] = max(0, min(9, new_x))
        p["y"] = max(0, min(9, new_y))

      state = {
          "type": "state",
          "players": {
              str(k): v
              for k, v in players.items()
          }
      }
      await asyncio.gather(*[ws.send(json.dumps(state)) for ws in connected])

  except websockets.exceptions.ConnectionClosed:
    pass
  finally:
    connected.remove(websocket)
    if player_id in players:
      del players[player_id]
    state = {
        "type": "state",
        "players": {
            str(k): v
            for k, v in players.items()
        }
    }
    await asyncio.gather(*[ws.send(json.dumps(state)) for ws in connected])


async def main():
  async with websockets.serve(handler, "localhost", 8765):
    print("Server started on ws://localhost:8765")
    await asyncio.Future()


if __name__ == "__main__":
  asyncio.run(main())
