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


def _get_font(size="small"):
    if size == "large":
        return l_font
    if size == "medium":
        return m_font
    if size == "vsmall":
        return vs_font
    return s_font


def txt_object(txt, color, size="small"):
    font = _get_font(size)
    txtSrfc = font.render(txt, True, color)
    return txtSrfc, txtSrfc.get_rect()


def msg_screen_topleft(surface, message, color, topleft, size="small"):
    txtSrf, textRect = txt_object(message, color, size)
    textRect.topleft = topleft
    surface.blit(txtSrf, textRect)


def _msg_center(surface, message, color, y_displace=0, size="small", shadow=False):
    """Render centered text with optional shadow."""
    font = _get_font(size)
    cx = cfg.DISPLAY_WIDTH // 2
    cy = cfg.DISPLAY_HEIGHT // 2 + y_displace

    if shadow:
        off = cfg.SCREEN_TEXT_SHADOW_OFFSET
        shadow_surf = font.render(message, True, cfg.SCREEN_TEXT_SHADOW_COLOR)
        shadow_rect = shadow_surf.get_rect(center=(cx + off, cy + off))
        surface.blit(shadow_surf, shadow_rect)

    text_surf = font.render(message, True, color)
    text_rect = text_surf.get_rect(center=(cx, cy))
    surface.blit(text_surf, text_rect)


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
        surface.fill(cfg.ARENA_BG_COLOR)
        start_pressed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    quit()
                if event.key == pygame.K_s:
                    start_pressed = True

        # Draw panel background
        panel_x = cfg.LOBBY_TEXT_TOPLEFT[0] - cfg.LOBBY_PANEL_PADDING
        panel_y = cfg.LOBBY_TEXT_TOPLEFT[1] - cfg.LOBBY_PANEL_PADDING
        panel_w = cfg.DISPLAY_WIDTH - 2 * panel_x
        num_entries = len(color_operator_dict) + 2  # title + entries + start line
        panel_h = cfg.LOBBY_PANEL_PADDING * 2 + num_entries * cfg.LOBBY_LINE_HEIGHT
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((*cfg.LOBBY_PANEL_BG_COLOR, cfg.LOBBY_PANEL_BG_ALPHA))
        surface.blit(panel, (panel_x, panel_y))

        line_height = cfg.LOBBY_LINE_HEIGHT
        topleft = cfg.LOBBY_TEXT_TOPLEFT
        _msg_center(surface, "Waiting for players:", white,
                     topleft[1] - cfg.DISPLAY_HEIGHT // 2, size="medium", shadow=True)

        ready_players = {}
        y_pos = topleft[1] + line_height
        for color_key, operator in color_operator_dict.items():
            color = color_lookup[color_key]

            # Color indicator square
            indicator_size = cfg.LOBBY_COLOR_INDICATOR_SIZE
            ind_rect = pygame.Rect(topleft[0], y_pos + 6, indicator_size, indicator_size)
            pygame.draw.rect(surface, color, ind_rect)
            pygame.draw.rect(surface, white, ind_rect, 1)

            player_line = operator.get_operator_name()
            if player_line is None:
                player_line = "<Player not found>"
                try:
                    player_line = "<Waiting for player on:" + operator.get_connection_info_string() + ">"
                except AttributeError:
                    pass
            else:
                ready_players[color_key] = operator

            msg_screen_topleft(surface, player_line, color,
                               (topleft[0] + indicator_size + 10, y_pos), size="small")
            y_pos += line_height

        y_pos += 10
        if len(ready_players) == len(color_operator_dict):
            _msg_center(surface, ">>> Ready! Press 's' to start! <<<", white,
                         y_pos - cfg.DISPLAY_HEIGHT // 2, size="small", shadow=True)
        else:
            _msg_center(surface, "> Players NOT Ready! Press 's' to start anyway <",
                         light_yellow, y_pos - cfg.DISPLAY_HEIGHT // 2, size="small", shadow=True)

        pygame.display.update()
        clock.tick(cfg.LOBBY_FPS)

        if start_pressed:
            return ready_players
