# -*- coding: utf-8 -*-

import pygame
pygame.init()

import logging
import random
import time
import math

logger = logging.getLogger(__name__)
from src.vec import Vec
from tank_operator import OperatorActions
from tank_operator import GameState
from tank_operator import TankObject
from tank_operator import ShotObject
from src.countdown_timer import CountDownTimer
from src.screens import game_wait_for_players_screen
from src.screens import msg_screen_topleft
from src.health_bar import draw_health_bar
import server_settings
import game_config as cfg

fullscreen = 0 #
if server_settings.server_fullscreen:
    fullscreen = pygame.FULLSCREEN

display_size = Vec(cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT)

game_time_out_secs = cfg.GAME_TIMEOUT_SECS

intro_display_seconds = cfg.INTRO_DISPLAY_SECS
game_fps = cfg.GAME_FPS
tank_image_size = cfg.TANK_IMAGE_SIZE

tank_start_health = cfg.TANK_START_HEALTH
max_shot_damage = cfg.MAX_SHOT_DAMAGE

##Movement:
tank_turn_speed = cfg.TANK_TURN_SPEED
tank_turret_turn_speed = cfg.TANK_TURRET_TURN_SPEED
tank_maxspeed = cfg.TANK_MAX_SPEED

shot_speed = cfg.SHOT_SPEED
tank_shots_cooldown = cfg.SHOT_COOLDOWN_SECS

# Some resources
game_layout_display = pygame.display.set_mode(display_size.as_tuple(), flags=fullscreen)
pygame.display.set_caption(cfg.WINDOW_CAPTION_SERVER)

icon = pygame.image.load("res/tank_alpha.png")
pygame.display.set_icon(icon)

shot_image = pygame.transform.scale(pygame.image.load('res/shot.png'), cfg.SHOT_IMAGE_SIZE)
turret_image = pygame.transform.scale(pygame.image.load('res/turret.png'), cfg.TURRET_IMAGE_SIZE)

# for picking current time for the frames per second
clock = pygame.time.Clock()


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
def msg_screen(message, color, y_displace=0, size="small"):
    txtSrf, textRect = txt_object(message, color, size)
    textRect.center = (int(display_size.x / 2), int(display_size.y / 2) + y_displace)
    game_layout_display.blit(txtSrf, textRect)

def game_intro():
    intro_time = time.time()

    while True:
        for event in pygame.event.get():
            # print(event)
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    quit()

        msg_screen("Trophy Wall Tank Wars!", cfg.COLOR_WHITE, -100, size="medium")
        msg_screen("Battle commencing...", cfg.COLOR_WHEAT, 15)

        pygame.display.update()

        clock.tick(cfg.INTRO_FPS)
        if time.time() - intro_time > intro_display_seconds:
            print("5 seconds have passed.")
            break

# function for game Over screen
def game_over(winner):
    print("Winner(s): " + winner)

    while True:
        for event in pygame.event.get():
            # print(event)
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                pygame.quit()
                quit()

        game_layout_display.fill(cfg.COLOR_BLACK)
        msg_screen("Game Over - Winner(s):", cfg.COLOR_WHITE, -100, size="medium")
        msg_screen(winner, cfg.COLOR_WHITE, 0, size="medium")
        msg_screen("Press any key to quit", cfg.COLOR_WHEAT, 100, size="small")

        pygame.display.update()

        clock.tick(cfg.INTRO_FPS)

class GameEntity:
    def get_orientation_angle(self):
        return self.direction.get_orientation_angle()

    def get_gamestate_object(self):
        raise NotImplementedError()

    def turn_vector(vector, turn_action_scalar, max_turn_speed):
        # Calculate the current orientation angle
        current_angle = math.atan2(vector.y, vector.x)

        # Cap turning:
        turn_value = max(-1.0, min(1.0, turn_action_scalar))

        # Calculate the change in angle based on the turn value and turn speed
        # The turn value is between -1 and 1, so multiplying by the turn speed gives the angle change
        angle_change = turn_value * max_turn_speed

        # Update the current angle based on the angle change
        new_angle = current_angle + angle_change

        # Calculate the new orientation vector from the new angle
        vector.x = math.cos(new_angle)
        vector.y = math.sin(new_angle)

        vector.normalize()

    def apply_turn(self, operator_actions):
        GameEntity.turn_vector(self.direction, operator_actions.turn, tank_turn_speed)
        # Special gotcha: when tank turns, turret turns with it!
        GameEntity.turn_vector(self.turret_direction, operator_actions.turn, tank_turn_speed)
        # But turret also turns independently..
        GameEntity.turn_vector(self.turret_direction, operator_actions.turn_turret, tank_turret_turn_speed)

    def move_check_boundary(self, operator_engine_scalar, maxspeed):
        # Cap Speed
        operator_speed_value = max(-1.0, min(1.0, operator_engine_scalar))

        move_vector = self.direction * operator_speed_value * maxspeed

        self.position += move_vector

        def cap_value_zero_max(cap, max_val):
            if cap > max_val or cap < 0:
                return True, max(0.0, min(max_val, cap))
            else:
                return False, cap

        cappedX, self.position.x = cap_value_zero_max(self.position.x, display_size.x)
        cappedY, self.position.y = cap_value_zero_max(self.position.y, display_size.y)

        return cappedX or cappedY

    def _render_entity(self, image, angle, center_tuple ):
        ent_image = pygame.transform.rotate(image, -1.0 * angle)
        ent_image_rect = ent_image.get_rect(center=center_tuple ) #self.position.as_tuple())

        # Draw rotated images
        game_layout_display.blit(ent_image, ent_image_rect.topleft)

    def get_intersection_geometry(self):
        # pygame cant rotate rectangles, so It will never be pixel perfect
        width, height = self.image.get_size()
        wh = max(width, height) #int((self.image.width + self.image.height) / 2.0)
        rect = pygame.Rect((0,0),(wh,wh))
        rect.center = self.position.as_tuple()
        return rect

