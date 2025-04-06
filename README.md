# Dialogue System Design and Technical Specification

## 1. Overview

The dialogue system is a fundamental component of this 2D top-down RPG built with Pygame. It facilitates interactions between the player and non-player characters (NPCs) through text-based conversations. The system supports both simple, linear dialogues and complex, branching conversations that adapt to player choices and game state, enhancing the game's interactivity and storytelling capabilities.

## 2. Design Goals

The dialogue system is designed with the following objectives:

- **NPC Communication**: Enable NPCs to convey information, instructions, or story elements to the player.
- **Player Agency**: Allow players to influence conversation flow through input or choices.
- **Dynamic Responses**: Support dialogue that changes based on the player's inventory or other game conditions.
- **Game Integration**: Permit dialogue choices to trigger in-game events, such as starting quests.
- **User-Friendly UI**: Present dialogue in a clear, visually appealing manner without obstructing gameplay.

## 3. Features

- **Simple Dialogue**: NPCs can deliver a sequence of predefined lines, displayed sequentially upon interaction.
- **Interactive Dialogue**: Supports branching conversations where the flow depends on player input or predefined conditions.
- **Text Display**: Dialogue appears in a semi-transparent box at the bottom of the screen for easy reading.
- **Input Handling**: Players can type responses to specific dialogue prompts, influencing the conversation.
- **Conditional Transitions**: Conversation paths can diverge based on conditions like inventory items or player actions.
- **Actions**: Dialogue nodes can execute functions to trigger game events, such as quest initiation.

## 4. Components

The dialogue system comprises several key classes, each with distinct responsibilities:

- **DialogueNode**: Represents a single point in a conversation, containing text, input requirements, conditional transitions, and optional actions.
- **DialogueTree**: Organizes multiple `DialogueNode` instances into a tree structure, managing conversation flow.
- **DialogueSystem**: Manages the user interface, rendering dialogue text, and collecting player input.
- **NPC**: A basic entity with a list of dialogue lines for simple, linear interactions.
- **InteractiveNPC**: An advanced NPC that leverages a `DialogueTree` for complex, branching conversations.

## 5. Usage Scenarios

### Simple NPC Interaction
- **Steps**:
  1. Player approaches an NPC and presses `Enter`.
  2. The NPC displays the next line from its dialogue list.
  3. The conversation continues line-by-line with each `Enter` press.
  4. When all lines are exhausted, the dialogue resets to the beginning.
- **Purpose**: Ideal for delivering static information or greetings.

### Interactive NPC Interaction
- **Steps**:
  1. Player approaches an `InteractiveNPC` and presses `Enter`.
  2. The conversation begins at the root of the `DialogueTree`.
  3. If the current node requires input, the player types a response and submits it with `Enter`.
  4. The conversation advances based on the input or game conditions.
  5. The dialogue ends when a terminal node (leaf) is reached.
- **Purpose**: Enables dynamic, player-driven conversations with conditional outcomes.

## 6. Technical Details

### 6.1 DialogueNode

#### Attributes
- **`text: str`**: The text displayed to the player.
- **`is_input: bool`**: Indicates if player input is required to proceed.
- **`conditional_next: List[Tuple[Optional[str], Callable[[], bool], DialogueNode]]`**: List of conditional transitions, each with an optional input pattern, a condition function, and the next node.
- **`default_next: Optional[DialogueNode]`**: Fallback node if no conditions are met.
- **`action: Optional[Callable[[], None]]`**: Function executed when the node is entered.

#### Methods
- **`add_conditional_next(pattern: Optional[str], condition: Callable[[], bool], next_node: DialogueNode)`**: Adds a conditional transition based on input and/or game state.
- **`set_default_next(next_node: DialogueNode)`**: Sets the default next node.
- **`get_next_node(player_input: str = "") -> Optional[DialogueNode]`**: Determines the next node based on player input and conditions.
- **`enter()`**: Executes the node's action, if defined.

