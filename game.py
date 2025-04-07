import pygame
import openai
import os
import logging
from entities import Player, AINPC, Entity
from dialogue import DialogueSystem, DialogueState
from constants import *

class Game:
    def __init__(self):
        # Initialize Pygame display and clock
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Simple 2D RPG")
        self.clock = pygame.time.Clock()
        self.running = True

        # Configure logging to file
        logging.basicConfig(filename='game.log', level=logging.INFO)

        # Load OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set. AI NPCs require an API key.")
        self.client = openai.OpenAI(api_key=api_key)

        # Initialize game entities
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.walls = [
            Entity(100, 100, 50, 200, RED),
            Entity(300, 200, 200, 50, RED),
            Entity(600, 300, 50, 200, RED),
        ]
        self.npcs = [
            AINPC(350, 300, YELLOW, self.client, "You are a helpful assistant.", "Hello, how can I assist you today?")
        ]

        # Initialize dialogue system and interaction variables
        self.dialogue_system = DialogueSystem()
        self.interacting_with = None
        self.interaction_cooldown = 0

    def handle_input(self):
        """Handle all user input and game events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == RESPONSE_READY:
                # Handle AI response readiness
                if self.dialogue_system.state == DialogueState.WAITING_FOR_RESPONSE:
                    self.dialogue_system.show_dialogue(event.message)
                    # Automatically transition to input mode instead of just showing dialogue
                    self.dialogue_system.start_input_mode()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Close dialogue or quit game
                    if self.dialogue_system.state != DialogueState.INACTIVE:
                        self.dialogue_system.close()
                        if self.interacting_with:
                            self.interacting_with.reset_conversation()
                        self.interacting_with = None
                    else:
                        self.running = False
                elif self.dialogue_system.state == DialogueState.INPUT_MODE:
                    # Handle text input in input mode
                    if event.key == pygame.K_RETURN:
                        player_input = self.dialogue_system.submit_input()
                        self.interacting_with.respond_to_input_async(player_input)
                        self.dialogue_system.start_waiting_for_response()
                    elif event.key == pygame.K_BACKSPACE:
                        self.dialogue_system.remove_character()
                    elif event.unicode and event.unicode.isprintable():
                        self.dialogue_system.add_character(event.unicode)
                elif event.key == pygame.K_RETURN and self.interaction_cooldown <= 0:
                    # Only use Enter to initiate interaction with NPCs
                    if self.dialogue_system.state == DialogueState.INACTIVE:
                        self.try_interaction()
                    self.interaction_cooldown = INTERACTION_COOLDOWN
                elif event.key == pygame.K_m:
                    # Toggle NPC memory (debug feature)
                    if self.interacting_with and isinstance(self.interacting_with, AINPC):
                        memory_status = self.interacting_with.toggle_memory()
                        self.dialogue_system.show_dialogue(f"[System: {memory_status}]")

    def try_interaction(self):
        """Attempt to interact with an NPC within range."""
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
                    self.dialogue_system.show_dialogue(dialogue)
                    # Start input mode immediately after showing initial dialogue
                    self.dialogue_system.start_input_mode()
                    self.interacting_with = npc
                break

    def update(self):
        """Update game state."""
        self.handle_input()
        self.dialogue_system.update()
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= 1
        if self.dialogue_system.state == DialogueState.INACTIVE:
            # Player movement when dialogue is inactive
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
        """Render all game elements to the screen."""
        self.screen.fill(BLACK)
        for wall in self.walls:
            wall.draw(self.screen)
        for npc in self.npcs:
            npc.draw(self.screen)
        self.player.draw(self.screen)
        self.dialogue_system.draw(self.screen)
        pygame.display.flip()

    def run(self):
        """Main game loop."""
        while self.running:
            self.update()
            self.draw()
            self.clock.tick(60)
