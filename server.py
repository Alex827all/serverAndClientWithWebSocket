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

    # Стартовая позиция и цвет
    players[player_id] = {
        "x": 0,
        "y": 0,
        "color": f"hsl({(player_id * 70) % 360}, 70%, 50%)"
    }

    # Отправляем клиенту его ID
    await websocket.send(json.dumps({"type": "init", "player_id": player_id}))

    try:
        while True:
            data = await websocket.recv()
            try:
                message = json.loads(data)
                if message.get("type") == "move":
                    dx = int(message.get("dx", 0))
                    dy = int(message.get("dy", 0))
                    p = players[player_id]
                    p["x"] = max(0, min(9, p["x"] + dx))
                    p["y"] = max(0, min(9, p["y"] + dy))
            except Exception as e:
                print(f"Error processing message from player {player_id}: {e}")

            # Обновляем всех клиентов
            state = {
                "type": "state",
                # Ключи в JSON должны быть строками, приводим
                "players": {str(k): v for k, v in players.items()}
            }
            websockets_to_send = set(websocket.server.websockets)
            await asyncio.gather(*[
                ws.send(json.dumps(state))
                for ws in websockets_to_send
            ])
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if player_id in players:
            del players[player_id]
        # Сообщаем об обновлённом состоянии после отключения
        state = {
            "type": "state",
            "players": {str(k): v for k, v in players.items()}
        }
        websockets_to_send = set(websocket.server.websockets)
        await asyncio.gather(*[
            ws.send(json.dumps(state))
            for ws in websockets_to_send
        ])

async def main():
    port = int(os.environ.get("PORT", "8765"))  # Используй переменную окружения или 8765
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"Server started on port {port}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