### 6.2 DialogueTree

#### Attributes
- **`root: DialogueNode`**: The starting node of the conversation.
- **`current_node: DialogueNode`**: The current position within the tree.

#### Methods
- **`reset()`**: Resets `current_node` to `root`.
- **`get_current_text() -> str`**: Returns the text of the current node.
- **`requires_input() -> bool`**: Checks if the current node needs player input.
- **`advance(player_input: str = "") -> str`**: Advances to the next node based on input and returns its text.
- **`is_at_end() -> bool`**: Returns `True` if the conversation has concluded (i.e., `current_node` is `None`).

### 6.3 DialogueSystem

#### Attributes
- **`font: pygame.Font`**: Font used for rendering text (default: system font, size 24).
- **`active: bool`**: Whether the dialogue UI is currently displayed.
- **`input_mode: bool`**: Whether the system is awaiting player input.
- **`response_mode: bool`**: Indicates if the current text is an NPC response.
- **`final_response: bool`**: Indicates if this is the last message in the conversation.
- **`current_text: str`**: The text being displayed.
- **`input_text: str`**: The player's typed input.
- **Rendering Attributes**: Various surfaces and rects for positioning and drawing the UI.

#### Methods
- **`show_dialogue(text: str, is_response: bool = False, is_final: bool = False)`**: Displays the specified text with optional response or final flags.
- **`start_input_mode()`**: Switches to input mode, showing a text field.
- **`add_character(char: str)`**: Appends a character to `input_text` (up to `INPUT_MAX_LENGTH`).
- **`remove_character()`**: Deletes the last character from `input_text`.
- **`submit_input() -> str`**: Returns the input text and exits input mode.
- **`close()`**: Hides the dialogue UI and resets its state.
- **`update()`**: Manages cursor blinking (toggles every 30 frames).
- **`draw(surface: pygame.Surface)`**: Renders the dialogue box, text, and input field (if applicable).

### 6.4 NPC and InteractiveNPC

#### NPC
- **Attributes**:
  - **`dialogue: List[str]`**: List of dialogue lines.
  - **`dialogue_index: int`**: Current position in the dialogue list.
  - **`requires_input: bool`**: Always `False` for basic NPCs.
- **Methods**:
  - **`interact() -> str`**: Returns the next dialogue line and increments the index; resets to 0 when finished.

#### InteractiveNPC
- **Attributes**:
  - **`dialogue_tree: DialogueTree`**: The conversation tree.
  - **`requires_input: bool`**: Reflects whether the current node needs input.
- **Methods**:
  - **`interact() -> str`**: Returns the current node's text.
  - **`respond_to_input(player_input: str) -> str`**: Advances the tree based on input and updates `requires_input`.
  - **`is_conversation_complete() -> bool`**: Checks if the tree has reached its end.
  - **`reset_conversation()`**: Resets the tree to its root node.

## 7. Interaction Flow

1. **Initiation**: Player presses `Enter` within an NPC's interaction range (a 60x60 pixel rect around the player).
2. **Simple NPCs**:
   - The next line from `dialogue` is displayed.
   - Pressing `Enter` advances to the next line or closes the dialogue if finished.
3. **Interactive NPCs**:
   - Displays the current `DialogueNode` text.
   - If input is required, enters `input_mode`; player types and submits with `Enter`.
   - The tree advances based on input or conditions, displaying the next node's text.
   - Continues until a leaf node is reached, then closes with `Enter`.
4. **UI Handling**:
   - Dialogue appears in a semi-transparent box at the screen bottom.
   - Input mode shows a text field with a blinking cursor.
   - Instructions ("Press Enter to continue/exit") guide the player.

## 8. Example Implementations

This section provides both high-level descriptions and concrete code examples to illustrate how to implement various types of dialogues using the dialogue system.

### 8.1 Simple NPC Dialogue
**Description**: A basic NPC that delivers a sequence of predefined lines.

