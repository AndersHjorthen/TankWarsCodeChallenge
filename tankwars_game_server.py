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
from tank_operator import ObstacleObject
from tank_operator import PowerUpObject
from src.countdown_timer import CountDownTimer
from src.screens import game_wait_for_players_screen
from src.screens import msg_screen_topleft
from src.health_bar import draw_health_bar
from src.obstacles import Obstacle
from src.powerups import PowerUp, ActiveEffect
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

# Load arena obstacles
arena_obstacles = [Obstacle(*obs) for obs in cfg.ARENA_OBSTACLES]
obstacle_gamestate_objects = [ObstacleObject(*obs) for obs in cfg.ARENA_OBSTACLES]

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
def game_over(winner, tank_stats=None):
    print("Winner(s): " + winner)
    if tank_stats:
        print("\n--- End-of-Game Stats ---")
        for s in tank_stats:
            print(f"  {s['name']}: kills={s['kills']} dmg={s['damage_dealt']} "
                  f"acc={s['accuracy']}% powerups={s['powerups_collected']}")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                pygame.quit()
                quit()

        game_layout_display.fill(cfg.COLOR_BLACK)
        msg_screen("Game Over - Winner(s):", cfg.COLOR_WHITE, -100, size="medium")
        msg_screen(winner, cfg.COLOR_WHITE, -30, size="medium")

        # Display stats table
        if tank_stats:
            y_offset = 40
            msg_screen("Name       Kills  Damage  Accuracy  Powerups", cfg.COLOR_GREY, y_offset, size="vsmall")
            for i, s in enumerate(tank_stats):
                line = f"{s['name']:<12} {s['kills']}     {s['damage_dealt']:>6}    {s['accuracy']:>5}%     {s['powerups_collected']}"
                msg_screen(line, cfg.COLOR_WHEAT, y_offset + 25 + i * 22, size="vsmall")

        msg_screen("Press any key to quit", cfg.COLOR_WHEAT, 200, size="small")

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
        self.shots_fired = 0
        self.shots_hit = 0
        self.powerups_collected = 0
        self.active_effects = []

    def has_effect(self, power_type):
        return any(e.power_type == power_type and not e.is_expired() for e in self.active_effects)

    def get_effective_max_speed(self):
        if self.has_effect("speed_boost"):
            return tank_maxspeed * cfg.POWERUP_SPEED_MULTIPLIER
        return tank_maxspeed

    def get_effective_shot_cooldown(self):
        if self.has_effect("rapid_fire"):
            return cfg.POWERUP_RAPID_FIRE_COOLDOWN
        return tank_shots_cooldown

    def get_damage_multiplier(self):
        if self.has_effect("shield"):
            return cfg.POWERUP_SHIELD_DAMAGE_REDUCTION
        return 1.0

    def update_effects(self):
        self.active_effects = [e for e in self.active_effects if not e.is_expired()]

    def add_effect(self, power_type):
        # Refresh if already active, otherwise add new
        for e in self.active_effects:
            if e.power_type == power_type:
                e.expiry_time = time.time() + cfg.POWERUP_DURATION
                return
        self.active_effects.append(ActiveEffect(power_type, cfg.POWERUP_DURATION))

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

def render_obstacles(screen, obstacles):
    for obs in obstacles:
        obs.render(screen, cfg.OBSTACLE_COLOR, cfg.OBSTACLE_BORDER_COLOR)

def check_shot_obstacle_collision(shot, obstacles):
    shot_rect = shot.get_intersection_geometry()
    for obs in obstacles:
        if obs.collides_with_rect(shot_rect):
            return True
    return False

def check_tank_powerup_collision(tank, powerups):
    collected = []
    tank_rect = tank.get_intersection_geometry()
    for pu in powerups:
        if pu.alive and tank_rect.colliderect(pu.get_pickup_rect(cfg.POWERUP_PICKUP_RADIUS)):
            pu.alive = False
            collected.append(pu)
    return collected

