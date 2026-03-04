import logging
import pygame
import game_config as cfg

logger = logging.getLogger(__name__)

# colors - reference centralized config
wheat = cfg.COLOR_WHEAT

white = cfg.COLOR_WHITE
black = cfg.COLOR_BLACK
blue = cfg.COLOR_BLUE

red = cfg.COLOR_RED
light_red = cfg.COLOR_LIGHT_RED

yellow = cfg.COLOR_YELLOW
light_yellow = cfg.COLOR_LIGHT_YELLOW

green = cfg.COLOR_GREEN
light_green = cfg.COLOR_LIGHT_GREEN

color_lookup = cfg.COLOR_LOOKUP

s_font = pygame.font.SysFont(cfg.FONT_NAME, cfg.FONT_SIZE_SMALL)
m_font = pygame.font.SysFont(cfg.FONT_NAME, cfg.FONT_SIZE_MEDIUM)
l_font = pygame.font.SysFont(cfg.FONT_NAME, cfg.FONT_SIZE_LARGE)
vs_font = pygame.font.SysFont(cfg.FONT_NAME, cfg.FONT_SIZE_VSMALL)

# defining function to get the fonts and sizes assigned with them by size names by default size="small"
def txt_object(txt, color, size="small"):
    if size == "small":
        txtSrfc = s_font.render(txt, True, color)
    if size == "medium":
        txtSrfc = m_font.render(txt, True, color)
    if size == "large":
        txtSrfc = l_font.render(txt, True, color)
    if size == "vsmall":
        txtSrfc = vs_font.render(txt, True, color)

    return txtSrfc, txtSrfc.get_rect()

# function for texts that has to appear over screen
def msg_screen_topleft(surface, message, color, topleft, size="small"):
    txtSrf, textRect = txt_object(message, color, size)
    textRect.topleft = topleft
    surface.blit(txtSrf, textRect)

def print_lines_on_surface(surface, lines, color):

    topleft = cfg.LINES_PRINT_TOPLEFT

    def nextline(topleft):
        line_height = cfg.LINES_PRINT_LINE_HEIGHT
        return (cfg.LINES_PRINT_TOPLEFT[0], topleft[1] + line_height)

    for ll in lines:
        msg_screen_topleft(surface, ll, color, topleft)
        topleft = nextline(topleft)

def game_wait_for_players_screen(surface, clock, color_operator_dict):

    while True:
        surface.fill(cfg.COLOR_BLACK)
        start_pressed = False
        for event in pygame.event.get():
            # print(event)
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    quit()
                if event.key == pygame.K_s:
                    start_pressed = True

        line_height = cfg.LOBBY_LINE_HEIGHT
        topleft = cfg.LOBBY_TEXT_TOPLEFT
        msg_screen_topleft(surface, "Waiting for players:", white, topleft, size="medium")
        ready_players = {}
        for color_key, operator in color_operator_dict.items():
            color = color_lookup[color_key]
            topleft = (cfg.LOBBY_TEXT_TOPLEFT[0], topleft[1]+line_height)
            player_line = operator.get_operator_name()

            if player_line is None:
                player_line = "<Player not found>"
                try:
                    player_line = "<Waiting for player on:" + operator.get_connection_info_string() + ">"
                except AttributeError:
                    pass
            else:
                ready_players[color_key] = operator

            msg_screen_topleft(surface, player_line, color, topleft, size="small")

        topleft = (cfg.LOBBY_TEXT_TOPLEFT[0], topleft[1]+line_height)
        if len(ready_players) == len(color_operator_dict):
            msg_screen_topleft(surface, ">>> Ready! Press 's' to start! <<<", white, topleft, size="small")
        else:
            msg_screen_topleft(surface, "> Players NOT Ready! Press 's' to start anyway <", light_yellow, topleft, size="small")
        pygame.display.update()

        clock.tick(cfg.LOBBY_FPS) #fps

        if start_pressed:
            return ready_players
