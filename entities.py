import pygame
import threading
import logging
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
            logging.error(f"API Error: {e}")
            return "Sorry, I couldn't respond right now."

    def respond_to_input_async(self, player_input: str) -> None:
        def api_call():
            self.conversation_history.append({"role": "user", "content": player_input})
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=self.conversation_history
                )
                assistant_message = response.choices[0].message.content
                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                self.trim_history_if_needed()
                pygame.event.post(pygame.event.Event(RESPONSE_READY, {"message": assistant_message}))
            except Exception as e:
                logging.error(f"API Error: {e}")
                error_message = "Sorry, I couldn't respond."
                self.conversation_history.append({"role": "assistant", "content": error_message})
                pygame.event.post(pygame.event.Event(RESPONSE_READY, {"message": error_message}))

        threading.Thread(target=api_call).start()

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