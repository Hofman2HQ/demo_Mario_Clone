"""A polished arcade platformer inspired by Mario built with Pygame.

This version includes:
- A reactive parallax sky with twinkling stars.
- Three handcrafted levels with distinct layouts.
- Camera that smoothly follows the hero across wide stages.
- Collectable star shards, a flag goal, combo scoring and a time bonus.
- Particle effects for jumps, landings and pickups.
- Dynamic HUD, pause menu, victory and defeat screens.

Run with:  python GameMario.py
"""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass, field
from typing import List, Sequence, Tuple

import pygame

# ---------------------------------------------------------------------------
# Global configuration
# ---------------------------------------------------------------------------

pygame.init()

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 600
FPS = 60

# Colours
MIDNIGHT = pygame.Color(14, 16, 40)
SKY_BLUE = pygame.Color(46, 86, 168)
SUNSET = pygame.Color(255, 109, 85)
MOON_GLOW = pygame.Color(254, 248, 189)
WHITE = pygame.Color("white")
GOLD = pygame.Color(255, 210, 0)
GRASS = pygame.Color(56, 188, 97)
BRICK = pygame.Color(143, 86, 59)
CRIMSON = pygame.Color(214, 65, 65)
CYAN = pygame.Color(64, 224, 208)

GRAVITY = 0.65
PLAYER_SPEED = 6
PLAYER_JUMP = -15.5
CAMERA_LERP = 0.12

FONT = pygame.font.Font(None, 36)
TITLE_FONT = pygame.font.Font(None, 96)
SUBTITLE_FONT = pygame.font.Font(None, 48)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def draw_text(surface: pygame.Surface, text: str, pos: Tuple[int, int], *,
              colour: pygame.Color = WHITE, font: pygame.font.Font = FONT,
              anchor: str = "topleft") -> pygame.Rect:
    rendered = font.render(text, True, colour)
    rect = rendered.get_rect()
    setattr(rect, anchor, pos)
    surface.blit(rendered, rect)
    return rect

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Particle:
    pos: pygame.Vector2
    vel: pygame.Vector2
    life: float
    colour: pygame.Color
    radius: float

    def update(self, dt: float) -> None:
        self.life -= dt
        self.pos += self.vel * dt
        self.vel *= 0.92
        self.radius = max(0, self.radius - 15 * dt)

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        if self.life <= 0 or self.radius <= 0:
            return
        pygame.draw.circle(
            surface,
            self.colour,
            (int(self.pos.x - camera_x), int(self.pos.y)),
            int(self.radius),
        )


@dataclass
class Platform:
    rect: pygame.Rect
    colour: pygame.Color = field(default=BRICK)

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        offset_rect = self.rect.move(-camera_x, 0)
        pygame.draw.rect(surface, self.colour, offset_rect, border_radius=4)
        top_rect = pygame.Rect(offset_rect.x, offset_rect.y, offset_rect.width, 12)
        pygame.draw.rect(surface, GRASS, top_rect, border_radius=6)


@dataclass
class MovingPlatform(Platform):
    bounds: Tuple[int, int] = field(default_factory=lambda: (0, 0))
    speed: float = 2.0
    direction: int = 1

    def update(self) -> None:
        self.rect.x += self.speed * self.direction
        if self.rect.left < self.bounds[0] or self.rect.right > self.bounds[1]:
            self.direction *= -1
            self.rect.x += self.speed * self.direction


@dataclass
class Enemy:
    rect: pygame.Rect
    patrol: Tuple[int, int]
    speed: float = 2.5
    direction: int = 1
    stomped: bool = False

    def update(self) -> None:
        if self.stomped:
            return
        self.rect.x += int(self.speed * self.direction)
        if self.rect.left < self.patrol[0] or self.rect.right > self.patrol[1]:
            self.direction *= -1
            self.rect.x += int(self.speed * self.direction)

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        offset = self.rect.move(-camera_x, 0)
        pygame.draw.rect(surface, CRIMSON, offset, border_radius=8)
        eye_radius = 4
        eye_offset_y = 8
        eye_offset_x = 10 * self.direction
        pygame.draw.circle(surface, WHITE,
                           (offset.centerx - eye_offset_x, offset.centery - eye_offset_y),
                           eye_radius)
        pygame.draw.circle(surface, WHITE,
                           (offset.centerx + eye_offset_x, offset.centery - eye_offset_y),
                           eye_radius)