**Code Example**:
```python
simple_npc = NPC(200, 200, GREEN, [
    "Hello traveler! Welcome to this simple RPG.",
    "Use WASD or arrow keys to move around.",
    "Press Enter to interact with NPCs like me!"
])
self.npcs.append(simple_npc)
```

### 8.2 Interactive NPC with Simple Sequential Dialogue
**Description**: An interactive NPC with a dialogue tree that progresses sequentially without requiring player input.

**Code Example**:
```python
simple_dialogue = DialogueTree("Hello, adventurer!")
simple_dialogue.root.set_default_next(DialogueNode("Welcome to our village."))
simple_dialogue.root.default_next.set_default_next(DialogueNode("Feel free to look around."))
simple_dialogue.root.default_next.default_next.set_default_next(DialogueNode("Goodbye!"))
self.npcs.append(InteractiveNPC(350, 300, PURPLE, simple_dialogue))
```

### 8.3 Interactive NPC with Input-Based Dialogue
**Description**: An interactive NPC that asks for player input and responds based on the input provided.

**Code Example**:
```python
input_dialogue = DialogueTree("What brings you to our village?")
ask_reason = DialogueNode("Are you here to trade or to rest?", is_input=True)
input_dialogue.root.set_default_next(ask_reason)
trade_response = DialogueNode("Ah, a merchant! We have plenty of goods to offer.")
rest_response = DialogueNode("Rest well, traveler. The inn is just ahead.")
farewell = DialogueNode("Safe travels!")
ask_reason.add_conditional_next("trade", lambda: True, trade_response)
ask_reason.add_conditional_next("rest", lambda: True, rest_response)
ask_reason.set_default_next(DialogueNode("I'm not sure what you mean."))
trade_response.set_default_next(farewell)
rest_response.set_default_next(farewell)
self.npcs.append(InteractiveNPC(350, 300, PURPLE, input_dialogue))
```

### 8.4 Interactive NPC with Inventory Check
**Description**: An interactive NPC whose dialogue changes based on the player's inventory, requiring player input to proceed.

**Code Example**:
```python
inventory_dialogue = DialogueTree("Hello, do you have the key to the dungeon?")
ask_key = DialogueNode("Do you have the key?", is_input=True)
has_key_response = DialogueNode("Great! You can enter the dungeon now.")
no_key_response = DialogueNode("You don't have the key! Don't lie to me.")
need_key_response = DialogueNode("You need to find the key first.")
invalid_response = DialogueNode("Please answer yes or no.")
dungeon_farewell = DialogueNode("Good luck in the dungeon!")
goodbye = DialogueNode("Goodbye.")
come_back = DialogueNode("Come back when you have the key.")
inventory_dialogue.root.set_default_next(ask_key)
ask_key.add_conditional_next("yes", lambda: self.player.has_item('key'), has_key_response)
ask_key.add_conditional_next("yes", lambda: not self.player.has_item('key'), no_key_response)
ask_key.add_conditional_next("no", lambda: True, need_key_response)
ask_key.set_default_next(invalid_response)
has_key_response.set_default_next(dungeon_farewell)
no_key_response.set_default_next(goodbye)
need_key_response.set_default_next(come_back)
self.npcs.append(InteractiveNPC(350, 300, PURPLE, inventory_dialogue))
```

### 8.5 Interactive NPC with Quest Initiation
**Description**: An interactive NPC that can start a quest based on the player's input.

