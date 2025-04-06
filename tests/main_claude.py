import pygame
import sys
from typing import List, Dict, Tuple, Optional

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 5
PLAYER_SIZE = 40
NPC_SIZE = 40
DIALOGUE_PADDING = 10
FONT_SIZE = 24
INPUT_MAX_LENGTH = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (160, 32, 240)
DIALOGUE_BG = (50, 50, 50, 200)
INPUT_BG = (30, 30, 30, 220)

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simple 2D RPG")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, FONT_SIZE)

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
    
    def move(self, dx: int, dy: int, walls: List[Entity]):
        # Store original position to revert if collision occurs
        original_x = self.rect.x
        original_y = self.rect.y
        
        # Move x
        self.rect.x += dx
        # Check for collisions
        if any(self.rect.colliderect(wall.rect) for wall in walls):
            self.rect.x = original_x
        
        # Move y
        self.rect.y += dy
        # Check for collisions
        if any(self.rect.colliderect(wall.rect) for wall in walls):
            self.rect.y = original_y
        
        # Keep player on screen
        self.rect.x = max(0, min(SCREEN_WIDTH - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(SCREEN_HEIGHT - self.rect.height, self.rect.y))

class NPC(Entity):
    """Non-player character with dialogue"""
    def __init__(self, x: int, y: int, color: Tuple[int, int, int], dialogue: List[str]):
        super().__init__(x, y, NPC_SIZE, NPC_SIZE, color)
        self.dialogue = dialogue
        self.dialogue_index = 0
        self.requires_input = False
    
    def interact(self) -> str:
        """Return current dialogue line and advance to the next"""
        if self.dialogue_index < len(self.dialogue):
            message = self.dialogue[self.dialogue_index]
            self.dialogue_index += 1  # Changed: Don't loop back to beginning
            return message
        # Reset dialogue index for future interactions
        self.dialogue_index = 0
        return ""  # Return empty string when no more dialogue

class DialogueNode:
    """A node in a dialogue tree representing a question or statement"""
    def __init__(self, text: str, is_input: bool = False):
        self.text = text  # Text to display
        self.is_input = is_input  # Whether this requires player input
        self.responses = {}  # Map of player inputs to next dialogue nodes (for branching)
        self.default_next = None  # Default next node if not branching
    
    def add_response(self, player_input: str, next_node):
        """Add a specific response path"""
        self.responses[player_input.lower()] = next_node
        
    def set_default_next(self, next_node):
        """Set the default next node"""
        self.default_next = next_node
        
    def get_next_node(self, player_input: str = ""):
        """Get the next node based on player input"""
        if not self.is_input:
            return self.default_next
            
        # Check for specific responses (case insensitive)
        if player_input.lower() in self.responses:
            return self.responses[player_input.lower()]
        
        # If no specific match, use default
        return self.default_next


class DialogueTree:
    """A complete dialogue tree for an NPC conversation"""
    def __init__(self, greeting: str):
        # Create the root node (greeting)
        self.root = DialogueNode(greeting)
        self.current_node = self.root
    
    def reset(self):
        """Reset to the beginning of the dialogue tree"""
        self.current_node = self.root
    
    def get_current_text(self) -> str:
        """Get text for the current node"""
        if self.current_node:
            return self.current_node.text
        return ""
    
    def requires_input(self) -> bool:
        """Check if current node requires player input"""
        if self.current_node:
            return self.current_node.is_input
        return False
    
    def advance(self, player_input: str = "") -> str:
        """Advance to the next node based on player input"""
        if not self.current_node:
            return ""
            
        next_node = self.current_node.get_next_node(player_input)
        self.current_node = next_node
        
        if self.current_node:
            return self.current_node.text
        return ""
    
    def is_at_end(self) -> bool:
        """Check if we've reached the end of the dialogue tree"""
        return self.current_node is None
        
        
class InteractiveNPC(NPC):
    """NPC that can respond to player input using a flexible dialogue tree"""
    def __init__(self, x: int, y: int, color: Tuple[int, int, int], dialogue_tree: DialogueTree):
        super().__init__(x, y, color, [dialogue_tree.get_current_text()])
        self.dialogue_tree = dialogue_tree
        self.requires_input = dialogue_tree.requires_input()
    
    def interact(self) -> str:
        """Initial interaction returns the current dialogue node text"""
        return self.dialogue_tree.get_current_text()
    
    def respond_to_input(self, player_input: str) -> str:
        """Process player input and advance dialogue tree"""
        # Advance the dialogue tree based on input
        response = self.dialogue_tree.advance(player_input)
        
        # Update requirements for next interaction
        self.requires_input = self.dialogue_tree.requires_input()
        
        return response
    
    def is_conversation_complete(self) -> bool:
        """Check if we've reached the end of the dialogue tree"""
        return self.dialogue_tree.is_at_end()
    
    def reset_conversation(self):
        """Reset the conversation to the beginning"""
        self.dialogue_tree.reset()
        self.requires_input = self.dialogue_tree.requires_input()

class DialogueSystem:
    """Handles displaying dialogue on screen and text input"""
    def __init__(self):
        self.active = False
        self.input_mode = False
        self.response_mode = False  # Flag to track when we're showing a response
        self.final_response = False  # Flag for the final response in a conversation
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
        self.response_mode = is_response  # Set response mode flag
        self.final_response = is_final    # Set final response flag
        
        # Render text surface
        self.text_surface = font.render(text, True, WHITE)
        # Position text box at bottom of screen
        self.text_rect = self.text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        
        # Add appropriate instruction text
        if is_response:
            if is_final:
                instruction_text = "Press Enter to exit"
            else:
                instruction_text = "Press Enter to continue"
                
            self.instruction_surface = font.render(instruction_text, True, WHITE)
            self.instruction_rect = self.instruction_surface.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40)
            )
    
    def start_input_mode(self):
        self.input_mode = True
        self.response_mode = False
        self.final_response = False
        self.input_text = ""
        # Create input box
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
        # Update cursor blink
        self.cursor_timer += 1
        if self.cursor_timer >= 30:  # Toggle cursor visibility every 30 frames (0.5 seconds at 60 FPS)
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self, surface: pygame.Surface):
        if not self.active:
            return
        
        # Draw dialogue box background
        padding = DIALOGUE_PADDING
        dialogue_bg = pygame.Rect(
            self.text_rect.left - padding,
            self.text_rect.top - padding,
            self.text_rect.width + padding * 2,
            self.text_rect.height + padding * 2
        )
        
        # Create a surface with alpha for semi-transparency
        bg_surface = pygame.Surface((dialogue_bg.width, dialogue_bg.height), pygame.SRCALPHA)
        bg_surface.fill(DIALOGUE_BG)
        surface.blit(bg_surface, (dialogue_bg.left, dialogue_bg.top))
        
        # Draw text
        surface.blit(self.text_surface, self.text_rect)
        
        # Draw instruction if in response mode
        if self.response_mode:
            surface.blit(self.instruction_surface, self.instruction_rect)
        
        # Draw input box if in input mode
        if self.input_mode:
            # Draw input box background
            input_bg_surface = pygame.Surface((self.input_rect.width, self.input_rect.height), pygame.SRCALPHA)
            input_bg_surface.fill(INPUT_BG)
            surface.blit(input_bg_surface, self.input_rect)
            
            # Draw input text
            display_text = self.input_text
            if self.cursor_visible:
                display_text += "|"  # Add blinking cursor
            
            input_text_surface = font.render(display_text, True, WHITE)
            input_text_rect = input_text_surface.get_rect(midleft=(self.input_rect.left + 10, self.input_rect.centery))
            surface.blit(input_text_surface, input_text_rect)

