import argparse
import pygame
# Initialize Pygame
pygame.init()

import client_settings
from operator_tcp_adapter import OperatorTCPadaptor_Client
from src.screens import print_lines_on_surface
import game_config as cfg




# Setting up the clock and FPS
clock = pygame.time.Clock()
client_fps = cfg.CLIENT_FPS

display_size = (cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT)

clientscreen = pygame.display.set_mode(display_size)
pygame.display.set_caption(cfg.WINDOW_CAPTION_CLIENT)
icon = pygame.image.load("res/tank_alpha.png")
pygame.display.set_icon(icon)

def run_client(port=None):
    if port == None:
        port = client_settings.serverPort
    print("Running Tank wars Operator client. Connecting to " + client_settings.serverIp + ":" + str(port))
    print("Using Tank operator: " + str(type(client_settings.tankoperator)) + " (Change this in client_settings.py if needed)")
    print("> use '-p <port>' as commandline argumet to override client_settings.py port number")
    print("Press Ctrl-C or close the window to quit client")

    try:
        op = OperatorTCPadaptor_Client(client_settings.serverIp, port, client_settings.tankoperator)
        while True:
            clientscreen.fill(cfg.COLOR_BLACK)
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    return

            more_data = True
            while more_data:
                more_data = op.run_client()

            txtlines = ["Tank Wars Game Client: Headless mode",
                        "Server=" + client_settings.serverIp + ":" + str(port) + " \tOperatorType="+ str(type(client_settings.tankoperator)),
                        "Client connected: " + str(op.tcp_client.connected),
                        "GameState msg received #: " + str(op._messages_received),
                        "Actions sent #: " + str(op._actions_sent),
                        "Press ESC to quit"
                        ]

            if op.game_over_message:
                txtlines.append(op.game_over_message)

            print_lines_on_surface(clientscreen, txtlines, cfg.COLOR_CLIENT_TEXT)
            pygame.display.update()
            clock.tick(client_fps)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        pygame.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Client program.')
    parser.add_argument('-p', type=int, help='Port number')

    args = parser.parse_args()

    run_client(port=args.p)

    print("Quitting Client")