**Code Example**:
```python
quest_dialogue = DialogueTree("I have a quest for you. Are you interested?")
ask_quest = DialogueNode("Do you want to take the quest to defeat the goblin king?", is_input=True)
accept_quest = DialogueNode("Excellent! The goblin king is in the forest.", action=lambda: self.start_quest('goblin_quest'))
reject_quest = DialogueNode("Maybe another time then.")
invalid_response = DialogueNode("Please answer yes or no.")
good_luck = DialogueNode("Good luck, hero!")
farewell = DialogueNode("Farewell.")
quest_dialogue.root.set_default_next(ask_quest)
ask_quest.add_conditional_next("yes", lambda: True, accept_quest)
ask_quest.add_conditional_next("no", lambda: True, reject_quest)
ask_quest.set_default_next(invalid_response)
accept_quest.set_default_next(good_luck)
reject_quest.set_default_next(farewell)
self.npcs.append(InteractiveNPC(350, 300, PURPLE, quest_dialogue))
```

### 8.6 Interactive NPC with Conditional Dialogue Based on Inventory (No Input)
**Description**: An interactive NPC whose dialogue branches based on the player's inventory without requiring input.

**Code Example**:
```python
self.player.inventory.append("sword") 
dialogue = DialogueTree("Hello, adventurer!")
branch_node = DialogueNode("Let me see your equipment.", is_input=False)
has_sword_node = DialogueNode("Ah, you have a fine sword!", is_input=False)
no_sword_node = DialogueNode("You should get a sword for protection.", is_input=False)
end_node = DialogueNode("Safe travels!", is_input=False)
branch_node.add_conditional_next(None, lambda: self.player.has_item('sword'), has_sword_node)
branch_node.add_conditional_next(None, lambda: not self.player.has_item('sword'), no_sword_node)
has_sword_node.set_default_next(end_node)
no_sword_node.set_default_next(end_node)
dialogue.root.set_default_next(branch_node)
self.npcs.append(InteractiveNPC(350, 300, PURPLE, dialogue))
```

**Note**: The Shopkeeper Dialogue (8.1) and Quest Giver Dialogue (8.2) described above can be implemented using combinations of these examples. For instance, the Shopkeeper Dialogue involves input-based dialogue and inventory checks, similar to examples 8.5 and 8.6. The Quest Giver Dialogue uses input-based dialogue with actions, as shown in example 8.7. The code snippets assume the existence of methods like `self.player.has_item()` and `self.start_quest()`, which should be defined in your game logic.

### 8.7 Shopkeeper and Quest Giver Dialogues
- **Shopkeeper Dialogue**:
  1. "Hello there! I'm the shopkeeper. What can I help you with?"
  2. "What's your name, traveler?" (Input required)
  3. "What kind of item are you looking for?" (Input required)
  4. Responses:
     - If "sword" and player has a sword: "A sword? You already have one, adventurer!"
     - If "sword" and no sword: "A sword? Excellent choice for adventuring!"
     - If "shield": "A shield? Good thinking for protection."
     - If "potion": "Potions? Always handy in a tight spot."
     - Otherwise: "I don’t have that in stock, sorry!"
  5. "Safe travels, friend!"

- **Quest Giver Dialogue**:
  1. "Psst! Over here. I need someone brave for a special task."
  2. "Are you brave enough to help me?" (Input: "yes"/"y" or other)
  3. If "yes"/"y":
     - "Excellent! I need you to recover a lost artifact."
     - "The artifact is in a cave to the north. Will you go now?" (Input: "yes"/"y" or other)
     - If "yes"/"y": "Thank you, hero! Return when you have found it." (Triggers `start_quest`)
     - If other: "Please reconsider. The fate of the kingdom depends on it!" (Loops back)
  4. If other: "Oh... perhaps another time then."

First, create the dialogue trees for the NPCs:

