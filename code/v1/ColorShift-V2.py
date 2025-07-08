# WARNING: If you are viewing this code as an outsider and not a developer, this code is held up by sticks, glue, and my will to live (which is very little), and is very confusing.
# If you don't know what you're doing, don't touch anything. If you do, still don't touch anything. This game will, most probably, break. You have been warned.

import pygame as py
import random, math, json, os, time, button

# Initialize Pygame
py.init()
py.font.init()

# Use relative paths for better portability
icon = py.image.load(os.path.join("Rhythm Game", "assets", "textures", "icon.png"))
hitsound = py.mixer.Sound(os.path.join("Rhythm Game", "assets", "sounds", "osu-hit-sound.mp3"))
misssound = py.mixer.Sound(os.path.join("Rhythm Game", "assets", "sounds", "miss-sound.mp3"))
click_sound = py.mixer.Sound(os.path.join("Rhythm Game", "assets", "sounds", "click-sound.wav"))
click_sound.set_volume(0.2)
py.display.set_icon(icon)  # Set the custom icon

# Resolution settings
DISPLAY_WIDTH, DISPLAY_HEIGHT = 1600, 900   # Display Size.
BOX_SIZE = 800  # Fixed box size for gameplay area
fps = 60  # default fps
current_side = "down"  # Default side

# Set up the display
screen = py.display.set_mode((1600, 900)) # FIXED DISPLAY (CANNOT BE BOTHERED TO DO RESOLUTION SCALING)
py.display.set_caption("ColorShift")
clock = py.time.Clock()
running = True

selected_song = None
song_library = []
song_buttons = []
start_time = 0

time_offset = 1000

# FONTS
# ======================
comfortaa_font_path = os.path.join("Rhythm Game", "assets", "fonts", "Comfortaa-VariableFont_wght.ttf")
comfortaa_font = py.font.Font(comfortaa_font_path, 46)
sub_font = py.font.Font(comfortaa_font_path, 32)
# ======================

colors = [(0, 255, 0), (0, 0, 255), (255, 0, 0), (255, 255, 0), (128, 128, 128)]  # green[0], blue[1], red[2], yellow[3], gray[4]
note_colors = {"green": (0, 255, 0), "blue": (0, 0, 255), "red": (255, 0, 0), "yellow": (255, 255, 0)}
current_colors = {"left": colors[4], "right": colors[4], "down": colors[4], "up": colors[4]}

side_colors = {
    "white": (255, 255, 255),
    "gray": (128, 128, 128),
}
intro_colors = {
    "white": (240, 240, 240),
    "black": (0, 0, 0),
    "red": (255, 50, 25),
    "green": (0, 255, 0),
    "blue": (78, 63, 255),
    "yellow": (240, 255, 25),
}

def fade_out(screen, speed=5):
    fade_surface = py.Surface(screen.get_size())
    fade_surface.fill((0, 0, 0))
    for alpha in range(0, 256, speed):
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        py.display.update()
        py.time.delay(5)  # delay to control fade speed

    original = screen.copy()
    screen_rect = screen.get_rect()
    clock = py.time.Clock()
    
    for scale in range(100, 0, -speed):
        shrink_factor = scale / 100.0
        new_size = (int(screen_rect.width * shrink_factor), int(screen_rect.height * shrink_factor))
        scaled_surface = py.transform.smoothscale(original, new_size)
        
        # Clear screen
        screen.fill((0, 0, 0))
        
        # Blit scaled surface to the center
        x = (screen_rect.width - new_size[0]) // 2
        y = (screen_rect.height - new_size[1]) // 2
        screen.blit(scaled_surface, (x, y))
        
        py.display.update()
        clock.tick(60)  # Smooth 60 FPS


def fade_in(screen, speed=5):
    fade_surface = py.Surface(screen.get_size())
    fade_surface.fill((0, 0, 0))
    for alpha in range(255, -1, -speed):
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        py.display.update()
        py.time.delay(20)  # delay to control fade speed

# Calculate the position of the box
def get_box_coordinates():
    # The box should be centered on the screen
    box_left = (DISPLAY_WIDTH - BOX_SIZE) // 2
    box_top = (DISPLAY_HEIGHT - BOX_SIZE) // 2
    box_right = box_left + BOX_SIZE
    box_bottom = box_top + BOX_SIZE
    
    return {
        "left": box_left,
        "top": box_top,
        "right": box_right,
        "bottom": box_bottom,
        "center_x": DISPLAY_WIDTH // 2,  # Exact center of the screen
        "center_y": DISPLAY_HEIGHT // 2  # Exact center of the screen
    }

