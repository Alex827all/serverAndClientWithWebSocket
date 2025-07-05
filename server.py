import asyncio
import json
import websockets
import os
import random

# Параметры
GRID_SIZE = 10
UPDATE_INTERVAL = 0.05  # секунды между рассылками state
MOVE_INTERVAL = 0.05  # секунды между шагами движения
MOVE_SPEED = 0.1  # шаг (в клетках) за тик MOVE_INTERVAL

players = {}
next_id = 1
websockets_list = set()


async def handler(websocket):
  global next_id
  player_id = next_id
  next_id += 1

  websockets_list.add(websocket)

  # Рандомная стартовая позиция
  start_x = float(random.randint(0, GRID_SIZE - 1))
  start_y = float(random.randint(0, GRID_SIZE - 1))

  players[player_id] = {
      "x": start_x,
      "y": start_y,
      "target_x": start_x,
      "target_y": start_y,
      "color": f"hsl({(player_id * 70) % 360}, 70%, 50%)"
  }

  await websocket.send(json.dumps({"type": "init", "player_id": player_id}))

  try:
    async for message in websocket:
      data = json.loads(message)
      if data.get("type") == "teleport":
        tx = float(max(0, min(GRID_SIZE - 1, data["x"])))
        ty = float(max(0, min(GRID_SIZE - 1, data["y"])))
        players[player_id]["target_x"] = tx
        players[player_id]["target_y"] = ty
  except websockets.exceptions.ConnectionClosed:
    pass
  finally:
    websockets_list.remove(websocket)
    players.pop(player_id, None)


async def update_positions():
  while True:
    for p in players.values():
      # Двигаемся по X
      dx = p["target_x"] - p["x"]
      if abs(dx) < MOVE_SPEED:
        p["x"] = p["target_x"]
      else:
        p["x"] += MOVE_SPEED if dx > 0 else -MOVE_SPEED
      # Двигаемся по Y
      dy = p["target_y"] - p["y"]
      if abs(dy) < MOVE_SPEED:
        p["y"] = p["target_y"]
      else:
        p["y"] += MOVE_SPEED if dy > 0 else -MOVE_SPEED
    await asyncio.sleep(MOVE_INTERVAL)


async def broadcast():
  while True:
    if websockets_list:
      state = {
          "type": "state",
          "players": {
              str(k): v
              for k, v in players.items()
          }
      }
      msg = json.dumps(state)
      await asyncio.gather(*(ws.send(msg) for ws in websockets_list))
    await asyncio.sleep(UPDATE_INTERVAL)


async def main():
  port = int(os.environ.get("PORT", "8765"))
  await websockets.serve(handler, "0.0.0.0", port)
  print(f"Server started on port {port}")
  await asyncio.gather(update_positions(), broadcast())


if __name__ == "__main__":
  asyncio.run(main())
