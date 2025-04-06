# dialogue.py

import pygame
from typing import Optional, Callable, List, Tuple
from constants import *

class DialogueNode:
    """A node in a dialogue tree, supporting conditional navigation and actions."""
    def __init__(self, text: str, is_input: bool = False, action: Optional[Callable[[], None]] = None):
        """
        Initialize a dialogue node.

        Args:
            text (str): The dialogue text to display.
            is_input (bool): Whether this node requires player input.
            action (Optional[Callable[[], None]]): Function to execute when the node is entered.
        """
        self.text = text
        self.is_input = is_input
        self.conditional_next: List[Tuple[Optional[str], Callable[[], bool], 'DialogueNode']] = []
        self.default_next: Optional['DialogueNode'] = None
        self.action: Optional[Callable[[], None]] = action

    def add_conditional_next(self, pattern: Optional[str], condition: Callable[[], bool], next_node: 'DialogueNode') -> None:
        """
        Add a conditional transition to another node.

        Args:
            pattern (Optional[str]): Expected player input (None for non-input nodes).
            condition (Callable[[], bool]): Condition that must be true to follow this path.
            next_node ('DialogueNode'): The next node to transition to.
        """
        self.conditional_next.append((pattern, condition, next_node))

    def set_default_next(self, next_node: 'DialogueNode') -> None:
        """
        Set the default next node if no conditions are met.

        Args:
            next_node ('DialogueNode'): The fallback node.
        """
        self.default_next = next_node

    def get_next_node(self, player_input: str = "") -> Optional['DialogueNode']:
        """
        Determine the next node based on input and conditions.

        Args:
            player_input (str): Player's input for input nodes.

        Returns:
            Optional['DialogueNode']: The next node, or None if the conversation ends.
        """
        if self.is_input:
            for pattern, condition, next_node in self.conditional_next:
                if pattern and player_input.lower() == pattern.lower() and condition():
                    return next_node
        else:
            for _, condition, next_node in self.conditional_next:
                if condition():
                    return next_node
        return self.default_next

    def enter(self) -> None:
        """Execute the node's action when entered, if one exists."""
        if self.action:
            self.action()

class DialogueTree:
    """A complete dialogue tree for an NPC conversation."""
    def __init__(self, greeting: str):
        """
        Initialize the dialogue tree with a root node.

        Args:
            greeting (str): The initial dialogue text.
        """
        self.root = DialogueNode(greeting)
        self.current_node = self.root

    def reset(self) -> None:
        """Reset the current node to the root."""
        self.current_node = self.root

    def get_current_text(self) -> str:
        """Get the text of the current node."""
        return self.current_node.text if self.current_node else ""

    def requires_input(self) -> bool:
        """Check if the current node requires player input."""
        return self.current_node.is_input if self.current_node else False

    def advance(self, player_input: str = "") -> str:
        """
        Advance to the next node based on player input.

        Args:
            player_input (str): Player's input for input nodes.

        Returns:
            str: The text of the next node, or empty string if at the end.
        """
        if not self.current_node:
            return ""
        next_node = self.current_node.get_next_node(player_input)
        self.current_node = next_node
        return self.current_node.text if self.current_node else ""

    def is_at_end(self) -> bool:
        """Check if the conversation has ended."""
        return self.current_node is None

class DialogueSystem:
    """Handles displaying dialogue and text input"""
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
        
        self.text_surface = self.font.render(text, True, WHITE)
        self.text_rect = self.text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        
        if is_response:
            instruction_text = "Press Enter to exit" if is_final else "Press Enter to continue"
            self.instruction_surface = self.font.render(instruction_text, True, WHITE)
            self.instruction_rect = self.instruction_surface.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40)
            )
    
    def start_input_mode(self):
        self.input_mode = True
        self.response_mode = False
        self.final_response = False
        self.input_text = ""
        self.input_rect = pygame.Rect(
            SCREEN_WIDTH // 4,
            SCREEN_HEIGHT - 40,
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
        dialogue_bg = pygame.Rect(
            self.text_rect.left - padding,
            self.text_rect.top - padding,
            self.text_rect.width + padding * 2,
            self.text_rect.height + padding * 2
        )
        
        bg_surface = pygame.Surface((dialogue_bg.width, dialogue_bg.height), pygame.SRCALPHA)
        bg_surface.fill(DIALOGUE_BG)
        surface.blit(bg_surface, (dialogue_bg.left, dialogue_bg.top))
        
        surface.blit(self.text_surface, self.text_rect)
        
        if self.response_mode:
            surface.blit(self.instruction_surface, self.instruction_rect)
        
        if self.input_mode:
            input_bg_surface = pygame.Surface((self.input_rect.width, self.input_rect.height), pygame.SRCALPHA)
            input_bg_surface.fill(INPUT_BG)
            surface.blit(input_bg_surface, self.input_rect)
            
            display_text = self.input_text + ("|" if self.cursor_visible else "")
            input_text_surface = self.font.render(display_text, True, WHITE)
            input_text_rect = input_text_surface.get_rect(midleft=(self.input_rect.left + 10, self.input_rect.centery))
            surface.blit(input_text_surface, input_text_rect)