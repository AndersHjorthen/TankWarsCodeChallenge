import pygame
import game_config as cfg

# Cached name font (initialized lazily)
_name_font = None


def _get_name_font():
    global _name_font
    if _name_font is None:
        _name_font = pygame.font.SysFont(cfg.FONT_NAME, cfg.HEALTH_BAR_NAME_FONT_SIZE)
    return _name_font


def _health_gradient_color(ratio):
    """Return a color that transitions green -> yellow -> red based on health ratio."""
    if ratio > 0.5:
        # Green to yellow (ratio 1.0 -> 0.5)
        t = (ratio - 0.5) * 2.0  # 1.0 at full, 0.0 at half
        r = int(255 * (1.0 - t))
        g = 255
    else:
        # Yellow to red (ratio 0.5 -> 0.0)
        t = ratio * 2.0  # 1.0 at half, 0.0 at empty
        r = 255
        g = int(255 * t)
    return (r, g, 0)


def draw_health_bar(surface, center, health_ratio, size=(40, 10), name=None):
    """
    Draw a health bar with gradient color, dark border, and optional player name.

    :param surface: The Pygame surface to draw on.
    :param center: A Vec or object with .x, .y for the center position.
    :param health_ratio: A float between 0 and 1 indicating health percentage.
    :param size: A tuple (width, height) for the size of the health bar.
    :param name: Optional player name to display below the bar.
    """
    width, height = size
    health_ratio = max(0.0, min(1.0, health_ratio))
    filled_width = int(width * health_ratio)

    bar_x = int(center.x) - width // 2
    bar_y = int(center.y) - height // 2

    # Dark background (empty portion)
    bg_rect = pygame.Rect(bar_x, bar_y, width, height)
    pygame.draw.rect(surface, (40, 10, 10), bg_rect)

    # Filled portion with gradient color
    if filled_width > 0:
        fill_color = _health_gradient_color(health_ratio)
        fill_rect = pygame.Rect(bar_x, bar_y, filled_width, height)
        pygame.draw.rect(surface, fill_color, fill_rect)

    # Dark border
    border_rect = pygame.Rect(bar_x - cfg.HEALTH_BAR_BORDER_WIDTH,
                              bar_y - cfg.HEALTH_BAR_BORDER_WIDTH,
                              width + 2 * cfg.HEALTH_BAR_BORDER_WIDTH,
                              height + 2 * cfg.HEALTH_BAR_BORDER_WIDTH)
    pygame.draw.rect(surface, cfg.HEALTH_BAR_BORDER_COLOR, border_rect,
                     cfg.HEALTH_BAR_BORDER_WIDTH)

    # Player name below bar
    if name:
        font = _get_name_font()
        name_surf = font.render(name, True, cfg.COLOR_WHITE)
        name_rect = name_surf.get_rect(
            midtop=(int(center.x), bar_y + height + cfg.HEALTH_BAR_NAME_OFFSET_Y))
        # Shadow
        shadow_surf = font.render(name, True, (0, 0, 0))
        shadow_rect = shadow_surf.get_rect(
            midtop=(name_rect.centerx + 1, name_rect.top + 1))
        surface.blit(shadow_surf, shadow_rect)
        surface.blit(name_surf, name_rect)
