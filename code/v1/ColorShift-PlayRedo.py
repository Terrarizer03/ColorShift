import pygame as py
import time, threading, os, json, random as rd
import button

py.init()

DISPLAY_WIDTH, DISPLAY_HEIGHT = 1600, 900   # Display Size.
clock = py.time.Clock()
fps = 60 

screen = py.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))

# Dictionary to track currently held keys
key_states = {
    "red": False,
    "blue": False,
    "green": False,
    "yellow": False
}

# Dictionary to track which keys are in active hit window
key_hit_windows = {
    "red": False,
    "blue": False,
    "green": False,
    "yellow": False
}

# Dictionary to track when keys were pressed (for hit window timing)
key_press_times = {
    "red": 0,
    "blue": 0,
    "green": 0,
    "yellow": 0
}

spawn_positions = {
    "lane1": 573,
    "lane2": 723,
    "lane3": 873,
    "lane4": 1023
}

# Hit window duration in milliseconds
HIT_WINDOW_DURATION = 150

selected_song = None
song_library = []
song_buttons = []

# FONTS
# ======================
comfortaa_font_path = os.path.join("Rhythm Game", "assets", "fonts", "Comfortaa-VariableFont_wght.ttf")
comfortaa_font = py.font.Font(comfortaa_font_path, 46)
sub_font = py.font.Font(comfortaa_font_path, 32)
# ======================

current_color = {"color": "gray"}
fade_event = threading.Event()

class Note:
    NOTERADIUS = 35  # Base radius at reference resolution
    FADE_DURATION = 500  # milliseconds

    def __init__(self, x, color, timestamp):
        self.pos = [x, -100]
        self.color = color
        self.color_rgb = py.Color(color) if isinstance(color, str) else color
        self.speed = 10
        self.direction = "down"
        self.timestamp = timestamp
        self.active = True  # Note starts active
        self.missed = False
        self.is_fading = False
        self.hit = False
        self.creation_time = time.time()  # Track when the note was created
        self.fade_start_time = None
        self.alpha = 255
        self.scale_factor = 1.0

    def update_position(self):
        # Updates the note's position based on speed and direction.
        if self.direction == "down":
            self.pos[1] += self.speed

    def move(self):
        # Handles note movement and checks for a hit/miss.
        self.update_position()

        # Only check for hits when the note is in the hit area
        if 775 <= self.pos[1] <= 850:
            self.check_hit()
        # Mark as missed if it passes the hit area without being hit
        elif self.pos[1] > 850 and not self.hit:
            self.missed = True

    def check_hit(self):
        # Checks if the note color matches any of the currently active colors in hit window.
        if not self.active or self.hit:
            return
            
        # Get the list of currently active colors that are in hit window
        active_hit_colors = [color for color, is_active in key_hit_windows.items() if is_active]
        
        # If the note's color is among the active hit window colors, mark it as hit
        if self.color in active_hit_colors:
            self.hit = True
            self.is_fading = True
            self.fade_start_time = time.time()
            self.active = False

    def fade_out(self):
        # Handles fading effect ONLY when the note is hit; missed notes keep moving until off-screen.
        if not self.hit:  # If note is NOT hit, allow it to keep moving until it disappears
            if self.pos[1] > DISPLAY_HEIGHT + 150:  # Once off-screen, deactivate it
                self.missed = True  # Mark as missed once out of play area
                self.active = False  
            return

        # If note is hit, apply fading effect
        if not self.is_fading:
            return

        elapsed = time.time() - self.fade_start_time
        if elapsed >= self.FADE_DURATION / 1000:
            self.is_fading = False
            self.active = False  # Remove note when fade completes
            return

        # Apply scale and alpha reduction for fade effect
        self.scale_factor = 1 + (elapsed / (self.FADE_DURATION / 1000))
        self.alpha = max(255 - int((elapsed / (self.FADE_DURATION / 1000)) * 255), 0)

    def draw(self, screen):
        # Draws the note with proper alpha fading.
        if not self.active and not self.is_fading:
            return

        self.fade_out()  # Ensure fading updates before drawing

        scaled_radius = int(self.NOTERADIUS * self.scale_factor)

        # Create a temporary surface with per-pixel alpha support
        temp_surface = py.Surface((scaled_radius * 2, scaled_radius * 2), py.SRCALPHA)
        
        # Apply fade color, including alpha
        fade_color = (*self.color_rgb[:3], self.alpha)
        py.draw.circle(temp_surface, fade_color, (scaled_radius, scaled_radius), scaled_radius)

        # Blit the faded surface onto the screen
        screen.blit(temp_surface, (self.pos[0] - scaled_radius, self.pos[1] - scaled_radius))

