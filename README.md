# Tank Wars Code Challenge

Tank Wars is a multiplayer tank battle game built with Python and Pygame. Players
program AI-controlled tank operators that compete in a real-time arena, maneuvering
to dodge incoming fire while aiming and shooting at opponents. The challenge: build
the smartest tank AI and claim victory.

Up to four tanks can battle simultaneously. Each tank is controlled by a
`TankOperator` -- either a human via keyboard, a networked remote player, or an
AI bot that you write.

---

## Quick Start

### Prerequisites

- Python 3.10 or newer
- pip (included with most Python installations)
- pygame

### Installation

```bash
pip install pygame
```

If a `requirements.txt` file is present:

```bash
pip install -r requirements.txt
```

### Running the Game

Start a local game server (opens the game window):

```bash
python tankwars_game_server.py
```

The lobby screen will appear showing all configured players. Press **s** to start
the match once players are ready, or press **q** to quit.

---

## How to Build Your Tank AI

Your goal is to implement a `TankOperator` subclass in the file
`my_tank_operator.py`. This class must provide two methods:

### The TankOperator Interface

```python
from tank_operator import TankOperator, OperatorActions, GameState

class MyTankOperator(TankOperator):
    def get_operator_name(self) -> str:
        """Return a display name for your tank."""
        return "MyBot"

    def get_tank_action(self, game_state: GameState) -> OperatorActions:
        """Called every frame. Inspect game_state and return your actions."""
        actions = OperatorActions()
        # ... your logic here ...
        return actions
```

### GameState

The `GameState` object passed to `get_tank_action` contains everything your bot
needs to make decisions:

| Attribute      | Type                | Description                                      |
|----------------|---------------------|--------------------------------------------------|
| `tank`         | `TankObject`        | Your own tank (position, direction, turret_direction) |
| `other_tanks`  | `list[TankObject]`  | All other tanks currently alive                  |
| `shots`        | `list[ShotObject]`  | All active shots on the field                    |

**TankObject** fields:

| Field               | Type  | Description                              |
|---------------------|-------|------------------------------------------|
| `position`          | `Vec` | 2D position on the game field            |
| `direction`         | `Vec` | Unit vector of the tank body facing direction |
| `turret_direction`  | `Vec` | Unit vector of the turret facing direction    |

**ShotObject** fields:

| Field       | Type  | Description                       |
|-------------|-------|-----------------------------------|
| `position`  | `Vec` | Current position of the shot      |
| `direction` | `Vec` | Unit vector of the shot direction |

### OperatorActions

Return an `OperatorActions` object from `get_tank_action` to control your tank:

| Field          | Type    | Range              | Description                                   |
|----------------|---------|--------------------|-----------------------------------------------|
| `turn`         | `float` | -1.0 to 1.0       | Turn the tank body (negative = left, positive = right) |
| `turn_turret`  | `float` | -1.0 to 1.0       | Turn the turret independently                 |
| `engine`       | `float` | -1.0 to 1.0       | Throttle (negative = reverse, positive = forward) |
| `shoot`        | `bool`  | True / False       | Fire the cannon (subject to cooldown)         |

### The Vec Class

All positions and directions use the `Vec` class from `src/vec.py`. It supports
standard 2D vector operations:

- Arithmetic: `v1 + v2`, `v1 - v2`, `v * scalar`
- `v.dot(other)` -- dot product
- `v.magnitude()` -- vector length
- `v.normalize()` -- unit vector
- `v.rotate(angle_degrees)` -- rotate by degrees
- `v.get_orientation_angle()` -- angle in degrees
- `v.as_tuple()` -- returns `(x, y)`

### Game Loop and Timing

- The game runs at **30 FPS**. Your `get_tank_action` is called once per frame.
- The cannon has a **5-second cooldown** between shots.
- The game has a **4-minute timeout**. If time runs out, the player with the most
  damage dealt wins.
- Tanks are eliminated when their health drops below zero.
- If only one tank remains, that tank wins. If all tanks are eliminated
  simultaneously, the game is a draw.

---

## Architecture Overview

