import pygame
import openai
import os
import pygame_menu
from entities import Player, AINPC, Entity, ShopNPC
from dialogue import DialogueSystem
from constants import *

class Game:
    def __init__(self):
        # Initialize pygame display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("LLMatrix RPG")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Set initial game state
        self.state = "MENU"  # MENU, PLAYING, PAUSED, SHOPPING
        
        # Create game elements
        self.init_game_elements()
        
        # Create menu
        self.create_menu()
        
    def init_game_elements(self):
        """Initialize all game elements."""
        # OpenAI setup (optional)
        self.client = None
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        
        # Create game entities
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        # Create walls
        self.walls = [
            Entity(100, 100, 50, 200, RED),
            Entity(300, 200, 200, 50, RED),
            Entity(600, 300, 50, 200, RED),
        ]
        
        # Create NPCs
        self.npcs = []
        if self.client:
            self.npcs.append(
                AINPC(350, 300, YELLOW, self.client, 
                     "You are a helpful assistant.", 
                     "Hello, how can I assist you today?")
            )
        self.npcs.append(ShopNPC(400, 400, GREEN))
        
        # Initialize dialogue system
        self.dialogue_system = DialogueSystem()
        self.interacting_with = None
        self.interaction_cooldown = 0
    
    def create_menu(self):
        """Create the menu system."""
        # Theme
        self.theme = pygame_menu.themes.THEME_DARK.copy()
        self.theme.title_background_color = PURPLE
        self.theme.background_color = (0, 0, 0, 180)
        
        # Main menu
        self.main_menu = pygame_menu.Menu(
            'LLMatrix RPG', 
            SCREEN_WIDTH, 
            SCREEN_HEIGHT,
            theme=self.theme
        )
        
        self.main_menu.add.button('Start Game', self._start_game)
        self.main_menu.add.button('Quit', pygame_menu.events.EXIT)
        
        # Pause menu
        self.pause_menu = pygame_menu.Menu(
            'Game Paused', 
            SCREEN_WIDTH // 2, 
            SCREEN_HEIGHT // 2,
            theme=self.theme
        )
        
        self.pause_menu.add.button('Resume', self._resume_game)
        self.pause_menu.add.button('Main Menu', self._return_to_main)
        self.pause_menu.add.button('Quit', pygame_menu.events.EXIT)
        
        # Shop menu
        self.shop_menu = pygame_menu.Menu(
            'Shop',
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
            theme=self.theme
        )
        self.shop_menu.add.button('Buy', self.buy_item)
        self.shop_menu.add.button('Sell', self.sell_item)
        self.shop_menu.add.button('Exit', self.close_shop)
        
        # Set current menu
        self.current_menu = self.main_menu
    
    def _start_game(self):
        """Start the game (called from menu)."""
        self.state = "PLAYING"
        self.current_menu = None
        return pygame_menu.events.CLOSE
    
    def _resume_game(self):
        """Resume the game from pause."""
        self.state = "PLAYING"
        self.current_menu = None
        return pygame_menu.events.CLOSE
    
    def _return_to_main(self):
        """Return to main menu."""
        self.state = "MENU"
        self.current_menu = self.main_menu
        return pygame_menu.events.RESET
    
    def buy_item(self):
        """Close the shop menu and show a dialogue message."""
        self.close_shop()  # Close the shop menu
        self.dialogue_system.show_dialogue("I have potions for you")
    
    def sell_item(self):
        """Placeholder for sell logic."""
        print("Selling item...")
        self.close_shop()
    
    def close_shop(self):
        """Close the shop menu and return to the game."""
        self.state = "PLAYING"
        self.current_menu = None
    
    def open_shop(self):
        """Open the shop menu."""
        self.state = "SHOPPING"
        self.current_menu = self.shop_menu
    
    def handle_events(self):
        """Handle all game events."""
        events = pygame.event.get()
        
        # Check for quit event
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return
        
        # Handle menus if active
        if self.state in ["MENU", "PAUSED", "SHOPPING"]:
            if self.current_menu is not None:
                self.current_menu.update(events)
            return
        
        # Handle gameplay events
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Toggle pause or exit dialogue
                if event.key == pygame.K_ESCAPE:
                    if self.dialogue_system.active:
                        self.dialogue_system.close()
                        # Only reset conversation if interacting with an AINPC
                        if self.interacting_with and isinstance(self.interacting_with, AINPC):
                            self.interacting_with.reset_conversation()
                        self.interacting_with = None
                    else:
                        self.state = "PAUSED"
                        self.current_menu = self.pause_menu
                
                # Handle dialogue
                elif self.dialogue_system.input_mode:
                    if event.key == pygame.K_RETURN:
                        player_input = self.dialogue_system.submit_input()
                        if self.interacting_with:
                            response = self.interacting_with.respond_to_input(player_input)
                            self.dialogue_system.show_dialogue(response)
                            self.dialogue_system.start_input_mode()
                    elif event.key == pygame.K_BACKSPACE:
                        self.dialogue_system.remove_character()
                    elif event.unicode and event.unicode.isprintable():
                        self.dialogue_system.add_character(event.unicode)
                
                # Interaction
                elif event.key == pygame.K_RETURN and self.interaction_cooldown <= 0:
                    if self.dialogue_system.active:
                        if self.dialogue_system.response_mode:
                            self.dialogue_system.start_input_mode()
                    else:
                        self.try_interaction()
                    self.interaction_cooldown = 10
                
                # Memory toggle
                elif event.key == pygame.K_m:
                    if self.interacting_with and isinstance(self.interacting_with, AINPC):
                        memory_status = self.interacting_with.toggle_memory()
                        self.dialogue_system.show_dialogue(f"[System: {memory_status}]", is_response=True)
    
    def try_interaction(self):
        """Try to interact with an NPC."""
        interaction_range = pygame.Rect(
            self.player.rect.x - 20,
            self.player.rect.y - 20,
            self.player.rect.width + 40,
            self.player.rect.height + 40
        )
        for npc in self.npcs:
            if interaction_range.colliderect(npc.rect):
                result = npc.interact()
                if result == "shop":
                    self.open_shop()
                    self.interacting_with = npc
                elif isinstance(result, str):
                    self.dialogue_system.show_dialogue(result, is_response=True)
                    self.interacting_with = npc
                break
    
    def update(self):
        """Update game state."""
        if self.state in ["MENU", "PAUSED", "SHOPPING"]:
            return
        if self.state == "PLAYING":
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
        """Draw everything to the screen."""
        self.screen.fill(BLACK)
        if self.state != "MENU":
            for wall in self.walls:
                wall.draw(self.screen)
            for npc in self.npcs:
                npc.draw(self.screen)
            self.player.draw(self.screen)
            self.dialogue_system.draw(self.screen)
        if self.current_menu is not None:
            self.current_menu.draw(self.screen)
        pygame.display.flip()
    
    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)