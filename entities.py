# entities.py

import pygame
from typing import List, Tuple
from constants import *
from dialogue import DialogueTree

class Entity:
    """Base class for all game entities"""
    def __init__(self, x: int, y: int, width: int, height: int, color: Tuple[int, int, int]):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
    
    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, self.color, self.rect)

class Player(Entity):
    """Player character controlled by the user"""
    def __init__(self, x: int, y: int):
        super().__init__(x, y, PLAYER_SIZE, PLAYER_SIZE, BLUE)
        self.speed = PLAYER_SPEED
        self.inventory: List[str] = []  # List to track items the player has
    
    def move(self, dx: int, dy: int, walls: List[Entity]):
        original_x = self.rect.x
        original_y = self.rect.y
        
        self.rect.x += dx
        if any(self.rect.colliderect(wall.rect) for wall in walls):
            self.rect.x = original_x
        
        self.rect.y += dy
        if any(self.rect.colliderect(wall.rect) for wall in walls):
            self.rect.y = original_y
        
        self.rect.x = max(0, min(SCREEN_WIDTH - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(SCREEN_HEIGHT - self.rect.height, self.rect.y))
    
    def has_item(self, item_name: str) -> bool:
        """
        Check if the player has a specific item in their inventory.
        
        Args:
            item_name (str): The name of the item to check for.
        
        Returns:
            bool: True if the item is in the inventory, False otherwise.
        """
        return item_name.lower() in (item.lower() for item in self.inventory)

class NPC(Entity):
    """Non-player character with dialogue"""
    def __init__(self, x: int, y: int, color: Tuple[int, int, int], dialogue: List[str]):
        super().__init__(x, y, NPC_SIZE, NPC_SIZE, color)
        self.dialogue = dialogue
        self.dialogue_index = 0
        self.requires_input = False
    
    def interact(self) -> str:
        if self.dialogue_index < len(self.dialogue):
            message = self.dialogue[self.dialogue_index]
            self.dialogue_index += 1
            return message
        self.dialogue_index = 0
        return ""

class InteractiveNPC(NPC):
    """NPC with a dialogue tree for interactive conversations"""
    def __init__(self, x: int, y: int, color: Tuple[int, int, int], dialogue_tree: DialogueTree):
        super().__init__(x, y, color, [dialogue_tree.get_current_text()])
        self.dialogue_tree = dialogue_tree
        self.requires_input = dialogue_tree.requires_input()
    
    def interact(self) -> str:
        return self.dialogue_tree.get_current_text()
    
    def respond_to_input(self, player_input: str) -> str:
        response = self.dialogue_tree.advance(player_input)
        self.requires_input = self.dialogue_tree.requires_input()
        return response
    
    def is_conversation_complete(self) -> bool:
        return self.dialogue_tree.is_at_end()
    
    def reset_conversation(self):
        self.dialogue_tree.reset()
        self.requires_input = self.dialogue_tree.requires_input()