class Game:
    """Main game class that manages all game elements"""
    def __init__(self):
        self.running = True
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        # Create walls
        self.walls = [
            Entity(100, 100, 50, 200, RED),
            Entity(300, 200, 200, 50, RED),
            Entity(600, 300, 50, 200, RED),
        ]
        
        # Create dialogue trees for NPCs
        shopkeeper_dialogue = self.create_shopkeeper_dialogue()
        quest_dialogue = self.create_quest_dialogue()
        
        # Create NPCs with dialogue
        self.npcs = [
            NPC(200, 200, GREEN, [
                "Hello traveler! Welcome to this simple RPG.",
                "Use WASD or arrow keys to move around.",
                "Press Enter to interact with NPCs like me!"
            ]),
            NPC(500, 400, YELLOW, [
                "I'm another NPC with different dialogue.",
                "The world is still under construction.",
                "Check back later for more content!"
            ]),
            # Add interactive NPCs with dialogue trees
            InteractiveNPC(350, 300, PURPLE, shopkeeper_dialogue),
            InteractiveNPC(150, 400, (255, 165, 0), quest_dialogue)  # Orange quest giver
        ]
        
        # Create dialogue system
        self.dialogue_system = DialogueSystem()
        
        # Track interaction state
        self.interacting_with = None
        self.interaction_cooldown = 0
    
    def create_shopkeeper_dialogue(self) -> DialogueTree:
        """Create a dialogue tree for the shopkeeper"""
        # Start with greeting
        dialogue = DialogueTree("Hello there! I'm the shopkeeper. What can I help you with?")
        
        # Create nodes
        name_question = DialogueNode("What's your name, traveler?", True)
        item_question = DialogueNode("What kind of item are you looking for?", True)
        sword_response = DialogueNode("A sword? Excellent choice for adventuring!")
        shield_response = DialogueNode("A shield? Good thinking for protection.")
        potion_response = DialogueNode("Potions? Always handy in a tight spot.")
        default_item_response = DialogueNode("I don't have that in stock, sorry!")
        farewell = DialogueNode("Safe travels, friend!")
        
        # Connect nodes
        dialogue.root.set_default_next(name_question)
        
        name_question.set_default_next(item_question)
        
        # Add specific responses for items
        item_question.add_response("sword", sword_response)
        item_question.add_response("shield", shield_response)
        item_question.add_response("potion", potion_response)
        item_question.set_default_next(default_item_response)
        
        # All item responses lead to farewell
        sword_response.set_default_next(farewell)
        shield_response.set_default_next(farewell)
        potion_response.set_default_next(farewell)
        default_item_response.set_default_next(farewell)
        
        # Farewell is the end (no next node)
        
        return dialogue
    
    def create_quest_dialogue(self) -> DialogueTree:
        """Create a dialogue tree for a quest giver"""
        # Start with greeting
        dialogue = DialogueTree("Psst! Over here. I need someone brave for a special task.")
        
        # Create nodes
        ask_brave = DialogueNode("Are you brave enough to help me?", True)
        yes_response = DialogueNode("Excellent! I need you to recover a lost artifact.")
        no_response = DialogueNode("Oh... perhaps another time then.")
        quest_details = DialogueNode("The artifact is in a cave to the north. Will you go now?", True)
        accept_quest = DialogueNode("Thank you, hero! Return when you have found it.")
        decline_quest = DialogueNode("Please reconsider. The fate of the kingdom depends on it!")
        
        # Connect nodes
        dialogue.root.set_default_next(ask_brave)
        
        # Branching based on bravery question
        ask_brave.add_response("yes", yes_response)
        ask_brave.add_response("y", yes_response)
        ask_brave.add_response("sure", yes_response)
        ask_brave.add_response("ok", yes_response)
        ask_brave.set_default_next(no_response)
        
        # Yes path continues to quest details
        yes_response.set_default_next(quest_details)
        
        # Quest acceptance branching
        quest_details.add_response("yes", accept_quest)
        quest_details.add_response("y", accept_quest)
        quest_details.add_response("sure", accept_quest)
        quest_details.add_response("ok", accept_quest)
        quest_details.set_default_next(decline_quest)
        
        # Decline leads back to asking if they'll go
        decline_quest.set_default_next(quest_details)
        
        return dialogue
    

    # Then in the Game class's handle_input method, fix the dialogue processing:
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Escape key - exit game or close dialogue
                    if self.dialogue_system.active:
                        self.dialogue_system.close()
                        if isinstance(self.interacting_with, InteractiveNPC):
                            self.interacting_with.reset_conversation()
                        self.interacting_with = None
                    else:
                        self.running = False
                elif self.dialogue_system.input_mode:
                    # Handle text input mode
                    if event.key == pygame.K_RETURN:
                        # Submit text input
                        player_input = self.dialogue_system.submit_input()
                        if isinstance(self.interacting_with, InteractiveNPC):
                            response = self.interacting_with.respond_to_input(player_input)
                            # Check if this is the final response in the conversation
                            is_final = self.interacting_with.is_conversation_complete()
                            
                            # If more input is required immediately after this response, show it as normal
                            if self.interacting_with.requires_input and not is_final:
                                self.dialogue_system.show_dialogue(response)
                                self.dialogue_system.start_input_mode()
                            else:
                                # Otherwise show as a response that will advance on next key press
                                self.dialogue_system.show_dialogue(response, is_response=True, is_final=is_final)
                    elif event.key == pygame.K_BACKSPACE:
                        # Remove character
                        self.dialogue_system.remove_character()
                    elif event.unicode and event.unicode.isprintable():
                        # Add character if printable
                        self.dialogue_system.add_character(event.unicode)
                elif event.key == pygame.K_RETURN and self.interaction_cooldown <= 0:
                    # Interaction key (Enter)
                    if self.dialogue_system.active:
                        # If showing a response from an interactive NPC
                        if self.dialogue_system.response_mode:
                            if self.dialogue_system.final_response:
                                # If it's the final response, exit dialogue completely
                                self.dialogue_system.close()
                                if isinstance(self.interacting_with, InteractiveNPC):
                                    self.interacting_with.reset_conversation()
                                self.interacting_with = None
                                self.interaction_cooldown = 30  # Longer cooldown to prevent immediate re-interaction
                            else:
                                # If not final, check if next node needs input
                                if isinstance(self.interacting_with, InteractiveNPC) and self.interacting_with.requires_input:
                                    self.dialogue_system.start_input_mode()
                                else:
                                    # Process next dialogue line
                                    if isinstance(self.interacting_with, InteractiveNPC):
                                        next_text = self.interacting_with.respond_to_input("")
                                        is_final = self.interacting_with.is_conversation_complete()
                                        self.dialogue_system.show_dialogue(next_text, is_response=True, is_final=is_final)
                                    elif isinstance(self.interacting_with, NPC):
                                        next_dialogue = self.interacting_with.interact()
                                        if next_dialogue:
                                            # If there's more dialogue, show it
                                            self.dialogue_system.show_dialogue(next_dialogue, is_response=True)
                                        else:
                                            # If no more dialogue, close
                                            self.dialogue_system.close()
                                            self.interacting_with = None
                                            self.interaction_cooldown = 30
                        # For first interaction with NPCs
                        elif isinstance(self.interacting_with, NPC):
                            if isinstance(self.interacting_with, InteractiveNPC):
                                if self.interacting_with.requires_input:
                                    self.dialogue_system.start_input_mode()
                                else:
                                    # Advance to next node without input
                                    next_text = self.interacting_with.respond_to_input("")
                                    is_final = self.interacting_with.is_conversation_complete()
                                    self.dialogue_system.show_dialogue(next_text, is_response=True, is_final=is_final)
                            else:
                                # Get next dialogue for regular NPC
                                next_dialogue = self.interacting_with.interact()
                                if next_dialogue:
                                    # If there's more dialogue, show it as a response (will advance on next key press)
                                    self.dialogue_system.show_dialogue(next_dialogue, is_response=True)
                                else:
                                    # If no more dialogue, close
                                    self.dialogue_system.close()
                                    self.interacting_with = None
                                    self.interaction_cooldown = 30
                    else:
                        # Try to interact with nearby NPCs
                        self.try_interaction()
                    self.interaction_cooldown = 10  # Set cooldown to prevent multiple interactions
    
    def try_interaction(self):
        """Check for nearby NPCs to interact with"""
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
                    self.interacting_with = npc
                    break
    
    def update(self):
        self.handle_input()
        self.dialogue_system.update()  # Update dialogue system for cursor blinking
        
        # Decrement interaction cooldown if active
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= 1
        
        # Handle movement if not in dialogue
        if not self.dialogue_system.active:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            
            # WASD or arrow keys for movement
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
        # Clear screen
        screen.fill(BLACK)
        
        # Draw walls
        for wall in self.walls:
            wall.draw(screen)
        
        # Draw NPCs
        for npc in self.npcs:
            npc.draw(screen)
        
        # Draw player
        self.player.draw(screen)
        
        # Draw dialogue if active
        self.dialogue_system.draw(screen)
        
        # Update display
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.update()
            self.draw()
            clock.tick(60)  # 60 FPS

# Start the game
if __name__ == "__main__":
    game = Game()
    game.run()
    
    # Clean up
    pygame.quit()
    sys.exit()