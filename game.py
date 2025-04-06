import pygame
import openai
import os
import pygame_menu
from entities import Player, AINPC, Entity, ShopNPC, StaticNPC
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
        
        # Add a Static NPC with dialogue
        villager_dialogue = {
            "default": {
                "messages": ["Hello there!", "I'm a local villager.", "How can I help you?"],
                "choices": [
                    {"text": "Tell me about this place", "next": "about_place"},
                    {"text": "I need information", "next": "information"},
                    {"text": "Goodbye", "next": None}
                ]
            },
            "about_place": {
                "messages": ["This is the town of Pixelburg.", "We've lived here for generations.", "It's a peaceful place, except for the monsters outside."],
                "next": "default"
            },
            "information": {
                "messages": ["What kind of information do you seek?", "I know many things about this area."],
                "choices": [
                    {"text": "Local rumors", "next": "rumors"},
                    {"text": "The nearby dungeon", "next": "dungeon"},
                    {"text": "Never mind", "next": "default"}
                ]
            },
            "rumors": {
                "messages": ["They say there's treasure hidden in the mountains.", "But no one has found it yet.", "Some believe it's just a myth."],
                "next": "default"
            },
            "dungeon": {
                "messages": ["The dungeon to the north is dangerous.", "Many have entered, few have returned.", "They say a powerful artifact lies within."],
                "next": "default"
            }
        }
        
        self.npcs.append(StaticNPC(500, 200, PURPLE, villager_dialogue, name="Villager"))
        
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
        """Start the game from the main menu."""
        self.state = "PLAYING"
        self.current_menu = None
        return pygame_menu.events.CLOSE
    
    def _resume_game(self):
        """Resume from pause."""
        self.state = "PLAYING"
        self.current_menu = None
        return pygame_menu.events.CLOSE
    
    def _return_to_main(self):
        """Go back to the main menu."""
        self.state = "MENU"
        self.current_menu = self.main_menu
        return pygame_menu.events.RESET
    
    def buy_item(self):
        """Close the shop and show a sequence of messages."""
        self.close_shop()
        self.dialogue_system.show_dialogue([
            "I have potions for you!",
            "They're quite handy in a pinch.",
            "Would you like to buy one?",
        ])

    def sell_item(self):
        """Placeholder for selling shit."""
        print("Selling item...")
        self.close_shop()

    def close_shop(self):
        """Close the shop and get back to playing."""
        self.state = "PLAYING"
        self.current_menu = None

    def open_shop(self):
        """Open the shop menu."""
        self.state = "SHOPPING"
        self.current_menu = self.shop_menu

    def handle_events(self):
        """Handle all the fucking events."""
        events = pygame.event.get()
        
        # Quit the game
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return
        
        # Handle menus
        if self.state in ["MENU", "PAUSED", "SHOPPING"]:
            if self.current_menu is not None:
                self.current_menu.update(events)
            return
        
        # Handle gameplay events
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Escape key: advance dialogue or pause
                if event.key == pygame.K_ESCAPE:
                    if self.dialogue_system.active:
                        # If choices are displayed, escape closes the dialogue
                        if self.dialogue_system.has_choices and self.dialogue_system.current_index == len(self.dialogue_system.messages) - 1:
                            self.dialogue_system.close()
                            if isinstance(self.interacting_with, StaticNPC):
                                self.interacting_with.reset_dialogue()
                            self.interacting_with = None
                        else:
                            self.dialogue_system.next_message()
                            if not self.dialogue_system.active:
                                if self.interacting_with and isinstance(self.interacting_with, AINPC):
                                    self.interacting_with.reset_conversation()
                                elif isinstance(self.interacting_with, StaticNPC):
                                    self.interacting_with.reset_dialogue()
                                self.interacting_with = None
                    else:
                        self.state = "PAUSED"
                        self.current_menu = self.pause_menu
                
                # Enter key: also advance dialogue or select choice
                elif event.key == pygame.K_RETURN:
                    if self.dialogue_system.active and not self.dialogue_system.input_mode:
                        # If displaying choices and at last message, select the currently highlighted choice
                        if self.dialogue_system.has_choices and self.dialogue_system.current_index == len(self.dialogue_system.messages) - 1:
                            if isinstance(self.interacting_with, StaticNPC):
                                choice_index = self.dialogue_system.get_selected_choice()
                                messages, has_choices, choices = self.interacting_with.advance_dialogue(choice_index)
                                
                                if messages:
                                    self.dialogue_system.show_dialogue_with_choices(
                                        messages, 
                                        choices if has_choices else None,
                                        self.interacting_with.name,
                                        self.interacting_with.sprite
                                    )
                                else:
                                    # End dialogue if no more messages
                                    self.dialogue_system.close()
                                    self.interacting_with = None
                        # For response mode dialogues, start input mode instead of advancing
                        elif self.dialogue_system.response_mode:
                            self.dialogue_system.start_input_mode()
                        # For regular dialogues, advance to next message
                        else:
                            self.dialogue_system.next_message()
                            if not self.dialogue_system.active:
                                if self.interacting_with and isinstance(self.interacting_with, AINPC):
                                    self.interacting_with.reset_conversation()
                                self.interacting_with = None
                    # Dialogue input handling
                    elif self.dialogue_system.input_mode:
                        player_input = self.dialogue_system.submit_input()
                        if self.interacting_with:
                            response = self.interacting_with.respond_to_input(player_input)
                            self.dialogue_system.show_dialogue(response)
                            self.dialogue_system.start_input_mode()
                    # Interact with NPCs
                    elif self.interaction_cooldown <= 0:
                        self.try_interaction()
                        self.interaction_cooldown = 10
                
                # Navigate choices with arrow keys
                elif self.dialogue_system.has_choices and self.dialogue_system.current_index == len(self.dialogue_system.messages) - 1:
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.dialogue_system.select_next_choice()
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.dialogue_system.select_prev_choice()
                
                # Dialogue input handling - backspace
                elif self.dialogue_system.input_mode and event.key == pygame.K_BACKSPACE:
                    self.dialogue_system.remove_character()
                # Add printable characters to input
                elif self.dialogue_system.input_mode and event.unicode and event.unicode.isprintable():
                    self.dialogue_system.add_character(event.unicode)
                
                # Toggle NPC memory
                elif event.key == pygame.K_m:
                    if self.interacting_with and isinstance(self.interacting_with, AINPC):
                        memory_status = self.interacting_with.toggle_memory()
                        self.dialogue_system.show_dialogue(f"[System: {memory_status}]", is_response=True)
    
    def try_interaction(self):
        """Try interacting with an NPC nearby."""
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
                elif result == "static_dialogue" and isinstance(npc, StaticNPC):
                    # Handle static NPC dialogue
                    messages, has_choices, choices = npc.get_current_dialogue()
                    self.dialogue_system.show_dialogue_with_choices(
                        messages,
                        choices if has_choices else None,
                        npc.name,
                        npc.sprite
                    )
                    self.interacting_with = npc
                elif isinstance(result, str):
                    self.dialogue_system.show_dialogue(result, is_response=True)
                    self.interacting_with = npc
                break
    
    def update(self):
        """Update the game state."""
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
        """Draw all the shit on the screen."""
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
        """Run the main fucking game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)