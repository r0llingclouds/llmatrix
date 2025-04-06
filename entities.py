import pygame
from typing import Tuple, List
from constants import *
import openai

class Entity:
    def __init__(self, x: int, y: int, width: int, height: int, color: Tuple[int, int, int]):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, self.color, self.rect)

class Player(Entity):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, PLAYER_SIZE, PLAYER_SIZE, BLUE)
        self.speed = PLAYER_SPEED
        self.inventory: List[str] = []

    def move(self, dx: int, dy: int, walls: List['Entity']):
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

class AINPC(Entity):
    def __init__(self, x: int, y: int, color: Tuple[int, int, int], client: openai.OpenAI, system_content: str, initial_assistant_content: str):
        super().__init__(x, y, NPC_SIZE, NPC_SIZE, color)
        self.client = client
        self.initial_history = [
            {"role": "system", "content": system_content},
            {"role": "assistant", "content": initial_assistant_content}
        ]
        self.conversation_history = self.initial_history.copy()
        self.is_conversational = True
        self.requires_input = True
        self.memory_enabled = True

    def interact(self) -> str:
        return self.conversation_history[1]["content"]

    def respond_to_input(self, player_input: str) -> str:
        self.conversation_history.append({"role": "user", "content": player_input})
        try:
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
        return False

    def reset_conversation(self):
        if not self.memory_enabled:
            self.conversation_history = self.initial_history.copy()
        else:
            self.conversation_history.append(
                {"role": "system", "content": "The player has ended this conversation and started a new one."}
            )
            self.trim_history_if_needed()

    def trim_history_if_needed(self, max_messages=20):
        if len(self.conversation_history) > max_messages + len(self.initial_history):
            preserved_messages = len(self.initial_history)
            self.conversation_history = (
                self.conversation_history[:preserved_messages] +
                self.conversation_history[-(max_messages - preserved_messages):]
            )
            self.conversation_history.insert(
                preserved_messages,
                {"role": "system", "content": "Some earlier conversation history has been summarized to save space."}
            )

    def toggle_memory(self):
        self.memory_enabled = not self.memory_enabled
        if not self.memory_enabled:
            self.conversation_history = self.initial_history.copy()
        return f"Memory {'enabled' if self.memory_enabled else 'disabled'}"

class ShopNPC(Entity):
    def __init__(self, x: int, y: int, color: Tuple[int, int, int]):
        super().__init__(x, y, NPC_SIZE, NPC_SIZE, color)

    def interact(self) -> str:
        return "shop"

class StaticNPC(Entity):
    def __init__(self, x: int, y: int, color: Tuple[int, int, int], dialogue_data: dict, name: str = None, sprite: pygame.Surface = None):
        super().__init__(x, y, NPC_SIZE, NPC_SIZE, color)
        self.dialogue_data = dialogue_data
        self.name = name or "NPC"
        self.sprite = sprite
        self.current_dialogue_key = "default"
    
    def interact(self) -> str:
        return "static_dialogue"
    
    def advance_dialogue(self, choice_index: int = None) -> tuple:
        """
        Advance dialogue based on player choice or to next dialogue sequence.
        Returns (messages, has_choices, choices)
        """
        current = self.dialogue_data[self.current_dialogue_key]
        
        # If choice_index is provided and there are choices, follow that branch
        if choice_index is not None and "choices" in current:
            if 0 <= choice_index < len(current["choices"]):
                next_key = current["choices"][choice_index]["next"]
                if next_key is not None:
                    self.current_dialogue_key = next_key
                    return self.get_current_dialogue()
                return None, False, []  # End conversation
        
        # If no choice but there's a next dialogue, advance to it
        elif "next" in current and current["next"]:
            self.current_dialogue_key = current["next"]
            return self.get_current_dialogue()
        
        # Default: end conversation
        return None, False, []
    
    def get_current_dialogue(self) -> tuple:
        """
        Get current dialogue messages and choices.
        Returns (messages, has_choices, choices)
        """
        current = self.dialogue_data[self.current_dialogue_key]
        messages = current.get("messages", [])
        has_choices = "choices" in current
        choices = current.get("choices", [])
        return messages, has_choices, choices
    
    def reset_dialogue(self):
        """Reset dialogue to default starting point."""
        self.current_dialogue_key = "default"