class Song:
    def __init__(self, json_path):
        self.json_path = json_path
        self.title = None
        self.artist = None
        self.song = None
        self.notes = []
        self.fadeout_started = False
        self.fadeout_start_time = 0
        self.rating = 0
        self.note_info = None


        self.load_metadata_and_notes()

    def load_metadata_and_notes(self):
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(f"{self.json_path} does not exist.")
        with open(self.json_path, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                raise ValueError(f"Failed to decode JSON from {self.json_path}")
        
        self.title = data.get('song_name', 'Unknown Title')
        self.artist = data.get('song_artist', 'Unknown Artist')
        self.song = py.mixer.Sound(data.get('song_path', 'No Song'))

        note_data = data.get('notes')
        self.note_info = note_data
        self.notes = self.load_notes(note_data)

    def load_notes(self, note_data):
        if not note_data:
            return []
        
        spawn_positions = {
            "lane1": 573,
            "lane2": 723,
            "lane3": 873,
            "lane4": 1023
        }
                    
        return [
            Note(spawn_positions[n['x']], n['color'], n['timestamp']) for n in note_data
            ]
    
    def play_song(self):
        self.song.play()

    def stop_song(self):
        if not self.fadeout_started:
            self.fadeout_started = True
            self.fadeout_start_time = py.time.get_ticks()

        elapsed = py.time.get_ticks() - self.fadeout_start_time
        if elapsed >= 500:  # 1000ms fade-out duration
            self.song.stop()
            self.fadeout_started = False
        else:
            self.song.fadeout(500)

    def reset_notes(self):
        self.song.stop()
        self.notes.clear()
        self.load_metadata_and_notes()

# SONG LOADING & NOTESPAWNING
# ========================
def load_song_library(folder_path):
    songs = []
    for subfolder in os.listdir(folder_path):
        subfolder_path = os.path.join(folder_path, subfolder)
        if os.path.isdir(subfolder_path):
            json_files = [f for f in os.listdir(subfolder_path) if f.endswith('.json')]
            if json_files:
                full_path = os.path.join(subfolder_path, json_files[0])
                try:
                    song = Song(full_path)
                    songs.append(song)
                except Exception as e:
                    print(f"Error loading {json_files[0]}: {e}")
    return songs

def create_song_buttons(songs, start_x, start_y, spacing_y, font):
    buttons = []
    for i, song in enumerate(songs):
        y = start_y + i * spacing_y
        song_text = f"{song.title} - {song.artist}"
        
        song_button = button.Button(
            audio=None,
            pos=(start_x, y),
            current_pos=start_x,  # Start at the proper position
            text_input=song_text,
            font=font,
            base_color="white",
            hovering_color="black",
            scale=1.0,
            padding=(20, 10),
            has_audio=False
        )
        
        buttons.append((song_button, song))
    
    return buttons
# ========================

def mix_colors():
    # Create a rainbow gradient based on currently held keys.
    active_colors = [color for color, state in key_states.items() if state]
    
    if not active_colors:
        return "gray"
    elif len(active_colors) == 1:
        return active_colors[0]
    else:
        # Create rainbow gradient from active colors
        # First, convert all color names to their RGB values
        rgb_colors = [py.Color(color) for color in active_colors]
        
        # We'll create a special "rainbow" indicator
        # The line drawing function will know to use this for a rainbow effect
        return "rainbow_gradient:" + ",".join(active_colors)

def update_current_color():
    # Update the current color based on key states.
    current_color["color"] = mix_colors()

def update_hit_windows():
    # Update which keys are in active hit window based on timing.
    current_time = py.time.get_ticks()
    
    for color in key_hit_windows:
        # If key is held down, check if it's still in hit window
        if key_states[color]:
            elapsed_since_press = current_time - key_press_times[color]
            # Only allow hit if within the hit window duration
            key_hit_windows[color] = elapsed_since_press <= HIT_WINDOW_DURATION
        else:
            # If key is not pressed, no hit window
            key_hit_windows[color] = False

def keybinds():
    global game_state
    
    for event in py.event.get():
        if event.type == py.QUIT:
            py.quit()
        elif event.type == py.KEYDOWN:
            if game_state == "song_select":
                if event.key == py.K_ESCAPE:
                    py.quit()
            elif game_state == "play":
                current_time = py.time.get_ticks()
                if event.key == py.K_ESCAPE:
                    game_state = "song_select"
                    selected_song.stop_song()
                elif event.key == py.K_q:
                    key_states["red"] = True
                    key_press_times["red"] = current_time
                    key_hit_windows["red"] = True
                elif event.key == py.K_w:
                    key_states["blue"] = True
                    key_press_times["blue"] = current_time
                    key_hit_windows["blue"] = True
                elif event.key == py.K_o:
                    key_states["green"] = True
                    key_press_times["green"] = current_time
                    key_hit_windows["green"] = True
                elif event.key == py.K_p:
                    key_states["yellow"] = True
                    key_press_times["yellow"] = current_time
                    key_hit_windows["yellow"] = True
                    
        elif event.type == py.KEYUP:
            if game_state == "play":
                if event.key == py.K_q:
                    key_states["red"] = False
                    key_hit_windows["red"] = False
                elif event.key == py.K_w:
                    key_states["blue"] = False
                    key_hit_windows["blue"] = False
                elif event.key == py.K_o:
                    key_states["green"] = False
                    key_hit_windows["green"] = False
                elif event.key == py.K_p:
                    key_states["yellow"] = False
                    key_hit_windows["yellow"] = False
        
    # Update the current color after processing key events
    update_current_color()

def draw_play_area():
    bar_width = 10

    # Play Area
    py.draw.line(screen, "white", (498, 0), (498, 804), 2) # Side Bars
    py.draw.line(screen, "white", (1100, 0), (1100, 804), 2)
    
    # Hit area indicator (subtle outline)
    py.draw.rect(screen, (50, 50, 50), (498, 775, 604, 75), 2)
    
    # Check if we need to draw a rainbow gradient
    if isinstance(current_color["color"], str) and current_color["color"].startswith("rainbow_gradient:"):
        # Extract the active colors from the string
        color_names = current_color["color"].split(":", 1)[1].split(",")
        
        # Create a surface for the gradient line
        gradient_surface = py.Surface((600, bar_width), py.SRCALPHA)
        
        # Calculate segment width based on number of colors
        segment_width = 600 // len(color_names)
        
        # Draw each color segment
        for i, color_name in enumerate(color_names):
            start_x = i * segment_width
            end_x = (i + 1) * segment_width
            color_value = py.Color(color_name)
            
            # Add visual indicator for active hit window
            if key_hit_windows[color_name]:
                # Make the color brighter for hit window
                brightness_boost = 50
                r = min(color_value.r + brightness_boost, 255)
                g = min(color_value.g + brightness_boost, 255)
                b = min(color_value.b + brightness_boost, 255)
                color_value = py.Color(r, g, b)
                
            py.draw.rect(gradient_surface, color_value, (start_x, 0, segment_width, bar_width))
        
        # Draw the gradient line
        screen.blit(gradient_surface, (500, 800 - bar_width // 2))
    else:
        # Main Line with current mixed color
        color_to_use = current_color["color"]
        # Single color case - add visual indicator for hit window
        if color_to_use in key_hit_windows and key_hit_windows[color_to_use]:
            color_value = py.Color(color_to_use)
            brightness_boost = 50
            r = min(color_value.r + brightness_boost, 255)
            g = min(color_value.g + brightness_boost, 255)
            b = min(color_value.b + brightness_boost, 255)
            color_to_use = py.Color(r, g, b)
        else:
            color_value = py.Color(color_to_use)
            
        py.draw.line(screen, color_to_use, (500, 800), (1100, 800), bar_width)

    # Draw hit window indicators for each active color
    font = py.font.SysFont('Arial', 14)
    
    # Display hit window status
    for i, (color, is_active) in enumerate(key_hit_windows.items()):
        if key_states[color]:  # Only show for held keys
            status = "ACTIVE" if is_active else "HOLDING"
            color_rgb = py.Color(color)
            text = font.render(f"{color}: {status}", True, color_rgb)
            screen.blit(text, (1120, 780 + i*20))

def song_select():
    global selected_song, game_state, song_buttons, start_time, song_library, button_cooldown

    if button_cooldown > 0:
        button_cooldown -= 1

    # Create song buttons if they don't exist yet
    if not song_buttons and song_library:
        song_buttons = create_song_buttons(
            song_library, 
            DISPLAY_WIDTH // 2,  # Center x
            200,                 # Start y position 
            80,                  # Spacing between buttons
            sub_font             # Font to use
        )
    
    # Draw background
    screen.fill((30, 30, 30))
    
    # Draw title
    title_text = comfortaa_font.render("Select a Song", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(DISPLAY_WIDTH // 2, 100))
    screen.blit(title_text, title_rect)
    
    # Draw buttons and handle clicks
    mouse_pos = py.mouse.get_pos()
    mouse_pressed = py.mouse.get_pressed()[0]
    
    for btn, song in song_buttons:
        # Update button hover state
        btn.change_color(mouse_pos)
        btn.update(screen)
        
        # Handle button clicks
        if btn.check_for_input(mouse_pos) and mouse_pressed and button_cooldown == 0:
            if selected_song == song and button_cooldown == 0:
                selected_song.reset_notes()
                selected_song.play_song()
                # Start the song
                selected_song = song
                start_time = py.time.get_ticks()
                game_state = "play"
                print(f"Starting song: {song.title}")
            else:
                # Just select the song
                selected_song = song
                print(f"Selected song: {song.title}")
        
        # Highlight selected song
        if selected_song == song:
            py.draw.rect(screen, (0, 255, 0), btn.button_rect, 3)

    keys = py.key.get_pressed()
    if keys[py.K_r]:
        song_library = load_song_library(os.path.join("Rhythm Game", "song_library"))
        song_buttons = create_song_buttons(
            song_library,
            DISPLAY_WIDTH // 2,
            200,
            80,
            sub_font
        )

    keybinds()

def play():
    screen.fill((0, 0, 0))
    
    # Update hit windows based on timing
    update_hit_windows()

    draw_play_area()

    current_time = py.time.get_ticks() - start_time

    # Update and draw all active notes
    # Use the selected song's notes
    if selected_song and hasattr(selected_song, 'notes'):
        for note in selected_song.notes:
            if note.timestamp <= current_time and (note.active or note.is_fading):
                if note.active:
                    note.move()
                note.draw(screen)

    # Display song info
    if selected_song:
        song_text = sub_font.render(f"{selected_song.title}", True, (200, 200, 200))
        screen.blit(song_text, (20, 20))   
        
# NO NEED TO CHANGE
# =====================
def main():
    global game_state, button_cooldown, start_time

    # Load song library at startup
    try:
        song_library = load_song_library(os.path.join("Rhythm Game", "song_library"))
        print(f"Loaded {len(song_library)} songs")
    except Exception as e:
        print(f"Error loading song library: {e}")
        song_library = []

    button_cooldown = 0
    game_state = "song_select"
    start_time = py.time.get_ticks()

    # Main game loop
    while True:

        if game_state == "play":
            play()
        elif game_state == "song_select":
            song_select()
    
        keybinds()

        for event in py.event.get():
            if event.type == py.QUIT:
                py.quit()
                
        py.display.flip()
        clock.tick(fps)
    # Quit Pygame
    py.quit()

if __name__ == "__main__":
    main()