# Helper function to scale a single value (like radius, thickness)
def scale_value(value):
    # Use a fixed scale factor based on the box size
    scale_factor = BOX_SIZE / 800  # Since we want 800x800 as our reference
    return int(value * scale_factor)

start_time = py.time.get_ticks()
bounce_amplitude = scale_value(5)  # Max bounce in pixels
bounce_speed = 2  # Controls how fast the arrow bounces

class Note:
    NOTERADIUS = 25  # Base radius at reference resolution
    FADE_DURATION = 500  # milliseconds

    def __init__(self, color, direction, speed, timestamp):
        self.timestamp = timestamp
        self.color = color
        self.speed = speed * (BOX_SIZE / 800)  # Scale speed based on box size
        self.direction = direction
        
        # Spawn notes at the exact center of the screen
        self.x, self.y = DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2
        self.active = True # Currently true, fix later
        self.hit = False
        self.missed = False
        self.approaching = False

        # Position relative to center (for resize handling)
        self.offset_x = 0
        self.offset_y = 0

        # Fading-related attributes
        self.fading = False
        self.fade_start_time = None
        self.alpha = 255
        self.scale_factor = 1.0

    def approach(self):
        self.approaching = True

    def update_position(self, old_center_x, old_center_y, new_center_x, new_center_y):
        """Update note position after screen resize"""
        if self.active or self.fading:
            # Calculate offset from center
            self.offset_x = self.x - old_center_x
            self.offset_y = self.y - old_center_y
            
            # Apply offset to new center
            self.x = new_center_x + self.offset_x
            self.y = new_center_y + self.offset_y

    def draw(self):
        # Real Code, finish later
        # if not self.active:
        #     pass
        
        # remove not self.active later
        if not self.active and not self.fading:
            return

        # Create a temporary surface with alpha
        scaled_radius = scale_value(Note.NOTERADIUS * self.scale_factor)
        temp_surface = py.Surface((scaled_radius * 2, scaled_radius * 2), py.SRCALPHA)
        fade_color = (*self.color[:3], self.alpha)
        py.draw.circle(temp_surface, fade_color, (scaled_radius, scaled_radius), scaled_radius)

        # Draw the surface centered at (x, y)
        screen.blit(temp_surface, (self.x - scaled_radius, self.y - scaled_radius))

    def move(self):
        if not self.active:
            return

        box = get_box_coordinates()
        
        # Calculate movement based on direction
        if self.direction == "left":
            self.x -= self.speed
        elif self.direction == "right":
            self.x += self.speed
        elif self.direction == "up":
            self.y -= self.speed
        elif self.direction == "down":
            self.y += self.speed
            
        # Update offsets from center
        self.offset_x = self.x - box["center_x"]
        self.offset_y = self.y - box["center_y"]

        if self.is_at_edge():
            self.check_hit()

    def is_at_edge(self):
        box = get_box_coordinates()
        buffer = scale_value(5)
        
        if self.direction == "left" and self.x <= box["left"] + buffer:
            return True
        elif self.direction == "right" and self.x >= box["right"] - buffer:
            return True
        elif self.direction == "up" and self.y <= box["top"] + buffer:
            return True
        elif self.direction == "down" and self.y >= box["bottom"] - buffer:
            return True
        return False

    def check_hit(self):
        self.active = False
        self.fading = True
        self.fade_start_time = py.time.get_ticks()

        if self.direction in current_colors and current_colors[self.direction] == self.color:
            self.hit = True
            hitsound.play()
            return True
        else:
            misssound.play()
            self.missed = True
            return False

    def fade_out(self):
        if not self.fading:
            return

        elapsed = py.time.get_ticks() - self.fade_start_time
        if elapsed >= Note.FADE_DURATION:
            self.fading = False
            return

        # Update scale and alpha
        self.scale_factor = 1 + (elapsed / Note.FADE_DURATION) * 1
        self.alpha = max(255 - int((elapsed / Note.FADE_DURATION) * 255), 0)

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
        return [
            Note(note_colors[n['color']], n['direction'], n['speed'], n['timestamp']) for n in note_data
        ]
    
    def play_song(self):
        self.song.play()

    def stop_song(self):
        if not self.fadeout_started:
            self.fadeout_started = True
            self.fadeout_start_time = py.time.get_ticks()

        elapsed = py.time.get_ticks() - self.fadeout_start_time
        if elapsed >= 1000:  # 1000ms fade-out duration
            self.song.stop()
            self.fadeout_started = False
        else:
            self.song.fadeout(1000)

    def reset_notes(self):
        self.song.stop()
        self.notes.clear()
        self.load_metadata_and_notes()
    
    def calculate_difficulty(self):
        notes = self.note_info

        if len(notes) <= 1:
            self.rating = 1
        
        # Calculate song duration (time from first note to last note)
        timestamps = [note["timestamp"] for note in notes]
        song_duration = max(timestamps) - min(timestamps)
        if song_duration <= 0:
            song_duration = 1  # Prevent division by zero
        
        # Track changes
        color_changes = 0
        direction_changes = 0
        combined_changes = 0
        
        # Calculate changes between consecutive notes
        for i in range(1, len(notes)):
            color_changed = notes[i]["color"] != notes[i-1]["color"]
            direction_changed = notes[i]["direction"] != notes[i-1]["direction"]
            
            if color_changed:
                color_changes += 1
            
            if direction_changed:
                direction_changes += 1
            
            if color_changed and direction_changed:
                combined_changes += 1
        
        # Calculate change densities (changes per second)
        duration_in_seconds = song_duration / 1000.0
        
        # Heavily reduced weights for tutorial-level songs
        color_change_density = (color_changes / duration_in_seconds) * 0.4
        direction_change_density = (direction_changes / duration_in_seconds) * 0.4
        combined_change_density = (combined_changes / duration_in_seconds) * 0.7
        
        # Calculate quick change intervals (when changes happen very close together)
        change_intervals = []
        last_change_time = notes[0]["timestamp"]
        
        for i in range(1, len(notes)):
            current_time = notes[i]["timestamp"]
            if notes[i]["color"] != notes[i-1]["color"] or notes[i]["direction"] != notes[i-1]["direction"]:
                interval = current_time - last_change_time
                change_intervals.append(interval)
                last_change_time = current_time
        
        # Calculate quick changes factor (changes that happen very close together)
        # Increased threshold to 400ms - makes it less likely to trigger for beginner songs
        quick_changes = sum(1 for interval in change_intervals if interval < 300)
        quick_changes_factor = (quick_changes * 0.6) if change_intervals else 0
        
        # Note Speed - reduced weight
        average_speed = sum(note.get("speed", 5) for note in notes) / len(notes)
        # Adjust speed factor - lower values for beginner songs
        if average_speed <= 3:
            speed_factor = average_speed * 0.2  # Reduced impact for slow notes
        else:
            speed_factor = (average_speed - 3) * 0.5 + 0.6  # More impact as speed increases
        
        # Calculate pattern complexity
        if change_intervals:
            avg_interval = sum(change_intervals) / len(change_intervals)
            if avg_interval > 0:
                interval_variance = sum((interval - avg_interval) ** 2 for interval in change_intervals) / len(change_intervals)
                pattern_complexity = (interval_variance ** 0.5) / 100  # Further scaled down
            else:
                pattern_complexity = 0
        else:
            pattern_complexity = 0

        notes_per_second = len(notes) / duration_in_seconds

        # Adjust note density factor to be gentler on beginner songs
        if notes_per_second < 0.5:  # Very slow note density
            notes_density_factor = notes_per_second * 0.1
        else:
            notes_density_factor = (notes_per_second - 0.5) * 0.7 + 0.05
        
        # Apply exponential scaling for more complex patterns
        # This makes simple songs rate much lower while still allowing complex songs to rate high
        raw_difficulty = (
            color_change_density +
            direction_change_density +
            combined_change_density * 1.2 +
            speed_factor * 0.9 +
            pattern_complexity * 1.0 +
            quick_changes_factor * 1.0 +
            notes_density_factor * 0.8
        )
        
        # Scale to 1-40+ range with a more gradual start
        if raw_difficulty < 2:
            difficulty = 1 + (raw_difficulty * 0.5)  # Very easy songs: 1-2
        elif raw_difficulty < 5:
            difficulty = 2 + (raw_difficulty - 2) * 0.7  # Easy beginner songs: 2-4
        elif raw_difficulty < 10:
            difficulty = 4 + (raw_difficulty - 5) * 0.8  # Standard easy songs: 4-8
        elif raw_difficulty < 15:
            difficulty = 8 + (raw_difficulty - 10) * 1.0  # Challenging easy songs: 8-13
        elif raw_difficulty < 25:
            difficulty = 13 + (raw_difficulty - 15) * 1.2  # Intermediate songs: 13-25
        elif raw_difficulty < 35:
            difficulty = 25 + (raw_difficulty - 25) * 1.0  # Hard songs: 25-35
        else:
            difficulty = 35 + (raw_difficulty - 35) * 1.2  # Expert/Master songs: 35+
        
        # Ensure minimum difficulty isn't below 5
        difficulty = max(5, difficulty)
        
        self.rating = round(difficulty, 1) 
            
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
        song.calculate_difficulty()
        song_text = f"{song.title} - {song.artist} | Rating: {song.rating}"
        
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

