# Simple Mario-Clone Game using Pygame
# To run this game:
# 1. Install Pygame if not already installed: pip install pygame
# 2. Save this code to a file, e.g., mario_clone.py
# 3. Run it with: python mario_clone.py
#
# Controls:
# - Arrow Left/Right: Move
# - Arrow Up: Jump
# - Escape: Quit
#
# This is a basic one-level game with a player (blue rectangle), ground/platforms (green rectangles),
# an enemy (red rectangle that moves back and forth), and a coin (yellow circle) to collect.
# Physics include gravity, jumping, and basic collisions.

import pygame
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)   # Player
GREEN = (0, 255, 0) # Platforms
RED = (255, 0, 0)    # Enemy
YELLOW = (255, 255, 0) # Coin
WHITE = (255, 255, 255)

# Game settings
GRAVITY = 0.5
JUMP_STRENGTH = -15
PLAYER_SPEED = 5

# Create screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simple Mario Clone")

# Clock for frame rate
clock = pygame.time.Clock()

# Player properties
player_rect = pygame.Rect(100, 500, 40, 60)  # x, y, width, height
player_vel_x = 0
player_vel_y = 0
on_ground = False

# Platforms (ground and some blocks)
platforms = [
    pygame.Rect(0, 550, SCREEN_WIDTH, 50),  # Ground
    pygame.Rect(200, 400, 100, 20),         # Platform 1
    pygame.Rect(400, 300, 100, 20),         # Platform 2
    pygame.Rect(600, 200, 100, 20)          # Platform 3
]

# Enemy
enemy_rect = pygame.Rect(300, 500, 40, 40)
enemy_vel_x = 2  # Moves right initially

# Coin
coin_rect = pygame.Rect(450, 250, 20, 20)
coin_collected = False

# Score
score = 0
font = pygame.font.Font(None, 36)

# Main game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # Get keys
    keys = pygame.key.get_pressed()
    player_vel_x = 0
    if keys[pygame.K_LEFT]:
        player_vel_x = -PLAYER_SPEED
    if keys[pygame.K_RIGHT]:
        player_vel_x = PLAYER_SPEED
    if keys[pygame.K_UP] and on_ground:
        player_vel_y = JUMP_STRENGTH
        on_ground = False

    # Apply gravity
    player_vel_y += GRAVITY

    # Update player position
    player_rect.x += player_vel_x
    player_rect.y += player_vel_y

    # Check collisions with platforms
    on_ground = False
    for platform in platforms:
        if player_rect.colliderect(platform):
            if player_vel_y > 0:  # Falling down
                player_rect.bottom = platform.top
                player_vel_y = 0
                on_ground = True
            elif player_vel_y < 0:  # Hitting head
                player_rect.top = platform.bottom
                player_vel_y = 0

    # Keep player within screen bounds
    if player_rect.left < 0:
        player_rect.left = 0
    if player_rect.right > SCREEN_WIDTH:
        player_rect.right = SCREEN_WIDTH
    if player_rect.top < 0:
        player_rect.top = 0
        player_vel_y = 0
    if player_rect.bottom > SCREEN_HEIGHT:
        player_rect.bottom = SCREEN_HEIGHT
        player_vel_y = 0
        on_ground = True

    # Update enemy
    enemy_rect.x += enemy_vel_x
    # Bounce enemy on screen edges or platforms
    if enemy_rect.left < 0 or enemy_rect.right > SCREEN_WIDTH:
        enemy_vel_x = -enemy_vel_x
    # Simple enemy collision with platforms (just ground for simplicity)
    if enemy_rect.bottom > platforms[0].top:
        enemy_rect.bottom = platforms[0].top

    # Check player-enemy collision (game over)
    if player_rect.colliderect(enemy_rect):
        print("Game Over! You hit the enemy.")
        running = False

    # Check coin collection
    if not coin_collected and player_rect.colliderect(coin_rect):
        score += 1
        coin_collected = True

    # Draw everything
    screen.fill(BLACK)  # Background

    # Draw platforms
    for platform in platforms:
        pygame.draw.rect(screen, GREEN, platform)

    # Draw player
    pygame.draw.rect(screen, BLUE, player_rect)

    # Draw enemy
    pygame.draw.rect(screen, RED, enemy_rect)

    # Draw coin if not collected
    if not coin_collected:
        pygame.draw.circle(screen, YELLOW, coin_rect.center, 10)

    # Draw score
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # Update display
    pygame.display.flip()

    # Cap frame rate
    clock.tick(60)

# Quit Pygame
pygame.quit()
sys.exit()