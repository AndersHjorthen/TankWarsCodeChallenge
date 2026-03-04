import pygame
import game_config as cfg

def draw_health_bar(surface, center, health_ratio, size=(40, 10)):
    """
    Draw a health bar in Pygame.

    :param surface: The Pygame surface to draw on.
    :param center: A tuple (x, y) for the center position of the health bar.
    :param health_ratio: A float between 0 and 1 indicating health percentage.
    :param size: A tuple (width, height) for the size of the health bar.
    """

    # Calculate the dimensions of the health bar
    width, height = size
    green_width = int(width * health_ratio)
    red_width = width - green_width

    # Create rectangles for the green and red parts
    green_rect = pygame.Rect(center.x - width // 2, center.y - height // 2, green_width, height)
    red_rect = pygame.Rect(center.x - width // 2 + green_width, center.y - height // 2, red_width, height)

    # Draw the green and red parts of the health bar
    pygame.draw.rect(surface, cfg.COLOR_HEALTH_GREEN, green_rect)  # Green part
    pygame.draw.rect(surface, cfg.COLOR_HEALTH_RED, red_rect)    # Red part
