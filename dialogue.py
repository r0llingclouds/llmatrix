import pygame
from constants import *
from typing import Union, List

class DialogueSystem:
    def __init__(self):
        self.font = pygame.font.SysFont(None, FONT_SIZE)
        self.active = False
        self.input_mode = False
        self.response_mode = False
        self.final_response = False
        self.current_text = ""
        self.messages = []  # Holds the sequence of messages
        self.current_index = 0  # Tracks which message we’re on
        self.input_text = ""
        self.text_surface = None
        self.text_rect = None
        self.input_rect = None
        self.cursor_visible = True
        self.cursor_timer = 0

    def show_dialogue(self, messages: Union[str, List[str]], is_response=False, is_final=False):
        """Show a dialogue, either a single message or a list of them."""
        if isinstance(messages, str):
            messages = [messages]  # Turn a single string into a list
        self.messages = messages
        self.current_index = 0
        self.active = True
        self.input_mode = False  # No input needed for static dialogue
        self.response_mode = is_response
        self.final_response = is_final
        if messages:
            self.current_text = self.messages[0]  # Start with the first message
        else:
            self.current_text = ""
        self.text_rect = pygame.Rect(
            SCREEN_WIDTH // 8,
            SCREEN_HEIGHT - 200,
            SCREEN_WIDTH * 3 // 4,
            100
        )

    def next_message(self):
        """Move to the next message or close if we’re done."""
        if self.current_index < len(self.messages) - 1:
            self.current_index += 1
            self.current_text = self.messages[self.current_index]
        else:
            self.close()

    def start_input_mode(self):
        """Switch to input mode for typing (not used in static dialogue)."""
        self.input_mode = True
        self.input_text = ""
        self.input_rect = pygame.Rect(
            SCREEN_WIDTH // 4,
            SCREEN_HEIGHT - 85,
            SCREEN_WIDTH // 2,
            30
        )

    def add_character(self, char: str):
        """Add a character to the input text."""
        if len(self.input_text) < INPUT_MAX_LENGTH:
            self.input_text += char

    def remove_character(self):
        """Remove the last character from input text."""
        if self.input_text:
            self.input_text = self.input_text[:-1]

    def submit_input(self) -> str:
        """Submit the input text and clear it."""
        text = self.input_text
        self.input_text = ""
        self.input_mode = False
        return text

    def close(self):
        """Shut down the dialogue and reset everything."""
        self.active = False
        self.input_mode = False
        self.response_mode = False
        self.final_response = False
        self.current_text = ""
        self.messages = []
        self.current_index = 0
        self.input_text = ""

    def update(self):
        """Update the cursor blink timer."""
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self, surface: pygame.Surface):
        """Draw the dialogue box and text on the screen."""
        if not self.active:
            return

        padding = DIALOGUE_PADDING

        lines = self.calculate_wrapped_lines(self.current_text, self.font,
                                             self.text_rect.width - padding * 2)

        total_text_height = len(lines) * self.font.get_height()
        required_height = total_text_height + padding * 2

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

        bg_surface = pygame.Surface((dialogue_bg.width, dialogue_bg.height), pygame.SRCALPHA)
        bg_surface.fill(DIALOGUE_BG)
        surface.blit(bg_surface, (dialogue_bg.left, dialogue_bg.top))

        self.draw_text_lines(surface, lines, self.font, WHITE,
                             pygame.Rect(dialogue_bg.left + padding, dialogue_bg.top + padding,
                                         dialogue_bg.width - padding * 2, dialogue_bg.height - padding * 2))

        if self.input_mode:
            input_bg_surface = pygame.Surface((self.input_rect.width, self.input_rect.height), pygame.SRCALPHA)
            input_bg_surface.fill(INPUT_BG)
            surface.blit(input_bg_surface, self.input_rect)

            display_text = self.input_text + ("|" if self.cursor_visible else "")
            input_text_surface = self.font.render(display_text, True, WHITE)
            input_text_rect = input_text_surface.get_rect(midleft=(self.input_rect.left + 10, self.input_rect.centery))
            surface.blit(input_text_surface, input_text_rect)

    def calculate_wrapped_lines(self, text, font, max_width):
        """Wrap text into lines that fit the width."""
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            test_surface = font.render(test_line, True, (0, 0, 0))
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "

        lines.append(current_line)
        return lines

    def draw_text_lines(self, surface, lines, font, color, rect):
        """Draw each line of text centered vertically."""
        total_height = len(lines) * font.get_height()

        if total_height > rect.height:
            y_pos = rect.top
        else:
            y_pos = rect.top + (rect.height - total_height) // 2

        for line in lines:
            if line.strip():
                line_surface = font.render(line, True, color)
                line_rect = line_surface.get_rect(midtop=(rect.centerx, y_pos))
                surface.blit(line_surface, line_rect)
            y_pos += font.get_height()