@dataclass
class Coin:
    rect: pygame.Rect
    collected: bool = False
    pulse: float = field(default_factory=lambda: random.random() * math.tau)

    def update(self, dt: float) -> None:
        self.pulse = (self.pulse + dt * 4) % math.tau

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        if self.collected:
            return
        offset = self.rect.move(-camera_x, 0)
        scale = 1 + 0.15 * math.sin(self.pulse)
        radius_x = int(self.rect.width * 0.5 * scale)
        radius_y = int(self.rect.height * 0.4 * scale)
        centre = offset.center
        pygame.draw.ellipse(surface, GOLD,
                             pygame.Rect(centre[0] - radius_x, centre[1] - radius_y,
                                         radius_x * 2, radius_y * 2))
        pygame.draw.ellipse(surface, WHITE,
                             pygame.Rect(centre[0] - radius_x // 2, centre[1] - radius_y,
                                         radius_x, radius_y), 2)


@dataclass
class GoalFlag:
    rect: pygame.Rect
    flutter: float = 0.0

    def update(self, dt: float) -> None:
        self.flutter = (self.flutter + dt * 5) % math.tau

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        offset = self.rect.move(-camera_x, 0)
        pygame.draw.rect(surface, WHITE, (offset.x, offset.y - self.rect.height, 6, self.rect.height))
        flag_wave = int(16 * math.sin(self.flutter))
        flag_points = [
            (offset.x + 6, offset.y - self.rect.height + 10),
            (offset.x + 6 + 46 + flag_wave, offset.y - self.rect.height + 24),
            (offset.x + 6, offset.y - self.rect.height + 38),
        ]
        pygame.draw.polygon(surface, CYAN, flag_points)


@dataclass
class Player:
    rect: pygame.Rect
    vel: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    on_ground: bool = False
    combo: int = 0
    invincible_timer: float = 0.0

    def jump(self) -> None:
        if self.on_ground:
            self.vel.y = PLAYER_JUMP
            self.on_ground = False

    def apply_gravity(self) -> None:
        self.vel.y += GRAVITY

    def move(self, direction: float) -> None:
        self.vel.x = direction * PLAYER_SPEED

    def update(self, platforms: Sequence[Platform]) -> List[Particle]:
        particles: List[Particle] = []
        previous_bottom = self.rect.bottom
        self.apply_gravity()
        self.rect.x += int(self.vel.x)
        self._horizontal_collisions(platforms)
        self.rect.y += int(self.vel.y)
        landed = self._vertical_collisions(platforms, previous_bottom)
        if landed:
            particles.extend(self._spawn_landing_particles())
        if self.invincible_timer > 0:
            self.invincible_timer = max(0, self.invincible_timer - 1 / FPS)
        return particles

    def _horizontal_collisions(self, platforms: Sequence[Platform]) -> None:
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel.x > 0:
                    self.rect.right = platform.rect.left
                elif self.vel.x < 0:
                    self.rect.left = platform.rect.right
                self.vel.x = 0

    def _vertical_collisions(self, platforms: Sequence[Platform], previous_bottom: int) -> bool:
        landed = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel.y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel.y = 0
                    self.on_ground = True
                    landed = previous_bottom <= platform.rect.top
                elif self.vel.y < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel.y = 0
        if self.rect.bottom >= SCREEN_HEIGHT - 20:
            self.rect.bottom = SCREEN_HEIGHT - 20
            self.vel.y = 0
            self.on_ground = True
            landed = True
        return landed

    def _spawn_landing_particles(self) -> List[Particle]:
        particles = []
        for i in range(8):
            speed = random.uniform(120, 220)
            angle = random.uniform(math.pi, math.tau)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            particles.append(
                Particle(
                    pos=pygame.Vector2(self.rect.centerx, self.rect.bottom - 4),
                    vel=vel,
                    life=random.uniform(0.2, 0.6),
                    colour=GRASS,
                    radius=random.uniform(2, 5),
                )
            )
        return particles

    def emit_jump_particles(self) -> List[Particle]:
        particles = []
        for _ in range(6):
            vel = pygame.Vector2(random.uniform(-90, 90), random.uniform(-10, -160))
            particles.append(
                Particle(
                    pos=pygame.Vector2(self.rect.centerx, self.rect.bottom),
                    vel=vel,
                    life=random.uniform(0.3, 0.6),
                    colour=CYAN,
                    radius=random.uniform(2, 4),
                )
            )
        return particles

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        offset = self.rect.move(-camera_x, 0)
        flicker = self.invincible_timer > 0 and int(self.invincible_timer * 30) % 2 == 0
        colour = pygame.Color(120, 190, 255) if not flicker else pygame.Color(255, 255, 255)
        pygame.draw.rect(surface, colour, offset, border_radius=8)
        eye_y = offset.top + 18
        pygame.draw.circle(surface, MIDNIGHT, (offset.left + 12, eye_y), 4)
        pygame.draw.circle(surface, MIDNIGHT, (offset.left + 28, eye_y), 4)
        pygame.draw.rect(surface, pygame.Color(255, 255, 255, 150),
                         pygame.Rect(offset.left, offset.bottom - 8, offset.width, 6), 0, 4)