```python
    def create_shopkeeper_dialogue(self) -> DialogueTree:
        """Create a dialogue tree for the shopkeeper with conditional responses."""
        dialogue = DialogueTree("Hello there! I'm the shopkeeper. What can I help you with?")
        
        # Define dialogue nodes
        name_question = DialogueNode("What's your name, traveler?", is_input=True)
        item_question = DialogueNode("What kind of item are you looking for?", is_input=True)
        sword_has = DialogueNode("A sword? You already have one, adventurer!")
        sword_none = DialogueNode("A sword? Excellent choice for adventuring!")
        shield_response = DialogueNode("A shield? Good thinking for protection.")
        potion_response = DialogueNode("Potions? Always handy in a tight spot.")
        default_item_response = DialogueNode("I don't have that in stock, sorry!")
        farewell = DialogueNode("Safe travels, friend!")
        
        # Set up dialogue flow
        dialogue.root.set_default_next(name_question)
        name_question.set_default_next(item_question)
        
        # Conditional transitions for item question
        item_question.add_conditional_next("sword", lambda: self.player.has_item('sword'), sword_has)
        item_question.add_conditional_next("sword", lambda: True, sword_none)
        item_question.add_conditional_next("shield", lambda: True, shield_response)
        item_question.add_conditional_next("potion", lambda: True, potion_response)
        item_question.set_default_next(default_item_response)
        
        # Link all responses to farewell
        sword_has.set_default_next(farewell)
        sword_none.set_default_next(farewell)
        shield_response.set_default_next(farewell)
        potion_response.set_default_next(farewell)
        default_item_response.set_default_next(farewell)
        
        return dialogue
    
    def create_quest_dialogue(self) -> DialogueTree:
        """Create a dialogue tree for the quest giver with actions."""
        dialogue = DialogueTree("Psst! Over here. I need someone brave for a special task.")
        
        # Define dialogue nodes
        ask_brave = DialogueNode("Are you brave enough to help me?", is_input=True)
        yes_response = DialogueNode("Excellent! I need you to recover a lost artifact.")
        no_response = DialogueNode("Oh... perhaps another time then.")
        quest_details = DialogueNode("The artifact is in a cave to the north. Will you go now?", is_input=True)
        accept_quest = DialogueNode("Thank you, hero! Return when you have found it.", 
                                    action=lambda: self.start_quest('artifact_quest'))
        decline_quest = DialogueNode("Please reconsider. The fate of the kingdom depends on it!")
        
        # Set up dialogue flow
        dialogue.root.set_default_next(ask_brave)
        ask_brave.add_conditional_next("yes", lambda: True, yes_response)
        ask_brave.add_conditional_next("y", lambda: True, yes_response)
        ask_brave.set_default_next(no_response)
        yes_response.set_default_next(quest_details)
        quest_details.add_conditional_next("yes", lambda: True, accept_quest)
        quest_details.add_conditional_next("y", lambda: True, accept_quest)
        quest_details.set_default_next(decline_quest)
        decline_quest.set_default_next(quest_details)
        
        return dialogue
```

Then, initialize the NPCs with the dialogue trees:

```python
# Create dialogue trees for NPCs
shopkeeper_dialogue = self.create_shopkeeper_dialogue()
quest_dialogue = self.create_quest_dialogue()

#Initialize NPCs
self.npcs.append(
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
    InteractiveNPC(350, 300, PURPLE, shopkeeper_dialogue),
    InteractiveNPC(150, 400, (255, 165, 0), quest_dialogue)
)
```

## 9. Integration with Game

- **Game Class**: Manages the player, NPCs, walls, and dialogue system.
- **Input Handling**: The `handle_input` method processes key events (`Enter`, `Escape`, text input) to control dialogue flow.
- **State Management**: Disables player movement when `dialogue_system.active` is `True`, ensuring focus on the conversation.
- **Rendering**: The `draw` method renders all entities and the dialogue UI on the Pygame screen.
- **Interaction Cooldown**: Prevents spamming interactions with a 10-30 frame cooldown.

## 10. Future Enhancements

- **Multiple Choice**: Replace text input with predefined options for streamlined interactions.
- **Quest Tracking**: Integrate with a quest system to update objectives based on dialogue actions.
- **Complex Conditions**: Expand conditions to include player stats, previous choices, or time-based triggers.
- **Text Animation**: Add typewriter-style text display for a more engaging presentation.