import pygame
from enum import Enum
from constants import *

# Define the DialogueState enum to manage dialogue states
class DialogueState(Enum):
    INACTIVE = 0            # No dialogue is active
    SHOWING_DIALOGUE = 1    # Displaying dialogue text
    INPUT_MODE = 2          # Player is entering input
    WAITING_FOR_RESPONSE = 3  # Waiting for AI response

class DialogueSystem:
    def __init__(self):
        """Initialize the DialogueSystem with a state machine and essential attributes."""
        self.font = pygame.font.SysFont(None, FONT_SIZE)
        self.state = DialogueState.INACTIVE
        self.current_text = ""      # Text to display in the dialogue box
        self.input_text = ""        # Text entered by the player
        self.text_rect = None       # Rectangle for dialogue text, set when showing dialogue
        self.input_rect = None      # Rectangle for input box, set in input mode
        self.cursor_visible = True  # Controls cursor blinking in input mode
        self.cursor_timer = 0       # Timer for cursor blinking

    def show_dialogue(self, text: str) -> None:
        """Display dialogue text and set the state to SHOWING_DIALOGUE."""
        self.state = DialogueState.SHOWING_DIALOGUE
        self.current_text = text
        self.text_rect = pygame.Rect(
            SCREEN_WIDTH // 8,
            SCREEN_HEIGHT - 200,
            SCREEN_WIDTH * 3 // 4,
            100
        )

    def start_input_mode(self) -> None:
        """Switch to input mode and initialize the input box."""
        self.state = DialogueState.INPUT_MODE
        self.input_text = ""
        self.input_rect = pygame.Rect(
            SCREEN_WIDTH // 4,
            SCREEN_HEIGHT - 85,
            SCREEN_WIDTH // 2,
            30
        )

    def start_waiting_for_response(self) -> None:
        """Set state to WAITING_FOR_RESPONSE and show a waiting message."""
        self.state = DialogueState.WAITING_FOR_RESPONSE
        self.current_text = "NPC is thinking..."

    def add_character(self, char: str) -> None:
        """Add a character to the input text if within max length."""
        if len(self.input_text) < INPUT_MAX_LENGTH:
            self.input_text += char

    def remove_character(self) -> None:
        """Remove the last character from the input text."""
        if self.input_text:
            self.input_text = self.input_text[:-1]

    def submit_input(self) -> str:
        """Return the current input text and clear it."""
        text = self.input_text
        self.input_text = ""
        return text

    def close(self) -> None:
        """Close the dialogue system and reset state."""
        self.state = DialogueState.INACTIVE
        self.current_text = ""
        self.input_text = ""

    def update(self) -> None:
        """Update the cursor blinking for input mode."""
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self, surface: pygame.Surface) -> None:
        """Render the dialogue system based on the current state."""
        if self.state == DialogueState.INACTIVE:
            return

        padding = DIALOGUE_PADDING
        lines = self.calculate_wrapped_lines(self.current_text, self.font, self.text_rect.width - padding * 2)
        total_text_height = len(lines) * self.font.get_height()
        required_height = total_text_height + padding * 2

        # Adjust dialogue box height if text exceeds initial height
        if required_height > self.text_rect.height:
            y_offset = required_height - self.text_rect.height
            self.text_rect.y -= y_offset
            self.text_rect.height = required_height

        dialogue_bg = pygame.Rect(
            self.text_rect.left - padding,
            self.text_rect.top - padding,
            self.text_rect.width + padding * 2,
            self.text_rect.height + padding * 2
        )

        # Draw dialogue background
        bg_surface = pygame.Surface((dialogue_bg.width, dialogue_bg.height), pygame.SRCALPHA)
        bg_surface.fill(DIALOGUE_BG)
        surface.blit(bg_surface, (dialogue_bg.left, dialogue_bg.top))

        # Draw dialogue text
        self.draw_text_lines(surface, lines, self.font, WHITE,
                             pygame.Rect(dialogue_bg.left + padding, dialogue_bg.top + padding,
                                         dialogue_bg.width - padding * 2, dialogue_bg.height - padding * 2))

        # Draw input box if in INPUT_MODE
        if self.state == DialogueState.INPUT_MODE:
            input_bg_surface = pygame.Surface((self.input_rect.width, self.input_rect.height), pygame.SRCALPHA)
            input_bg_surface.fill(INPUT_BG)
            surface.blit(input_bg_surface, self.input_rect)

            display_text = self.input_text + ("|" if self.cursor_visible else "")
            input_text_surface = self.font.render(display_text, True, WHITE)
            input_text_rect = input_text_surface.get_rect(midleft=(self.input_rect.left + 10, self.input_rect.centery))
            surface.blit(input_text_surface, input_text_rect)

    def calculate_wrapped_lines(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        """Wrap text into lines that fit within the specified width."""
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            test_surface = font.render(test_line, True, (0, 0, 0))
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "

        lines.append(current_line.strip())
        return lines

    def draw_text_lines(self, surface: pygame.Surface, lines: list[str], font: pygame.font.Font, 
                        color: tuple, rect: pygame.Rect) -> None:
        """Draw wrapped text lines within the specified rectangle."""
        total_height = len(lines) * font.get_height()
        y_pos = rect.top + (rect.height - total_height) // 2 if total_height < rect.height else rect.top

        for line in lines:
            if line:
                line_surface = font.render(line, True, color)
                line_rect = line_surface.get_rect(midtop=(rect.centerx, y_pos))
                surface.blit(line_surface, line_rect)
            y_pos += font.get_height()