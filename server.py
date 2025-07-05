import asyncio
import json
import websockets
import os
import random

players = {}
next_id = 1
websockets_list = set()


async def handler(websocket):
  global next_id
  player_id = next_id
  next_id += 1

  websockets_list.add(websocket)

  # Стартовая позиция с float координатами
  start_x = float(random.randint(0, 9))
  start_y = float(random.randint(0, 9))

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
        tx = float(max(0, min(9, data["x"])))
        ty = float(max(0, min(9, data["y"])))
        players[player_id]["target_x"] = tx
        players[player_id]["target_y"] = ty
  except websockets.exceptions.ConnectionClosed:
    pass
  finally:
    websockets_list.remove(websocket)
    if player_id in players:
      del players[player_id]


async def update_positions():
  speed = 0.1  # клеток за тик
  while True:
    for p in players.values():
      # Двигаемся по оси X
      dx = p["target_x"] - p["x"]
      if abs(dx) < speed:
        p["x"] = p["target_x"]
      else:
        p["x"] += speed if dx > 0 else -speed

      # Двигаемся по оси Y
      dy = p["target_y"] - p["y"]
      if abs(dy) < speed:
        p["y"] = p["target_y"]
      else:
        p["y"] += speed if dy > 0 else -speed

    await asyncio.sleep(0.05)  # обновляем 20 раз в секунду


async def broadcast():
  while True:
    if websockets_list:
      # Передаём координаты с float, клиент должен рисовать по ним
      state = {
          "type": "state",
          "players": {
              str(k): v
              for k, v in players.items()
          }
      }
      msg = json.dumps(state)
      await asyncio.gather(*[ws.send(msg) for ws in websockets_list])
    await asyncio.sleep(0.05)


async def main():
  port = int(os.environ.get("PORT", "8765"))
  server = await websockets.serve(handler, "0.0.0.0", port)
  print(f"Server started on port {port}")

  await asyncio.gather(update_positions(), broadcast())


if __name__ == "__main__":
  asyncio.run(main())