shots_cooldown_expiry = {}
def check_shots_fired(player_context, operator_actions):
    shot = None

    if operator_actions.shoot:
        cooldown = False
        effective_cooldown = player_context.get_effective_shot_cooldown()
        try:
            if shots_cooldown_expiry[player_context] > time.time():
                cooldown = True
        except Exception:
            pass

        if not cooldown:
            shot = Shot(player_context, shot_image)
            player_context.shots_fired += 1
            shots_cooldown_expiry[player_context] = time.time() + effective_cooldown
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
    all_tanks_started = list(tanks)

    shots = []
    explosions = []
    powerups = []
    last_powerup_spawn = time.time()

    while winner is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "NONE - quitting early?", []

        ## Render
        game_layout_display.fill(cfg.COLOR_BLACK)

        # Render obstacles
        render_obstacles(game_layout_display, arena_obstacles)

        # Spawn power-ups periodically
        if time.time() - last_powerup_spawn > cfg.POWERUP_SPAWN_INTERVAL:
            pu = PowerUp.spawn_random(cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT, arena_obstacles)
            if pu:
                powerups.append(pu)
            last_powerup_spawn = time.time()

        # Render power-ups
        for pu in powerups:
            if pu.alive:
                pu.render(game_layout_display, cfg.POWERUP_COLORS, cfg.POWERUP_LABELS, cfg.POWERUP_RADIUS)

        # Build powerup gamestate objects
        powerup_gamestate_objects = [PowerUpObject(pu.x, pu.y, pu.power_type) for pu in powerups if pu.alive]

        # Calculate time remaining
        time_remaining = max(0.0, count_down_timer.end_time - time.time())

        ## Update tank movement
        for tank in tanks:
            tank.update_effects()

            gamestate = GameState(tank.get_gamestate_object(),
                                    [tt.get_gamestate_object() for tt in tanks if tt != tank],
                                    [ss.get_gamestate_object() for ss in shots],
                                    obstacles=obstacle_gamestate_objects,
                                    powerups=powerup_gamestate_objects,
                                    my_health=tank.health,
                                    arena_width=display_size.x,
                                    arena_height=display_size.y,
                                    game_time_remaining=time_remaining)
            tankActions = tank.operator.get_tank_action(gamestate)
            if tankActions:
                shot = check_shots_fired(tank, tankActions)
                if not shot is None:
                    shots.append(shot)
                tank.apply_turn(tankActions)
                tank.move_check_boundary(tankActions.engine, tank.get_effective_max_speed())

            # Check power-up collection
            collected = check_tank_powerup_collision(tank, powerups)
            for pu in collected:
                tank.add_effect(pu.power_type)
                tank.powerups_collected += 1

            tank.render_entity()

        # Remove collected power-ups
        powerups = [pu for pu in powerups if pu.alive]

        for ss in shots:
            # Check shot-obstacle collision
            if check_shot_obstacle_collision(ss, arena_obstacles):
                shots.remove(ss)
                explosions.append(Explosion(ss.position.as_tuple(), 0.3))
                continue

            if ss.move_check_boundary(1, shot_speed):
                shots.remove(ss)
                explosions.append(Explosion(ss.position.as_tuple(), cfg.EXPLOSION_DURATION_BORDER))
                continue

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

                    if shot_rect.colliderect(tank_rect):
                        shots.remove(shot)
                        explosions.append(Explosion(tank.position.as_tuple(), cfg.EXPLOSION_DURATION_HIT))

                        damage = calculate_damage(shot, tank)
                        damage *= tank.get_damage_multiplier()
                        shot.playerContext.damage_dealt += damage
                        shot.playerContext.shots_hit += 1
                        tank.health -= damage

                        if tank.health < 0:
                            shot.playerContext.kills += 1
                            tanks.remove(tank)
                            try:
                                tank.operator.send_game_over_message("Game Over: you lose")
                            except AttributeError:
                                pass

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

    # Collect end-of-game stats
    all_tank_stats = []
    for t in all_tanks_started:
        accuracy = (t.shots_hit / t.shots_fired * 100) if t.shots_fired > 0 else 0
        all_tank_stats.append({
            "name": t.name,
            "kills": t.kills,
            "damage_dealt": round(t.damage_dealt, 1),
            "shots_fired": t.shots_fired,
            "shots_hit": t.shots_hit,
            "accuracy": round(accuracy, 1),
            "powerups_collected": t.powerups_collected,
            "health_remaining": max(0, round(t.health, 1)),
        })
    all_tank_stats.sort(key=lambda s: (s["kills"], s["damage_dealt"]), reverse=True)

    return winner, all_tank_stats

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


winner, tank_stats = game_loop(player_tanks)
game_over(winner, tank_stats)
pygame.quit()