# SIDE BARS AND ARROWS
# ========================
def get_bounce_offset():
    # Calculate the time since start
    time_elapsed = py.time.get_ticks() - start_time
    # Sinusoidal motion for smooth bouncing
    return math.sin(time_elapsed * bounce_speed * 0.001) * bounce_amplitude

def draw_bars():
    bar_width = scale_value(10)  # Scale bar width based on box size
    box = get_box_coordinates()
    
    # Draw the fixed 800x800 box
    py.draw.line(screen, current_colors["left"], (box["left"], box["top"]), (box["left"], box["bottom"]), bar_width)  # left bar
    py.draw.line(screen, current_colors["right"], (box["right"], box["top"]), (box["right"], box["bottom"]), bar_width)  # right bar
    py.draw.line(screen, current_colors["down"], (box["left"], box["bottom"]), (box["right"], box["bottom"]), bar_width)  # down bar
    py.draw.line(screen, current_colors["up"], (box["left"], box["top"]), (box["right"], box["top"]), bar_width)  # up bar

def draw_arrow(side):
    box = get_box_coordinates()
    bounce_offset = get_bounce_offset()
    arrow_size = scale_value(20)  # Scale arrow size
    
    # Position arrows relative to the fixed box
    if side == "left":
        base_x = box["left"] + scale_value(70)  # Increased from 50 to move inward
        base_y = box["center_y"]
        arrow_points = [
            (base_x - scale_value(30) + bounce_offset, base_y),  # Adjusted from 50 to 30
            (base_x - scale_value(10) + bounce_offset, base_y - arrow_size),  # Adjusted from 30 to 10
            (base_x - scale_value(10) + bounce_offset, base_y + arrow_size)   # Adjusted from 30 to 10
        ]
    elif side == "right":
        base_x = box["right"] - scale_value(70)  # Increased from 50 to move inward
        base_y = box["center_y"]
        arrow_points = [
            (base_x + scale_value(30) - bounce_offset, base_y),  # Adjusted from 50 to 30
            (base_x + scale_value(10) - bounce_offset, base_y - arrow_size),  # Adjusted from 30 to 10
            (base_x + scale_value(10) - bounce_offset, base_y + arrow_size)   # Adjusted from 30 to 10
        ]
    elif side == "down":
        base_x = box["center_x"]
        base_y = box["bottom"] - scale_value(70)  # Increased from 50 to move inward
        arrow_points = [
            (base_x, base_y + scale_value(30) - bounce_offset),  # Adjusted from 50 to 30
            (base_x - arrow_size, base_y + scale_value(10) - bounce_offset),  # Adjusted from 30 to 10
            (base_x + arrow_size, base_y + scale_value(10) - bounce_offset)   # Adjusted from 30 to 10
        ]
    elif side == "up":
        base_x = box["center_x"]
        base_y = box["top"] + scale_value(70)  # Increased from 50 to move inward
        arrow_points = [
            (base_x, base_y - scale_value(30) + bounce_offset),  # Adjusted from 50 to 30
            (base_x - arrow_size, base_y - scale_value(10) + bounce_offset),  # Adjusted from 30 to 10
            (base_x + arrow_size, base_y - scale_value(10) + bounce_offset)   # Adjusted from 30 to 10
        ]

    py.draw.polygon(screen, (255, 255, 255), arrow_points)
