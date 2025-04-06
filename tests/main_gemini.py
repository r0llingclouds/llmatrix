import pygame
import sys

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SIZE = 50
NPC_SIZE = 50
PLAYER_SPEED = 5
DIALOGUE_BOX_HEIGHT = 150
INTERACTION_DISTANCE = 70 # How close player needs to be to interact
TEXT_INPUT_LIMIT = 50 # Max characters for user input

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)  # Player color
GREEN = (0, 255, 0) # NPC1 color
YELLOW = (255, 255, 0) # NPC2 color
GRAY = (100, 100, 100) # Dialogue box color
RED = (255, 0, 0) # Interaction prompt color

# --- Initialization ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simple 2D RPG with Input")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36) # Default font, size 36
small_font = pygame.font.Font(None, 24) # For interaction prompt and small text

# --- Game Objects ---
# Player
player_rect = pygame.Rect(SCREEN_WIDTH // 2 - PLAYER_SIZE // 2,
                          SCREEN_HEIGHT // 2 - PLAYER_SIZE // 2,
                          PLAYER_SIZE, PLAYER_SIZE)

# NPC1 (Dialogue Cycle)
npc1_rect = pygame.Rect(100, 100, NPC_SIZE, NPC_SIZE)
npc1_dialogue = [
    "Hello there, traveler!",
    "It's a fine day, isn't it?",
    "Be careful wandering around alone."
]
current_dialogue_index = 0 # Which line NPC1 is currently saying

# NPC2 (Text Input)
npc2_rect = pygame.Rect(SCREEN_WIDTH - 100 - NPC_SIZE,
                          SCREEN_HEIGHT - 100 - NPC_SIZE,
                          NPC_SIZE, NPC_SIZE)
# No pre-set dialogue needed here initially

# --- Game State ---
dialogue_active = False          # Is any dialogue box open?
active_interaction_npc = None  # Which NPC are we interacting with? (None, 1, or 2)
show_interaction_prompt_npc = None # Which NPC's prompt should show? (None, 1, or 2)

# State specific to NPC2's input
is_typing = False                # Is the player currently typing input?
show_npc2_response = False       # Should NPC2 show the echoed response?
user_input_text = ""             # The text the user is typing
npc2_response_text = ""          # The text NPC2 will say

# --- Helper Function ---
def draw_text(surface, text, font, color, rect, center=True, wrap=False, max_width=None):
    """Draws text onto a surface, optionally centering or wrapping."""
    if wrap and max_width:
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            test_surface = font.render(test_line, True, color)
            if test_surface.get_width() < max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line) # Add the last line

        y_offset = 0
        base_rect = pygame.Rect(rect.left + 10, rect.top + 10, max_width, font.get_height())
        for line in lines:
            line_surface = font.render(line, True, color)
            line_rect = line_surface.get_rect(topleft=base_rect.topleft)
            line_rect.y += y_offset
            surface.blit(line_surface, line_rect)
            y_offset += font.get_height() # Move down for next line
    else:
        # Original non-wrapping logic
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if center:
            text_rect.center = rect.center
        else:
            text_rect.topleft = rect.topleft # Align top-left
            text_rect.x += 10 # Add some padding
            text_rect.y += 10
        surface.blit(text_surface, text_rect)

