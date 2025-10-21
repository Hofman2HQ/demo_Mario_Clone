"""A polished arcade platformer inspired by Mario built with Pygame.

This version includes:
- A reactive parallax sky with twinkling stars.
- Three procedurally generated levels for endless variety.
- Camera that smoothly follows the hero across wide stages.
- Collectable star shards, a flag goal, combo scoring and a time bonus.
- Heart-based lives with dramatic respawns and tougher stakes.
- Animated hero with run/jump poses and wind gust launches.
- Stationary prism turrets that fire orbiting bolts and single-use double-jump orbs.
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
GRASS = pygame.Color(58, 196, 108)
BRICK = pygame.Color(143, 86, 59)
CRIMSON = pygame.Color(214, 65, 65)
CYAN = pygame.Color(64, 224, 208)
EMBER = pygame.Color(255, 120, 90)
MINT = pygame.Color(140, 255, 214)
SLATE = pygame.Color(76, 94, 140)
LILAC = pygame.Color(184, 168, 255)
SMOKE = pygame.Color(210, 238, 255)
STEEL = pygame.Color(130, 140, 160)
NEON_GREEN = pygame.Color(120, 255, 180)
SUN_FLOW = pygame.Color(255, 230, 120)
PLASMA_BLUE = pygame.Color(88, 210, 255)
PLASMA_CORE = pygame.Color(255, 255, 255)
BOUNCY_CORAL = pygame.Color(255, 160, 140)
BOUNCY_TOP = pygame.Color(255, 220, 200)
VOID_PURPLE = pygame.Color(96, 60, 180)

BACKGROUND_THEMES = [
    {
        "name": "Cosmic Dusk",
        "top": pygame.Color(24, 26, 64),
        "bottom": pygame.Color(150, 90, 180),
        "moon": pygame.Color(255, 240, 210),
        "stars": pygame.Color(230, 230, 255),
    },
    {
        "name": "Aurora Rise",
        "top": pygame.Color(12, 22, 54),
        "bottom": pygame.Color(60, 200, 220),
        "moon": pygame.Color(255, 255, 230),
        "stars": pygame.Color(190, 255, 240),
    },
    {
        "name": "Synth Sunset",
        "top": pygame.Color(40, 16, 64),
        "bottom": pygame.Color(255, 120, 120),
        "moon": pygame.Color(255, 214, 180),
        "stars": pygame.Color(255, 200, 200),
    },
    {
        "name": "Neon Midnight",
        "top": pygame.Color(10, 10, 24),
        "bottom": pygame.Color(120, 0, 180),
        "moon": pygame.Color(200, 210, 255),
        "stars": pygame.Color(255, 255, 255),
    },
]

LILAC = pygame.Color(180, 160, 255)
EMBER = pygame.Color(255, 120, 90)
MINT = pygame.Color(140, 255, 214)
SLATE = pygame.Color(70, 90, 130)
SMOKE = pygame.Color(200, 235, 255)

GRAVITY = 0.65
PLAYER_SPEED = 6
PLAYER_JUMP = -15.5
MAX_FALL_SPEED = 24.0
CAMERA_LERP = 0.12
ENEMY_DEATH_DURATION = 0.35
PROJECTILE_SPEED = 420
DOUBLE_JUMP_DECAY = 0.9
SWORD_BEAM_SPEED = 980
SWORD_BEAM_DURATION = 0.45
SWORD_BEAM_LENGTH = 180
SWORD_BEAM_HEIGHT = 42
SWORD_BEAM_MAX_RANGE = 1400
BOUNCE_VELOCITY = -17.0
BOSS_SHIELD_TIME = 0.8
MIN_BOUNCY_CHANCE = 0.18
MOVING_BOUNCY_CHANCE = 0.28
MAX_DOUBLE_JUMP_STACK = 3
MAX_SWORD_CHARGES = 4
MAX_SHIELD_CHARGES = 3
HIT_INVINC_DURATION = 2.5
FALL_RESPAWN_INVULN = 1.4
COMBO_NOVA_RADIUS = 400
STOMP_PROTECT_DURATION = 0.25

FONT = pygame.font.Font(None, 36)
TITLE_FONT = pygame.font.Font(None, 96)
SUBTITLE_FONT = pygame.font.Font(None, 48)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def draw_text(surface: pygame.Surface, text: str, pos: Tuple[int, int], *,
              colour: pygame.Color = WHITE, font: pygame.font.Font = FONT,
              anchor: str = "topleft") -> pygame.Rect:
    rendered = font.render(text, True, colour)
    rect = rendered.get_rect()
    setattr(rect, anchor, pos)
    surface.blit(rendered, rect)
    return rect


def draw_heart(surface: pygame.Surface, centre: Tuple[int, int], size: int,
               colour: pygame.Color, outline: pygame.Color | None = None) -> None:
    half = size // 2
    top_offset = int(size * 0.2)
    left_circle = (centre[0] - half // 2, centre[1] - top_offset)
    right_circle = (centre[0] + half // 2, centre[1] - top_offset)
    radius = int(size * 0.35)
    points = [
        (centre[0] - half, centre[1] - top_offset),
        (centre[0], centre[1] + half),
        (centre[0] + half, centre[1] - top_offset),
    ]
    pygame.draw.circle(surface, colour, left_circle, radius)
    pygame.draw.circle(surface, colour, right_circle, radius)
    pygame.draw.polygon(surface, colour, points)
    if outline:
        pygame.draw.circle(surface, outline, left_circle, radius, 2)
        pygame.draw.circle(surface, outline, right_circle, radius, 2)
        pygame.draw.polygon(surface, outline, points, 2)

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
        self.radius = max(0.0, self.radius - 18 * dt)

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        if self.life <= 0 or self.radius <= 0:
            return
        pygame.draw.circle(surface, self.colour,
                           (int(self.pos.x - camera_x), int(self.pos.y)),
                           int(self.radius))


@dataclass
class Platform:
    rect: pygame.Rect
    colour: pygame.Color = field(default_factory=lambda: pygame.Color(BRICK))
    is_bouncy: bool = False
    bounce_velocity: float = PLAYER_JUMP

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        offset = self.rect.move(-camera_x, 0)
        pygame.draw.rect(surface, self.colour, offset, border_radius=4)
        if self.is_bouncy:
            pad = offset.inflate(-6, -4)
            pad.height = max(12, pad.height - 6)
            pad.top = offset.top + 3
            bounce_surface = pygame.Surface(pad.size, pygame.SRCALPHA)
            pygame.draw.rect(bounce_surface, BOUNCY_CORAL, bounce_surface.get_rect(), border_radius=8)
            highlight = bounce_surface.get_rect().inflate(-12, -10)
            highlight.top = 4
            pygame.draw.rect(bounce_surface, BOUNCY_TOP, highlight, border_radius=6)
            stripes = 4
            stripe_height = max(2, pad.height // (stripes * 2))
            for i in range(stripes):
                y = 6 + i * stripe_height * 2
                pygame.draw.rect(
                    bounce_surface,
                    pygame.Color(255, 255, 255, 80),
                    pygame.Rect(6, y, pad.width - 12, stripe_height),
                    border_radius=4,
                )
            surface.blit(bounce_surface, pad.topleft)
        else:
            grass_top = pygame.Rect(offset.x, offset.y, offset.width, 12)
            pygame.draw.rect(surface, GRASS, grass_top, border_radius=6)


@dataclass
class MovingPlatform(Platform):
    bounds_x: Tuple[int, int] = field(default_factory=lambda: (0, 0))
    bounds_y: Tuple[int, int] = field(default_factory=lambda: (0, 0))
    speed_x: float = 0.0
    speed_y: float = 0.0
    direction_x: int = 1
    direction_y: int = 1
    _float_pos: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    last_move: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0), init=False)

    def __post_init__(self) -> None:
        self._float_pos = pygame.Vector2(self.rect.topleft)
        if self.bounds_x == (0, 0):
            self.bounds_x = (self.rect.left, self.rect.left)
        if self.bounds_y == (0, 0):
            self.bounds_y = (self.rect.top, self.rect.top)
        self.last_move = pygame.Vector2(0, 0)

    def update(self, dt: float, obstacles: Sequence[pygame.Rect] | None = None) -> None:
        obstacles = obstacles or ()
        previous_pos = self._float_pos.copy()
        proposed_x = self._float_pos.x
        proposed_y = self._float_pos.y
        if self.speed_x:
            proposed_x += self.speed_x * self.direction_x * dt * 60
            if proposed_x < self.bounds_x[0]:
                proposed_x = self.bounds_x[0]
                self.direction_x *= -1
            elif proposed_x + self.rect.width > self.bounds_x[1]:
                proposed_x = self.bounds_x[1] - self.rect.width
                self.direction_x *= -1
        if self.speed_y:
            proposed_y += self.speed_y * self.direction_y * dt * 60
            if proposed_y < self.bounds_y[0]:
                proposed_y = self.bounds_y[0]
                self.direction_y *= -1
            elif proposed_y + self.rect.height > self.bounds_y[1]:
                proposed_y = self.bounds_y[1] - self.rect.height
                self.direction_y *= -1
        candidate_rect = pygame.Rect(
            int(round(proposed_x)),
            int(round(proposed_y)),
            self.rect.width,
            self.rect.height,
        )
        collision_found = False
        for obstacle in obstacles:
            if obstacle is self.rect:
                continue
            if candidate_rect.colliderect(obstacle):
                collision_found = True
                break
        if collision_found:
            if self.speed_x:
                self.direction_x *= -1
            if self.speed_y:
                self.direction_y *= -1
            self.last_move.xy = (0, 0)
            self._float_pos = pygame.Vector2(self.rect.topleft)
            return
        self._float_pos.xy = (proposed_x, proposed_y)
        self.rect.topleft = candidate_rect.topleft
        self.last_move.xy = (self._float_pos.x - previous_pos.x, self._float_pos.y - previous_pos.y)


def clone_platform(source: Platform) -> Platform:
    base_kwargs = {
        "rect": source.rect.copy(),
        "colour": pygame.Color(source.colour),
        "is_bouncy": source.is_bouncy,
        "bounce_velocity": source.bounce_velocity,
    }
    if isinstance(source, MovingPlatform):
        clone = MovingPlatform(
            **base_kwargs,
            bounds_x=source.bounds_x,
            bounds_y=source.bounds_y,
            speed_x=source.speed_x,
            speed_y=source.speed_y,
        )
        clone.direction_x = source.direction_x
        clone.direction_y = source.direction_y
        return clone
    return Platform(**base_kwargs)

@dataclass
class Enemy:
    rect: pygame.Rect
    patrol: Tuple[int, int]
    speed: float = 2.5
    direction: int = 1
    health: int = 1
    max_health: int = 1
    invulnerable: float = 0.0
    stomped: bool = False
    death_timer: float = 0.0

    def update(self, dt: float) -> bool:
        if self.stomped:
            self.death_timer -= dt
            return self.death_timer > 0
        if self.invulnerable > 0:
            self.invulnerable = max(0.0, self.invulnerable - dt)
        self.rect.x += int(self.speed * self.direction)
        if self.rect.left < self.patrol[0] or self.rect.right > self.patrol[1]:
            self.direction *= -1
            self.rect.x += int(self.speed * self.direction)
        return True

    def take_hit(self) -> str:
        if self.invulnerable > 0:
            return "ignored"
        self.health -= 1
        if self.health <= 0:
            self.stomped = True
            self.death_timer = ENEMY_DEATH_DURATION
            return "killed"
        self.invulnerable = 0.3
        return "damaged"

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        offset = self.rect.move(-camera_x, 0)
        if self.stomped:
            progress = clamp(self.death_timer / ENEMY_DEATH_DURATION, 0, 1)
            squashed_height = max(6, int(offset.height * progress))
            squashed_rect = pygame.Rect(offset.left, offset.bottom - squashed_height,
                                        offset.width, squashed_height)
            pygame.draw.rect(surface, CRIMSON, squashed_rect, border_radius=8)
            return
        if self.max_health == 1:
            body_colour = CRIMSON
        else:
            body_colour = pygame.Color(180, 110, 200) if self.health == self.max_health else pygame.Color(210, 150, 240)
        pygame.draw.rect(surface, body_colour, offset, border_radius=8)
        eye_radius = 4
        eye_offset_y = 8
        eye_offset_x = 10 * self.direction
        pygame.draw.circle(surface, WHITE,
                           (offset.centerx - eye_offset_x, offset.centery - eye_offset_y),
                           eye_radius)
        pygame.draw.circle(surface, WHITE,
                           (offset.centerx + eye_offset_x, offset.centery - eye_offset_y),
                           eye_radius)
        if self.max_health > 1 and self.health > 0:
            bar_height = 4
            bar_rect = pygame.Rect(offset.left + 4, offset.top + 4, offset.width - 8, bar_height)
            pygame.draw.rect(surface, pygame.Color(40, 10, 60), bar_rect)
            fill_width = int(bar_rect.width * (self.health / self.max_health))
            if fill_width > 0:
                fill_rect = pygame.Rect(bar_rect.left, bar_rect.top, fill_width, bar_rect.height)
                pygame.draw.rect(surface, pygame.Color(200, 140, 255), fill_rect)


@dataclass
class ShooterEnemy:
    rect: pygame.Rect
    facing: int = 1
    fire_rate: float = 2.4
    cooldown: float = field(default_factory=lambda: random.uniform(0.6, 1.0))
    stomped: bool = False
    death_timer: float = 0.0
    pulse: float = field(default_factory=lambda: random.random() * math.tau)

    def update(self, dt: float, target_x: float) -> tuple[bool, List["Projectile"]]:
        projectiles: List["Projectile"] = []
        if self.stomped:
            self.death_timer -= dt
            return self.death_timer > 0, projectiles
        self.pulse = (self.pulse + dt * 3.0) % math.tau
        self.facing = 1 if target_x >= self.rect.centerx else -1
        self.cooldown -= dt
        if self.cooldown <= 0:
            self.cooldown = self.fire_rate + random.uniform(-0.4, 0.6)
            projectiles.append(self._fire_projectile())
        return True, projectiles

    def _fire_projectile(self) -> "Projectile":
        start = pygame.Vector2(self.rect.centerx + self.facing * (self.rect.width // 2 + 10),
                               self.rect.centery - 6)
        variance = random.uniform(-40, 40)
        velocity = pygame.Vector2(PROJECTILE_SPEED * self.facing, variance)
        return Projectile(pos=start, vel=velocity, radius=8, colour=EMBER)

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        offset = self.rect.move(-camera_x, 0)
        if self.stomped:
            crush = clamp(self.death_timer / ENEMY_DEATH_DURATION, 0, 1)
            husk_height = max(6, int(offset.height * crush * 0.4))
            husk = pygame.Rect(offset.left, offset.bottom - husk_height, offset.width, husk_height)
            pygame.draw.rect(surface, CRIMSON, husk, border_radius=6)
            return
        glow = (math.sin(self.pulse) + 1) * 0.5
        body_colour = pygame.Color(
            int(200 + 40 * glow),
            int(70 + 50 * glow),
            int(140 + 60 * glow),
        )
        pygame.draw.rect(surface, body_colour, offset, border_radius=10)
        base = pygame.Rect(offset.left, offset.bottom - 10, offset.width, 10)
        pygame.draw.rect(surface, MIDNIGHT, base, border_radius=4)
        nozzle = pygame.Rect(0, 0, 18, 12)
        nozzle.center = (offset.centerx + self.facing * (offset.width // 2 + 6), offset.centery - 4)
        pygame.draw.rect(surface, SLATE, nozzle, border_radius=6)
        lens_colour = pygame.Color(255, 255, 255, 190)
        pygame.draw.circle(surface, lens_colour, (nozzle.centerx + self.facing * 4, nozzle.centery), 6)


@dataclass
class Player:
    rect: pygame.Rect
    vel: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    on_ground: bool = False
    combo: int = 0
    invincible_timer: float = 0.0
    animation_time: float = 0.0
    facing: int = 1
    double_jump_stock: int = 0
    airborne_time: float = 0.0
    sword_ready: bool = False
    sword_cooldown: float = 0.0
    sword_charges: int = 0
    shield_charges: int = 0
    _float_pos: pygame.Vector2 = field(init=False)
    _pending_bounce: Platform | None = field(default=None, init=False)
    _pending_double_jump_effect: bool = field(default=False, init=False)
    ground_platform: Platform | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self._float_pos = pygame.Vector2(self.rect.topleft)

    def set_position(self, pos: Tuple[int, int]) -> None:
        self.rect.topleft = (int(pos[0]), int(pos[1]))
        self._float_pos.xy = (float(self.rect.x), float(self.rect.y))

    def jump(self) -> bool:
        if self.can_ground_jump():
            self.start_ground_jump()
            return True
        if self.can_double_jump():
            self.use_double_jump()
            return True
        return False

    def grant_double_jump(self) -> None:
        self.double_jump_stock = min(self.double_jump_stock + 1, MAX_DOUBLE_JUMP_STACK)

    def grant_sword(self) -> None:
        self.sword_charges = min(self.sword_charges + 1, MAX_SWORD_CHARGES)
        self.sword_ready = True
        self.sword_cooldown = 0.0

    def add_shield(self) -> None:
        self.shield_charges = min(self.shield_charges + 1, MAX_SHIELD_CHARGES)

    def consume_shield(self) -> bool:
        if self.shield_charges <= 0:
            return False
        self.shield_charges -= 1
        return True

    def consume_double_jump_effect(self) -> bool:
        if not self._pending_double_jump_effect:
            return False
        self._pending_double_jump_effect = False
        return True

    def apply_gravity(self, frame_scale: float) -> None:
        self.vel.y += GRAVITY * frame_scale

    def move(self, direction: float, dt: float) -> None:
        frame_scale = clamp(dt * FPS, 0.0, 1.5)
        target = direction * PLAYER_SPEED
        self.vel.x = lerp(self.vel.x, target, clamp(frame_scale * 0.35, 0.0, 1.0))
        if abs(self.vel.x) < 0.05:
            self.vel.x = 0.0
        if direction:
            self.facing = 1 if direction > 0 else -1

    def can_ground_jump(self) -> bool:
        return self.on_ground

    def start_ground_jump(self) -> None:
        self.vel.y = PLAYER_JUMP
        self.on_ground = False
        self.airborne_time = 0.0
        self.ground_platform = None
        self._pending_double_jump_effect = False

    def can_double_jump(self) -> bool:
        return (not self.on_ground) and self.double_jump_stock > 0

    def use_double_jump(self) -> None:
        self.vel.y = PLAYER_JUMP * DOUBLE_JUMP_DECAY
        self.double_jump_stock -= 1
        self.airborne_time = 0.0
        self._pending_double_jump_effect = True

    def update(self, platforms: Sequence[Platform], dt: float) -> List[Particle]:
        particles: List[Particle] = []
        if self.ground_platform and isinstance(self.ground_platform, MovingPlatform):
            motion = self.ground_platform.last_move
            if motion.x or motion.y:
                self._float_pos.x += motion.x
                self._float_pos.y += motion.y
                self.rect.topleft = (int(round(self._float_pos.x)), int(round(self._float_pos.y)))
        frame_scale = clamp(dt * FPS, 0.0, 2.0)
        previous_bottom = self.rect.bottom
        previous_top = self.rect.top
        was_on_ground = self.on_ground
        self.animation_time += dt
        self.apply_gravity(frame_scale)
        self.vel.y = min(self.vel.y, MAX_FALL_SPEED)
        self._pending_bounce = None
        self._resolve_initial_overlap(platforms)

        delta_x = self.vel.x * frame_scale
        if delta_x != 0.0:
            self._horizontal_collisions(platforms, delta_x)
        else:
            self._float_pos.x = float(self.rect.x)

        delta_y = self.vel.y * frame_scale
        landed = self._vertical_collisions(platforms, delta_y, previous_bottom, previous_top, was_on_ground)

        if self.on_ground:
            self.airborne_time = 0.0
        else:
            self.airborne_time += dt
        if landed:
            particles.extend(self._spawn_landing_particles())
        if self._pending_bounce:
            particles.extend(self.emit_bounce_particles(self._pending_bounce))
            self._pending_bounce = None
        if self.invincible_timer > 0:
            self.invincible_timer = max(0.0, self.invincible_timer - dt)
        if self.sword_cooldown > 0:
            self.sword_cooldown = max(0.0, self.sword_cooldown - dt)
        if self.sword_cooldown <= 0:
            self.sword_ready = self.sword_charges > 0
        return particles

    def _resolve_initial_overlap(self, platforms: Sequence[Platform]) -> None:
        attempts = 0
        while attempts < 4:
            overlap_found = False
            for platform in platforms:
                if not self.rect.colliderect(platform.rect):
                    continue
                overlap = self.rect.clip(platform.rect)
                if overlap.width <= 0 or overlap.height <= 0:
                    continue
                overlap_found = True
                if overlap.width < overlap.height:
                    if self.rect.centerx < platform.rect.centerx:
                        self.rect.right = platform.rect.left
                    else:
                        self.rect.left = platform.rect.right
                    self._float_pos.x = float(self.rect.x)
                    self.vel.x = 0.0
                    self.ground_platform = None
                else:
                    if self.rect.centery < platform.rect.centery:
                        self.rect.bottom = platform.rect.top
                        self.on_ground = True
                        self.ground_platform = platform
                    else:
                        self.rect.top = platform.rect.bottom
                        self.ground_platform = None
                    self._float_pos.y = float(self.rect.y)
                    self.vel.y = 0.0
                break
            if not overlap_found:
                break
            attempts += 1

    def _horizontal_collisions(self, platforms: Sequence[Platform], delta_x: float) -> None:
        left = self._float_pos.x
        right = left + self.rect.width
        top = self.rect.top
        bottom = self.rect.bottom
        target_left = left + delta_x
        target_right = right + delta_x
        move = delta_x
        collided: Platform | None = None

        if delta_x > 0:
            for platform in platforms:
                rect = platform.rect
                if bottom <= rect.top or top >= rect.bottom:
                    continue
                if right <= rect.left and target_right > rect.left:
                    distance = rect.left - right
                    if distance < move:
                        move = max(distance, 0.0)
                        collided = platform
        else:
            for platform in platforms:
                rect = platform.rect
                if bottom <= rect.top or top >= rect.bottom:
                    continue
                if left >= rect.right and target_left < rect.right:
                    distance = rect.right - left
                    if distance > move:
                        move = min(distance, 0.0)
                        collided = platform

        self._float_pos.x += move
        self.rect.x = int(round(self._float_pos.x))
        if collided:
            if delta_x > 0:
                self.rect.right = collided.rect.left
            else:
                self.rect.left = collided.rect.right
            self._float_pos.x = float(self.rect.x)
            self.vel.x = 0.0

    def _vertical_collisions(
        self,
        platforms: Sequence[Platform],
        delta_y: float,
        previous_bottom: int,
        previous_top: int,
        was_on_ground: bool,
    ) -> bool:
        if delta_y == 0.0:
            self._float_pos.y = float(self.rect.y)
            return False

        left = self.rect.left
        right = self.rect.right
        top = self._float_pos.y
        bottom = top + self.rect.height
        target_top = top + delta_y
        target_bottom = bottom + delta_y
        move = delta_y
        collided: Platform | None = None
        landed = False

        if delta_y > 0:
            for platform in platforms:
                rect = platform.rect
                if right <= rect.left or left >= rect.right:
                    continue
                if bottom <= rect.top and target_bottom > rect.top:
                    gap = rect.top - bottom
                    if gap < move:
                        move = max(gap, 0.0)
                        collided = platform
        else:
            for platform in platforms:
                rect = platform.rect
                if right <= rect.left or left >= rect.right:
                    continue
                if top >= rect.bottom and target_top < rect.bottom:
                    gap = rect.bottom - top
                    if gap > move:
                        move = min(gap, 0.0)
                        collided = platform

        self._float_pos.y += move
        self.rect.y = int(round(self._float_pos.y))
        self.on_ground = False
        ground_platform: Platform | None = None

        if collided:
            if delta_y > 0:
                self.rect.bottom = collided.rect.top
                self._float_pos.y = float(self.rect.y)
                if collided.is_bouncy:
                    self.vel.y = collided.bounce_velocity
                    self.on_ground = False
                    self._pending_bounce = collided
                    ground_platform = None
                else:
                    self.vel.y = 0.0
                    self.on_ground = True
                    ground_platform = collided
                    if not was_on_ground and previous_bottom <= collided.rect.top + 2:
                        landed = True
            else:
                self.rect.top = collided.rect.bottom
                self._float_pos.y = float(self.rect.y)
                self.vel.y = 0.0
                ground_platform = None
        else:
            for platform in platforms:
                if not self.rect.colliderect(platform.rect):
                    continue
                overlap = self.rect.clip(platform.rect)
                if overlap.height <= 0:
                    continue
                if self.rect.centery <= platform.rect.centery:
                    self.rect.bottom = platform.rect.top
                    self._float_pos.y = float(self.rect.y)
                    if platform.is_bouncy:
                        self.vel.y = platform.bounce_velocity
                        self._pending_bounce = platform
                        self.on_ground = False
                        ground_platform = None
                    else:
                        self.vel.y = 0.0
                        self.on_ground = True
                        ground_platform = platform
                        if not was_on_ground and previous_bottom <= platform.rect.top + 2:
                            landed = True
                    break
                else:
                    self.rect.top = platform.rect.bottom
                    self._float_pos.y = float(self.rect.y)
                    self.vel.y = 0.0
                    ground_platform = None
                    break

        if self.on_ground and self.vel.y > 0:
            self.vel.y = 0.0
        if not self.on_ground:
            ground_platform = None
        self.ground_platform = ground_platform

        return landed

    def _spawn_landing_particles(self) -> List[Particle]:
        particles = []
        for _ in range(10):
            speed = random.uniform(150, 260)
            angle = random.uniform(math.pi, math.tau)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            particles.append(
                Particle(
                    pos=pygame.Vector2(self.rect.centerx, self.rect.bottom - 4),
                    vel=vel,
                    life=random.uniform(0.2, 0.55),
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

    def emit_wind_gust(self) -> List[Particle]:
        gusts: List[Particle] = []
        for _ in range(5):
            vel = pygame.Vector2(random.uniform(-50, 50), random.uniform(140, 220))
            gusts.append(
                Particle(
                    pos=pygame.Vector2(self.rect.centerx + random.uniform(-12, 12), self.rect.bottom + 6),
                    vel=vel,
                    life=random.uniform(0.25, 0.45),
                    colour=SMOKE,
                    radius=random.uniform(3, 5),
                )
            )
        return gusts

    def emit_bounce_particles(self, platform: Platform) -> List[Particle]:
        bursts: List[Particle] = []
        base_colour = BOUNCY_TOP if platform.is_bouncy else CYAN
        for _ in range(12):
            angle = random.uniform(math.pi, math.tau)
            speed = random.uniform(180, 320)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            bursts.append(
                Particle(
                    pos=pygame.Vector2(self.rect.centerx, platform.rect.top),
                    vel=vel,
                    life=random.uniform(0.25, 0.55),
                    colour=base_colour,
                    radius=random.uniform(2.5, 5),
                )
            )
        return bursts

    def perform_sword_attack(self) -> SwordBeam:
        width = SWORD_BEAM_LENGTH
        height = SWORD_BEAM_HEIGHT
        if self.facing > 0:
            left = self.rect.right - 10
        else:
            left = self.rect.left - width + 10
        top = self.rect.centery - height // 2
        slash_rect = pygame.Rect(int(left), int(top), width, height)
        if self.sword_charges > 0:
            self.sword_charges -= 1
        self.sword_ready = False
        self.sword_cooldown = 0.5
        return SwordBeam(rect=slash_rect, facing=self.facing)

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        offset = self.rect.move(-camera_x, 0)
        flicker = self.invincible_timer > 0 and int(self.invincible_timer * 30) % 2 == 0

        suit_base = pygame.Rect(offset.left + 8, offset.top + 4, offset.width - 16, offset.height - 10)
        run_phase = math.sin(self.animation_time * 12.0) * min(1.0, abs(self.vel.x) / (PLAYER_SPEED + 1e-3))
        bob = -run_phase * 3.0 if self.on_ground and abs(self.vel.x) > 0.4 else 0.0
        if not self.on_ground:
            stretch = clamp(-self.vel.y * 0.04, -0.3, 0.5)
            suit_base = suit_base.inflate(-6, -int(16 * stretch))
            bob -= stretch * 6
        suit_base.y += int(round(bob))

        torso_surface = pygame.Surface(suit_base.size, pygame.SRCALPHA)
        torso_rect = torso_surface.get_rect()
        pygame.draw.rect(torso_surface, pygame.Color(90, 150, 255), torso_rect, border_radius=16)
        chestplate = pygame.Rect(6, 10, torso_rect.width - 12, torso_rect.height - 18)
        pygame.draw.rect(torso_surface, pygame.Color(140, 200, 255), chestplate, border_radius=12)
        glow_colour = pygame.Color(40, 70, 200, 180)
        pygame.draw.rect(torso_surface, glow_colour, chestplate.inflate(-16, -16), border_radius=10)
        if flicker:
            torso_surface.fill((255, 255, 255, 90), special_flags=pygame.BLEND_RGBA_ADD)
        surface.blit(torso_surface, suit_base.topleft)

        visor = pygame.Rect(suit_base.centerx - 24, suit_base.top + 6, 48, 18)
        pygame.draw.rect(surface, pygame.Color(40, 50, 120), visor, border_radius=10)
        visor_glow = pygame.Surface((visor.width, visor.height), pygame.SRCALPHA)
        pygame.draw.rect(visor_glow, pygame.Color(100, 200, 255, 160), visor_glow.get_rect(), border_radius=10)
        surface.blit(visor_glow, visor)
        eye_y = visor.centery
        gaze = int(6 * self.facing)
        pygame.draw.circle(surface, MIDNIGHT, (visor.centerx - 12 + gaze, eye_y), 4)
        pygame.draw.circle(surface, MIDNIGHT, (visor.centerx + 12 + gaze, eye_y), 4)

        jet_rect = pygame.Rect(suit_base.left + 10, suit_base.bottom - 8, suit_base.width - 20, 6)
        pygame.draw.rect(surface, pygame.Color(255, 255, 255, 160), jet_rect, border_radius=3)
        exhaust = pygame.Rect(jet_rect.left, jet_rect.bottom, jet_rect.width, 10)
        pygame.draw.rect(surface, pygame.Color(120, 200, 255, 160), exhaust, border_radius=3)

        leg_colour = pygame.Color(60, 80, 150)
        foot_y = suit_base.bottom + 4
        if self.on_ground and abs(self.vel.x) > 0.4:
            stride = math.sin(self.animation_time * 16)
            spread = 16
            pygame.draw.circle(surface, leg_colour, (suit_base.centerx - int(stride * spread), foot_y), 7)
            pygame.draw.circle(surface, leg_colour, (suit_base.centerx + int(stride * spread), foot_y), 7)
        else:
            pygame.draw.circle(surface, leg_colour, (suit_base.centerx - 8, foot_y), 7)
            pygame.draw.circle(surface, leg_colour, (suit_base.centerx + 8, foot_y), 7)

        arm_colour = pygame.Color(180, 170, 255)
        sway = math.sin(self.animation_time * 14) * 6 if self.on_ground and abs(self.vel.x) > 0.5 else 0
        left_arm = pygame.Rect(suit_base.left - 10, suit_base.top + 20 + sway, 18, 24)
        right_arm = pygame.Rect(suit_base.right - 8, suit_base.top + 20 - sway, 18, 24)
        pygame.draw.ellipse(surface, arm_colour, left_arm)
        pygame.draw.ellipse(surface, arm_colour, right_arm)

        if self.shield_charges > 0:
            shield_radius = max(suit_base.width, suit_base.height) + 14
            shield_surface = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            shimmer = int(120 + 60 * math.sin(self.animation_time * 8.0))
            pygame.draw.circle(
                shield_surface,
                (150, 230, 255, shimmer),
                (shield_radius, shield_radius),
                shield_radius,
                3,
            )
            inner_radius = max(8, shield_radius - 10)
            pygame.draw.circle(
                shield_surface,
                (90, 180, 255, 60),
                (shield_radius, shield_radius),
                inner_radius,
            )
            surface.blit(shield_surface, shield_surface.get_rect(center=suit_base.center))

        if self.sword_ready:
            glow_radius = max(suit_base.width, suit_base.height)
            glow = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                glow,
                (NEON_GREEN.r, NEON_GREEN.g, NEON_GREEN.b, 90),
                (glow_radius, glow_radius),
                glow_radius,
            )
            surface.blit(glow, glow.get_rect(center=suit_base.center))


@dataclass
class Projectile:
    pos: pygame.Vector2
    vel: pygame.Vector2
    radius: float
    colour: pygame.Color = field(default_factory=lambda: EMBER.copy())
    life: float = 4.0

    def update(self, dt: float) -> bool:
        self.pos += self.vel * dt
        self.life -= dt
        return self.life > 0

    @property
    def rect(self) -> pygame.Rect:
        size = int(self.radius * 2)
        return pygame.Rect(int(self.pos.x - self.radius), int(self.pos.y - self.radius), size, size)

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        centre = (int(self.pos.x - camera_x), int(self.pos.y))
        pygame.draw.circle(surface, self.colour, centre, int(self.radius))
        tail_end = (centre[0] - int(self.vel.x * 0.06), centre[1] - int(self.vel.y * 0.06))
        pygame.draw.line(surface, pygame.Color(255, 200, 160), centre, tail_end, 3)


@dataclass
class SwordBeam:
    rect: pygame.Rect
    facing: int
    life: float = SWORD_BEAM_DURATION
    speed: float = SWORD_BEAM_SPEED
    travelled: float = 0.0
    _float_pos: pygame.Vector2 = field(init=False)
    phase: float = field(default_factory=lambda: random.random() * math.tau)

    def __post_init__(self) -> None:
        self._float_pos = pygame.Vector2(self.rect.topleft)

    def update(self, dt: float) -> bool:
        advance = self.speed * dt
        self.travelled += advance
        self._float_pos.x += advance * self.facing
        self.rect.x = int(round(self._float_pos.x))
        self.life -= dt
        self.phase = (self.phase + dt * 16.0) % math.tau
        return self.life > 0 and self.travelled < SWORD_BEAM_MAX_RANGE

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        offset = self.rect.move(-camera_x, 0)
        if offset.width <= 0 or offset.height <= 0:
            return
        glow = pygame.Surface((offset.width + 24, offset.height + 24), pygame.SRCALPHA)
        core_rect = glow.get_rect()
        pygame.draw.rect(
            glow,
            pygame.Color(80, 255, 210, 180),
            core_rect,
            border_radius=16,
        )
        pulse = (math.sin(self.phase) + 1) * 0.5
        band_intensity = int(160 + 60 * pulse)
        middle_rect = core_rect.inflate(-12, -8)
        pygame.draw.rect(
            glow,
            pygame.Color(PLASMA_BLUE.r, PLASMA_BLUE.g, PLASMA_BLUE.b, band_intensity),
            middle_rect,
            border_radius=12,
        )
        core = middle_rect.inflate(-max(6, middle_rect.width // 5), -max(6, middle_rect.height // 3))
        pygame.draw.rect(
            glow,
            pygame.Color(PLASMA_CORE.r, PLASMA_CORE.g, PLASMA_CORE.b, 220),
            core,
            border_radius=10,
        )
        stripe_height = max(2, core.height // 5)
        for i in range(3):
            stripe = pygame.Rect(core.left + 4, core.top + 6 + i * stripe_height * 2, core.width - 8, stripe_height)
            pygame.draw.rect(
                glow,
                pygame.Color(255, 255, 255, 140 - i * 30),
                stripe,
                border_radius=4,
            )
        tip_width = max(12, offset.height // 2)
        tip_shape = pygame.Surface((tip_width, offset.height + 20), pygame.SRCALPHA)
        tip_height = tip_shape.get_height()
        pygame.draw.polygon(
            tip_shape,
            pygame.Color(255, 255, 255, 160),
            [
                (0, tip_height // 2),
                (tip_width - 2, 4),
                (tip_width - 2, tip_height - 4),
            ],
        )
        tip = tip_shape if self.facing > 0 else pygame.transform.flip(tip_shape, True, False)
        glow.blit(
            tip,
            (
                core.right - tip_width // 2 if self.facing > 0 else core.left - tip_width // 2,
                (glow.get_height() - tip.get_height()) // 2,
            ),
            special_flags=pygame.BLEND_ADD,
        )
        jitter = math.sin(self.phase * 2.0) * 3.0
        glow_rect = glow.get_rect(center=offset.center)
        glow_rect.x += int(jitter * self.facing)
        surface.blit(glow, glow_rect)


@dataclass
class JumpSphereEffect:
    centre: pygame.Vector2
    width: float
    height: float
    timer: float = 0.35
    lifetime: float = 0.35

    def update(self, dt: float) -> bool:
        self.timer -= dt
        return self.timer > 0

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        progress = clamp(self.timer / self.lifetime, 0.0, 1.0)
        radius_scale = 0.6 + 0.4 * progress
        alpha = int(180 * progress)
        size = (int(self.width * radius_scale), int(self.height * radius_scale))
        ellipse_surface = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.ellipse(
            ellipse_surface,
            pygame.Color(140, 230, 255, alpha),
            ellipse_surface.get_rect(),
            4,
        )
        fill = ellipse_surface.get_rect().inflate(-int(size[0] * 0.25), -int(size[1] * 0.35))
        pygame.draw.ellipse(
            ellipse_surface,
            pygame.Color(200, 255, 255, int(alpha * 0.4)),
            fill,
        )
        draw_pos = (int(self.centre.x - camera_x - size[0] / 2), int(self.centre.y - size[1] / 2))
        surface.blit(ellipse_surface, draw_pos)

@dataclass
class Boss:
    rect: pygame.Rect
    anchors: List[pygame.Vector2]
    health: int = 5
    speed: float = 180.0
    attack_cooldown: float = 2.4
    invulnerable: float = 0.0
    defeated: bool = False
    celebration_timer: float = 1.2
    anchor_index: int = 0
    move_timer: float = 0.0
    pulse: float = field(default_factory=lambda: random.random() * math.tau)
    roam_bounds: pygame.Rect = field(init=False)
    roam_target: pygame.Vector2 = field(init=False)

    def __post_init__(self) -> None:
        self._setup_roam_area()
        self.roam_target = pygame.Vector2(self.rect.center)
        self._pick_new_roam_target(force=True)

    def clone(self) -> "Boss":
        return Boss(
            self.rect.copy(),
            [pygame.Vector2(anchor) for anchor in self.anchors],
            health=self.health,
            speed=self.speed,
            attack_cooldown=self.attack_cooldown,
            invulnerable=0.0,
            defeated=self.defeated,
            celebration_timer=self.celebration_timer,
            anchor_index=self.anchor_index,
            move_timer=0.0,
            pulse=random.random() * math.tau,
        )

    def update(self, dt: float, player_rect: pygame.Rect) -> tuple[bool, List[Projectile]]:
        projectiles: List[Projectile] = []
        self.pulse = (self.pulse + dt * 5.2) % math.tau
        if self.defeated:
            self.celebration_timer = max(0.0, self.celebration_timer - dt)
            return self.celebration_timer > 0, projectiles

        self._update_roaming(dt)

        self.attack_cooldown -= dt
        if self.attack_cooldown <= 0:
            self.attack_cooldown = 2.9
            projectiles.extend(self._spawn_waves(player_rect))

        if self.invulnerable > 0:
            self.invulnerable = max(0.0, self.invulnerable - dt)

        return True, projectiles

    def _setup_roam_area(self) -> None:
        if self.anchors:
            xs = [anchor.x for anchor in self.anchors]
            ys = [anchor.y for anchor in self.anchors]
            left = min(xs) - 120
            right = max(xs) + 120
            top = min(ys) - 140
            bottom = min(max(ys) + 80, min(ys) + 220)
        else:
            left = self.rect.centerx - 200
            right = self.rect.centerx + 200
            top = self.rect.centery - 180
            bottom = self.rect.centery + 80
        left = int(left)
        top = int(max(40, top))
        right = int(max(left + 10, right))
        bottom = int(max(top + 120, bottom))
        width = max(160, right - left)
        height = max(120, bottom - top)
        self.roam_bounds = pygame.Rect(left, top, width, height)

    def _pick_new_roam_target(self, *, force: bool = False) -> None:
        margin_x = self.rect.width * 0.5 + 24
        margin_y = self.rect.height * 0.5 + 24
        left = self.roam_bounds.left + margin_x
        right = self.roam_bounds.right - margin_x
        top = self.roam_bounds.top + margin_y
        bottom = self.roam_bounds.bottom - margin_y
        if right <= left:
            right = left
        if bottom <= top:
            bottom = top
        self.roam_target = pygame.Vector2(
            random.uniform(left, right) if right > left else left,
            random.uniform(top, bottom) if bottom > top else top,
        )
        if not force:
            self.move_timer = random.uniform(0.35, 0.8)
        else:
            self.move_timer = 0.0

    def _update_roaming(self, dt: float) -> None:
        current = pygame.Vector2(self.rect.center)
        distance = current.distance_to(self.roam_target)
        if distance <= 8:
            if self.move_timer > 0:
                self.move_timer = max(0.0, self.move_timer - dt)
                if self.move_timer > 0:
                    return
            self._pick_new_roam_target()
            return
        direction = self.roam_target - current
        if direction.length_squared() <= 0:
            return
        direction = direction.normalize()
        direction.y += math.sin(self.pulse * 1.6) * 0.04
        step = direction * self.speed * dt
        if step.length() > distance:
            step = self.roam_target - current
        self.rect.centerx += int(round(step.x))
        self.rect.centery += int(round(step.y))
        half_w = self.rect.width // 2
        half_h = self.rect.height // 2
        self.rect.centerx = int(
            clamp(self.rect.centerx, self.roam_bounds.left + half_w, self.roam_bounds.right - half_w)
        )
        self.rect.centery = int(
            clamp(self.rect.centery, self.roam_bounds.top + half_h, self.roam_bounds.bottom - half_h)
        )

    def _spawn_waves(self, player_rect: pygame.Rect) -> List[Projectile]:
        projectiles: List[Projectile] = []
        origin = pygame.Vector2(self.rect.centerx, self.rect.bottom - 12)
        for offset in (-2, -1, 0, 1, 2):
            vel = pygame.Vector2(offset * 90, 240 + abs(offset) * 30)
            colour = pygame.Color(VOID_PURPLE)
            projectiles.append(Projectile(pos=origin.copy(), vel=vel, radius=9, colour=colour, life=3.4))
        sky_origin = pygame.Vector2(self.rect.centerx, self.rect.top + 6)
        to_player = pygame.Vector2(player_rect.centerx - self.rect.centerx, player_rect.centery - self.rect.centery)
        if to_player.length_squared() > 1:
            to_player = to_player.normalize()
        else:
            to_player = pygame.Vector2(0, 1)
        to_player.y = max(to_player.y, 0.3)
        projectile_speed = 340
        targeted_colour = pygame.Color(200, 160, 255)
        projectiles.append(
            Projectile(
                pos=sky_origin,
                vel=to_player * projectile_speed,
                radius=10,
                colour=targeted_colour,
                life=3.6,
            )
        )
        return projectiles

    def take_hit(self) -> bool:
        if self.invulnerable > 0 or self.defeated:
            return False
        self.health -= 1
        self.invulnerable = BOSS_SHIELD_TIME
        if self.health <= 0:
            self.defeated = True
            self.celebration_timer = 1.2
        return True

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        if self.celebration_timer <= 0 and self.defeated:
            return
        offset = self.rect.move(-camera_x, 0)
        body = pygame.Surface((offset.width + 20, offset.height + 20), pygame.SRCALPHA)
        body_rect = body.get_rect()
        base_colour = pygame.Color(150, 110, 255, 220)
        pygame.draw.ellipse(body, base_colour, body_rect.inflate(-6, -6))
        inner_rect = body_rect.inflate(-22, -18)
        glow_alpha = int(140 + 60 * math.sin(self.pulse))
        pygame.draw.ellipse(body, pygame.Color(90, 40, 200, glow_alpha), inner_rect)
        eye_offset = int(10 + 4 * math.sin(self.pulse * 2))
        pygame.draw.circle(body, pygame.Color(255, 255, 255, 220), (body_rect.centerx, body_rect.centery - 6), 10)
        pygame.draw.circle(body, pygame.Color(40, 10, 80), (body_rect.centerx + eye_offset, body_rect.centery - 6), 6)
        mouth = pygame.Rect(0, 0, body_rect.width // 2, 10)
        mouth.center = (body_rect.centerx, body_rect.centery + 18)
        pygame.draw.ellipse(body, pygame.Color(30, 0, 60), mouth)

        if self.invulnerable > 0 and not self.defeated:
            shield_rect = body_rect.inflate(16, 14)
            shield_alpha = int(80 + 80 * math.sin(self.invulnerable * 22))
            pygame.draw.ellipse(body, pygame.Color(120, 220, 255, shield_alpha), shield_rect, 4)
        elif self.defeated:
            fade = clamp(self.celebration_timer / 1.2, 0.0, 1.0)
            body.fill((255, 255, 255, int(180 * fade)), special_flags=pygame.BLEND_RGBA_MULT)

        surface.blit(body, body_rect.move(offset.left - 10, offset.top - 10))

        # Draw health pips
        pip_width = 16
        pip_spacing = 6
        total_width = self.health * pip_width + (self.health - 1) * pip_spacing if self.health > 0 else 0
        start_x = offset.centerx - total_width // 2
        pip_y = offset.top - 24
        for i in range(max(self.health, 0)):
            pip_rect = pygame.Rect(start_x + i * (pip_width + pip_spacing), pip_y, pip_width, 8)
            pygame.draw.rect(surface, pygame.Color(255, 210, 120), pip_rect, border_radius=4)

@dataclass
class Coin:
    rect: pygame.Rect
    collected: bool = False
    pulse: float = field(default_factory=lambda: random.random() * math.tau)

    def update(self, dt: float) -> None:
        self.pulse = (self.pulse + dt * 4.0) % math.tau

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        if self.collected:
            return
        offset = self.rect.move(-camera_x, 0)
        scale = 1 + 0.15 * math.sin(self.pulse)
        radius_x = int(self.rect.width * 0.5 * scale)
        radius_y = int(self.rect.height * 0.4 * scale)
        centre = offset.center
        glow_radius = int(max(radius_x, radius_y) * 1.6)
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (255, 235, 140, 120), (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surface, glow_surface.get_rect(center=centre))
        coin_colour = pygame.Color(255, 240, 100)
        coin_rect = pygame.Rect(centre[0] - radius_x, centre[1] - radius_y,
                                radius_x * 2, radius_y * 2)
        pygame.draw.ellipse(surface, coin_colour, coin_rect)
        highlight_rect = pygame.Rect(centre[0] - radius_x // 2, centre[1] - radius_y,
                                     radius_x, radius_y)
        pygame.draw.ellipse(surface, WHITE, highlight_rect, 2)
        inner = pygame.Rect(centre[0] - radius_x // 3, centre[1] - radius_y // 2,
                             radius_x // 2, radius_y // 2)
        pygame.draw.ellipse(surface, pygame.Color(255, 255, 255, 190), inner)


@dataclass
class DoubleJumpPowerUp:
    rect: pygame.Rect
    pulse: float = field(default_factory=lambda: random.random() * math.tau)
    collected: bool = False

    def update(self, dt: float) -> None:
        self.pulse = (self.pulse + dt * 3.2) % math.tau

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        if self.collected:
            return
        offset = self.rect.move(-camera_x, 0)
        halo_radius = max(offset.width, offset.height)
        halo_surface = pygame.Surface((halo_radius * 2, halo_radius * 2), pygame.SRCALPHA)
        intensity = int(90 + 60 * math.sin(self.pulse))
        pygame.draw.circle(halo_surface, (120, 200, 255, intensity), (halo_radius, halo_radius), halo_radius)
        surface.blit(halo_surface, halo_surface.get_rect(center=offset.center))
        rotation = math.sin(self.pulse) * 8
        diamond = [
            (offset.centerx, offset.top - 6),
            (offset.right + rotation * 0.5, offset.centery),
            (offset.centerx, offset.bottom + 6),
            (offset.left - rotation * 0.5, offset.centery),
        ]
        pygame.draw.polygon(surface, MINT, diamond)
        inner = [
            (offset.centerx, offset.top + 4),
            (offset.right - 6, offset.centery),
            (offset.centerx, offset.bottom - 4),
            (offset.left + 6, offset.centery),
        ]
        pygame.draw.polygon(surface, WHITE, inner, 2)


@dataclass
class SwordPowerUp:
    rect: pygame.Rect
    pulse: float = field(default_factory=lambda: random.random() * math.tau)
    collected: bool = False

    def update(self, dt: float) -> None:
        self.pulse = (self.pulse + dt * 5.5) % math.tau

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        if self.collected:
            return
        offset = self.rect.move(-camera_x, 0)
        glow = pygame.Surface((offset.width + 18, offset.height + 18), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 255, 255, 100), (glow.get_width() // 2, glow.get_height() // 2), glow.get_width() // 2)
        surface.blit(glow, glow.get_rect(center=offset.center))
        blade = pygame.Rect(0, 0, 8, offset.height)
        blade.center = offset.center
        pygame.draw.rect(surface, WHITE, blade, border_radius=3)
        pygame.draw.rect(surface, CYAN, blade.inflate(-3, -3), border_radius=3)
        handle = pygame.Rect(0, 0, 18, 6)
        handle.center = (offset.centerx, offset.bottom - 4)
        pygame.draw.rect(surface, STEEL, handle, border_radius=3)


@dataclass
class ShieldPowerUp:
    rect: pygame.Rect
    pulse: float = field(default_factory=lambda: random.random() * math.tau)
    collected: bool = False

    def update(self, dt: float) -> None:
        self.pulse = (self.pulse + dt * 4.2) % math.tau

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        if self.collected:
            return
        offset = self.rect.move(-camera_x, 0)
        halo = pygame.Surface((offset.width + 24, offset.height + 24), pygame.SRCALPHA)
        halo_radius = halo.get_width() // 2
        alpha = int(130 + 70 * math.sin(self.pulse))
        pygame.draw.circle(halo, (120, 220, 255, alpha), (halo_radius, halo_radius), halo_radius)
        surface.blit(halo, halo.get_rect(center=offset.center))
        gem = pygame.Surface(offset.size, pygame.SRCALPHA)
        pygame.draw.ellipse(gem, pygame.Color(180, 240, 255, 220), gem.get_rect())
        crest = gem.get_rect().inflate(-10, -14)
        pygame.draw.ellipse(gem, pygame.Color(60, 110, 200, 210), crest, 4)
        pygame.draw.ellipse(gem, pygame.Color(255, 255, 255, 160), crest.inflate(-8, -10))
        surface.blit(gem, offset)

@dataclass
class GoalFlag:
    rect: pygame.Rect
    flutter: float = 0.0

    def update(self, dt: float) -> None:
        self.flutter = (self.flutter + dt * 5.0) % math.tau

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        offset = self.rect.move(-camera_x, 0)
        pygame.draw.rect(surface, WHITE,
                         (offset.x, offset.y - self.rect.height, 6, self.rect.height))
        flag_wave = int(16 * math.sin(self.flutter))
        flag_points = [
            (offset.x + 6, offset.y - self.rect.height + 10),
            (offset.x + 6 + 46 + flag_wave, offset.y - self.rect.height + 24),
            (offset.x + 6, offset.y - self.rect.height + 38),
        ]
        pygame.draw.polygon(surface, CYAN, flag_points)


def generate_level(stage: int, rng: random.Random, theme_index: int) -> dict:
    segment_count = 6 + stage * 2
    min_y = 260
    max_y = 520
    platform_height = 40
    base_bounce_chance = MIN_BOUNCY_CHANCE + 0.03 * stage
    bounce_multiplier = 1.0 + 0.05 * stage

    def mark_bouncy(platform: Platform, strength: float = 1.0) -> None:
        platform.is_bouncy = True
        platform.bounce_velocity = BOUNCE_VELOCITY * strength
        platform.colour = pygame.Color(BOUNCY_CORAL)

    def maybe_make_bouncy(platform: Platform, chance: float, strength: float = 1.0) -> None:
        if not platform.is_bouncy and rng.random() < chance:
            mark_bouncy(platform, strength)

    platforms: List[Platform] = []
    first_width = rng.randint(220, 280)
    first_rect = pygame.Rect(0, max_y, first_width, platform_height)
    platforms.append(Platform(first_rect))
    spawn_point = (first_rect.left + 36, first_rect.top - 60)
    current_right = first_rect.right
    current_y = first_rect.y

    for _ in range(segment_count):
        gap = rng.randint(70, 120 + stage * 20)
        width = rng.randint(160, 260 + stage * 20)
        delta_y = rng.randint(-80 - stage * 10, 80 + stage * 10)
        current_y = int(clamp(current_y + delta_y, min_y, max_y))
        rect = pygame.Rect(current_right + gap, current_y, width, platform_height)
        new_platform = Platform(rect)
        maybe_make_bouncy(new_platform, base_bounce_chance, bounce_multiplier)
        platforms.append(new_platform)
        current_right = rect.right

    final_gap = rng.randint(80, 140)
    final_width = rng.randint(220, 320)
    final_y = int(clamp(current_y + rng.randint(-60, 60), min_y, max_y))
    final_rect = pygame.Rect(current_right + final_gap, final_y, final_width, platform_height)
    platforms.append(Platform(final_rect))
    current_right = final_rect.right

    base_platforms = list(platforms)

    floating_platforms: List[Platform] = []
    for platform in base_platforms[1:-1]:
        if rng.random() < 0.35 + 0.08 * stage:
            float_width = rng.randint(90, 140)
            min_x = platform.rect.left + 20
            max_x = platform.rect.right - float_width - 20
            if max_x <= min_x:
                continue
            x = rng.randint(min_x, max_x)
            target_top = platform.rect.y - rng.randint(110, 170 + stage * 10)
            y = int(clamp(target_top, min_y - 160, platform.rect.y - 90))
            if platform.rect.y - y < 80:
                continue
            candidate_rect = pygame.Rect(x, y, float_width, 28)
            too_close = False
            for existing in platforms:
                overlap = min(candidate_rect.right, existing.rect.right) - max(candidate_rect.left, existing.rect.left)
                if overlap <= 0:
                    continue
                vertical_gap = existing.rect.top - candidate_rect.bottom
                if 0 <= vertical_gap < 100 and overlap > float_width * 0.6:
                    too_close = True
                    break
            if too_close:
                continue
            float_platform = Platform(candidate_rect)
            maybe_make_bouncy(float_platform, base_bounce_chance + 0.08, bounce_multiplier + 0.05)
            floating_platforms.append(float_platform)
    platforms.extend(floating_platforms)

    def create_horizontal_platform() -> MovingPlatform | None:
        anchor_choices = base_platforms[1:-1] if len(base_platforms) > 2 else base_platforms
        if not anchor_choices:
            return None
        anchor = rng.choice(anchor_choices)
        width = rng.randint(100, 140)
        left_bound = anchor.rect.left + 20
        right_bound = anchor.rect.right - width - 20
        if right_bound <= left_bound:
            return None
        start_x = rng.randint(left_bound, right_bound)
        height_offset = rng.randint(80, 150)
        y = max(min_y - 60, anchor.rect.y - height_offset)
        span_left = max(0, start_x - rng.randint(80, 160))
        span_right = min(current_right - 40, start_x + width + rng.randint(80, 160))
        if span_right - span_left <= width + 10:
            return None
        speed = 2.0 + 0.4 * stage
        mp = MovingPlatform(
            pygame.Rect(start_x, y, width, 26),
            bounds_x=(span_left, span_right),
            bounds_y=(y, y + 1),
            speed_x=speed,
            speed_y=0.0,
        )
        mp.colour = pygame.Color(160, 110, 90)
        for other in platforms:
            if mp.rect.colliderect(other.rect.inflate(-12, -12)):
                return None
        for other in moving_platforms:
            if mp.rect.colliderect(other.rect.inflate(-12, -12)):
                return None
        maybe_make_bouncy(mp, MOVING_BOUNCY_CHANCE, bounce_multiplier + 0.04)
        return mp

    def create_vertical_platform() -> MovingPlatform | None:
        candidates = base_platforms[1:-1] if len(base_platforms) > 2 else base_platforms
        if not candidates:
            return None
        anchor = rng.choice(candidates)
        width = rng.randint(90, 130)
        left_bound = anchor.rect.left + 20
        right_bound = anchor.rect.right - width - 20
        if right_bound <= left_bound:
            return None
        start_x = rng.randint(left_bound, right_bound)
        top = max(min_y - 200, anchor.rect.y - rng.randint(160, 220))
        bottom = anchor.rect.y - rng.randint(70, 110)
        if bottom - top < 60:
            return None
        start_y = rng.randint(top, bottom - 40)
        speed = 1.2 + 0.3 * stage
        mp = MovingPlatform(
            pygame.Rect(start_x, start_y, width, 26),
            bounds_x=(start_x, start_x + width),
            bounds_y=(top, bottom),
            speed_x=0.0,
            speed_y=speed,
        )
        mp.colour = pygame.Color(150, 105, 120)
        for other in platforms:
            if mp.rect.colliderect(other.rect.inflate(-12, -12)):
                return None
        for other in moving_platforms:
            if mp.rect.colliderect(other.rect.inflate(-12, -12)):
                return None
        maybe_make_bouncy(mp, MOVING_BOUNCY_CHANCE, bounce_multiplier + 0.06)
        return mp

    moving_platforms: List[MovingPlatform] = []

    def try_add(generator) -> bool:
        for _ in range(6):
            platform = generator()
            if not platform:
                continue
            overlap = any(platform.rect.colliderect(other.rect.inflate(-12, -12)) for other in moving_platforms)
            if overlap:
                continue
            moving_platforms.append(platform)
            return True
        return False

    if stage >= 1:
        try_add(create_horizontal_platform)
        try_add(create_vertical_platform)
    else:
        try_add(create_horizontal_platform)

    target_total = clamp(1 + stage, 1, 5)
    attempts = 0
    while len(moving_platforms) < target_total and attempts < target_total * 6:
        attempts += 1
        generator = create_vertical_platform if rng.random() < 0.4 else create_horizontal_platform
        try_add(generator)

    platforms_with_motion: List[Platform | MovingPlatform] = platforms + moving_platforms

    def has_low_headroom(surface: Platform | MovingPlatform, min_gap: int = 120) -> bool:
        surface_rect = surface.rect
        for other in platforms_with_motion:
            if other is surface:
                continue
            other_rect = other.rect
            if other_rect.top >= surface_rect.top:
                continue
            horizontal_overlap = min(surface_rect.right, other_rect.right) - max(surface_rect.left, other_rect.left)
            if horizontal_overlap <= 0:
                continue
            vertical_gap = surface_rect.top - other_rect.bottom
            if 0 <= vertical_gap < min_gap and horizontal_overlap > surface_rect.width * 0.4:
                return True
        return False

    enemies: List[Enemy] = []
    for platform in platforms[1:-1]:
        patrol_left = platform.rect.left + 12
        patrol_right = platform.rect.right - 12
        if patrol_right - patrol_left < 50:
            continue
        if rng.random() < 0.35 + 0.12 * stage and not has_low_headroom(platform, min_gap=110):
            size = 38 if stage == 0 else 42
            x = rng.randint(patrol_left, patrol_right - size)
            rect = pygame.Rect(x, platform.rect.y - size, size, size)
            speed = 1.3 + rng.random() * (0.6 + 0.4 * stage)
            tough = stage >= 1 and rng.random() < 0.35
            hp = 2 if tough else 1
            enemies.append(Enemy(rect, (patrol_left, patrol_right), speed=speed, health=hp, max_health=hp))

    solid_rects = [p.rect for p in platforms_with_motion]

    def area_is_clear(area: pygame.Rect, ignore: pygame.Rect | None = None) -> bool:
        for other in solid_rects:
            if other is ignore:
                continue
            if area.colliderect(other):
                return False
        return True

    def coin_rect_for(surface_rect: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(surface_rect.centerx - 14, surface_rect.top - 52, 28, 28)

    def has_coin_clearance(surface_rect: pygame.Rect) -> bool:
        coin_rect = coin_rect_for(surface_rect)
        expanded = coin_rect.inflate(6, 6)
        expanded.bottom = surface_rect.top - 4
        return area_is_clear(expanded, surface_rect)

    def is_surface_reachable(surface: Platform | MovingPlatform) -> bool:
        if surface in base_platforms:
            return True
        surface_rect = surface.rect
        max_vertical = 220 + stage * 10
        for anchor in platforms_with_motion:
            if anchor is surface:
                continue
            anchor_rect = anchor.rect
            if anchor_rect.top <= surface_rect.top:
                continue
            vertical_gap = anchor_rect.top - surface_rect.top
            if vertical_gap > max_vertical:
                continue
            if anchor_rect.right + 40 < surface_rect.left:
                continue
            if anchor_rect.left - 40 > surface_rect.right:
                continue
            return True
        return False

    surfaces = [s for s in platforms_with_motion if has_coin_clearance(s.rect) and is_surface_reachable(s)]
    if len(surfaces) < 5:
        fallback = [s for s in platforms_with_motion if is_surface_reachable(s)]
        surfaces = fallback or platforms_with_motion
    rng.shuffle(surfaces)
    desired_coins = min(len(surfaces), rng.randint(5, 6))
    coins: List[Coin] = []
    for surface in surfaces[:desired_coins]:
        if has_low_headroom(surface, min_gap=110):
            continue
        coins.append(Coin(coin_rect_for(surface.rect)))

    shooters: List[ShooterEnemy] = []
    shooter_goal = min(stage + 1, 3)
    shooter_candidates = [p for p in base_platforms[1:-1] if p.rect.width >= 120]
    rng.shuffle(shooter_candidates)
    for platform in shooter_candidates:
        clearance = pygame.Rect(platform.rect.left + 8, platform.rect.top - 120, platform.rect.width - 16, 120)
        clearance.bottom = platform.rect.top - 6
        if not area_is_clear(clearance, platform.rect):
            continue
        enemy_width = 46
        enemy_height = 52
        min_x = platform.rect.left + 20
        max_x = platform.rect.right - enemy_width - 20
        if max_x <= min_x:
            continue
        x = rng.randint(min_x, max_x)
        rect = pygame.Rect(x, platform.rect.top - enemy_height, enemy_width, enemy_height)
        shooters.append(ShooterEnemy(rect))
        if len(shooters) >= shooter_goal:
            break

    double_jump_orbs: List[DoubleJumpPowerUp] = []
    orb_candidates = [p for p in platforms_with_motion if has_coin_clearance(p.rect) and is_surface_reachable(p)]
    rng.shuffle(orb_candidates)
    for platform in orb_candidates:
        pu_rect = pygame.Rect(platform.rect.centerx - 18, platform.rect.top - 60, 36, 36)
        aura = pu_rect.inflate(10, 10)
        aura.bottom = platform.rect.top - 8
        if not area_is_clear(aura, platform.rect):
            continue
        if has_low_headroom(platform, min_gap=130):
            continue
        double_jump_orbs.append(DoubleJumpPowerUp(pu_rect))
        break
    if not double_jump_orbs:
        anchor = platforms[len(platforms) // 2]
        if not has_low_headroom(anchor, min_gap=130):
            double_jump_orbs.append(DoubleJumpPowerUp(pygame.Rect(anchor.rect.centerx - 18, anchor.rect.top - 60, 36, 36)))

    shield_tokens: List[ShieldPowerUp] = []
    shield_candidates = [p for p in platforms_with_motion if has_coin_clearance(p.rect)]
    rng.shuffle(shield_candidates)
    for platform in shield_candidates:
        shield_rect = pygame.Rect(platform.rect.centerx - 20, platform.rect.top - 62, 40, 40)
        aura = shield_rect.inflate(12, 12)
        aura.bottom = platform.rect.top - 6
        if not area_is_clear(aura, platform.rect):
            continue
        if any(shield_rect.colliderect(orb.rect) for orb in double_jump_orbs):
            continue
        if has_low_headroom(platform, min_gap=120):
            continue
        shield_tokens.append(ShieldPowerUp(shield_rect))
        break

    sword_tokens: List[SwordPowerUp] = []
    sword_candidates = [p for p in platforms_with_motion if has_coin_clearance(p.rect) and is_surface_reachable(p)]
    rng.shuffle(sword_candidates)
    for platform in sword_candidates:
        sword_rect = pygame.Rect(platform.rect.centerx - 16, platform.rect.top - 56, 32, 32)
        aura = sword_rect.inflate(8, 8)
        aura.bottom = platform.rect.top - 6
        if not area_is_clear(aura, platform.rect):
            continue
        if has_low_headroom(platform, min_gap=120):
            continue
        sword_tokens.append(SwordPowerUp(sword_rect))
        break

    final_platform = platforms[-1]
    goal_rect = pygame.Rect(final_platform.rect.right - 48, final_platform.rect.y, 32, 80)
    goal = GoalFlag(goal_rect)

    tallest = max([p.rect.bottom for p in platforms] + [mp.rect.bottom for mp in moving_platforms] + [final_rect.bottom])
    kill_plane = tallest + 240
    level_length = max(current_right + 180, SCREEN_WIDTH)

    return {
        "platforms": platforms,
        "moving_platforms": moving_platforms,
        "enemies": enemies,
        "shooters": shooters,
        "double_jump": double_jump_orbs,
        "swords": sword_tokens,
        "shields": shield_tokens,
        "coins": coins,
        "goal": goal,
        "spawn_point": spawn_point,
        "kill_plane": kill_plane,
        "length": level_length,
        "theme": theme_index,
        "is_boss": False,
        "boss": None,
    }


def generate_boss_level(stage: int, rng: random.Random, theme_index: int) -> dict:
    level_length = 1280
    base_y = 520
    platform_height = 44

    def make_platform(rect: pygame.Rect, *, bouncy: bool = False, strength: float = 1.0) -> Platform:
        platform = Platform(rect)
        if bouncy:
            platform.is_bouncy = True
            platform.bounce_velocity = BOUNCE_VELOCITY * strength
            platform.colour = pygame.Color(BOUNCY_CORAL)
        return platform

    platforms: List[Platform] = [
        make_platform(pygame.Rect(0, base_y, 320, platform_height)),
        make_platform(pygame.Rect(360, base_y, 320, platform_height)),
        make_platform(pygame.Rect(720, base_y, 320, platform_height)),
    ]

    bounce_strength = 1.12
    bounce_pad_left = make_platform(pygame.Rect(90, base_y - 70, 120, 30), bouncy=True, strength=bounce_strength)
    bounce_pad_right = make_platform(pygame.Rect(820, base_y - 70, 120, 30), bouncy=True, strength=bounce_strength + 0.05)
    elevated = make_platform(pygame.Rect(480, base_y - 150, 160, 28))

    platforms.extend([bounce_pad_left, bounce_pad_right, elevated])

    moving_platforms: List[MovingPlatform] = []

    vertical_platform = MovingPlatform(
        pygame.Rect(560, base_y - 220, 130, 26),
        bounds_x=(560, 560 + 130),
        bounds_y=(base_y - 300, base_y - 80),
        speed_x=0.0,
        speed_y=2.3,
        is_bouncy=True,
        bounce_velocity=BOUNCE_VELOCITY * 1.1,
    )
    vertical_platform.colour = pygame.Color(200, 150, 255)
    moving_platforms.append(vertical_platform)

    horizontal_platform = MovingPlatform(
        pygame.Rect(280, base_y - 210, 140, 26),
        bounds_x=(160, level_length - 260),
        bounds_y=(base_y - 210, base_y - 180),
        speed_x=2.6,
        speed_y=0.0,
        is_bouncy=False,
    )
    horizontal_platform.colour = pygame.Color(180, 120, 200)
    moving_platforms.append(horizontal_platform)

    aerial_pad = MovingPlatform(
        pygame.Rect(900, base_y - 260, 120, 24),
        bounds_x=(780, level_length - 180),
        bounds_y=(base_y - 320, base_y - 240),
        speed_x=2.1,
        speed_y=0.0,
        is_bouncy=True,
        bounce_velocity=BOUNCE_VELOCITY * 1.05,
    )
    aerial_pad.colour = pygame.Color(230, 170, 220)
    moving_platforms.append(aerial_pad)

    spawn_point = (platforms[0].rect.left + 48, platforms[0].rect.top - 60)

    double_jump_orbs = [
        DoubleJumpPowerUp(pygame.Rect(360, base_y - 220, 36, 36)),
        DoubleJumpPowerUp(pygame.Rect(980, base_y - 320, 36, 36)),
    ]

    sword_tokens = [
        SwordPowerUp(pygame.Rect(640, base_y - 260, 32, 32)),
        SwordPowerUp(pygame.Rect(220, base_y - 200, 32, 32)),
    ]

    shield_tokens = [
        ShieldPowerUp(pygame.Rect(500, base_y - 220, 38, 38)),
        ShieldPowerUp(pygame.Rect(1030, base_y - 280, 38, 38)),
    ]

    coins: List[Coin] = []
    for anchor in (bounce_pad_left, bounce_pad_right, elevated):
        coin_rect = pygame.Rect(anchor.rect.centerx - 14, anchor.rect.top - 50, 28, 28)
        coins.append(Coin(coin_rect))

    goal = GoalFlag(pygame.Rect(level_length - 120, base_y, 32, 80))
    kill_plane = SCREEN_HEIGHT + 220

    anchors = [
        pygame.Vector2(600, base_y - 260),
        pygame.Vector2(860, base_y - 280),
        pygame.Vector2(380, base_y - 250),
        pygame.Vector2(620, base_y - 340),
    ]

    boss_rect = pygame.Rect(0, 0, 96, 96)
    boss_rect.center = (620, base_y - 280)
    boss = Boss(boss_rect, anchors, health=6, speed=200.0, attack_cooldown=2.2)

    return {
        "platforms": platforms,
        "moving_platforms": moving_platforms,
        "enemies": [],
        "shooters": [],
        "double_jump": double_jump_orbs,
        "swords": sword_tokens,
        "shields": shield_tokens,
        "coins": coins,
        "goal": goal,
        "spawn_point": spawn_point,
        "kill_plane": kill_plane,
        "length": level_length,
        "theme": theme_index,
        "is_boss": True,
        "boss": boss,
    }

def generate_level_pack(count: int, seed: int | None = None) -> List[dict]:
    rng = random.Random(seed)
    themes = [i % len(BACKGROUND_THEMES) for i in range(count)]
    rng.shuffle(themes)
    if count <= 0:
        return []
    boss_index = rng.randrange(1, count) if count > 1 else 0
    pack: List[dict] = []
    for stage in range(count):
        theme_index = themes[stage]
        if stage == boss_index:
            pack.append(generate_boss_level(stage, rng, theme_index))
        else:
            pack.append(generate_level(stage, rng, theme_index))
    return pack


# ---------------------------------------------------------------------------
# Camera and sky rendering
# ---------------------------------------------------------------------------

class Camera:
    def __init__(self) -> None:
        self.x = 0.0

    def update(self, target_x: float, level_length: float) -> None:
        max_offset = max(0.0, level_length - SCREEN_WIDTH)
        desired = clamp(target_x - SCREEN_WIDTH / 2, 0, max_offset)
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
        self.theme_gradients: List[pygame.Surface] = []
        self.theme_star_colours: List[pygame.Color] = []
        self.theme_moons: List[pygame.Color] = []
        for theme in BACKGROUND_THEMES:
            gradient = pygame.Surface((width, height)).convert()
            for y in range(height):
                blend = y / height
                colour = pygame.Color(
                    int(lerp(theme["top"].r, theme["bottom"].r, blend)),
                    int(lerp(theme["top"].g, theme["bottom"].g, blend)),
                    int(lerp(theme["top"].b, theme["bottom"].b, blend)),
                )
                pygame.draw.line(gradient, colour, (0, y), (width, y))
            self.theme_gradients.append(gradient)
            self.theme_star_colours.append(theme["stars"])
            self.theme_moons.append(theme["moon"])
        self.theme_index = 0

    def update(self, dt: float) -> None:
        self.timer += dt

    def set_theme(self, index: int) -> None:
        if not self.theme_gradients:
            return
        self.theme_index = index % len(self.theme_gradients)

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        gradient = self.theme_gradients[self.theme_index]
        surface.blit(gradient, (0, 0))

        moon_x = int((camera_x * 0.2) % (self.width + 200) - 100)
        pygame.draw.circle(surface, self.theme_moons[self.theme_index], (moon_x, 120), 38)
        pygame.draw.circle(surface, pygame.Color(255, 255, 255, 220), (moon_x - 12, 110), 9)

        star_colour = self.theme_star_colours[self.theme_index]
        for pos, radius, twinkle in self.stars:
            twinkle_factor = (math.sin(self.timer * twinkle + pos.x) + 1) * 0.5
            intensity = 0.35 + 0.65 * twinkle_factor
            colour = pygame.Color(
                int(clamp(star_colour.r * intensity, 0, 255)),
                int(clamp(star_colour.g * intensity, 0, 255)),
                int(clamp(star_colour.b * intensity, 0, 255)),
            )
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
    def __init__(self, stage_count: int = 3) -> None:
        self.stage_count = stage_count
        self.level_index = 0
        self.level_blueprints: List[dict] = []
        self.platforms: List[Platform] = []
        self.moving_platforms: List[MovingPlatform] = []
        self.enemies: List[Enemy] = []
        self.shooters: List[ShooterEnemy] = []
        self.double_jump_orbs: List[DoubleJumpPowerUp] = []
        self.sword_tokens: List[SwordPowerUp] = []
        self.shield_tokens: List[ShieldPowerUp] = []
        self.coins: List[Coin] = []
        self.goal = GoalFlag(pygame.Rect(0, 0, 32, 80))
        self.spawn_point: Tuple[int, int] = (80, 420)
        self.kill_plane = SCREEN_HEIGHT + 200
        self.level_length = SCREEN_WIDTH
        self.total_levels = stage_count
        self.theme_index = 0
        self.boss: Boss | None = None
        self.boss_victory_timer: float = 0.0
        self._boss_transition_pending: bool = False
        self.boss_level_index: int = 0
        self._is_boss_level: bool = False
        self.sword_spawn_points: List[pygame.Rect] = []
        self.sword_spawn_timer: float = 0.0
        self.sword_spawn_index: int = 0
        self.generate_new_levels()

    def generate_new_levels(self, seed: int | None = None) -> None:
        seed_value = seed if seed is not None else random.randrange(1 << 30)
        self.level_blueprints = generate_level_pack(self.stage_count, seed_value)
        self.total_levels = len(self.level_blueprints)
        self.level_index = 0
        self.boss_level_index = next(
            (i for i, blueprint in enumerate(self.level_blueprints) if blueprint.get("is_boss")), -1
        )
        self.reset_level()

    def reset_level(self) -> None:
        data = self.level_blueprints[self.level_index]
        self.platforms = [clone_platform(p) for p in data["platforms"]]
        self.moving_platforms = [clone_platform(mp) for mp in data["moving_platforms"]]
        self.enemies = [
            Enemy(
                e.rect.copy(),
                e.patrol,
                e.speed,
                e.direction,
                e.health,
                e.max_health,
                e.invulnerable,
                e.stomped,
                e.death_timer,
            )
            for e in data["enemies"]
        ]
        self.shooters = [
            ShooterEnemy(s.rect.copy(), s.facing, s.fire_rate, s.cooldown, s.stomped, s.death_timer, s.pulse)
            for s in data["shooters"]
        ]
        self.double_jump_orbs = []
        for orb in data["double_jump"]:
            clone = DoubleJumpPowerUp(orb.rect.copy())
            clone.pulse = orb.pulse
            self.double_jump_orbs.append(clone)
        raw_swords = data.get("swords", [])
        self.sword_tokens = []
        self.coins = []
        for c in data["coins"]:
            coin = Coin(c.rect.copy())
            coin.pulse = c.pulse
            self.coins.append(coin)
        goal = data["goal"]
        self.goal = GoalFlag(goal.rect.copy())
        self.spawn_point = data["spawn_point"]
        self.kill_plane = data["kill_plane"]
        self.level_length = data["length"]
        self.theme_index = data.get("theme", 0)
        self.shield_tokens = []
        for shield in data.get("shields", []):
            clone = ShieldPowerUp(shield.rect.copy())
            clone.pulse = shield.pulse
            self.shield_tokens.append(clone)
        self._is_boss_level = data.get("is_boss", False)
        self.sword_spawn_points = []
        self.sword_spawn_index = 0
        self.sword_spawn_timer = 0.0
        if self._is_boss_level:
            self.sword_spawn_points = [s.rect.copy() for s in raw_swords]
            self.sword_tokens = []
            if self.sword_spawn_points:
                self._spawn_boss_sword(initial=True)
        else:
            for sword in raw_swords:
                clone = SwordPowerUp(sword.rect.copy())
                clone.pulse = sword.pulse
                self.sword_tokens.append(clone)
        boss_template = data.get("boss")
        self.boss = boss_template.clone() if boss_template else None
        self.boss_victory_timer = 0.0
        self._boss_transition_pending = False

    def _spawn_boss_sword(self, *, initial: bool = False) -> None:
        if not self.sword_spawn_points:
            return
        slot = self.sword_spawn_points[self.sword_spawn_index % len(self.sword_spawn_points)]
        sword = SwordPowerUp(slot.copy())
        sword.pulse = random.random() * math.tau
        self.sword_tokens.append(sword)
        self.sword_spawn_index = (self.sword_spawn_index + 1) % max(1, len(self.sword_spawn_points))
        self.sword_spawn_timer = 3.0 if not initial else 2.0

    @property
    def all_platforms(self) -> List[Platform]:
        return self.platforms + self.moving_platforms

    @property
    def powerups(self) -> List[DoubleJumpPowerUp | SwordPowerUp | ShieldPowerUp]:
        return [*self.double_jump_orbs, *self.sword_tokens, *self.shield_tokens]

    def update(self, dt: float, player_rect: pygame.Rect) -> List[Projectile]:
        spawned: List[Projectile] = []
        static_rects = [platform.rect for platform in self.platforms]
        moving_rects = [mp.rect for mp in self.moving_platforms]
        for index, platform in enumerate(self.moving_platforms):
            obstacles = static_rects + [moving_rects[i] for i in range(len(self.moving_platforms)) if i != index]
            platform.update(dt, obstacles)
            moving_rects[index] = platform.rect
        self.enemies = [enemy for enemy in self.enemies if enemy.update(dt)]
        updated_shooters: List[ShooterEnemy] = []
        for shooter in self.shooters:
            alive, new_projectiles = shooter.update(dt, player_rect.centerx)
            spawned.extend(new_projectiles)
            if alive:
                updated_shooters.append(shooter)
        self.shooters = updated_shooters
        for orb in self.double_jump_orbs:
            orb.update(dt)
        for sword in list(self.sword_tokens):
            sword.update(dt)
        if self._is_boss_level:
            collected_any = False
            for sword in list(self.sword_tokens):
                if sword.collected:
                    self.sword_tokens.remove(sword)
                    collected_any = True
            if collected_any:
                self.sword_spawn_timer = max(self.sword_spawn_timer, 2.2)
            if not self.sword_tokens and self.sword_spawn_points:
                if self.sword_spawn_timer > 0:
                    self.sword_spawn_timer = max(0.0, self.sword_spawn_timer - dt)
                else:
                    self._spawn_boss_sword()
        for shield in self.shield_tokens:
            if not shield.collected:
                shield.update(dt)
        if self.boss:
            _, boss_projectiles = self.boss.update(dt, player_rect)
            spawned.extend(boss_projectiles)
        if self.goal:
            self.goal.update(dt)
        if self.boss and self.boss.defeated and self._boss_transition_pending and self.boss_victory_timer > 0:
            self.boss_victory_timer = max(0.0, self.boss_victory_timer - dt)
        return spawned

    def remaining_coins(self) -> int:
        return sum(not coin.collected for coin in self.coins)

    def advance(self) -> bool:
        if self.level_index + 1 < self.total_levels:
            self.level_index += 1
            self.reset_level()
            return True
        return False

    def is_boss_stage(self) -> bool:
        return self._is_boss_level

    def on_boss_hit(self) -> None:
        if self.boss and self.boss.defeated:
            self._boss_transition_pending = True
            self.boss_victory_timer = max(self.boss_victory_timer, 1.4)

    def consume_boss_transition(self) -> bool:
        if self._boss_transition_pending and self.boss_victory_timer == 0.0:
            self._boss_transition_pending = False
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
        self.hard_mode = False
        self.levels = LevelManager()
        spawn_x, spawn_y = self.levels.spawn_point
        self.player = Player(pygame.Rect(spawn_x, spawn_y, 44, 60))
        self.particles: List[Particle] = []
        self.projectiles: List[Projectile] = []
        self.slashes: List[SwordBeam] = []
        self.jump_spheres: List[JumpSphereEffect] = []
        self.score = 0
        self.combo_timer = 0.0
        self.time_elapsed = 0.0
        self.max_lives = 3
        self.lives = self.max_lives
        self.jump_was_pressed = False
        self.attack_was_pressed = False
        self.nova_was_pressed = False
        self.combo_nova_ready = False
        self.combo_nova_cooldown = 0.0
        self.sky.set_theme(self.levels.theme_index)

    # ---------------------------- State transitions ---------------------
    def start_game(self) -> None:
        self.state = GameState.PLAYING
        self.levels.generate_new_levels()
        spawn_x, spawn_y = self.levels.spawn_point
        self.player = Player(pygame.Rect(spawn_x, spawn_y, 44, 60))
        self.particles.clear()
        self.projectiles.clear()
        self.slashes.clear()
        self.jump_spheres.clear()
        self.score = 0
        self.combo_timer = 0.0
        self.time_elapsed = 0.0
        self.lives = self.max_lives
        self.camera.x = 0
        self.jump_was_pressed = False
        self.attack_was_pressed = False
        self.nova_was_pressed = False
        self.combo_nova_ready = False
        self.combo_nova_cooldown = 0.0
        self.sky.set_theme(self.levels.theme_index)

    def pause(self) -> None:
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
        elif self.state == GameState.PAUSED:
            self.state = GameState.PLAYING

    def game_over(self) -> None:
        self.state = GameState.GAME_OVER

    def victory(self) -> None:
        self.state = GameState.VICTORY

    def lose_life(self, reason: str) -> None:
        if self.state != GameState.PLAYING or self.player.invincible_timer > 0:
            return
        self.lives -= 1
        if self.lives <= 0:
            self.lives = 0
            self.game_over()
            return
        self._apply_damage_penalties()
        if self.hard_mode:
            self._restart_level_after_life_loss()
            return
        if reason == "fall":
            self._respawn_at_spawn()
            return
        self._phase_player_after_hit()

    def _apply_damage_penalties(self) -> None:
        self.combo_timer = 0.0
        self.player.combo = 0
        self.player.double_jump_stock = 0
        self.player.sword_ready = False
        self.player.sword_cooldown = 0.0
        self.player.sword_charges = 0
        self.player.shield_charges = 0
        self.combo_nova_ready = False
        self.combo_nova_cooldown = 0.0
        self.player.vel.xy = (0, 0)
        self.player.on_ground = False
        self.player.invincible_timer = 0.0
        self.jump_was_pressed = False
        self.attack_was_pressed = False
        self.nova_was_pressed = False

    def _restart_level_after_life_loss(self) -> None:
        self.player.invincible_timer = 1.2
        self.levels.reset_level()
        spawn_x, spawn_y = self.levels.spawn_point
        self.player.set_position((spawn_x, spawn_y))
        self.time_elapsed = 0.0
        self.camera.x = 0
        self.projectiles.clear()
        self.slashes.clear()
        self.particles.clear()
        self.jump_spheres.clear()
        self.particles.extend(self._sparkle_effect(self.player.rect.midbottom))
        self.sky.set_theme(self.levels.theme_index)

    def _respawn_at_spawn(self) -> None:
        spawn_x, spawn_y = self.levels.spawn_point
        self.player.set_position((spawn_x, spawn_y))
        self.player.invincible_timer = max(self.player.invincible_timer, FALL_RESPAWN_INVULN)
        self.camera.x = 0
        self.particles.extend(self._sparkle_effect(self.player.rect.midbottom))

    def _phase_player_after_hit(self) -> None:
        self.player.invincible_timer = max(self.player.invincible_timer, HIT_INVINC_DURATION)
        self.particles.extend(self._sparkle_effect(self.player.rect.midbottom))

    # ------------------------------ Update ------------------------------
    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        if self.state == GameState.PLAYING:
            self.time_elapsed += dt
            if self.combo_nova_cooldown > 0:
                self.combo_nova_cooldown = max(0.0, self.combo_nova_cooldown - dt)
            nova_pressed = keys[pygame.K_e]
            if (
                nova_pressed
                and not self.nova_was_pressed
                and self.combo_nova_ready
                and self.combo_nova_cooldown <= 0
            ):
                self._trigger_combo_nova()
            self.nova_was_pressed = nova_pressed
            direction = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                direction -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                direction += 1
            self.player.move(direction, dt)

            jump_pressed = keys[pygame.K_UP] or keys[pygame.K_SPACE] or keys[pygame.K_w]
            if jump_pressed and not self.jump_was_pressed and self.player.jump():
                self.particles.extend(self.player.emit_jump_particles())
                self.particles.extend(self.player.emit_wind_gust())
                if self.player.consume_double_jump_effect():
                    centre = pygame.Vector2(self.player.rect.centerx, self.player.rect.bottom + 12)
                    self.jump_spheres.append(
                        JumpSphereEffect(
                            centre=centre,
                            width=self.player.rect.width + 36,
                            height=28,
                        )
                    )
            self.jump_was_pressed = jump_pressed

            attack_pressed = keys[pygame.K_LSHIFT]
            if (
                attack_pressed
                and not self.attack_was_pressed
                and self.player.sword_ready
                and self.player.sword_cooldown <= 0
                and self.player.sword_charges > 0
            ):
                slash = self.player.perform_sword_attack()
                self.slashes.append(slash)
                self.particles.extend(self._sparkle_effect(slash.rect.center))
                self._apply_slash_damage(slash)
            self.attack_was_pressed = attack_pressed

            new_particles = self.player.update(self.levels.all_platforms, dt)
            self.particles.extend(new_particles)

            if self.player.rect.top > self.levels.kill_plane:
                self.lose_life("fall")
                return

            spawned_projectiles = self.levels.update(dt, self.player.rect)
            if spawned_projectiles:
                self.projectiles.extend(spawned_projectiles)

            boss_centre = self.levels.boss.rect.center if self.levels.boss else None
            if self.levels.consume_boss_transition():
                if self.levels.advance():
                    self._transition_to_next_level(boss_centre)
                else:
                    self.victory()
                return

            self.update_projectiles(dt)
            self.update_slashes(dt)
            self.handle_collisions(dt)
            if self.state != GameState.PLAYING:
                return

            self.update_particles(dt)
            self.update_jump_spheres(dt)
            self.camera.update(self.player.rect.centerx, self.levels.level_length)
            self.sky.update(dt)
            self.update_combo_timer(dt)
        else:
            self.sky.update(dt)
            self.update_particles(dt)
            self.update_jump_spheres(dt)
            if self.projectiles:
                self.update_projectiles(dt)
            if self.slashes:
                self.update_slashes(dt)
            self.nova_was_pressed = False

    def update_projectiles(self, dt: float) -> None:
        level_rects = [platform.rect for platform in self.levels.all_platforms]
        for projectile in list(self.projectiles):
            if not projectile.update(dt):
                self.projectiles.remove(projectile)
                continue
            rect = projectile.rect
            if rect.right < -160 or rect.left > self.levels.level_length + 220 or rect.top > SCREEN_HEIGHT + 220 or rect.bottom < -220:
                self.projectiles.remove(projectile)
                continue
            if any(rect.colliderect(platform_rect) for platform_rect in level_rects):
                self.projectiles.remove(projectile)
                self.particles.extend(self._sparkle_effect(rect.center))

    def update_slashes(self, dt: float) -> None:
        for slash in list(self.slashes):
            if not slash.update(dt):
                self.slashes.remove(slash)
                continue
            self._apply_slash_damage(slash)

    def update_particles(self, dt: float) -> None:
        for particle in list(self.particles):
            particle.update(dt)
            if particle.life <= 0:
                self.particles.remove(particle)

    def update_jump_spheres(self, dt: float) -> None:
        for sphere in list(self.jump_spheres):
            if not sphere.update(dt):
                self.jump_spheres.remove(sphere)

    def update_combo_timer(self, dt: float) -> None:
        if self.combo_timer > 0:
            self.combo_timer = max(0.0, self.combo_timer - dt)
            if self.combo_timer == 0:
                self.player.combo = 0

    def _apply_slash_damage(self, slash: SwordBeam) -> None:
        hitbox = slash.rect.inflate(24, 12)
        scored = False
        for enemy in self.levels.enemies:
            if enemy.stomped:
                continue
            if not hitbox.colliderect(enemy.rect):
                continue
            outcome = enemy.take_hit()
            if outcome == "ignored":
                continue
            if outcome == "killed":
                scored = True
                self.add_score(150, combo_bonus=True)
            elif outcome == "damaged":
                scored = True
                self.score += 40
            self.particles.extend(self._sparkle_effect(enemy.rect.center))
        for shooter in self.levels.shooters:
            if shooter.stomped:
                continue
            if hitbox.colliderect(shooter.rect):
                shooter.stomped = True
                shooter.death_timer = ENEMY_DEATH_DURATION
                scored = True
                self.add_score(200, combo_bonus=True)
        for projectile in list(self.projectiles):
            if hitbox.colliderect(projectile.rect):
                self.projectiles.remove(projectile)
                self.particles.extend(self._sparkle_effect(projectile.rect.center))
                scored = True
        boss = self.levels.boss
        if boss and not boss.defeated:
            boss_hitbox = boss.rect.inflate(-12, -12)
            if hitbox.colliderect(boss_hitbox):
                if boss.take_hit():
                    scored = True
                    self.add_score(450, combo_bonus=True)
                    self.particles.extend(self._sparkle_effect(boss.rect.center))
                    self.levels.on_boss_hit()
        if scored:
            centre = hitbox.center
            self.particles.extend(self._sparkle_effect(centre))

    # --------------------------- Collision logic ------------------------
    def handle_collisions(self, dt: float) -> None:
        player_rect = self.player.rect

        for enemy in self.levels.enemies:
            if enemy.stomped:
                continue
            if player_rect.colliderect(enemy.rect):
                landed = self.player.vel.y > 0 and player_rect.bottom - enemy.rect.top < 22
                if landed:
                    self.player.vel.y = PLAYER_JUMP * 0.6
                    self.player.on_ground = False
                    self.player.rect.bottom = enemy.rect.top
                    self.player._float_pos.y = float(self.player.rect.y)
                    self.player.invincible_timer = max(self.player.invincible_timer, STOMP_PROTECT_DURATION)
                    outcome = enemy.take_hit()
                    if outcome == "killed":
                        self.add_score(150, combo_bonus=True)
                        self.particles.extend(self.player.emit_jump_particles())
                    elif outcome == "damaged":
                        self.score += 40
                        self.particles.extend(self._sparkle_effect(enemy.rect.center))
                elif self.player.invincible_timer <= 0:
                    if self._absorb_hit("enemy", player_rect.midtop):
                        continue
                    self.lose_life("enemy")
                    return

        for shooter in self.levels.shooters:
            if shooter.stomped:
                continue
            if player_rect.colliderect(shooter.rect):
                landed = self.player.vel.y > 0 and player_rect.bottom - shooter.rect.top < 24
                if landed:
                    shooter.stomped = True
                    shooter.death_timer = ENEMY_DEATH_DURATION
                    self.player.vel.y = PLAYER_JUMP * 0.65
                    self.player.on_ground = False
                    self.add_score(200, combo_bonus=True)
                    self.particles.extend(self.player.emit_jump_particles())
                elif self.player.invincible_timer <= 0:
                    if self._absorb_hit("laser", shooter.rect.midtop):
                        continue
                    self.lose_life("laser")
                    return

        player_hitbox = player_rect.inflate(-12, -6)
        for projectile in list(self.projectiles):
            if projectile.rect.colliderect(player_hitbox):
                self.projectiles.remove(projectile)
                if self.player.invincible_timer <= 0:
                    if self._absorb_hit("projectile", projectile.rect.center):
                        continue
                    self.lose_life("projectile")
                return

        boss = self.levels.boss
        if boss and not boss.defeated:
            boss_body = boss.rect.inflate(-18, -18)
            if player_hitbox.colliderect(boss_body):
                if self.player.invincible_timer <= 0:
                    if not self._absorb_hit("boss", boss.rect.center):
                        self.lose_life("boss")
                return

        for coin in self.levels.coins:
            coin.update(dt)
            if not coin.collected and player_rect.colliderect(coin.rect):
                coin.collected = True
                self.add_score(100, combo_bonus=True)
                self.particles.extend(self._sparkle_effect(coin.rect.center))

        for orb in self.levels.double_jump_orbs:
            if orb.collected:
                continue
            if player_hitbox.colliderect(orb.rect.inflate(6, 6)):
                orb.collected = True
                self.player.grant_double_jump()
                self.particles.extend(self._sparkle_effect(orb.rect.center))
                self.add_score(50)

        for sword in self.levels.sword_tokens:
            if sword.collected:
                continue
            if player_hitbox.colliderect(sword.rect.inflate(6, 6)):
                sword.collected = True
                self.player.grant_sword()
                self.particles.extend(self._sparkle_effect(sword.rect.center))
                self.add_score(75)

        for shield in self.levels.shield_tokens:
            if shield.collected:
                continue
            if player_hitbox.colliderect(shield.rect.inflate(6, 6)):
                shield.collected = True
                self.player.add_shield()
                self.particles.extend(self._shield_pickup_effect(shield.rect.center))
                self.add_score(60)

        goal_ready = self.levels.remaining_coins() == 0
        if self.levels.is_boss_stage():
            goal_ready = goal_ready and (boss is None or boss.defeated)
        if goal_ready and player_rect.colliderect(self.levels.goal.rect.inflate(40, 40)):
            bonus = max(0, int(2500 - self.time_elapsed * 30))
            self.add_score(500 + bonus)
            if self.levels.advance():
                self._transition_to_next_level(self.levels.goal.rect.midtop)
            else:
                self.victory()

    def add_score(self, base: int, *, combo_bonus: bool = False) -> None:
        if combo_bonus:
            if self.combo_timer > 0:
                self.player.combo += 1
            else:
                self.player.combo = 1
            combo_multiplier = 1 + 0.5 * (self.player.combo - 1)
            gained = int(base * combo_multiplier)
            self.combo_timer = 2.5
            if self.player.combo >= 5 and not self.combo_nova_ready:
                self.combo_nova_ready = True
        else:
            gained = base
        self.score += gained

    def _transition_to_next_level(self, sparkle_pos: Tuple[int, int] | None = None) -> None:
        spawn_x, spawn_y = self.levels.spawn_point
        self.player.set_position((spawn_x, spawn_y))
        self.player.vel.xy = (0, 0)
        self.player.on_ground = False
        self.player.double_jump_stock = 0
        self.player.sword_charges = 0
        self.player.sword_ready = False
        self.player.sword_cooldown = 0.0
        self.player.shield_charges = 0
        self.camera.x = 0
        self.time_elapsed = 0.0
        self.projectiles.clear()
        self.slashes.clear()
        self.jump_spheres.clear()
        self.combo_timer = 0.0
        self.player.combo = 0
        if sparkle_pos:
            self.particles.extend(self._sparkle_effect(sparkle_pos))
        self.sky.set_theme(self.levels.theme_index)
        self.jump_was_pressed = False
        self.attack_was_pressed = False
        self.nova_was_pressed = False

    def _shield_pickup_effect(self, pos: Tuple[int, int]) -> List[Particle]:
        particles: List[Particle] = []
        for _ in range(14):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(140, 240)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            particles.append(
                Particle(
                    pos=pygame.Vector2(pos),
                    vel=vel,
                    life=random.uniform(0.35, 0.6),
                    colour=pygame.Color(140, 230, 255),
                    radius=random.uniform(2.5, 4.5),
                )
            )
        return particles

    def _shield_break_effect(self, pos: Tuple[int, int]) -> List[Particle]:
        particles: List[Particle] = []
        for _ in range(20):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(200, 320)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            particles.append(
                Particle(
                    pos=pygame.Vector2(pos),
                    vel=vel,
                    life=random.uniform(0.25, 0.5),
                    colour=pygame.Color(120, 200, 255),
                    radius=random.uniform(2.0, 4.0),
                )
            )
        return particles

    def _absorb_hit(self, reason: str, impact_pos: Tuple[int, int]) -> bool:
        if not self.player.consume_shield():
            return False
        self.player.invincible_timer = max(self.player.invincible_timer, 0.6)
        self.particles.extend(self._shield_break_effect(impact_pos))
        return True

    def _trigger_combo_nova(self) -> None:
        if not self.combo_nova_ready:
            return
        centre = pygame.Vector2(self.player.rect.center)
        radius = COMBO_NOVA_RADIUS
        self.combo_nova_ready = False
        self.combo_nova_cooldown = 8.0
        self.player.combo = 0
        self.combo_timer = 0.0
        self.jump_spheres.append(
            JumpSphereEffect(
                centre=centre.copy(),
                width=radius * 1.6,
                height=radius * 0.9,
                timer=0.55,
                lifetime=0.55,
            )
        )
        defeated = 0
        for enemy in self.levels.enemies:
            if enemy.stomped:
                continue
            distance = pygame.Vector2(enemy.rect.center).distance_to(centre)
            if distance <= radius:
                enemy.health = 0
                enemy.stomped = True
                enemy.death_timer = ENEMY_DEATH_DURATION
                defeated += 1
                self.particles.extend(self._sparkle_effect(enemy.rect.center))
        for shooter in self.levels.shooters:
            if shooter.stomped:
                continue
            distance = pygame.Vector2(shooter.rect.center).distance_to(centre)
            if distance <= radius:
                shooter.stomped = True
                shooter.death_timer = ENEMY_DEATH_DURATION
                defeated += 1
                self.particles.extend(self._sparkle_effect(shooter.rect.center))
        for projectile in list(self.projectiles):
            distance = pygame.Vector2(projectile.rect.center).distance_to(centre)
            if distance <= radius:
                self.projectiles.remove(projectile)
                self.particles.extend(self._sparkle_effect(projectile.rect.center))
        if defeated > 0:
            self.add_score(200 * defeated)
        self.particles.extend(self._sparkle_effect((int(centre.x), int(centre.y))))

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
        for shooter in self.levels.shooters:
            shooter.draw(self.screen, self.camera.x)
        for coin in self.levels.coins:
            coin.draw(self.screen, self.camera.x)
        for powerup in self.levels.double_jump_orbs:
            powerup.draw(self.screen, self.camera.x)
        for shield in self.levels.shield_tokens:
            shield.draw(self.screen, self.camera.x)
        for sword in self.levels.sword_tokens:
            sword.draw(self.screen, self.camera.x)
        if self.levels.boss:
            self.levels.boss.draw(self.screen, self.camera.x)
        show_goal = self.levels.remaining_coins() == 0
        if self.levels.is_boss_stage():
            boss = self.levels.boss
            show_goal = show_goal and (boss is None or boss.defeated)
        if show_goal:
            self.levels.goal.draw(self.screen, self.camera.x)
        for projectile in self.projectiles:
            projectile.draw(self.screen, self.camera.x)
        for sphere in self.jump_spheres:
            sphere.draw(self.screen, self.camera.x)
        for slash in self.slashes:
            slash.draw(self.screen, self.camera.x)
        self.player.draw(self.screen, self.camera.x)
        for particle in self.particles:
            particle.draw(self.screen, self.camera.x)

    def _draw_hud(self) -> None:
        draw_text(self.screen, f"Score: {self.score}", (20, 20))
        draw_text(self.screen, f"Level: {self.levels.level_index + 1}/{self.levels.total_levels}", (20, 60))
        theme_name = BACKGROUND_THEMES[self.levels.theme_index]["name"]
        heart_y = 110
        for i in range(self.max_lives):
            centre = (30 + i * 38, heart_y)
            filled = i < self.lives
            colour = CRIMSON if filled else pygame.Color(70, 70, 70)
            outline = pygame.Color(255, 255, 255) if filled else pygame.Color(120, 120, 120)
            draw_heart(self.screen, centre, 28, colour, outline)
        draw_text(self.screen, f"Theme: {theme_name}", (20, heart_y + 36), colour=SMOKE)
        mode_label = "Hard Mode" if self.hard_mode else "Normal Mode"
        mode_colour = CRIMSON if self.hard_mode else CYAN
        draw_text(self.screen, f"Mode: {mode_label}", (20, heart_y + 64), colour=mode_colour)
        boss = self.levels.boss
        if self.levels.is_boss_stage() and boss and not boss.defeated:
            draw_text(
                self.screen,
                "Boss shrugs off stomps—grab swords and fire L-Shift beams!",
                (SCREEN_WIDTH // 2, 18),
                colour=NEON_GREEN,
                anchor="midtop",
            )
        status_y = 20
        if self.levels.is_boss_stage() and boss:
            if not boss.defeated:
                draw_text(
                    self.screen,
                    f"Boss HP: {max(boss.health, 0)}",
                    (SCREEN_WIDTH - 20, status_y),
                    colour=VOID_PURPLE,
                    anchor="topright",
                )
                status_y += 32
        if self.levels.remaining_coins() > 0:
            draw_text(
                self.screen,
                f"Collect {self.levels.remaining_coins()} more star shards!",
                (SCREEN_WIDTH - 20, status_y),
                anchor="topright",
            )
        info_y = max(status_y + 40, 60)
        if self.player.combo > 1:
            draw_text(self.screen, f"Combo x{self.player.combo}", (SCREEN_WIDTH - 20, info_y), colour=CYAN, anchor="topright")
            info_y += 32
        if self.player.double_jump_stock > 0:
            draw_text(
                self.screen,
                f"Double Jump x{self.player.double_jump_stock}",
                (SCREEN_WIDTH - 20, info_y),
                colour=MINT,
                anchor="topright",
            )
            info_y += 28
        if self.player.shield_charges > 0:
            draw_text(
                self.screen,
                f"Shield x{self.player.shield_charges}",
                (SCREEN_WIDTH - 20, info_y),
                colour=pygame.Color(150, 230, 255),
                anchor="topright",
            )
            info_y += 28
        if self.player.sword_ready and self.player.sword_charges > 0:
            draw_text(
                self.screen,
                f"Sword x{self.player.sword_charges}",
                (SCREEN_WIDTH - 20, info_y),
                colour=NEON_GREEN,
                anchor="topright",
            )
            info_y += 28
        elif self.player.sword_cooldown > 0:
            draw_text(
                self.screen,
                f"Sword cooling {self.player.sword_cooldown:.1f}s",
                (SCREEN_WIDTH - 20, info_y),
                colour=pygame.Color(180, 200, 200),
                anchor="topright",
            )
            info_y += 28
        if self.combo_nova_ready:
            draw_text(
                self.screen,
                "Nova Ready (E)",
                (SCREEN_WIDTH - 20, info_y),
                colour=GOLD,
                anchor="topright",
            )
        elif self.combo_nova_cooldown > 0:
            draw_text(
                self.screen,
                f"Nova {self.combo_nova_cooldown:.1f}s",
                (SCREEN_WIDTH - 20, info_y),
                colour=pygame.Color(200, 210, 255),
                anchor="topright",
            )
        if self.player.invincible_timer > 0:
            draw_text(
                self.screen,
                f"Invincible {self.player.invincible_timer:.1f}s",
                (SCREEN_WIDTH - 20, info_y + 32),
                colour=SMOKE,
                anchor="topright",
            )


    def _draw_menu(self) -> None:
        draw_text(self.screen, "Neon Night Run", (SCREEN_WIDTH // 2, 160), font=TITLE_FONT, colour=GOLD, anchor="center")
        draw_text(self.screen, "Press ENTER to start", (SCREEN_WIDTH // 2, 300), font=SUBTITLE_FONT, anchor="center")
        draw_text(self.screen, "Arrow keys / WASD to move, Space to jump", (SCREEN_WIDTH // 2, 360), anchor="center")
        draw_text(self.screen, "Collect all star shards before touching the flag!", (SCREEN_WIDTH // 2, 400), anchor="center")
        draw_text(self.screen, "Keep your hearts safe - three hits ends the run!", (SCREEN_WIDTH // 2, 440), anchor="center")
        mode_text = "Hard Mode: ON" if self.hard_mode else "Hard Mode: OFF"
        mode_colour = CRIMSON if self.hard_mode else CYAN
        draw_text(self.screen, mode_text, (SCREEN_WIDTH // 2, 500), colour=mode_colour, anchor="center")
        draw_text(self.screen, "Press H to toggle Hard Mode", (SCREEN_WIDTH // 2, 540), colour=SMOKE, anchor="center")

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
                elif event.key == pygame.K_h:
                    if self.state in (GameState.MENU, GameState.GAME_OVER, GameState.VICTORY, GameState.PAUSED):
                        self.hard_mode = not self.hard_mode
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
