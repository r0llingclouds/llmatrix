import pygame
from constants import *

class DialogueSystem:
    def __init__(self):
        self.font = pygame.font.SysFont(None, FONT_SIZE)
        self.active = False
        self.input_mode = False
        self.response_mode = False
        self.final_response = False
        self.current_text = ""
        self.input_text = ""
        self.text_surface = None
        self.text_rect = None
        self.input_rect = None
        self.cursor_visible = True
        self.cursor_timer = 0

    def show_dialogue(self, text: str, is_response=False, is_final=False):
        self.active = True
        self.current_text = text
        self.response_mode = is_response
        self.final_response = is_final

        self.text_rect = pygame.Rect(
            SCREEN_WIDTH // 8,
            SCREEN_HEIGHT - 200,
            SCREEN_WIDTH * 3 // 4,
            100
        )

    def start_input_mode(self):
        self.input_mode = True
        self.response_mode = False
        self.final_response = False
        self.input_text = ""
        self.input_rect = pygame.Rect(
            SCREEN_WIDTH // 4,
            SCREEN_HEIGHT - 85,
            SCREEN_WIDTH // 2,
            30
        )

    def add_character(self, char: str):
        if len(self.input_text) < INPUT_MAX_LENGTH:
            self.input_text += char

    def remove_character(self):
        if self.input_text:
            self.input_text = self.input_text[:-1]

    def submit_input(self) -> str:
        text = self.input_text
        self.input_text = ""
        self.input_mode = False
        return text

    def close(self):
        self.active = False
        self.input_mode = False
        self.response_mode = False
        self.final_response = False
        self.current_text = ""
        self.input_text = ""

    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self, surface: pygame.Surface):
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