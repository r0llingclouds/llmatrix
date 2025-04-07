import pygame

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Player and NPC properties
PLAYER_SPEED = 5
PLAYER_SIZE = 40
NPC_SIZE = 40

# Interaction properties
INTERACTION_COOLDOWN = 10  # Add this line

# Dialogue properties
DIALOGUE_PADDING = 10
FONT_SIZE = 24
INPUT_MAX_LENGTH = 30

# Colors (RGBA for transparency where needed)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (160, 32, 240)
DIALOGUE_BG = (50, 50, 50, 200)  # Semi-transparent dark gray
INPUT_BG = (30, 30, 30, 220)    # Slightly darker for input box

# Custom events
RESPONSE_READY = pygame.USEREVENT + 1