| File                        | Description                                                  |
|-----------------------------|--------------------------------------------------------------|
| `tankwars_game_server.py`   | Main game server -- runs the game loop, rendering, and physics |
| `tankwars_game_client.py`   | Headless network client for connecting a remote operator     |
| `tank_operator.py`          | Core interfaces: `TankOperator`, `GameState`, `OperatorActions`, `TankObject`, `ShotObject` |
| `my_tank_operator.py`       | Your AI implementation goes here                             |
| `dummy_operator.py`         | Simple example bot that spins and shoots                     |
| `keyboard_operator.py`      | Human-controlled operator using keyboard input               |
| `operator_tcp_adapter.py`   | TCP adapter for server-side and client-side network play     |
| `server_settings.py`        | Server configuration: which operators to load, starting positions |
| `client_settings.py`        | Client configuration: server IP/port, which operator to use  |
| `src/vec.py`                | 2D vector class used throughout the game                     |
| `src/json_protocol.py`      | JSON-over-TCP message framing protocol                       |
| `src/tcp_client.py`         | Non-blocking TCP client                                      |
| `src/tcp_server.py`         | Non-blocking TCP server                                      |
| `src/countdown_timer.py`    | Game countdown timer utility                                 |
| `src/health_bar.py`         | Health bar rendering (gradient color, border, name label)    |
| `src/screens.py`            | UI screens (intro, lobby, game-over with styled visuals)     |
| `src/arena.py`              | Pre-rendered arena background with grid and decorative border |
| `src/particles.py`          | Reusable particle system (Particle + ParticleSystem classes) |
| `src/effects.py`            | Visual effects manager (smoke, tracers, explosions, shake, aura) |
| `src/hud.py`                | HUD overlay (scoreboard, timer, kill feed)                   |
| `src/obstacles.py`          | Textured obstacle rendering and collision detection          |
| `src/powerups.py`           | Power-up spawning, rendering, and active effect tracking     |
| `example_operators.py`      | Three example AI bots: ChaserOperator, DodgerOperator, SniperOperator |
| `game_config.py`            | Centralized configuration constants for all game systems     |
| `test_visual.py`            | Quick visual test launcher with 4 AI operators (no TCP)      |

---

## Configuration

### server_settings.py

Edit this file to configure which operators participate in a local game:

```python
def get_tank_operators_and_starting_positions():
    return {
        "red"   : DummyOperator(),
        "blue"  : KeyboardOperator("BlueBob"),
        "yellow": OperatorTCPadaptor_Server(server_ip),
        "green" : MyTankOperator(),
    }
```

Each color key (`red`, `blue`, `yellow`, `green`) corresponds to a starting
corner of the arena. You can assign any `TankOperator` subclass to any slot.
Set `server_fullscreen = True` to run in fullscreen mode.

### Game Parameters (in tankwars_game_server.py)

| Parameter              | Default   | Description                          |
|------------------------|-----------|--------------------------------------|
| `display_size`         | 1200x800  | Arena dimensions in pixels           |
| `game_time_out_secs`   | 240 (4 min) | Match duration before timeout      |
| `game_fps`             | 30        | Frames per second                    |
| `tank_start_health`    | 200       | Starting health for each tank        |
| `max_shot_damage`      | 100       | Maximum damage per shot              |
| `tank_turn_speed`      | 7.5 deg   | Tank body rotation speed per frame   |
| `tank_turret_turn_speed` | 20 deg  | Turret rotation speed per frame      |
| `tank_maxspeed`        | 3.5       | Maximum tank movement speed          |
| `shot_speed`           | 15.0      | Projectile movement speed            |
| `tank_shots_cooldown`  | 5 sec     | Cooldown between shots               |

---

## Network Play

Tank Wars supports remote players over TCP. One machine runs the game server;
remote players connect as clients.

### Server Setup

In `server_settings.py`, assign an `OperatorTCPadaptor_Server` to one or more
color slots:

```python
from operator_tcp_adapter import OperatorTCPadaptor_Server

"yellow": OperatorTCPadaptor_Server('0.0.0.0'),  # listen on all interfaces
```