# ======================

# BUTTONS
# ======================
play_button = button.Button(audio=click_sound, pos=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 1.7), current_pos=DISPLAY_WIDTH * 1.5, text_input="Play", font=comfortaa_font, base_color="black", hovering_color="white", scale=1.0, padding=(DISPLAY_WIDTH // 6,10), has_audio=True)
options_button = button.Button(audio=click_sound, pos=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 1.45), current_pos=DISPLAY_WIDTH * -0.5, text_input="Options", font=comfortaa_font, base_color="black", hovering_color="white", scale=1.0, padding=(DISPLAY_WIDTH // 6,10), has_audio=True)
exit_button = button.Button(audio=click_sound, pos=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 1.27), current_pos=DISPLAY_WIDTH * 1.5, text_input="Exit", font=comfortaa_font, base_color="black", hovering_color="white", scale=1.0, padding=(DISPLAY_WIDTH // 6,10), has_audio=True)
# ======================

def keybinds():
    global running, current_side, DISPLAY_WIDTH, DISPLAY_HEIGHT, screen, notes, game_state, start_time, logo_target_x, logo_target_y

    for event in py.event.get():
        if event.type == py.QUIT:
            running = False
        elif event.type == py.KEYDOWN:
            # PLAY KEYBINDS
            if game_state == "play":
                if event.key == py.K_ESCAPE:
                    game_state = "song_select"
                    selected_song.stop_song()
                elif event.key == py.K_LEFT:
                    current_side = "left"
                elif event.key == py.K_RIGHT:
                    current_side = "right"
                elif event.key == py.K_DOWN:
                    current_side = "down"
                elif event.key == py.K_UP:
                    current_side = "up"
                elif event.key == py.K_1:
                    current_colors[current_side] = colors[0]
                elif event.key == py.K_2:
                    current_colors[current_side] = colors[1]
                elif event.key == py.K_3:
                    current_colors[current_side] = colors[2]
                elif event.key == py.K_4:
                    current_colors[current_side] = colors[3]
            # MENU KEYBINDS
            elif game_state == "menu":
                if event.key == py.K_RETURN:
                    game_state = "opened_menu"
                    om_logo()   
            # OPENED MENU GAMESTATE
            elif game_state == "opened_menu":
                if event.key == py.K_ESCAPE:
                    game_state = "menu"
                    logo_target_x, logo_target_y = DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2
            elif game_state == "song_select":
                if event.key == py.K_ESCAPE:
                    game_state = "opened_menu"
                    # Reset Time
                    start_time = py.time.get_ticks() 
                    # Reset the notes
                    # reset_notes() 
                    # Resets the current side
                    current_side = "down"
                    # Reset Side Bar Colors
                    for i in ["left", "right", "up", "down"]:
                        current_colors[i] = colors[4]
            elif game_state == "map_editor":
                if event.key == py.K_ESCAPE:
                    py.quit()
        elif event.type == py.VIDEORESIZE:
            # Store old center coordinates
            old_center_x, old_center_y = DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2
            
            # Update display dimensions
            DISPLAY_WIDTH, DISPLAY_HEIGHT = event.size
            screen = py.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), py.RESIZABLE)
            
            # Get new center coordinates
            new_center_x, new_center_y = DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2
            
            if game_state == "menu":
                logo_target_x, logo_target_y = new_center_x, new_center_y
            elif game_state == "opened_menu":
                om_logo()
            # Update positions of all active notes
            for note in notes:
                note.update_position(old_center_x, old_center_y, new_center_x, new_center_y)
# ========================

# EXTRA FUNCTIONS
# ========================
def options():
    hitsound.set_volume(1)  # Set the volume to 100%
    misssound.set_volume(0.5)  # Set the volume to 50%

def map_editor():
    pass
    # global mouse_pos
    # keybinds()
    # screen.fill("black")

    # place_note = button.Button(image=None, pos=(DISPLAY_WIDTH // 4, DISPLAY_HEIGHT // 2), text_input="Place Note", font=font, base_color="White", hovering_color="Green")
    
    # place_note.changeColor(mouse_pos)
    # place_note.update(screen)
    # if game_state == "map_editor":
    #     for event in py.event.get():
    #         if event.type == py.MOUSEBUTTONDOWN:
    #             if place_note.checkForInput(mouse_pos):
    #                 print("Hello!")
# ========================

# Pre-compute gradient colors to avoid calculating them every frame
def create_gradient_background(width, height):
    gradient_surface = py.Surface((width, height))
    for y in range(height):
        r = 255
        g = int(180 + (y / height) * 40)
        b = int(200 + (y / height) * 50)
        py.draw.line(gradient_surface, (r, g, b), (0, y), (width, y))
    return gradient_surface

# Cache the gradient background
gradient_background = None

def draw_gradient_background(surface):
    global gradient_background, DISPLAY_WIDTH, DISPLAY_HEIGHT
    
    # Only recreate the gradient if it doesn't exist or if the display size has changed
    if gradient_background is None or gradient_background.get_size() != (DISPLAY_WIDTH, DISPLAY_HEIGHT):
        gradient_background = create_gradient_background(DISPLAY_WIDTH, DISPLAY_HEIGHT)
    
    # Blit the cached gradient
    surface.blit(gradient_background, (0, 0))

# Diagonal light beam
class LightBeam:
    def __init__(self, x, y):
        self.length = random.randint(250, 400)  # Varying lengths
        self.width = random.randint(30, 50)     # Varying widths
        self.x = x
        self.y = y
        self.speed = random.uniform(0.4, 1.2)   # Varying speeds
        self.alpha = random.randint(40, 80)     # Varying transparency
        self.angle = -45  # Default angle (diagonal)

        # Pre-render the beam surface
        self.beam_surface = py.Surface((self.length, self.width), py.SRCALPHA)
        py.draw.rect(self.beam_surface, (255, 255, 255, self.alpha),
                     (0, 0, self.length, self.width), border_radius=20)
        self.rotated_beam = py.transform.rotate(self.beam_surface, self.angle)
        self.beam_rect = self.rotated_beam.get_rect(topleft=(self.x, self.y))

    def move(self):
        # Move diagonally
        self.x += self.speed
        self.y += self.speed
        
        # Reset position when off-screen
        if self.x > DISPLAY_WIDTH + 100 or self.y > DISPLAY_HEIGHT + 100:
            # Reset to somewhere along the top or left edge
            if random.choice([True, False]):
                # Reset along the top edge with random position
                self.x = random.randint(-400, DISPLAY_WIDTH)
                self.y = -self.length
            else:
                # Reset along the left edge with random position
                self.x = -self.length
                self.y = random.randint(-400, DISPLAY_HEIGHT)
                
            # Regenerate beam properties for variety
            self.length = random.randint(250, 400)
            self.width = random.randint(30, 50)
            self.speed = random.uniform(0.4, 1.2)
            self.alpha = random.randint(40, 80)
            
            # Recreate the beam surface with new properties
            self.beam_surface = py.Surface((self.length, self.width), py.SRCALPHA)
            py.draw.rect(self.beam_surface, (255, 255, 255, self.alpha),
                        (0, 0, self.length, self.width), border_radius=20)
            self.rotated_beam = py.transform.rotate(self.beam_surface, self.angle)
        
        self.beam_rect.topleft = (self.x, self.y)

    def draw(self, surface):
        surface.blit(self.rotated_beam, self.beam_rect)

center_x, center_y = DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2
radius = 150
dot_radius = 57

start_time = time.time()

# Pre-render text surfaces that don't change
base_text_surface = comfortaa_font.render("ColorShift", True, intro_colors["black"])
press_enter_text = sub_font.render("Press Enter to Start", True, intro_colors["black"])

# Initialize positions
logo_x, logo_y = DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2  # Start in center
logo_target_x, logo_target_y = DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2  # Target position
logo_move_speed = 10  # Pixels per frame

# Calculate colors for orbiting circles once
orbit_colors = [intro_colors["red"], intro_colors["blue"], 
               intro_colors["green"], intro_colors["yellow"]]

light_beams = []

# Create beams with staggered spawn positions
num_beams = 18  # Increased number for more frequent appearance

# Create beams distributed along top and left edges
for i in range(num_beams):
    if i < num_beams // 2:
        # Top edge beams
        x_pos = -400 + (DISPLAY_WIDTH + 800) * (i / (num_beams/2 - 1))
        y_pos = -random.randint(100, 500)  # Staggered vertical positions
    else:
        # Left edge beams
        x_pos = -random.randint(100, 500)  # Staggered horizontal positions
        y_pos = -400 + (DISPLAY_HEIGHT + 800) * ((i - num_beams//2) / (num_beams/2 - 1))
    
    # Add randomness to prevent even spacing
    x_pos += random.randint(-100, 100)
    y_pos += random.randint(-100, 100)
    
    light_beams.append(LightBeam(x_pos, y_pos))

def om_logo():
    global logo_target_x, logo_target_y
    logo_target_x = DISPLAY_WIDTH // 2
    logo_target_y = DISPLAY_HEIGHT // 3.5

# Cache for orbiting circles positions
circle_positions = [(0, 0)] * 4
circle_surfaces = [None] * 4

def intro():
    global elapsed, logo_x, logo_y, logo_target_x, logo_target_y, circle_positions
    
    # Smoothly move logo toward target position
    dx = logo_target_x - logo_x
    dy = logo_target_y - logo_y
    
    # Only move if we're not very close to the target
    if abs(dx) > 2 or abs(dy) > 2:
        logo_x += dx * 0.15
        logo_y += dy * 0.15
    
    # Draw circle with updated coordinates
    py.draw.circle(screen, intro_colors["black"], (int(logo_x), int(logo_y)), radius, 7)

    # Orbiting circles with updated coordinates
    orbit_radius = 80
    orbit_speed = 0.5

    # Calculate the four angles
    base_angle = elapsed * orbit_speed
    angles = [
        base_angle,
        base_angle + math.pi / 2,
        base_angle + math.pi,
        base_angle + 3 * math.pi / 2
    ]

    # Update positions of orbiting circles
    for i, angle in enumerate(angles):
        x = logo_x + orbit_radius * math.cos(angle)
        y = logo_y + orbit_radius * math.sin(angle)
        circle_positions[i] = (int(x), int(y))
        py.draw.circle(screen, orbit_colors[i], circle_positions[i], dot_radius)

    # Pulsing ColorShift text with updated coordinates
    scale_factor = 1.0 + 0.05 * math.sin(elapsed * 10)
    width = int(base_text_surface.get_width() * scale_factor)
    height = int(base_text_surface.get_height() * scale_factor)
    scaled_surface = py.transform.scale(base_text_surface, (width, height))
    rect = scaled_surface.get_rect(center=(int(logo_x), int(logo_y)))
    screen.blit(scaled_surface, rect)

# Pre-compute fade alphas for efficiency
def p_enter():
    global logo_target_x, logo_target_y
    
    # Calculate fade alpha
    fade = (math.sin(elapsed * 2) + 1) / 2
    min_alpha, max_alpha = 100, 255
    current_alpha = min_alpha + fade * (max_alpha - min_alpha)
    
    # Create a temporary surface with the right alpha
    temp_surface = press_enter_text.copy()
    temp_surface.set_alpha(int(current_alpha))
    
    # Position and blit
    text_rect = temp_surface.get_rect(center=(logo_target_x, logo_target_y + 240))
    screen.blit(temp_surface, text_rect)
    
    return current_alpha

# Define these variables globally or before your game loop
has_faded = False
fade_started = False
fading_in = True
fade_alpha = 255

def menu():
    global mouse_pos, elapsed, fade_alpha, has_faded, fade_started, fading_in, logo_target_x, logo_target_y, game_state, button_cooldown
    
    # Update button colors just once per frame
    for btn in [play_button, options_button, exit_button]:
        btn.change_color(mouse_pos)

    # Draw background
    draw_gradient_background(screen)

    # Draw a limited number of light beams for better performance
    for beam in light_beams:
        beam.move()
        beam.draw(screen)

    # Calculate elapsed time just once
    elapsed = time.time() - start_time

    # Draw the intro elements
    intro()

    # Handle the "Press Enter to Start" text
    if game_state == "menu":
        has_faded = False
        fade_started = False

        # Get the target alpha from the sine wave
        fade_target = (math.sin(elapsed * 2) + 1) / 2
        min_alpha, max_alpha = 100, 255
        target_alpha = min_alpha + fade_target * (max_alpha - min_alpha)

        if fading_in:
            fade_alpha += 5
            if fade_alpha >= target_alpha:
                fade_alpha = target_alpha
                fading_in = False

            # Create a temporary surface with the calculated alpha
            temp_surface = press_enter_text.copy()
            temp_surface.set_alpha(int(fade_alpha))
            text_rect = temp_surface.get_rect(center=(logo_target_x, logo_target_y + 240))
            screen.blit(temp_surface, text_rect)
        else:
            fade_alpha = p_enter()
    else:
        fading_in = True
        if not fade_started:
            fade_started = True

        if not has_faded and fade_alpha > 0:
            fade_alpha -= 5
            fade_alpha = max(0, fade_alpha)

            # Only render and draw if there's something to see
            if fade_alpha > 0:
                temp_surface = press_enter_text.copy()
                temp_surface.set_alpha(int(fade_alpha))
                text_rect = temp_surface.get_rect(center=(logo_target_x, center_y + 240))
                screen.blit(temp_surface, text_rect)
        elif fade_alpha <= 0:
            has_faded = True

    # Handle button states and rendering
    if game_state == "menu":
        for btn in [options_button, play_button, exit_button]:
            btn.slide_out()
            btn.update(screen)
    elif game_state == "opened_menu":
        for btn in [options_button, play_button, exit_button]:
            btn.slide_in()
            btn.smooth_resize()
            btn.update(screen)
        if exit_button.check_for_input(mouse_pos) and mouse_pressed:
            py.quit()
        elif play_button.check_for_input(mouse_pos) and mouse_pressed:
            fade_out(screen, 3)
            game_state = "song_select"
            button_cooldown = 15
    
    # Process keybinds
    keybinds()

def confirm_leave():
    screen.fill((0, 0, 0, 128))  # Fill the screen with black and set transparency

def song_select():
    global selected_song, game_state, song_buttons, start_time, current_side, song_library, button_cooldown

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
                # Resets the current side
                current_side = "down"
                # Reset Side Bar Colors
                for i in ["left", "right", "up", "down"]:
                    current_colors[i] = colors[4]
                print(f"Starting song: {song.title}")
            else:
                # Just select the song
                selected_song = song
                print(f"Selected song: {song.title}")
        
        # Highlight selected song
        if selected_song == song:
            py.draw.rect(screen, (0, 255, 0), btn.button_rect, 3)
    
    # # Instructions
    # if selected_song:
    #     instructions = sub_font.render("Click again to play!", True, (200, 200, 200))
    #     screen.blit(instructions, (DISPLAY_WIDTH // 2 - instructions.get_width() // 2, DISPLAY_HEIGHT - 100))

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
    global selected_song, start_time, game_state

    overall_combo = 0
    combo = 0

    # Fill the screen with black
    screen.fill((0, 0, 0))
    
    # Calculate current time
    current_time = py.time.get_ticks() - start_time

    # Draw gameplay elements
    draw_bars()
    draw_arrow(current_side)
    keybinds()     
    print(overall_combo)

    # Use the selected song's notes
    if selected_song and hasattr(selected_song, 'notes'):
        for note in selected_song.notes:
            if note.timestamp <= current_time and (note.active or note.fading):
                if note.active:
                    note.move()
                    if note.is_at_edge():
                        if note.check_hit():
                            combo += 1
                            if combo > overall_combo:
                                overall_combo = combo
                        elif not note.check_hit():
                            combo = 0
                note.fade_out()
                note.draw()
                
    
    # Display song info
    if selected_song:
        song_text = sub_font.render(f"{selected_song.title}", True, (200, 200, 200))
        screen.blit(song_text, (20, 20))        

def main():
    global running, game_state, start_time, mouse_pos, mouse_pressed, song_library, button_cooldown

    button_cooldown = 0
    
    # Load song library at startup
    try:
        song_library = load_song_library(os.path.join("Rhythm Game", "song_library"))
        print(f"Loaded {len(song_library)} songs")
    except Exception as e:
        print(f"Error loading song library: {e}")
        song_library = []
    
    misssound.set_volume(0.5)  # Set the volume to 50%
    game_state = "menu"  # change to "menu" once the menu is implemented

    start_time = py.time.get_ticks()

    game_states = {
        "menu": menu,
        "opened_menu": menu,
        "song_select": song_select,
        "options": options,
        "map_editor": map_editor,
        "play": play
    }

    # Main game loop
    while running:
        mouse_pos = py.mouse.get_pos()
        mouse_pressed = py.mouse.get_pressed()[0]

        game_states.get(game_state, lambda: None)()

        for event in py.event.get():
            if event.type == py.QUIT:
                py.quit()
        
        py.display.flip()
        clock.tick(fps)
    # Quit Pygame
    py.quit()
# =========================

if __name__ == "__main__":
    main()