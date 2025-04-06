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
        self.current_index = 0  # Tracks which message we're on
        self.input_text = ""
        self.text_surface = None
        self.text_rect = None
        self.input_rect = None
        self.cursor_visible = True
        self.cursor_timer = 0
        
        # New attributes for choice-based dialogue
        self.has_choices = False
        self.choices = []
        self.selected_choice = 0
        self.choice_rects = []
        self.npc_name = None
        self.npc_sprite = None

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
        # Reset choices when showing new dialogue
        self.has_choices = False
        self.choices = []
        self.selected_choice = 0
        self.choice_rects = []

    def show_dialogue_with_choices(self, messages: List[str], choices: List[dict] = None, 
                                  npc_name: str = None, npc_sprite: pygame.Surface = None):
        """Show dialogue with potential choices."""
        self.show_dialogue(messages)
        self.npc_name = npc_name
        self.npc_sprite = npc_sprite
        
        if choices:
            self.has_choices = True
            self.choices = choices
            self.selected_choice = 0
            self.choice_rects = []
        else:
            self.has_choices = False
            self.choices = []

    def next_message(self):
        """Move to the next message or close if we're done."""
        if self.current_index < len(self.messages) - 1:
            self.current_index += 1
            self.current_text = self.messages[self.current_index]
        else:
            if self.has_choices:
                # Last message reached and choices are available
                # Keep dialogue open for choice selection
                pass
            else:
                self.close()

    def select_next_choice(self):
        """Move selection to the next choice."""
        if self.has_choices and self.choices:
            self.selected_choice = (self.selected_choice + 1) % len(self.choices)

    def select_prev_choice(self):
        """Move selection to the previous choice."""
        if self.has_choices and self.choices:
            self.selected_choice = (self.selected_choice - 1) % len(self.choices)

    def get_selected_choice(self):
        """Get the currently selected choice index."""
        if self.has_choices and self.choices:
            return self.selected_choice
        return None

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
        
        # Add extra height for choices if needed
        if self.has_choices and self.current_index == len(self.messages) - 1:
            choice_height = len(self.choices) * (self.font.get_height() + 10)
            required_height += choice_height + padding
        
        # Add extra height for input area
        if self.input_mode:
            required_height += self.font.get_height() + padding * 2

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
        
        # Draw NPC name if available
        if self.npc_name:
            name_surface = self.font.render(self.npc_name, True, WHITE)
            name_rect = name_surface.get_rect(topleft=(dialogue_bg.left + padding, dialogue_bg.top + padding))
            surface.blit(name_surface, name_rect)
            
            # Adjust text area to account for name
            text_top = name_rect.bottom + padding
        else:
            text_top = dialogue_bg.top + padding

        # Draw the main dialogue text
        self.draw_text_lines(surface, lines, self.font, WHITE,
                             pygame.Rect(dialogue_bg.left + padding, text_top,
                                         dialogue_bg.width - padding * 2, dialogue_bg.height - padding * 2))

        # Draw choices if showing the last message and choices are available
        if self.has_choices and self.current_index == len(self.messages) - 1:
            self.draw_choices(surface, dialogue_bg, padding)

        # Draw input area if in input mode
        if self.input_mode:
            input_y = dialogue_bg.bottom - self.font.get_height() - padding * 2
            
            if self.input_rect is None or self.input_rect.y != input_y:
                self.input_rect = pygame.Rect(
                    dialogue_bg.left + padding,
                    input_y,
                    dialogue_bg.width - padding * 2,
                    self.font.get_height() + padding
                )
            
            input_bg_surface = pygame.Surface((self.input_rect.width, self.input_rect.height), pygame.SRCALPHA)
            input_bg_surface.fill(INPUT_BG)
            surface.blit(input_bg_surface, self.input_rect)

            prompt_text = "> "
            prompt_surface = self.font.render(prompt_text, True, WHITE)
            prompt_rect = prompt_surface.get_rect(
                topleft=(self.input_rect.left + 5, self.input_rect.top + padding // 2)
            )
            surface.blit(prompt_surface, prompt_rect)

            display_text = self.input_text + ("|" if self.cursor_visible else "")
            input_text_surface = self.font.render(display_text, True, WHITE)
            input_text_rect = input_text_surface.get_rect(
                topleft=(prompt_rect.right, self.input_rect.top + padding // 2)
            )
            surface.blit(input_text_surface, input_text_rect)
            
            # Draw hint for AI dialogue mode
            hint_text = "Type 'exit' to end conversation"
            hint_surface = self.font.render(hint_text, True, GRAY)
            hint_rect = hint_surface.get_rect(
                bottomright=(dialogue_bg.right - padding, dialogue_bg.bottom - padding // 2)
            )
            surface.blit(hint_surface, hint_rect)

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

    def draw_choices(self, surface, dialogue_bg, padding):
        """Draw the choice options."""
        self.choice_rects = []
        
        # Start position for choices
        choice_y = dialogue_bg.bottom - (len(self.choices) * (self.font.get_height() + 10)) - padding
        
        for i, choice in enumerate(self.choices):
            choice_text = choice["text"]
            choice_color = CHOICE_HIGHLIGHT if i == self.selected_choice else CHOICE_NORMAL
            
            choice_surface = self.font.render(f"> {choice_text}", True, choice_color)
            choice_rect = choice_surface.get_rect(
                topleft=(dialogue_bg.left + padding * 2, choice_y)
            )
            
            surface.blit(choice_surface, choice_rect)
            self.choice_rects.append(choice_rect)
            
            choice_y += self.font.get_height() + 5