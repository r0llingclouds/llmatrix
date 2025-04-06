# main.py

import pygame
import sys
import pygame_menu
from constants import *

# Import the game after defining simplified menu
from game import Game

if __name__ == "__main__":
    # Initialize pygame and its modules
    pygame.init()
    pygame.font.init()
    
    # Create and run the game
    game = Game()
    
    # Run the main game loop
    game.run()
    
    # Clean up and exit
    pygame.quit()
    sys.exit()