def calculate_damage(shot, tank):
    line_direction = shot.direction.normalize()

    point_vector = (tank.position - shot.position).normalize()
    projection = point_vector.dot(line_direction)
    closest_point_on_line = shot.position + line_direction * projection
    distance_vector = tank.position - closest_point_on_line

    dmg = max_shot_damage * distance_vector.magnitude() / cfg.DAMAGE_DIVISOR
    # print(dmg)
    return dmg

class PlayerContext(GameEntity):
    def __init__(self, posVec, directionVec, operator, image):
        self.position = posVec
        self.direction = Vec(directionVec)
        self.turret_direction = Vec(directionVec)
        # self.alive = True
        self.name = operator.get_operator_name()
        self.operator = operator
        self.image = image
        self.turret_image = turret_image
        self.kills = 0
        self.health = tank_start_health
        self.damage_dealt = 0

    def render_entity(self):
        self._render_entity(self.image, self.direction.get_orientation_angle(), self.position.as_tuple())
        self._render_entity(self.turret_image, self.turret_direction.get_orientation_angle(), self.position.as_tuple())
        draw_health_bar(game_layout_display,
                        self.position + Vec(0, cfg.TANK_HEALTH_BAR_OFFSET_Y),
                        self.health / tank_start_health,
                        size=cfg.TANK_HEALTH_BAR_SIZE)


    def get_gamestate_object(self):
        return TankObject(Vec(self.position), Vec(self.direction), Vec(self.turret_direction))

class Shot(GameEntity):
    def __init__(self, player_context, image):
        self.position = Vec(player_context.position)
        self.direction = Vec(player_context.turret_direction)
        self.playerContext = player_context
        self.image = image

    def render_entity(self):
        self._render_entity(self.image, self.direction.get_orientation_angle(), self.position.as_tuple())

    def get_gamestate_object(self):
        return ShotObject(Vec(self.position), Vec(self.direction))

shots_cooldown_expiry = {}
def check_shots_fired(player_context, operator_actions):
    shot = None

    if operator_actions.shoot:
        cooldown = False
        try:
            if shots_cooldown_expiry[player_context] > time.time():
                #cooldown in effect
                cooldown = True
        except Exception:
            pass

        if not cooldown:
            shot = Shot(player_context, shot_image)
            shots_cooldown_expiry[player_context] = time.time() + tank_shots_cooldown
    return shot

class Explosion:
    def __init__(self, center, duration):
        self.center = center
        self.start_time = pygame.time.get_ticks()
        self.duration = duration * 1000  # convert seconds to milliseconds
        self.alive = True

# Function to draw the explosion
def draw_explosion(screen, explosion):
    current_time = pygame.time.get_ticks()
    elapsed_time = current_time - explosion.start_time

    if elapsed_time > explosion.duration:
        explosion.alive = False
        return

    # Calculate the radius of the explosion based on elapsed time
    max_radius = cfg.EXPLOSION_MAX_RADIUS
    num_circles = cfg.EXPLOSION_NUM_CIRCLES
    for i in range(num_circles):
        # Randomize the color slightly to vary between red and orange
        color = (cfg.EXPLOSION_COLOR_RED,
                 random.randint(cfg.EXPLOSION_COLOR_GREEN_MIN, cfg.EXPLOSION_COLOR_GREEN_MAX),
                 cfg.EXPLOSION_COLOR_BLUE)
        # Each circle starts small and expands over time
        radius = max_radius * (i + 1) / num_circles * (elapsed_time / explosion.duration)
        pygame.draw.circle(screen, color, explosion.center, int(radius))