Start the server:

```bash
python tankwars_game_server.py
```

The lobby screen will show the IP and port for each TCP slot while waiting for
the remote player to connect.

### Client Setup

Edit `client_settings.py` with the server IP and port:

```python
serverIp = "192.168.1.100"
serverPort = 49909
tankoperator = MyTankOperator()   # or any TankOperator subclass
```

Then run the client:

```bash
python tankwars_game_client.py
```

Use the `-p` flag to override the port from the command line:

```bash
python tankwars_game_client.py -p 50123
```

---

## Development

### Running Tests

```bash
python -m pytest tests/ -v
```

### Linting

```bash
ruff check .
```

### Type Checking

```bash
mypy .
```

---

## Game Rules

- **Arena**: 1200 x 800 pixels. Tanks and shots are bounded by the arena edges.
- **Players**: 2 to 4 tanks per match.
- **Health**: Each tank starts with 200 HP. Damage is calculated based on the
  proximity of the shot impact.
- **Damage**: Maximum 100 damage per shot, scaled by distance from the impact
  point.
- **Shooting**: Cannon fires in the turret direction. There is a 5-second
  cooldown between shots.
- **Movement**: Tanks move in their facing direction. Speed and turn rate are
  capped.
- **Turret**: The turret rotates independently from the tank body, but also
  rotates with the tank when the tank turns.
- **Scoring**: If the timer runs out, the player with the highest total damage
  dealt wins.
- **Win Condition**: Last tank standing wins. If all remaining tanks are
  destroyed simultaneously, the result is a draw.
- **Timeout**: Matches last a maximum of 4 minutes.
- **Obstacles**: Walls are placed around the arena center, blocking movement and
  shots. Shots that hit obstacles explode on contact.
- **Power-ups**: Collectible items spawn periodically on the arena floor. Pick one
  up by driving over it. Each lasts 10 seconds:
  - **Speed Boost** (blue, "S") -- 1.5x movement speed.
  - **Rapid Fire** (red, "R") -- 1-second shot cooldown instead of 5.
  - **Shield** (green, "D") -- 50% damage reduction.

---

## Visual Features

The game includes a full set of visual effects designed to keep the action readable
while looking polished:

### Arena
- Dark blue-grey background with a subtle grid overlay.
- Double-line border with decorative corner accents.

### Particles and Effects
- **Smoke trails** -- wispy particles emitted behind moving tanks.
- **Shot tracers** -- glowing trail particles along each projectile's path.
- **Muzzle flash** -- bright burst of particles when a tank fires.
- **Particle explosions** -- shots that hit anything produce fire particles and
  debris chunks (replaces the old expanding-circle animation).
- **Screen shake** -- brief camera shake when a tank is destroyed.
- **Hit flash** -- white overlay flashes on a tank when it takes damage.
- **Shot glow** -- additive light halo drawn behind each projectile.
- **Power-up aura** -- pulsing colored ring around tanks with active effects.

### HUD (Heads-Up Display)
- **Scoreboard** (top-left) -- semi-transparent panel showing player names, kills,
  and damage dealt, sorted by score.
- **Timer** (top-center) -- countdown with color coding: white → yellow (< 60 s) →
  red (< 15 s).
- **Kill feed** (top-right) -- recent elimination events that fade after 5 seconds.

### Health Bars
- Gradient coloring: green at full health, yellow at half, red when low.
- Dark border outline and player name label displayed below the bar.

### Obstacles
- Pre-rendered textured surfaces with a diagonal hash pattern.
- Highlight edge (top/left) and shadow edge (bottom/right) for a 3D look.

### Screens
- **Intro** -- text shadow for depth.
- **Lobby** -- panel background, colored square indicators next to each player name.
- **Game over** -- gold-highlighted winner name, semi-transparent stats table
  background, shadow text.

### Performance
All textures and backgrounds are pre-rendered once at startup. The particle system
enforces a hard cap of 500 particles. Total visual overhead is approximately 8 ms
per frame, well within the 33 ms budget at 30 FPS.
