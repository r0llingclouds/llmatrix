import pygame
import openai  # For OpenAI API integration
import os  # For environment variable access
from entities import Player, NPC, InteractiveNPC, AINPC, Entity
from dialogue import DialogueNode, DialogueTree, DialogueSystem
from constants import *

class Game:
    """Main game class managing all game elements"""
    def __init__(self):
        # Initialize Pygame window
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Simple 2D RPG")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None
            print("Warning: OPENAI_API_KEY not set. AI NPCs will not function.")
        
        # Create player at center of screen
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        # Define walls for collision
        self.walls = [
            Entity(100, 100, 50, 200, RED),
            Entity(300, 200, 200, 50, RED),
            Entity(600, 300, 50, 200, RED),
        ]

        self.npcs = []
        
        # Example InteractiveNPC with a dialogue tree
        dialogue = DialogueTree("Hello, adventurer!")
        branch_node = DialogueNode("Let me see your equipment.", is_input=False)
        has_sword_node = DialogueNode("Ah, you have a fine sword!", is_input=False)
        no_sword_node = DialogueNode("You should get a sword for protection.", is_input=False)
        end_node = DialogueNode("Safe travels!", is_input=False)
        dialogue.root.set_default_next(branch_node)
        branch_node.add_conditional_next(None, lambda: self.player.has_item('sword'), has_sword_node)
        branch_node.add_conditional_next(None, lambda: not self.player.has_item('sword'), no_sword_node)
        has_sword_node.set_default_next(end_node)
        no_sword_node.set_default_next(end_node)
        self.npcs.append(InteractiveNPC(350, 300, PURPLE, dialogue))
        
        # Add AINPC if OpenAI client is available, else fallback to simple NPC
        if self.client:
            self.npcs.append(AINPC(500, 300, YELLOW, self.client,
                                  "You are a wise old sage in a fantasy game.",
                                  "Greetings, traveler. What knowledge do you seek?"))
        else:
            self.npcs.append(NPC(500, 300, YELLOW, ["The sage is silent today."]))
        
        # Initialize dialogue system and interaction state
        self.dialogue_system = DialogueSystem()
        self.interacting_with = None
        self.interaction_cooldown = 0
    
    def handle_input(self):
        """Handle all user input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.dialogue_system.active:
                        self.dialogue_system.close()
                        if hasattr(self.interacting_with, 'reset_conversation'):
                            self.interacting_with.reset_conversation()
                        self.interacting_with = None
                    else:
                        self.running = False
                elif self.dialogue_system.input_mode:
                    if event.key == pygame.K_RETURN:
                        player_input = self.dialogue_system.submit_input()
                        if self.interacting_with.is_conversational:
                            response = self.interacting_with.respond_to_input(player_input)
                            is_final = self.interacting_with.is_conversation_complete()
                            if self.interacting_with.requires_input and not is_final:
                                self.dialogue_system.show_dialogue(response)
                                self.dialogue_system.start_input_mode()
                            else:
                                self.dialogue_system.show_dialogue(response, is_response=True, is_final=is_final)
                            if isinstance(self.interacting_with, InteractiveNPC) and self.interacting_with.dialogue_tree.current_node:
                                self.interacting_with.dialogue_tree.current_node.enter()
                    elif event.key == pygame.K_BACKSPACE:
                        self.dialogue_system.remove_character()
                    elif event.unicode and event.unicode.isprintable():
                        self.dialogue_system.add_character(event.unicode)
                elif event.key == pygame.K_RETURN and self.interaction_cooldown <= 0:
                    if self.dialogue_system.active:
                        if self.dialogue_system.response_mode:
                            if self.dialogue_system.final_response:
                                self.dialogue_system.close()
                                if hasattr(self.interacting_with, 'reset_conversation'):
                                    self.interacting_with.reset_conversation()
                                self.interacting_with = None
                                self.interaction_cooldown = 30
                            else:
                                if self.interacting_with.is_conversational:
                                    if self.interacting_with.requires_input:
                                        self.dialogue_system.start_input_mode()
                                    else:
                                        next_text = self.interacting_with.respond_to_input("")
                                        is_final = self.interacting_with.is_conversation_complete()
                                        self.dialogue_system.show_dialogue(next_text, is_response=True, is_final=is_final)
                                        if isinstance(self.interacting_with, InteractiveNPC) and self.interacting_with.dialogue_tree.current_node:
                                            self.interacting_with.dialogue_tree.current_node.enter()
                                else:  # Simple NPC
                                    next_dialogue = self.interacting_with.interact()
                                    if next_dialogue:
                                        self.dialogue_system.show_dialogue(next_dialogue, is_response=True)
                                    else:
                                        self.dialogue_system.close()
                                        self.interacting_with = None
                                        self.interaction_cooldown = 30
                    else:
                        self.try_interaction()
                    self.interaction_cooldown = 10
    
    def try_interaction(self):
        """Attempt to interact with an NPC within range"""
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
                    if isinstance(npc, InteractiveNPC):
                        npc.dialogue_tree.current_node.enter()
                break
    
    def update(self):
        """Update game state"""
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
        """Render all game elements"""
        self.screen.fill(BLACK)
        for wall in self.walls:
            wall.draw(self.screen)
        for npc in self.npcs:
            npc.draw(self.screen)
        self.player.draw(self.screen)
        self.dialogue_system.draw(self.screen)
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.update()
            self.draw()
            self.clock.tick(60)