def game_loop(tanks):
    winner = None
    count_down_timer = CountDownTimer(game_time_out_secs)

    shots = []
    explosions = []

    while winner is None:
        for event in pygame.event.get():
            # print(event)
            if event.type == pygame.QUIT:
                return "NONE - quitting early?"
        #main game loop - render, act, repeat

        ## Render
        # Clear the screen
        game_layout_display.fill(cfg.COLOR_BLACK)

        ## Update tank movement
        for tank in tanks:
            # if tank.alive:
            # gamestate represents the input to the decision making for the operator. ie. a copy of the game world state..
            gamestate = GameState(tank.get_gamestate_object(),
                                    [tt.get_gamestate_object() for tt in tanks if tt != tank], ## game objects for other tanks
                                    [ss.get_gamestate_object() for ss in shots])
            tankActions = tank.operator.get_tank_action(gamestate)
            if tankActions:
                shot = check_shots_fired(tank, tankActions)
                if not shot is None:
                    shots.append(shot)
                tank.apply_turn(tankActions)
                tank.move_check_boundary(tankActions.engine, tank_maxspeed)

            tank.render_entity()

        for ss in shots:
            if ss.move_check_boundary(1, shot_speed):
                #shot reached border
                shots.remove(ss)
                explosions.append(Explosion(ss.position.as_tuple(), cfg.EXPLOSION_DURATION_BORDER))

            ss.render_entity()

        for ee in explosions:
            draw_explosion(game_layout_display, ee)
            if not ee.alive:
                explosions.remove(ee)

        ## Check for impacts
        for shot in shots:
            shot_rect = shot.get_intersection_geometry()
            for tank in tanks:
                if tank != shot.playerContext:
                    tank_rect = tank.get_intersection_geometry()
                    # pygame.draw.rect(game_layout_display, red, tank_rect, 3)  # width = 3

                    if shot_rect.colliderect(tank_rect):
                        shots.remove(shot)
                        explosions.append(Explosion(tank.position.as_tuple(), cfg.EXPLOSION_DURATION_HIT))

                        damage = calculate_damage(shot, tank)
                        shot.playerContext.damage_dealt += damage
                        tank.health -= damage

                        if tank.health < 0:
                            #tank dead
                            shot.playerContext.kills += 1
                            tanks.remove(tank)
                            #if tank was operated over network, send game over message
                            try:
                                tank.operator.send_game_over_message("Game Over: you lose")
                            except AttributeError:
                                pass  # not a OperatorTCPadaptor_Server

        #tanksalive = [tt for tt in tanks if tt.alive]

        if len(tanks) == 1:
            winner = tanks[0].name
            try:
                tanks[0].operator.send_game_over_message("Game Over: you WIN!")
            except AttributeError:
                pass  # not a OperatorTCPadaptor_Server
        if len(tanks) == 0:
            #Hmm?
            winner = "Draw - no one survived"

        timed_out, timer_string = count_down_timer.get_countdown_reached_and_timer_string()
        msg_screen_topleft(game_layout_display, timer_string, cfg.COLOR_GREY, cfg.TIMER_POSITION, "vsmall")
        if timed_out:
            max_score = max(obj.damage_dealt for obj in tanks)
            top_scorers = [obj for obj in tanks if obj.damage_dealt == max_score]
            winner = ', '.join([tt.name for tt in top_scorers])
            for top_tank in top_scorers:
                try:
                    top_tank.operator.send_game_over_message("Game Over: you WIN!")
                except AttributeError:
                    pass  # not a OperatorTCPadaptor_Server

        pygame.display.update()
        clock.tick(game_fps)

    # before ending, let the winner explosion render to completion
    while explosions:
        for ee in explosions:
            draw_explosion(game_layout_display, ee)
            if not ee.alive:
                explosions.remove(ee)
        pygame.display.update()
        clock.tick(game_fps)

    return winner

########################################### ACTION!
#game_intro() #TODO:Prod


operators_and_start_pos = game_wait_for_players_screen(game_layout_display, clock,
                                server_settings.get_tank_operators_and_starting_positions() )

starting_positions = {
    name: (Vec(data["pos"][0], data["pos"][1]), Vec(data["dir"][0], data["dir"][1]))
    for name, data in cfg.STARTING_POSITIONS.items()
}

tank_images = {
    "red": pygame.transform.scale(pygame.image.load('res/tankred.png'), tank_image_size),
    "blue": pygame.transform.scale(pygame.image.load('res/tankblue.png'), tank_image_size),
    "yellow":pygame.transform.scale(pygame.image.load('res/tankyellow.png'), tank_image_size),
    "green":pygame.transform.scale(pygame.image.load('res/tankgreen.png'), tank_image_size),
}

player_tanks = [PlayerContext(starting_positions[pos_name][0],
                              starting_positions[pos_name][1],
                              operator,
                              tank_images[pos_name])
                                for pos_name, operator in operators_and_start_pos.items() if operator is not None]


winner = game_loop(player_tanks)
game_over(winner)
pygame.quit()