# ---------------------------------------------------------------------------
# Level definitions
# ---------------------------------------------------------------------------

LEVELS = [
    {
        "platforms": [
            Platform(pygame.Rect(0, 520, 320, 40)),
            Platform(pygame.Rect(330, 480, 220, 40)),
            Platform(pygame.Rect(620, 440, 260, 40)),
            Platform(pygame.Rect(950, 420, 200, 40)),
            Platform(pygame.Rect(1260, 360, 160, 40)),
            Platform(pygame.Rect(1500, 520, 320, 40)),
        ],
        "moving_platforms": [
            MovingPlatform(pygame.Rect(770, 300, 120, 32), bounds=(700, 980), speed=2.4),
        ],
        "enemies": [
            Enemy(pygame.Rect(360, 430, 42, 42), patrol=(330, 540), speed=1.6),
            Enemy(pygame.Rect(1540, 470, 42, 42), patrol=(1500, 1800), speed=1.8),
        ],
        "coins": [
            Coin(pygame.Rect(380, 420, 28, 28)),
            Coin(pygame.Rect(660, 380, 28, 28)),
            Coin(pygame.Rect(1090, 320, 28, 28)),
        ],
        "goal": GoalFlag(pygame.Rect(1760, 520, 32, 80)),
    },
    {
        "platforms": [
            Platform(pygame.Rect(0, 520, 260, 40)),
            Platform(pygame.Rect(290, 450, 160, 40)),
            Platform(pygame.Rect(520, 360, 160, 40)),
            Platform(pygame.Rect(760, 300, 160, 40)),
            Platform(pygame.Rect(1040, 400, 160, 40)),
            Platform(pygame.Rect(1310, 480, 200, 40)),
            Platform(pygame.Rect(1580, 520, 200, 40)),
        ],
        "moving_platforms": [
            MovingPlatform(pygame.Rect(900, 380, 120, 28), bounds=(840, 1120), speed=3.2),
            MovingPlatform(pygame.Rect(1220, 340, 140, 28), bounds=(1180, 1460), speed=2.4),
        ],
        "enemies": [
            Enemy(pygame.Rect(290, 400, 38, 38), patrol=(280, 460), speed=1.7),
            Enemy(pygame.Rect(760, 250, 38, 38), patrol=(740, 920), speed=2.0),
            Enemy(pygame.Rect(1500, 470, 42, 42), patrol=(1460, 1700), speed=1.6),
        ],
        "coins": [
            Coin(pygame.Rect(600, 310, 28, 28)),
            Coin(pygame.Rect(910, 330, 28, 28)),
            Coin(pygame.Rect(1230, 290, 28, 28)),
            Coin(pygame.Rect(1650, 470, 28, 28)),
        ],
        "goal": GoalFlag(pygame.Rect(1800, 520, 32, 80)),
    },
    {
        "platforms": [
            Platform(pygame.Rect(0, 520, 320, 40)),
            Platform(pygame.Rect(340, 440, 160, 40)),
            Platform(pygame.Rect(620, 360, 160, 40)),
            Platform(pygame.Rect(880, 280, 160, 40)),
            Platform(pygame.Rect(1140, 280, 160, 40)),
            Platform(pygame.Rect(1400, 360, 160, 40)),
            Platform(pygame.Rect(1660, 440, 160, 40)),
            Platform(pygame.Rect(1920, 520, 320, 40)),
        ],
        "moving_platforms": [
            MovingPlatform(pygame.Rect(520, 500, 120, 28), bounds=(520, 760), speed=3.4),
            MovingPlatform(pygame.Rect(1130, 220, 160, 28), bounds=(1000, 1340), speed=2.8),
            MovingPlatform(pygame.Rect(1530, 300, 140, 28), bounds=(1480, 1780), speed=2.2),
        ],
        "enemies": [
            Enemy(pygame.Rect(360, 390, 38, 38), patrol=(340, 460), speed=1.8),
            Enemy(pygame.Rect(620, 310, 38, 38), patrol=(600, 760), speed=2.3),
            Enemy(pygame.Rect(1660, 390, 38, 38), patrol=(1640, 1800), speed=2.0),
            Enemy(pygame.Rect(1980, 470, 42, 42), patrol=(1940, 2180), speed=2.6),
        ],
        "coins": [
            Coin(pygame.Rect(700, 310, 28, 28)),
            Coin(pygame.Rect(960, 230, 28, 28)),
            Coin(pygame.Rect(1320, 230, 28, 28)),
            Coin(pygame.Rect(1580, 250, 28, 28)),
            Coin(pygame.Rect(2060, 470, 28, 28)),
        ],
        "goal": GoalFlag(pygame.Rect(2140, 520, 32, 80)),
    },
]

