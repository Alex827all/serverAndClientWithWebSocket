import pygame
import asyncio
import json
import websockets
import colorsys

# Параметры
CELL_SIZE = 40
GRID_SIZE = 10
WINDOW_SIZE = CELL_SIZE * GRID_SIZE
FRAME_RATE = 60  # FPS

players = {}
my_player_id = None

pygame.init()
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Multiplayer Squares")

WS_URL = "wss://..."  # или wss://...

async def main():
    global my_player_id
    clock = pygame.time.Clock()
    running = True

    async with websockets.connect(WS_URL) as ws:
        # Вспомогательная отправка
        async def teleport(x_cell: int, y_cell: int):
            await ws.send(json.dumps({
                "type": "teleport",
                "x": x_cell,
                "y": y_cell
            }))

        while running:
            # Приём сообщений
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=0.01)
                    data = json.loads(msg)
                    if data.get("type") == "init":
                        my_player_id = data["player_id"]
                    elif data.get("type") == "state":
                        players.clear()
                        for pid_str, p in data["players"].items():
                            players[int(pid_str)] = p
            except asyncio.TimeoutError:
                pass

            # Обработка ввода
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.MOUSEBUTTONDOWN and my_player_id is not None:
                    mx, my = ev.pos
                    gx = mx // CELL_SIZE
                    gy = my // CELL_SIZE
                    gx = max(0, min(GRID_SIZE - 1, gx))
                    gy = max(0, min(GRID_SIZE - 1, gy))
                    asyncio.create_task(teleport(gx, gy))

            # Отрисовка
            screen.fill((230, 230, 230))
            # Сетка
            for i in range(GRID_SIZE + 1):
                pygame.draw.line(screen, (200, 200, 200),
                                 (i * CELL_SIZE, 0), (i * CELL_SIZE, WINDOW_SIZE))
                pygame.draw.line(screen, (200, 200, 200),
                                 (0, i * CELL_SIZE), (WINDOW_SIZE, i * CELL_SIZE))

            # Рисуем игроков
            for pid, p in players.items():
                x_px = p["x"] * CELL_SIZE
                y_px = p["y"] * CELL_SIZE
                hue = int(p["color"].split("(")[1].split(",")[0]) / 360
                rgb = colorsys.hls_to_rgb(hue, 0.7, 0.5)
                color = tuple(int(c * 255) for c in rgb)
                rect = pygame.Rect(x_px, y_px, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, color, rect)
                if pid == my_player_id:
                    pygame.draw.rect(screen, (0, 0, 0), rect, 3)

            pygame.display.flip()
            clock.tick(FRAME_RATE)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())

