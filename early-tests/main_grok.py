import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_RADIUS = 10
NPC_SIZE = 20
PLAYER_SPEED = 5
DIALOGUE_DISTANCE = 50

# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simple 2D RPG Game")

# Player position
player_x = 100.0
player_y = 100.0

# NPC1 position (green)
npc1_x = 400.0
npc1_y = 300.0

# NPC2 position (red)
npc2_x = 600.0
npc2_y = 200.0

# Dialogue and input states
current_npc = None
show_dialogue = False
input_mode = False
show_response = False
player_input = ""

# Load font for dialogue
font = pygame.font.SysFont('Arial', 24)

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Main game loop
while True:
    # Calculate distances to NPCs
    distance_to_npc1 = ((player_x - npc1_x) ** 2 + (player_y - npc1_y) ** 2) ** 0.5
    distance_to_npc2 = ((player_x - npc2_x) ** 2 + (player_y - npc2_y) ** 2) ** 0.5

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if current_npc is None:
                    if distance_to_npc1 < DIALOGUE_DISTANCE:
                        current_npc = 'npc1'
                        show_dialogue = True
                    elif distance_to_npc2 < DIALOGUE_DISTANCE:
                        current_npc = 'npc2'
                        input_mode = True
                        show_dialogue = True
                elif not input_mode:
                    # Close dialogue
                    current_npc = None
                    show_dialogue = False
                    input_mode = False
                    show_response = False
                    player_input = ""
            elif event.key == pygame.K_ESCAPE:
                # Emergency exit from dialogue
                current_npc = None
                show_dialogue = False
                input_mode = False
                show_response = False
                player_input = ""
            if input_mode and current_npc == 'npc2':
                if event.key == pygame.K_RETURN:
                    input_mode = False
                    show_response = True
                elif event.key == pygame.K_BACKSPACE:
                    player_input = player_input[:-1]
                elif event.unicode and len(player_input) < 50:
                    player_input += event.unicode

    # Player movement (disabled in input mode)
    if not input_mode:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            player_x += PLAYER_SPEED
        if keys[pygame.K_UP]:
            player_y -= PLAYER_SPEED
        if keys[pygame.K_DOWN]:
            player_y += PLAYER_SPEED

    # Boundary checks
    player_x = max(PLAYER_RADIUS, min(SCREEN_WIDTH - PLAYER_RADIUS, player_x))
    player_y = max(PLAYER_RADIUS, min(SCREEN_HEIGHT - PLAYER_RADIUS, player_y))

    # Check distance to current NPC
    if current_npc == 'npc1' and distance_to_npc1 > DIALOGUE_DISTANCE:
        current_npc = None
        show_dialogue = False
    elif current_npc == 'npc2' and distance_to_npc2 > DIALOGUE_DISTANCE:
        current_npc = None
        show_dialogue = False
        input_mode = False
        show_response = False
        player_input = ""

    # Rendering
    screen.fill((0, 0, 0))  # Black background

    # Draw player (blue circle)
    pygame.draw.circle(screen, (0, 0, 255), (int(player_x), int(player_y)), PLAYER_RADIUS)

    # Draw NPC1 (green rectangle)
    pygame.draw.rect(screen, (0, 255, 0), (int(npc1_x - NPC_SIZE // 2), int(npc1_y - NPC_SIZE // 2), NPC_SIZE, NPC_SIZE))

    # Draw NPC2 (red rectangle)
    pygame.draw.rect(screen, (255, 0, 0), (int(npc2_x - NPC_SIZE // 2), int(npc2_y - NPC_SIZE // 2), NPC_SIZE, NPC_SIZE))

    # Draw dialogue box
    if show_dialogue:
        pygame.draw.rect(screen, (255, 255, 255), (0, 500, 800, 100))  # White box
        if current_npc == 'npc1':
            text = "Hello, adventurer!"
        elif current_npc == 'npc2':
            if input_mode:
                text = "Type your message: " + player_input
            elif show_response:
                text = "You said: " + player_input
        text_surface = font.render(text, True, (0, 0, 0))
        screen.blit(text_surface, (100, 525))

    pygame.display.flip()
    clock.tick(60)