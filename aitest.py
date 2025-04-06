import pygame
import openai
import os
import sys

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Simple Dialogue System")
clock = pygame.time.Clock()

# Set up font
font = pygame.font.SysFont("Arial", 24)

# Get OpenAI API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: Please set the OPENAI_API_KEY environment variable.")
    sys.exit(1)

# New client instance for OpenAI API
client = openai.OpenAI(api_key=api_key)

# Initialize conversation with system and assistant messages
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "assistant", "content": "Hello! How can I help you today?"}
]
user_input = ""

# Function to wrap text to fit within a maximum width
def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = []
    current_width = 0
    space_width = font.size(' ')[0]
    
    for word in words:
        word_width = font.size(word)[0]
        if current_width + word_width <= max_width:
            current_line.append(word)
            current_width += word_width + space_width
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_width = word_width + space_width
    if current_line:
        lines.append(' '.join(current_line))
    return lines

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_BACKSPACE:
                user_input = user_input[:-1]
            elif event.key == pygame.K_RETURN:
                if user_input.strip():
                    messages.append({"role": "user", "content": user_input})
                    try:
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=messages
                        )
                        assistant_message = response.choices[0].message.content
                        messages.append({"role": "assistant", "content": assistant_message})
                    except Exception as e:
                        print(f"API Error: {e}")
                        messages.append({"role": "assistant", "content": "Sorry, I couldn't respond right now."})
                    user_input = ""
            elif event.unicode and event.unicode.isprintable() and len(user_input) < 100:
                user_input += event.unicode

    # Clear the screen
    screen.fill((255, 255, 255))  # White background

    # Render conversation (y=0 to y=500)
    line_height = 30
    y_position = 500 - line_height
    for message in reversed(messages):
        if message["role"] == "user":
            prefix = "User: "
            color = (0, 0, 255)  # Blue
        elif message["role"] == "assistant":
            prefix = "Assistant: "
            color = (255, 0, 0)  # Red
        else:
            continue  # Skip system messages
        
        text = prefix + message["content"]
        lines = wrap_text(text, font, 780)  # 800 - 20 for margins
        for line in reversed(lines):
            if y_position >= 0:
                text_surface = font.render(line, True, color)
                screen.blit(text_surface, (10, y_position))
                y_position -= line_height
            if y_position < 0:
                break
        if y_position < 0:
            break

    # Render input area (y=500 to y=600)
    input_text = "You: " + user_input
    input_surface = font.render(input_text, True, (0, 0, 0))  # Black
    screen.blit(input_surface, (10, 510))

    # Update display
    pygame.display.flip()
    clock.tick(60)  # Limit to 60 FPS

# Quit Pygame
pygame.quit()
sys.exit()