# ---------------------------------------------------------------------------
# Camera and sky rendering
# ---------------------------------------------------------------------------

class Camera:
    def __init__(self) -> None:
        self.x = 0.0

    def update(self, target_x: float) -> None:
        desired = clamp(target_x - SCREEN_WIDTH / 2, 0, 2400)
        self.x = lerp(self.x, desired, CAMERA_LERP)


class ParallaxSky:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.stars = [
            (
                pygame.Vector2(random.uniform(0, width), random.uniform(0, height * 0.7)),
                random.uniform(1, 3),
                random.uniform(0.5, 1.0),
            )
            for _ in range(120)
        ]
        self.timer = 0.0

    def update(self, dt: float) -> None:
        self.timer += dt

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        gradient = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            blend = y / self.height
            colour = pygame.Color(
                int(lerp(MIDNIGHT.r, SUNSET.r, blend)),
                int(lerp(MIDNIGHT.g, SUNSET.g, blend)),
                int(lerp(MIDNIGHT.b, SUNSET.b, blend)),
            )
            pygame.draw.line(gradient, colour, (0, y), (self.width, y))
        surface.blit(gradient, (0, 0))

        moon_x = int((camera_x * 0.2) % (self.width + 200) - 100)
        pygame.draw.circle(surface, MOON_GLOW, (moon_x, 120), 38)
        pygame.draw.circle(surface, WHITE, (moon_x - 10, 110), 8)

        for pos, radius, twinkle in self.stars:
            brightness = 128 + 127 * math.sin(self.timer * twinkle + pos.x)
            colour = pygame.Color(brightness, brightness, brightness)
            offset_x = (pos.x - camera_x * 0.3) % self.width
            pygame.draw.circle(surface, colour, (int(offset_x), int(pos.y)), int(radius))

# ---------------------------------------------------------------------------
# Game state manager
# ---------------------------------------------------------------------------

class GameState:
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    VICTORY = "victory"


class LevelManager:
    def __init__(self) -> None:
        self.level_index = 0
        self.reset_level()

    def reset_level(self) -> None:
        data = LEVELS[self.level_index]
        self.platforms: List[Platform] = [Platform(p.rect.copy(), p.colour) for p in data["platforms"]]
        self.moving_platforms: List[MovingPlatform] = [
            MovingPlatform(mp.rect.copy(), mp.colour, mp.bounds, mp.speed, mp.direction) for mp in data["moving_platforms"]
        ]
        self.enemies: List[Enemy] = [Enemy(e.rect.copy(), e.patrol, e.speed, e.direction, e.stomped) for e in data["enemies"]]
        self.coins: List[Coin] = [Coin(c.rect.copy()) for c in data["coins"]]
        goal = data["goal"]
        self.goal = GoalFlag(goal.rect.copy())

    @property
    def all_platforms(self) -> List[Platform]:
        return self.platforms + self.moving_platforms

    def update(self) -> None:
        for platform in self.moving_platforms:
            platform.update()
        for enemy in self.enemies:
            enemy.update()
        self.goal.update(1 / FPS)

    def remaining_coins(self) -> int:
        return sum(not coin.collected for coin in self.coins)

    def advance(self) -> bool:
        if self.level_index + 1 < len(LEVELS):
            self.level_index += 1
            self.reset_level()
            return True
        return False

# ---------------------------------------------------------------------------
# Main game object
# ---------------------------------------------------------------------------

