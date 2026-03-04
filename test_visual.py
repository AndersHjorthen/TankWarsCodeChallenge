"""Quick visual test: launches the game with 4 AI operators (no TCP needed).
Auto-starts after a brief lobby display. Press 'q' to quit at any time.
"""
import pygame
pygame.init()

import time
import game_config as cfg
import server_settings
from example_operators import ChaserOperator, DodgerOperator, SniperOperator

# Monkey-patch to use only local AI operators
server_settings.get_tank_operators_and_starting_positions = lambda: {
    "red": ChaserOperator(),
    "blue": DodgerOperator(),
    "yellow": SniperOperator(),
    "green": ChaserOperator(),
}

# Shorten game for testing
cfg.GAME_TIMEOUT_SECS = 12

# Monkey-patch the lobby screen to auto-start
import src.screens as screens

def _auto_start(surface, clock, color_operator_dict):
    print("[test] Lobby: auto-starting with all AI operators")
    start = time.time()
    while time.time() - start < 1.0:
        surface.fill(cfg.ARENA_BG_COLOR)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); quit()
        screens._msg_center(surface, "Visual Test - Starting...", (255, 255, 255), 0, size="medium", shadow=True)
        pygame.display.update()
        clock.tick(5)
    return {k: v for k, v in color_operator_dict.items() if v.get_operator_name() is not None}

screens.game_wait_for_players_screen = _auto_start

print("[test] Loading game server...")
import tankwars_game_server
print("[test] Game finished successfully!")
