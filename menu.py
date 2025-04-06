import pygame
import pygame_menu
from constants import *
import sys

class MenuSystem:
    def __init__(self, screen):
        self.screen = screen
        self.main_menu = None
        self.options_menu = None
        self.pause_menu = None
        self.current_menu = None
        
        # Theme for all menus
        self.theme = pygame_menu.themes.THEME_DARK.copy()
        self.theme.title_background_color = PURPLE
        self.theme.background_color = (0, 0, 0, 180)  # Semi-transparent background
        self.theme.widget_font = pygame_menu.font.FONT_OPEN_SANS
        self.theme.title_font = pygame_menu.font.FONT_OPEN_SANS_BOLD
        self.theme.title_font_size = 36
        self.theme.widget_font_size = 24
        
        # Menu music and sound effects
        self.sound_enabled = True
        self.music_volume = 0.7
        self.sfx_volume = 0.5
        
        self.create_menus()
    
    def create_menus(self):
        # Main Menu
        self.main_menu = pygame_menu.Menu(
            'LLMatrix RPG', 
            SCREEN_WIDTH, 
            SCREEN_HEIGHT,
            theme=self.theme
        )
        
        self.main_menu.add.button('Start Game', self.start_game)
        self.main_menu.add.button('Options', self.open_options)
        self.main_menu.add.button('Quit', pygame_menu.events.EXIT)
        
        # Options Menu
        self.options_menu = pygame_menu.Menu(
            'Options', 
            SCREEN_WIDTH, 
            SCREEN_HEIGHT,
            theme=self.theme
        )
        
        self.options_menu.add.toggle_switch(
            'Sound Effects', 
            self.sound_enabled, 
            onchange=self.toggle_sound
        )
        
        self.options_menu.add.range_slider(
            'Music Volume', 
            default=self.music_volume,
            range_values=(0, 1),
            increment=0.1,
            onchange=self.set_music_volume
        )
        
        self.options_menu.add.range_slider(
            'SFX Volume', 
            default=self.sfx_volume,
            range_values=(0, 1),
            increment=0.1,
            onchange=self.set_sfx_volume
        )
        
        self.options_menu.add.button('Back', pygame_menu.events.BACK)
        
        # Pause Menu
        self.pause_menu = pygame_menu.Menu(
            'Paused', 
            SCREEN_WIDTH//2, 
            SCREEN_HEIGHT//2,
            center_content=True,
            theme=self.theme
        )
        
        self.pause_menu.add.button('Resume', self.resume_game)
        self.pause_menu.add.button('Options', self.open_pause_options)
        self.pause_menu.add.button('Main Menu', self.confirm_exit_to_main)
        self.pause_menu.add.button('Quit Game', self.confirm_quit)
        
        # Confirmation Menu for quitting to main menu
        self.confirm_main_menu = pygame_menu.Menu(
            'Return to Main Menu?', 
            SCREEN_WIDTH//2, 
            SCREEN_HEIGHT//3,
            theme=self.theme
        )
        
        self.confirm_main_menu.add.label('All unsaved progress will be lost')
        self.confirm_main_menu.add.button('Yes', self.exit_to_main)
        self.confirm_main_menu.add.button('No', pygame_menu.events.BACK)
        
        # Confirmation Menu for quitting game
        self.confirm_quit_menu = pygame_menu.Menu(
            'Quit Game?', 
            SCREEN_WIDTH//2, 
            SCREEN_HEIGHT//3,
            theme=self.theme
        )
        
        self.confirm_quit_menu.add.label('All unsaved progress will be lost')
        self.confirm_quit_menu.add.button('Yes', pygame_menu.events.EXIT)
        self.confirm_quit_menu.add.button('No', pygame_menu.events.BACK)
        
        # Set main menu as default
        self.current_menu = self.main_menu
    
    def show_main_menu(self):
        """Display the main menu and get the user selection."""
        self.current_menu = self.main_menu
        self.current_menu.enable()
    
    def show_pause_menu(self):
        """Display the pause menu."""
        self.current_menu = self.pause_menu
        self.current_menu.enable()
    
    def toggle_sound(self, value):
        """Toggle sound effects on/off."""
        self.sound_enabled = value
        # Implement actual sound toggling here
    
    def set_music_volume(self, value):
        """Set music volume."""
        self.music_volume = value
        # Implement actual volume setting here
    
    def set_sfx_volume(self, value):
        """Set sound effects volume."""
        self.sfx_volume = value
        # Implement actual volume setting here
    
    def start_game(self):
        """Start or resume the game."""
        # This will be overridden by the Game class
        self.current_menu.disable()
        return pygame_menu.events.CLOSE
    
    def resume_game(self):
        """Resume the game from pause."""
        # Just disable the current menu to return to gameplay
        self.current_menu.disable()
        return pygame_menu.events.CLOSE
    
    def open_options(self):
        """Open options menu from main menu."""
        self.current_menu = self.options_menu
    
    def open_pause_options(self):
        """Open options menu from pause menu."""
        # This is a placeholder, can be replaced with direct options
        self.current_menu = self.options_menu
    
    def confirm_exit_to_main(self):
        """Show confirmation before exiting to main menu."""
        self.current_menu = self.confirm_main_menu
    
    def confirm_quit(self):
        """Show confirmation before quitting game."""
        self.current_menu = self.confirm_quit_menu
    
    def exit_to_main(self):
        """Exit current game and return to main menu."""
        # This method needs to be connected to the Game.return_to_main_menu
        # The connection will be made in Game.__init__
        self.current_menu.disable()
        return pygame_menu.events.BACK
    
    def update(self, events):
        """Update the menu with given events."""
        if self.current_menu and self.current_menu.is_enabled():
            self.current_menu.update(events)
    
    def draw(self):
        """Draw the current menu if it's enabled."""
        if self.current_menu and self.current_menu.is_enabled():
            self.current_menu.draw(self.screen)