# --- Game Loop ---
running = True
while running:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # --- Dialogue Interaction / Closing ---
            if event.key == pygame.K_e and show_interaction_prompt_npc is not None:
                # --- Start Interaction ---
                if not dialogue_active:
                    dialogue_active = True
                    active_interaction_npc = show_interaction_prompt_npc # Set which NPC is active

                    if active_interaction_npc == 1:
                        # Cycle NPC1 dialogue
                        current_dialogue_index = (current_dialogue_index + 1) % len(npc1_dialogue)
                        is_typing = False
                        show_npc2_response = False
                    elif active_interaction_npc == 2:
                        # Start typing for NPC2
                        is_typing = True
                        show_npc2_response = False
                        user_input_text = "" # Clear previous input
                        npc2_response_text = ""
                # --- Close Interaction ---
                # (Allow 'E' to close only if not currently typing for NPC2)
                elif dialogue_active and not is_typing:
                     dialogue_active = False
                     active_interaction_npc = None
                     is_typing = False
                     show_npc2_response = False

            # --- Handle Typing Input (Only if dialogue with NPC2 is active and typing) ---
            elif is_typing and active_interaction_npc == 2:
                if event.key == pygame.K_RETURN: # Enter key
                    is_typing = False
                    show_npc2_response = True
                    # Prepare NPC2's response
                    if user_input_text:
                        npc2_response_text = f"You said: {user_input_text}"
                    else:
                        npc2_response_text = "You didn't say anything!"
                    user_input_text = "" # Clear input field visually after enter
                elif event.key == pygame.K_BACKSPACE:
                    user_input_text = user_input_text[:-1] # Remove last character
                elif len(user_input_text) < TEXT_INPUT_LIMIT:
                    # Add printable character to input text
                    user_input_text += event.unicode

            # --- Close dialogue with Escape key ---
            if event.key == pygame.K_ESCAPE and dialogue_active:
                dialogue_active = False
                active_interaction_npc = None
                is_typing = False
                show_npc2_response = False
                user_input_text = "" # Clear any partial input

    # --- Player Movement ---
    # Block movement if any dialogue/input is active
    if not dialogue_active:
        keys = pygame.key.get_pressed()
        new_x, new_y = player_rect.x, player_rect.y

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_x += PLAYER_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_y -= PLAYER_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_y += PLAYER_SPEED

        # Boundary checks
        if 0 <= new_x <= SCREEN_WIDTH - player_rect.width:
            player_rect.x = new_x
        if 0 <= new_y <= SCREEN_HEIGHT - player_rect.height:
             player_rect.y = new_y

    # --- Game Logic ---
    # Check proximity for interaction prompts (only if dialogue not already active)
    show_interaction_prompt_npc = None # Reset prompt check each frame
    if not dialogue_active:
        player_center = player_rect.center
        dist_npc1 = pygame.math.Vector2(player_center).distance_to(npc1_rect.center)
        dist_npc2 = pygame.math.Vector2(player_center).distance_to(npc2_rect.center)

        # Prioritize the closer NPC if in range of both
        if dist_npc1 < INTERACTION_DISTANCE and dist_npc2 < INTERACTION_DISTANCE:
            show_interaction_prompt_npc = 1 if dist_npc1 < dist_npc2 else 2
        elif dist_npc1 < INTERACTION_DISTANCE:
            show_interaction_prompt_npc = 1
        elif dist_npc2 < INTERACTION_DISTANCE:
             show_interaction_prompt_npc = 2

    # --- Drawing ---
    screen.fill(WHITE) # Clear screen

    # Draw NPCs
    pygame.draw.rect(screen, GREEN, npc1_rect)
    pygame.draw.rect(screen, YELLOW, npc2_rect)

    # Draw Player
    pygame.draw.rect(screen, BLUE, player_rect)

    # Draw Interaction Prompt if needed
    prompt_npc_rect = None
    if show_interaction_prompt_npc == 1:
        prompt_npc_rect = npc1_rect
    elif show_interaction_prompt_npc == 2:
        prompt_npc_rect = npc2_rect

    if prompt_npc_rect:
         prompt_surface = small_font.render("Press E", True, RED)
         prompt_rect = prompt_surface.get_rect(center=(prompt_npc_rect.centerx, prompt_npc_rect.top - 20))
         screen.blit(prompt_surface, prompt_rect)

    # Draw Dialogue Box and Text if active
    if dialogue_active:
        # Dialogue Box Background
        dialogue_box_rect = pygame.Rect(50, SCREEN_HEIGHT - DIALOGUE_BOX_HEIGHT - 20, SCREEN_WIDTH - 100, DIALOGUE_BOX_HEIGHT)
        pygame.draw.rect(screen, GRAY, dialogue_box_rect)
        pygame.draw.rect(screen, BLACK, dialogue_box_rect, 3) # Border
        dialogue_content_width = dialogue_box_rect.width - 20 # Width for text wrapping

        # --- Draw Content based on Active NPC ---
        if active_interaction_npc == 1:
            # NPC1's cycling text
            draw_text(screen, npc1_dialogue[current_dialogue_index], font, BLACK, dialogue_box_rect, center=False, wrap=True, max_width=dialogue_content_width)
            # Closing instruction for NPC1
            close_text = small_font.render("Press E or ESC to close", True, BLACK)

        elif active_interaction_npc == 2:
            if is_typing:
                # Show input prompt and current text
                input_display_text = f"Enter text: {user_input_text}"
                # Simple blinking cursor effect (toggle visibility)
                if pygame.time.get_ticks() % 1000 < 500: # Blink every second
                    input_display_text += "_"
                draw_text(screen, input_display_text, font, BLACK, dialogue_box_rect, center=False, wrap=True, max_width=dialogue_content_width)
                # Typing instructions
                close_text = small_font.render("Enter: Submit | Backspace: Delete | ESC: Cancel", True, BLACK)

            elif show_npc2_response:
                # Show NPC2's response
                draw_text(screen, npc2_response_text, font, BLACK, dialogue_box_rect, center=False, wrap=True, max_width=dialogue_content_width)
                 # Closing instruction after response
                close_text = small_font.render("Press E or ESC to close", True, BLACK)

        # Draw closing instructions (if text was generated)
        if 'close_text' in locals():
            close_rect = close_text.get_rect(bottomright=(dialogue_box_rect.right - 10, dialogue_box_rect.bottom - 10))
            screen.blit(close_text, close_rect)

    # --- Update Display ---
    pygame.display.flip()

    # --- Frame Rate Control ---
    clock.tick(60) # Limit frames per second

# --- Quit Pygame ---
pygame.quit()
sys.exit()