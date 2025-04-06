import pygame
from typing import List, Tuple
from constants import *
from dialogue import DialogueTree
import openai  # Required for AINPC

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
        return item_name.lower() in (item.lower() for item in self.inventory)

class NPC(Entity):
    """Non-player character with simple dialogue"""
    def __init__(self, x: int, y: int, color: Tuple[int, int, int], dialogue: List[str]):
        super().__init__(x, y, NPC_SIZE, NPC_SIZE, color)
        self.dialogue = dialogue
        self.dialogue_index = 0
        self.requires_input = False
        self.is_conversational = False  # Indicates this is not a conversational NPC
    
    def interact(self) -> str:
        if self.dialogue_index < len(self.dialogue):
            message = self.dialogue[self.dialogue_index]
            self.dialogue_index += 1
            return message
        self.dialogue_index = 0  # Reset for next interaction
        return ""

class InteractiveNPC(NPC):
    """NPC with a dialogue tree for interactive conversations"""
    def __init__(self, x: int, y: int, color: Tuple[int, int, int], dialogue_tree: DialogueTree):
        super().__init__(x, y, color, [dialogue_tree.get_current_text()])
        self.dialogue_tree = dialogue_tree
        self.requires_input = dialogue_tree.requires_input()
        self.is_conversational = True  # Mark as conversational
    
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
        
    def peek_next_response(self) -> str:
        """Preview the next dialogue response without advancing the conversation
        
        Returns:
            str: The text of the next node, or empty string if at the end
        """
        if not self.dialogue_tree.current_node:
            return ""
        
        # Temporarily store the current node
        current = self.dialogue_tree.current_node
        
        # Get next node without permanently advancing
        next_node = current.get_next_node("")  # Empty string for non-input nodes
        
        # If there's no next node, return empty string
        if not next_node:
            return ""
            
        return next_node.text

class AINPC(NPC):
    """NPC with AI-powered dialogue using OpenAI API with persistent memory"""
    def __init__(self, x: int, y: int, color: Tuple[int, int, int], client: openai.OpenAI, system_content: str, initial_assistant_content: str):
        super().__init__(x, y, color, [])
        self.client = client
        self.initial_history = [
            {"role": "system", "content": system_content},
            {"role": "assistant", "content": initial_assistant_content}
        ]
        self.conversation_history = self.initial_history.copy()
        self.is_conversational = True
        self.requires_input = True
        self.memory_enabled = True  # Flag to enable/disable memory
    
    def interact(self) -> str:
        """Returns the initial greeting from the assistant"""
        return self.conversation_history[1]["content"]
    
    def respond_to_input(self, player_input: str) -> str:
        """Processes player input and generates an AI response with memory management"""
        self.conversation_history.append({"role": "user", "content": player_input})
        try:
            # Trim history before API call if needed
            # self.trim_history_if_needed()
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_history
            )
            assistant_message = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            return assistant_message
        except Exception as e:
            print(f"API Error: {e}")
            return "Sorry, I couldn't respond right now."
    
    def is_conversation_complete(self) -> bool:
        """AINPC conversations are open-ended"""
        return False
    
    def reset_conversation(self):
        """
        Only resets to initial state if memory is disabled.
        With memory enabled, just adds a session separator.
        """
        if not self.memory_enabled:
            # Traditional reset - wipes memory
            self.conversation_history = self.initial_history.copy()
        else:
            # Add a separator to mark the end of a conversation session
            # but maintain all previous history
            self.conversation_history.append(
                {"role": "system", "content": "The player has ended this conversation and started a new one."}
            )
            
            # Trim history if needed after adding the separator
            self.trim_history_if_needed()
    
    def trim_history_if_needed(self, max_messages=20):
        """Trims conversation history if it gets too long, preserving system prompts"""
        # Always keep the initial system messages
        if len(self.conversation_history) > max_messages + len(self.initial_history):
            # Keep the initial messages and the most recent ones
            preserved_messages = len(self.initial_history)
            self.conversation_history = (
                self.conversation_history[:preserved_messages] + 
                self.conversation_history[-(max_messages-preserved_messages):]
            )
            # Add a summary message about trimmed history
            self.conversation_history.insert(
                preserved_messages,
                {"role": "system", "content": "Some earlier conversation history has been summarized to save space."}
            )
    
    def peek_next_response(self) -> str:
        """AINPC conversations are always ongoing, so always returns non-empty string"""
        return "..."  # This is never displayed, just used for checking
    
    def toggle_memory(self):
        """Toggle memory persistence on/off"""
        self.memory_enabled = not self.memory_enabled
        if not self.memory_enabled:
            # If turning memory off, reset to initial state
            self.conversation_history = self.initial_history.copy()
        return f"Memory {'enabled' if self.memory_enabled else 'disabled'}"