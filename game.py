import pygame
import openai
import os
from entities import Player, AINPC, Entity
from dialogue import DialogueSystem
from constants import *

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Simple 2D RPG")
        self.clock = pygame.time.Clock()
        self.running = True

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set. AI NPCs require an API key.")
        self.client = openai.OpenAI(api_key=api_key)

        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        self.walls = [
            Entity(100, 100, 50, 200, RED),
            Entity(300, 200, 200, 50, RED),
            Entity(600, 300, 50, 200, RED),
        ]

        self.npcs = [
            AINPC(350, 300, YELLOW, self.client, "You are a helpful assistant.", "Hello, how can I assist you today?")
        ]

        self.dialogue_system = DialogueSystem()
        self.interacting_with = None
        self.interaction_cooldown = 0

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.dialogue_system.active:
                        self.dialogue_system.close()
                        if self.interacting_with:
                            self.interacting_with.reset_conversation()
                        self.interacting_with = None
                    else:
                        self.running = False
                elif self.dialogue_system.input_mode:
                    if event.key == pygame.K_RETURN:
                        player_input = self.dialogue_system.submit_input()
                        response = self.interacting_with.respond_to_input(player_input)
                        self.dialogue_system.show_dialogue(response)
                        self.dialogue_system.start_input_mode()
                    elif event.key == pygame.K_BACKSPACE:
                        self.dialogue_system.remove_character()
                    elif event.unicode and event.unicode.isprintable():
                        self.dialogue_system.add_character(event.unicode)
                elif event.key == pygame.K_RETURN and self.interaction_cooldown <= 0:
                    if self.dialogue_system.active:
                        if self.dialogue_system.response_mode:
                            self.dialogue_system.start_input_mode()
                    else:
                        self.try_interaction()
                    self.interaction_cooldown = 10
                elif event.key == pygame.K_m:
                    if self.interacting_with and isinstance(self.interacting_with, AINPC):
                        memory_status = self.interacting_with.toggle_memory()
                        self.dialogue_system.show_dialogue(f"[System: {memory_status}]", is_response=True)

    def try_interaction(self):
        interaction_range = pygame.Rect(
            self.player.rect.x - 20,
            self.player.rect.y - 20,
            self.player.rect.width + 40,
            self.player.rect.height + 40
        )
        for npc in self.npcs:
            if interaction_range.colliderect(npc.rect):
                dialogue = npc.interact()
                if dialogue:
                    self.dialogue_system.show_dialogue(dialogue, is_response=True)
                    self.interacting_with = npc
                break

    def update(self):
        self.handle_input()
        self.dialogue_system.update()
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= 1
        if not self.dialogue_system.active:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -self.player.speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = self.player.speed
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -self.player.speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = self.player.speed
            if dx != 0 or dy != 0:
                self.player.move(dx, dy, self.walls)

    def draw(self):
        self.screen.fill(BLACK)
        for wall in self.walls:
            wall.draw(self.screen)
        for npc in self.npcs:
            npc.draw(self.screen)
        self.player.draw(self.screen)
        self.dialogue_system.draw(self.screen)
        pygame.display.flip()

    def run(self):
        while self.running:
            self.update()
            self.draw()
            self.clock.tick(60)