class MarioLikeGame:
    def __init__(self) -> None:
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Neon Night Run")
        self.clock = pygame.time.Clock()
        self.sky = ParallaxSky(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera = Camera()
        self.state = GameState.MENU
        self.levels = LevelManager()
        self.player = Player(pygame.Rect(80, 420, 44, 60))
        self.particles: List[Particle] = []
        self.score = 0
        self.combo_timer = 0.0
        self.time_elapsed = 0.0

    # ---------------------------- State transitions ---------------------
    def start_game(self) -> None:
        self.state = GameState.PLAYING
        self.levels.level_index = 0
        self.levels.reset_level()
        self.player = Player(pygame.Rect(80, 420, 44, 60))
        self.particles.clear()
        self.score = 0
        self.combo_timer = 0.0
        self.time_elapsed = 0.0

    def pause(self) -> None:
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
        elif self.state == GameState.PAUSED:
            self.state = GameState.PLAYING

    def game_over(self) -> None:
        self.state = GameState.GAME_OVER

    def victory(self) -> None:
        self.state = GameState.VICTORY

    # ------------------------------ Update ------------------------------
    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        if self.state == GameState.PLAYING:
            self.time_elapsed += dt
            direction = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                direction -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                direction += 1
            self.player.move(direction)
            if (keys[pygame.K_UP] or keys[pygame.K_SPACE] or keys[pygame.K_w]) and self.player.on_ground:
                self.player.jump()
                self.particles.extend(self.player.emit_jump_particles())

            new_particles = self.player.update(self.levels.all_platforms)
            self.particles.extend(new_particles)
            self.levels.update()
            self.handle_collisions()
            self.update_particles(dt)
            self.camera.update(self.player.rect.centerx)
            self.sky.update(dt)
            self.update_combo_timer(dt)

        elif self.state in (GameState.MENU, GameState.PAUSED, GameState.GAME_OVER, GameState.VICTORY):
            self.sky.update(dt)
            self.update_particles(dt)

    def update_particles(self, dt: float) -> None:
        for particle in list(self.particles):
            particle.update(dt)
            if particle.life <= 0:
                self.particles.remove(particle)

    def update_combo_timer(self, dt: float) -> None:
        if self.combo_timer > 0:
            self.combo_timer = max(0, self.combo_timer - dt)
            if self.combo_timer == 0:
                self.player.combo = 0

    # --------------------------- Collision logic ------------------------
    def handle_collisions(self) -> None:
        # Player with enemies
        for enemy in self.levels.enemies:
            if enemy.stomped:
                continue
            if self.player.rect.colliderect(enemy.rect):
                if self.player.vel.y > 0 and self.player.rect.bottom - enemy.rect.top < 20:
                    enemy.stomped = True
                    self.player.vel.y = PLAYER_JUMP * 0.6
                    self.player.on_ground = False
                    self.add_score(150, combo_bonus=True)
                    self.particles.extend(self.player.emit_jump_particles())
                elif self.player.invincible_timer <= 0:
                    self.game_over()
                    return

        # Player with coins
        for coin in self.levels.coins:
            if not coin.collected and self.player.rect.colliderect(coin.rect):
                coin.collected = True
                self.add_score(100, combo_bonus=True)
                self.particles.extend(self._sparkle_effect(coin.rect.center))

        # Update coin animation
        for coin in self.levels.coins:
            coin.update(1 / FPS)

        # Goal
        if self.player.rect.colliderect(self.levels.goal.rect.inflate(40, 40)):
            if self.levels.remaining_coins() == 0:
                bonus = max(0, int(2500 - self.time_elapsed * 30))
                self.add_score(500 + bonus)
                if self.levels.advance():
                    self.player.rect.topleft = (80, 420)
                    self.player.vel.xy = (0, 0)
                    self.camera.x = 0
                    self.time_elapsed = 0.0
                    self.particles.extend(self._sparkle_effect(self.levels.goal.rect.midtop))
                else:
                    self.victory()
            else:
                self.player.invincible_timer = 0.5

    def add_score(self, base: int, *, combo_bonus: bool = False) -> None:
        if combo_bonus:
            if self.combo_timer > 0:
                self.player.combo += 1
            else:
                self.player.combo = 1
            combo_multiplier = 1 + 0.5 * (self.player.combo - 1)
            gained = int(base * combo_multiplier)
            self.combo_timer = 2.5
        else:
            gained = base
        self.score += gained

    def _sparkle_effect(self, pos: Tuple[int, int]) -> List[Particle]:
        particles = []
        for _ in range(18):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(160, 260)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            particles.append(
                Particle(
                    pos=pygame.Vector2(pos),
                    vel=vel,
                    life=random.uniform(0.3, 0.7),
                    colour=GOLD,
                    radius=random.uniform(2, 5),
                )
            )
        return particles

    # ------------------------------- Draw -------------------------------
    def draw(self) -> None:
        self.sky.draw(self.screen, self.camera.x)
        if self.state == GameState.MENU:
            self._draw_menu()
        elif self.state == GameState.PLAYING:
            self._draw_world()
            self._draw_hud()
        elif self.state == GameState.PAUSED:
            self._draw_world()
            self._draw_hud()
            self._draw_pause_overlay()
        elif self.state == GameState.GAME_OVER:
            self._draw_world()
            self._draw_game_over()
        elif self.state == GameState.VICTORY:
            self._draw_world()
            self._draw_victory()
        pygame.display.flip()

    def _draw_world(self) -> None:
        for platform in self.levels.all_platforms:
            platform.draw(self.screen, self.camera.x)
        for enemy in self.levels.enemies:
            enemy.draw(self.screen, self.camera.x)
        for coin in self.levels.coins:
            coin.draw(self.screen, self.camera.x)
        self.levels.goal.draw(self.screen, self.camera.x)
        self.player.draw(self.screen, self.camera.x)
        for particle in self.particles:
            particle.draw(self.screen, self.camera.x)

    def _draw_hud(self) -> None:
        draw_text(self.screen, f"Score: {self.score}", (20, 20))
        draw_text(self.screen, f"Level: {self.levels.level_index + 1}/{len(LEVELS)}", (20, 60))
        if self.levels.remaining_coins() > 0:
            draw_text(self.screen, f"Collect {self.levels.remaining_coins()} more star shards!", (SCREEN_WIDTH - 20, 20), anchor="topright")
        if self.player.combo > 1:
            draw_text(self.screen, f"Combo x{self.player.combo}", (SCREEN_WIDTH - 20, 60), colour=CYAN, anchor="topright")

    def _draw_menu(self) -> None:
        draw_text(self.screen, "Neon Night Run", (SCREEN_WIDTH // 2, 160), font=TITLE_FONT, colour=GOLD, anchor="center")
        draw_text(self.screen, "Press ENTER to start", (SCREEN_WIDTH // 2, 300), font=SUBTITLE_FONT, anchor="center")
        draw_text(self.screen, "Arrow keys / WASD to move, Space to jump", (SCREEN_WIDTH // 2, 360), anchor="center")
        draw_text(self.screen, "Collect all star shards before touching the flag!", (SCREEN_WIDTH // 2, 400), anchor="center")

    def _draw_pause_overlay(self) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        draw_text(self.screen, "Paused", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40), font=SUBTITLE_FONT, anchor="center")
        draw_text(self.screen, "Press ESC to resume", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10), anchor="center")

    def _draw_game_over(self) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        draw_text(self.screen, "Game Over", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80), font=TITLE_FONT, colour=CRIMSON, anchor="center")
        draw_text(self.screen, f"Final Score: {self.score}", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), font=SUBTITLE_FONT, anchor="center")
        draw_text(self.screen, "Press ENTER to try again", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60), anchor="center")

    def _draw_victory(self) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        draw_text(self.screen, "You Saved the Skyline!", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100), font=TITLE_FONT, colour=CYAN, anchor="center")
        draw_text(self.screen, f"Final Score: {self.score}", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), font=SUBTITLE_FONT, anchor="center")
        draw_text(self.screen, "Press ENTER to replay", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60), anchor="center")

    # ------------------------------ Events ------------------------------
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.pause()
                    elif self.state == GameState.PAUSED:
                        self.pause()
                    elif self.state in (GameState.GAME_OVER, GameState.VICTORY):
                        self.state = GameState.MENU
                elif event.key == pygame.K_RETURN:
                    if self.state in (GameState.MENU, GameState.GAME_OVER, GameState.VICTORY):
                        self.start_game()
                elif event.key == pygame.K_r and self.state == GameState.PLAYING:
                    self.start_game()

    # ----------------------------- Game loop ----------------------------
    def run(self) -> None:
        while True:
            dt = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.draw()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    game = MarioLikeGame()
    game.run()


if __name__ == "__main__":
    main()
