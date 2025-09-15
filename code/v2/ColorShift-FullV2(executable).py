# WARNING: If you are viewing this code as an outsider and not a developer, this code is held up by sticks, glue, and my will to live which is very little, and is very confusing.
# If you don't know what you're doing, don't touch anything. If you do, still don't touch anything. This game will, most probably, break. You have been warned.

import pygame as py
import random, math, json, os, time, button, threading, sys

# Initialize Pygame
py.init()
py.font.init()

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

def get_resource_path(relative_path: str) -> str:
    try:
        # PyInstaller bundle
        base_path = sys._MEIPASS
    except Exception:
        # Go up from code/v2/ → code/ → ColorShift/
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    return os.path.normpath(os.path.join(base_path, relative_path))

print("Icon path:", get_resource_path("assets/textures/icon.png"))
print("Song path:", get_resource_path("song_library/Space Massacre.csz/song.json"))

icon_path = get_resource_path("assets/textures/icon.png")
if os.path.exists(icon_path):
    print("Icon file found!")
else:
    print(f"Icon file NOT found at: {icon_path}")
    print(f"Current script location: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"Files in assets/textures: {os.listdir(get_resource_path('assets/textures')) if os.path.exists(get_resource_path('assets/textures')) else 'Directory not found'}")

# Use relative paths for better portability
icon = py.image.load(get_resource_path("assets/textures/icon.png"))
hitsound = py.mixer.Sound(get_resource_path("assets/sounds/osu-hit-sound.mp3"))
misssound = py.mixer.Sound(get_resource_path("assets/sounds/miss-sound.mp3"))
click_sound = py.mixer.Sound(get_resource_path("assets/sounds/click-sound.wav"))
click_sound.set_volume(0.2)
py.display.set_icon(icon)  # Set the custom icon

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

# Global variables for keybind editing
keybind_editing = {
    "active": False,
    "editing_key": None,
    "flash_timer": 0
}

gameplay_keybinds = {
    "red": py.K_q,
    "blue": py.K_w,
    "green": py.K_o,
    "yellow": py.K_p
}

keybind_boxes = {}  # Will store the rectangles for each keybind box

# Hit window duration in milliseconds
HIT_WINDOW_DURATION = 150

selected_song = None
song_library = []
song_buttons = []
start_time = 0

time_offset = 1000

# FONTS
# ======================
comfortaa_font_path = get_resource_path("assets/fonts/Comfortaa-VariableFont_wght.ttf")
comfortaa_font = py.font.Font(comfortaa_font_path, 46)
sub_font = py.font.Font(comfortaa_font_path, 32)
# ======================

# OPTIMIZATION: Cache all fonts and surfaces
_font_cache = {}
_text_cache = {}
_last_mouse_pos = None
_cached_panel_surface = None
_cache_dirty = True

current_hit_rating = ""
hit_rating_display_time = 0
HIT_RATING_DURATION = 1000  # Display duration in milliseconds
current_color = {"color": "gray"}
fade_event = threading.Event()

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
        self.hit_rating = " "

    def update_position(self):
        """Updates the note's position based on speed and direction."""
        if self.direction == "down":
            self.pos[1] += self.speed

    def move(self):
        """Handles note movement and checks for a hit/miss."""
        self.update_position()

        # Only check for hits when the note is in the hit area
        if 775 <= self.pos[1] <= 850:
            self.check_hit()
        # Mark as missed if it passes the hit area without being hit
        elif self.pos[1] > 850 and not self.hit:
            global current_hit_rating, hit_rating_display_time
            
            self.missed = True
            self.hit_rating = "Miss"
            
            # Update global hit rating display for missed notes
            current_hit_rating = self.hit_rating
            hit_rating_display_time = py.time.get_ticks()
            
            # Play miss sound for notes that weren't hit at all
            if hasattr(globals(), 'misssound'):
                misssound.play()

    def check_hit(self):
        """Checks if any key is pressed while note is in hit window."""
        global current_hit_rating, hit_rating_display_time
        
        if not self.active or self.hit:
            return
            
        # Get the list of currently active colors that are in hit window
        active_hit_colors = [color for color, is_active in key_hit_windows.items() if is_active]
        
        # If ANY key is pressed while note is in hit window
        if active_hit_colors:
            # Check if the correct color was pressed
            if self.color in active_hit_colors:
                self.hit_rating = self.check_closeness()
                # Play hit sound for correct hits
                if hasattr(globals(), 'hitsound'):
                    hitsound.play()
            else:
                # Wrong color pressed - count as miss
                self.hit_rating = "Miss"
                # Play miss sound for wrong color
                if hasattr(globals(), 'misssound'):
                    misssound.play()
            
            # Mark note as hit regardless of correct/incorrect color
            self.hit = True
            self.is_fading = True
            self.fade_start_time = time.time()
            self.active = False
            
            # Update global hit rating display - this will override any previous rating
            current_hit_rating = self.hit_rating
            hit_rating_display_time = py.time.get_ticks()
    
    def check_closeness(self):
        """
        Evaluates the accuracy of the hit based on how close the note is to the ideal hit position.
        Returns "perfect", "great", "max", or "meh" depending on closeness to the hit line.
        """
        # The ideal hit position is at y=812 (middle of hit area 775-850)
        ideal_hit_position = 812
        
        # Calculate the distance from ideal hit position
        distance = abs(self.pos[1] - ideal_hit_position)
        
        # Determine rating based on distance
        if distance < 10:
            return "Max"
        elif distance < 20:
            return "Perfect"
        elif distance < 30:
            return "Great"
        elif distance < 40:
            return "Meh"

    def fade_out(self):
        """Handles fading effect ONLY when the note is hit; missed notes keep moving until off-screen."""
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
        """Draws the note with proper alpha fading."""
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
        self.song_path = None
        self.notes = []
        self.fadeout_started = False
        self.fadeout_start_time = 0
        self.rating = 0
        self.note_info = None
        self.end_time = 0
        
        # Load metadata first (fast operation)
        self.load_metadata()
        # Defer loading the actual audio until needed
        self.audio_loaded = False

    def load_metadata(self):
        """Load just the metadata without loading the audio file"""
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(f"{self.json_path} does not exist.")
        try:
            with open(self.json_path, 'r') as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    raise ValueError(f"Failed to decode JSON from {self.json_path}")
            
            self.title = data.get('song_name', 'Unknown Title')
            self.artist = data.get('song_artist', 'Unknown Artist')
            # Use get_resource_path for the song path
            raw_song_path = data.get('song_path', 'No Song')
            self.song_path = get_resource_path(raw_song_path) if raw_song_path != 'No Song' else None
            
            note_data = data.get('notes')
            self.note_info = note_data
            self.notes = self.load_notes(note_data)
            self.end_time = self.notes[-1].timestamp + 5000 if self.notes else 0
            
        except Exception as e:
            print(f"Error in load_metadata for {self.json_path}: {e}")
            raise

    def load_audio(self):
        """Load the audio file on demand"""
        if not self.audio_loaded and self.song_path:
            try:
                print(f"Loading audio for {self.title}...")
                # Check if file exists before trying to load
                if not os.path.exists(self.song_path):
                    raise FileNotFoundError(f"Audio file not found: {self.song_path}")
                
                # Use pygame.mixer.music for better memory management with large audio files
                py.mixer.music.load(self.song_path)
                self.audio_loaded = True
                print(f"Audio loaded successfully for {self.title}")
            except Exception as e:
                print(f"Error loading audio for {self.title}: {e}")
                print(f"Attempted path: {self.song_path}")
                self.audio_loaded = False

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
        """Play the song"""
        # Make sure audio is loaded before playing
        if not self.audio_loaded:
            self.load_audio()
        
        if self.audio_loaded:
            try:
                py.mixer.music.play()
                print(f"Playing: {self.title}")
            except Exception as e:
                print(f"Error playing song: {e}")
        else:
            print(f"Could not play {self.title} - audio not loaded")

    def stop_song(self):
        """Stop the song with fadeout"""
        if not self.audio_loaded:
            return
            
        try:
            if not self.fadeout_started:
                self.fadeout_started = True
                self.fadeout_start_time = py.time.get_ticks()
                py.mixer.music.fadeout(1000)  # Start 1-second fadeout
            else:
                # Check if fadeout is complete
                elapsed = py.time.get_ticks() - self.fadeout_start_time
                if elapsed >= 1000:  # 1000ms fade-out duration
                    py.mixer.music.stop()
                    self.fadeout_started = False
        except Exception as e:
            print(f"Error stopping song: {e}")

    def pause_song(self):
        """Pause the song"""
        if self.audio_loaded:
            py.mixer.music.pause()

    def unpause_song(self):
        """Unpause the song"""
        if self.audio_loaded:
            py.mixer.music.unpause()

    def is_playing(self):
        """Check if the song is currently playing"""
        return py.mixer.music.get_busy()

    def reset_notes(self):
        """Reset notes and stop the song"""
        if self.audio_loaded:
            py.mixer.music.stop()
            self.fadeout_started = False
        
        # Reset the song started flag
        if hasattr(self, '_song_started'):
            delattr(self, '_song_started')
        
        self.notes.clear()
        self.notes = self.load_notes(self.note_info)
            
# SONG LOADING & NOTESPAWNING
# ========================
def load_song_library(folder_path):
    print(f"Loading songs from {folder_path}...")
    songs = []
    if not os.path.exists(folder_path):
        print(f"Error: Path {folder_path} does not exist")
        return songs
        
    subfolders = os.listdir(folder_path)
    print(f"Found {len(subfolders)} potential song folders")
    
    for subfolder in subfolders:
        subfolder_path = os.path.join(folder_path, subfolder)
        if os.path.isdir(subfolder_path):
            json_files = [f for f in os.listdir(subfolder_path) if f.endswith('.json')]
            if json_files:
                full_path = os.path.join(subfolder_path, json_files[0])
                print(f"Loading {full_path}...")
                try:
                    song = Song(full_path)
                    songs.append(song)
                    print(f"Successfully loaded: {song.title} - {song.artist}")
                except Exception as e:
                    print(f"Error loading {json_files[0]}: {e}")
    
    print(f"Loaded {len(songs)} songs successfully")
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
    """Create a rainbow gradient based on currently held keys."""
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
    """Update the current color based on key states."""
    current_color["color"] = mix_colors()

def update_hit_windows():
    """Update which keys are in active hit window based on timing."""
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

# Play Area
# ========================
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
        screen.blit(gradient_surface, (500, 812.5 - bar_width // 2))
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
            
        py.draw.line(screen, color_to_use, (500, 812.5), (1100, 812.5), bar_width)

    # Draw hit window indicators for each active color
    font = py.font.SysFont('Arial', 14)
    
    # Display hit window status
    for i, (color, is_active) in enumerate(key_hit_windows.items()):
        if key_states[color]:  # Only show for held keys
            status = "ACTIVE" if is_active else "HOLDING"
            color_rgb = py.Color(color)
            text = font.render(f"{color}: {status}", True, color_rgb)
            screen.blit(text, (1120, 780 + i*20))
# ======================

# BUTTONS
# ======================
play_button = button.Button(audio=click_sound, pos=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 1.7), current_pos=DISPLAY_WIDTH * 1.5, text_input="Play", font=comfortaa_font, base_color="black", hovering_color="white", scale=1.0, padding=(DISPLAY_WIDTH // 6,10), has_audio=True)
options_button = button.Button(audio=click_sound, pos=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 1.45), current_pos=DISPLAY_WIDTH * -0.5, text_input="Options", font=comfortaa_font, base_color="black", hovering_color="white", scale=1.0, padding=(DISPLAY_WIDTH // 6,10), has_audio=True)
exit_button = button.Button(audio=click_sound, pos=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 1.27), current_pos=DISPLAY_WIDTH * 1.5, text_input="Exit", font=comfortaa_font, base_color="black", hovering_color="white", scale=1.0, padding=(DISPLAY_WIDTH // 6,10), has_audio=True)
# ======================

def leave_play():
    global selected_song, game_state

    if selected_song:
        selected_song.stop_song()
        # Reset the song started flag so it can play again
        if hasattr(selected_song, '_song_started'):
            delattr(selected_song, '_song_started')
    selected_song = None

def get_font(size):
    """Get cached font"""
    if size not in _font_cache:
        _font_cache[size] = py.font.Font(comfortaa_font_path, size)
    return _font_cache[size]

def get_text_surface(text, size, color=(255, 255, 255)):
    """Get cached text surface"""
    cache_key = (text, size, color)
    if cache_key not in _text_cache:
        font = get_font(size)
        _text_cache[cache_key] = font.render(text, True, color)
    return _text_cache[cache_key]

def clear_text_cache():
    """Clear text cache when needed"""
    global _text_cache, _cache_dirty
    _text_cache.clear()
    _cache_dirty = True

def get_key_name(key_code):
    """Convert pygame key code to readable string"""
    key_names = {
        py.K_q: "Q", py.K_w: "W", py.K_e: "E", py.K_r: "R", py.K_t: "T",
        py.K_y: "Y", py.K_u: "U", py.K_i: "I", py.K_o: "O", py.K_p: "P",
        py.K_a: "A", py.K_s: "S", py.K_d: "D", py.K_f: "F", py.K_g: "G",
        py.K_h: "H", py.K_j: "J", py.K_k: "K", py.K_l: "L", py.K_z: "Z",
        py.K_x: "X", py.K_c: "C", py.K_v: "V", py.K_b: "B", py.K_n: "N",
        py.K_m: "M", py.K_SPACE: "SPACE", py.K_RETURN: "ENTER",
        py.K_LSHIFT: "L-SHIFT", py.K_RSHIFT: "R-SHIFT",
        py.K_LCTRL: "L-CTRL", py.K_RCTRL: "R-CTRL",
        py.K_LALT: "L-ALT", py.K_RALT: "R-ALT",
        py.K_1: "1", py.K_2: "2", py.K_3: "3", py.K_4: "4", py.K_5: "5",
        py.K_6: "6", py.K_7: "7", py.K_8: "8", py.K_9: "9", py.K_0: "0",
        # Numpad keys
        py.K_KP0: "NUM_0", py.K_KP1: "NUM_1", py.K_KP2: "NUM_2",
        py.K_KP3: "NUM_3", py.K_KP4: "NUM_4", py.K_KP5: "NUM_5",
        py.K_KP6: "NUM_6", py.K_KP7: "NUM_7", py.K_KP8: "NUM_8",
        py.K_KP9: "NUM_9", py.K_KP_PERIOD: "NUM_.", py.K_KP_DIVIDE: "NUM_/",
        py.K_KP_MULTIPLY: "NUM_*", py.K_KP_MINUS: "NUM_-", py.K_KP_PLUS: "NUM_+",
        py.K_KP_ENTER: "NUM_ENTER", py.K_KP_EQUALS: "NUM_="
    }
    return key_names.get(key_code, f"KEY_{key_code}")

def save_keybinds():
    """Save keybinds to a file"""
    try:
        keybind_data = {
            "red": gameplay_keybinds["red"],
            "blue": gameplay_keybinds["blue"], 
            "green": gameplay_keybinds["green"],
            "yellow": gameplay_keybinds["yellow"]
        }
        
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(script_dir, "config")
        
        os.makedirs(config_dir, exist_ok=True)
        
        config_file_path = os.path.join(config_dir, "keybinds.json")
        with open(config_file_path, "w") as f:
            json.dump(keybind_data, f, indent=2)
        print("Keybinds saved successfully!")
    except Exception as e:
        print(f"Error saving keybinds: {e}")

def load_keybinds():
    """Load keybinds from file"""
    global gameplay_keybinds
    try:
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(script_dir, "config", "keybinds.json")
        
        with open(config_file_path, "r") as f:
            keybind_data = json.load(f)
            
        gameplay_keybinds.update(keybind_data)
        print("Keybinds loaded successfully!")
    except FileNotFoundError:
        print("No keybind file found, using defaults")
    except Exception as e:
        print(f"Error loading keybinds: {e}")

def create_static_panel_surface(panel_width, panel_height):
    """Create the static parts of the panel that don't change"""
    panel_color = (40, 40, 40)
    
    # Create base panel
    panel_surface = py.Surface((panel_width, panel_height), py.SRCALPHA)
    panel_surface.fill((*panel_color, 180))
    py.draw.rect(panel_surface, (*panel_color, 200), (0, 0, panel_width, panel_height))
    
    # Add title
    title_text = get_text_surface("OPTIONS", 36)
    title_rect = title_text.get_rect(center=(panel_width // 2, 30))
    panel_surface.blit(title_text, title_rect)
    
    # Add keybinds title
    keybinds_title = get_text_surface("KEYBINDS", 32)
    panel_surface.blit(keybinds_title, (20, 100))
    
    # Add static keybind labels and color indicators
    keybind_info = [
        ("red", "Red", (255, 80, 80)),
        ("blue", "Blue", (80, 120, 255)),
        ("green", "Green", (80, 255, 80)),
        ("yellow", "Yellow", (255, 255, 80))
    ]
    
    start_y = 150
    for i, (key_name, label, color) in enumerate(keybind_info):
        y_pos = start_y + i * 60
        
        # Draw color indicator
        color_rect = py.Rect(30, y_pos, 20, 20)
        py.draw.rect(panel_surface, color, color_rect)
        py.draw.rect(panel_surface, (255, 255, 255), color_rect, 2)
        
        # Draw label
        label_text = get_text_surface(label, 24)
        panel_surface.blit(label_text, (60, y_pos))
    
    return panel_surface

def draw_keybind_boxes(panel_x, panel_y, mouse_pos):
    """Draw only the dynamic keybind boxes"""
    global keybind_boxes, keybind_editing
    
    keybind_info = ["red", "blue", "green", "yellow"]
    start_y = panel_y + 150
    keybind_boxes.clear()
    
    for i, key_name in enumerate(keybind_info):
        y_pos = start_y + i * 60
        
        # Calculate box position
        box_x = panel_x + 150
        box_width = 80
        box_height = 30
        key_box = py.Rect(box_x, y_pos - 5, box_width, box_height)
        keybind_boxes[key_name] = key_box
        
        # Determine box color and text (only recalculate if needed)
        if keybind_editing["active"] and keybind_editing["editing_key"] == key_name:
            # Flashing effect when editing
            keybind_editing["flash_timer"] += 1
            if (keybind_editing["flash_timer"] // 10) % 2:
                box_color = (100, 100, 100)
                text_color = (255, 255, 255)
                key_text = "Press Key..."
            else:
                box_color = (60, 60, 60)
                text_color = (150, 150, 150)
                key_text = "Press Key..."
        else:
            # Normal state
            if key_box.collidepoint(mouse_pos):
                box_color = (80, 80, 80)  # Hover
            else:
                box_color = (50, 50, 50)  # Normal
            text_color = (255, 255, 255)
            key_text = get_key_name(gameplay_keybinds[key_name])
        
        # Draw the box
        py.draw.rect(screen, box_color, key_box, border_radius=5)
        py.draw.rect(screen, (150, 150, 150), key_box, 2, border_radius=5)
        
        # Draw the key text (use cached surface when possible)
        key_surface = get_text_surface(key_text, 14, text_color)
        key_rect = key_surface.get_rect(center=key_box.center)
        screen.blit(key_surface, key_rect)

def draw_panel_buttons(panel_x, panel_y, panel_width, panel_height, mouse_pos):
    """Draw the save and close buttons"""
    # Save button
    save_rect = py.Rect(panel_x + 30, panel_y + panel_height - 80, 80, 30)
    
    if save_rect.collidepoint(mouse_pos):
        save_color = (80, 120, 80)
    else:
        save_color = (60, 100, 60)
    
    py.draw.rect(screen, save_color, save_rect, border_radius=5)
    py.draw.rect(screen, (255, 255, 255), save_rect, 2, border_radius=5)
    
    save_text = get_text_surface("SAVE", 15)
    save_text_rect = save_text.get_rect(center=save_rect.center)
    screen.blit(save_text, save_text_rect)
    
    # Close button
    close_rect = py.Rect(panel_x + panel_width - 110, panel_y + panel_height - 80, 80, 30)
    
    if close_rect.collidepoint(mouse_pos):
        close_color = (120, 80, 80)
    else:
        close_color = (100, 60, 60)
    
    py.draw.rect(screen, close_color, close_rect, border_radius=5)
    py.draw.rect(screen, (255, 255, 255), close_rect, 2, border_radius=5)
    
    close_text = get_text_surface("CLOSE", 15)
    close_text_rect = close_text.get_rect(center=close_rect.center)
    screen.blit(close_text, close_text_rect)
    
    return close_rect, save_rect

def keybinds():
    global running, current_side, DISPLAY_WIDTH, DISPLAY_HEIGHT, screen, game_state, start_time, logo_target_x, logo_target_y
    for event in py.event.get():
        if event.type == py.QUIT:
            running = False
        elif event.type == py.KEYDOWN:
            if handle_keybind_input(event):
                continue
                
            if game_state == "play":
                current_time = py.time.get_ticks()
                if event.key == py.K_ESCAPE:
                    game_state = "song_select"
                    leave_play()
                elif event.key == gameplay_keybinds["red"]:
                    key_states["red"] = True
                    key_press_times["red"] = current_time
                    key_hit_windows["red"] = True
                elif event.key == gameplay_keybinds["blue"]:
                    key_states["blue"] = True
                    key_press_times["blue"] = current_time
                    key_hit_windows["blue"] = True
                elif event.key == gameplay_keybinds["green"]:
                    key_states["green"] = True
                    key_press_times["green"] = current_time
                    key_hit_windows["green"] = True
                elif event.key == gameplay_keybinds["yellow"]:
                    key_states["yellow"] = True
                    key_press_times["yellow"] = current_time
                    key_hit_windows["yellow"] = True
            elif game_state == "menu":
                if event.key == py.K_RETURN:
                    game_state = "opened_menu"
                    om_logo()   
            elif game_state == "opened_menu":
                if event.key == py.K_ESCAPE:
                    if not keybind_editing["active"]:
                        game_state = "menu"
                        logo_target_x, logo_target_y = DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2
            elif game_state == "song_select":
                if event.key == py.K_ESCAPE:
                    game_state = "opened_menu"
                    leave_play()
            elif game_state == "map_editor":
                if event.key == py.K_ESCAPE:
                    py.quit()
        elif event.type == py.KEYUP:
            if game_state == "play":
                if event.key == gameplay_keybinds["red"]:
                    key_states["red"] = False
                    key_hit_windows["red"] = False
                elif event.key == gameplay_keybinds["blue"]:
                    key_states["blue"] = False
                    key_hit_windows["blue"] = False
                elif event.key == gameplay_keybinds["green"]:
                    key_states["green"] = False
                    key_hit_windows["green"] = False
                elif event.key == gameplay_keybinds["yellow"]:
                    key_states["yellow"] = False
                    key_hit_windows["yellow"] = False
        elif event.type == py.VIDEORESIZE:
            old_center_x, old_center_y = DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2
            DISPLAY_WIDTH, DISPLAY_HEIGHT = event.size
            screen = py.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), py.RESIZABLE)
            new_center_x, new_center_y = DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2
            
            # Clear caches on resize
            global _cached_panel_surface, _cache_dirty
            _cached_panel_surface = None
            _cache_dirty = True
            
            if game_state == "menu":
                logo_target_x, logo_target_y = new_center_x, new_center_y
            elif game_state == "opened_menu":
                om_logo()
                    
    update_current_color()
            
# ========================

# EXTRA FUNCTIONS
# ========================
def map_editor():
    pass
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

def draw_options_panel(panel_x):
    """Optimized options panel drawing"""
    global _cached_panel_surface, _cache_dirty, _last_mouse_pos
    
    panel_width, panel_height = DISPLAY_WIDTH // 2.5, DISPLAY_HEIGHT
    panel_y = (DISPLAY_HEIGHT - panel_height) // 2
    
    # Create or update cached static surface
    if _cached_panel_surface is None or _cache_dirty:
        _cached_panel_surface = create_static_panel_surface(panel_width, panel_height)
        _cache_dirty = False
    
    # Draw the cached static panel
    screen.blit(_cached_panel_surface, (panel_x, panel_y))
    
    # Only redraw dynamic elements if mouse moved or we're editing
    mouse_moved = _last_mouse_pos != mouse_pos
    editing_active = keybind_editing["active"]
    
    if mouse_moved or editing_active:
        _last_mouse_pos = mouse_pos
    
    # Draw dynamic elements (keybind boxes and buttons)
    draw_keybind_boxes(panel_x, panel_y, mouse_pos)
    close_rect, save_rect = draw_panel_buttons(panel_x, panel_y, panel_width, panel_height, mouse_pos)
    
    return close_rect, save_rect

def handle_keybind_click(mouse_pos):
    """Handle clicks on keybind boxes"""
    global keybind_editing
    
    if not keybind_editing["active"]:
        for key_name, box_rect in keybind_boxes.items():
            if box_rect.collidepoint(mouse_pos):
                keybind_editing["active"] = True
                keybind_editing["editing_key"] = key_name
                keybind_editing["flash_timer"] = 0
                return True
    return False

def handle_keybind_input(event):
    """Handle key input for keybind editing"""
    global keybind_editing, gameplay_keybinds
    
    if keybind_editing["active"] and event.type == py.KEYDOWN:
        if event.key == py.K_ESCAPE:
            keybind_editing["active"] = False
            keybind_editing["editing_key"] = None
            return True
        
        # Check if key is already used
        key_already_used = False
        for existing_key, existing_code in gameplay_keybinds.items():
            if existing_code == event.key and existing_key != keybind_editing["editing_key"]:
                key_already_used = True
                break
        
        if not key_already_used:
            # Assign the new key
            gameplay_keybinds[keybind_editing["editing_key"]] = event.key
            keybind_editing["active"] = False
            keybind_editing["editing_key"] = None
            clear_text_cache()  # Clear cache since keybind text changed
            return True
        else:
            print(f"Key {get_key_name(event.key)} is already assigned!")
    
    return False  
        
def menu():
    global mouse_pos, elapsed, fade_alpha, has_faded, fade_started, fading_in, logo_target_x, logo_target_y, game_state, button_cooldown
    global options_panel_x, options_panel_target_x, options_panel_open, panel_close_rect, panel_save_rect
    
    # Initialize options panel variables if they don't exist
    if 'options_panel_x' not in globals():
        options_panel_x = -DISPLAY_WIDTH // 2.5
        options_panel_target_x = -DISPLAY_WIDTH // 2.5
        options_panel_open = False
        panel_close_rect = None
        panel_save_rect = None
    
    # Update button colors just once per frame
    for btn in [play_button, options_button, exit_button]:
        btn.change_color(mouse_pos)

    # Draw background
    draw_gradient_background(screen)

    # Draw light beams
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

        fade_target = (math.sin(elapsed * 2) + 1) / 2
        min_alpha, max_alpha = 100, 255
        target_alpha = min_alpha + fade_target * (max_alpha - min_alpha)

        if fading_in:
            fade_alpha += 5
            if fade_alpha >= target_alpha:
                fade_alpha = target_alpha
                fading_in = False

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
        # Animate options panel sliding
        slide_speed = 20
        if abs(options_panel_x - options_panel_target_x) > slide_speed:
            if options_panel_x < options_panel_target_x:
                options_panel_x += slide_speed
            else:
                options_panel_x -= slide_speed
        else:
            options_panel_x = options_panel_target_x
        
        for btn in [options_button, play_button, exit_button]:
            btn.slide_in()
            btn.smooth_resize()
            btn.update(screen)
            
        # Handle button clicks
        if button_cooldown <= 0:
            if exit_button.check_for_input(mouse_pos) and mouse_pressed:
                py.quit()
            elif play_button.check_for_input(mouse_pos) and mouse_pressed and not options_panel_open:
                fade_out(screen, 3)
                game_state = "song_select"
                button_cooldown = 15
            elif options_button.check_for_input(mouse_pos) and mouse_pressed and not options_panel_open:
                options_panel_open = True
                options_panel_target_x = 0
                button_cooldown = 15
        
        # Draw options panel if visible
        if options_panel_open or options_panel_x > -DISPLAY_WIDTH // 2.5:
            panel_close_rect, panel_save_rect = draw_options_panel(options_panel_x)
            
            # Handle panel button clicks
            if button_cooldown <= 0 and mouse_pressed:
                if panel_close_rect and panel_close_rect.collidepoint(mouse_pos):
                    options_panel_open = False
                    options_panel_target_x = -DISPLAY_WIDTH // 2.5
                    keybind_editing["active"] = False
                    button_cooldown = 15
                elif panel_save_rect and panel_save_rect.collidepoint(mouse_pos):
                    save_keybinds()
                    button_cooldown = 15
                else:
                    handle_keybind_click(mouse_pos)
    
    # Decrease button cooldown
    if button_cooldown > 0:
        button_cooldown -= 1

def confirm_leave():
    screen.fill((0, 0, 0, 128))  # Fill the screen with black and set transparency

# Add this new variable to track loading state
loading_songs = False
loading_start_time = 0

def song_select():
    global selected_song, game_state, song_buttons, start_time, current_side, song_library, button_cooldown
    global loading_songs, loading_start_time, song_start_delay_time
    
    # Handle button cooldown
    if button_cooldown > 0:
        button_cooldown -= 1

    
    # Draw background
    screen.fill((30, 30, 30))
    
    # Check if we're currently loading songs
    if loading_songs:
        # Show loading indicator
        current_time = py.time.get_ticks()
        elapsed = current_time - loading_start_time
        
        # Animated loading text with dots
        dots = "." * (1 + (elapsed // 500) % 4)  # Changes every 500ms
        loading_text = comfortaa_font.render(f"Loading songs{dots}", True, (255, 255, 255))
        loading_rect = loading_text.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2))
        screen.blit(loading_text, loading_rect)
        
        # Check if songs should be loaded by now (give it some time)
        if elapsed > 100:  # Small delay to allow rendering before loading
            # Do the actual loading
            song_library = load_song_library(get_resource_path("song_library"))
            song_buttons = create_song_buttons(
                song_library,
                DISPLAY_WIDTH // 2,
                200,
                80,
                sub_font
            )
            loading_songs = False
        
        # Early return to avoid drawing buttons while loading
        return
    
    # Draw title
    title_text = comfortaa_font.render("Select a Song", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(DISPLAY_WIDTH // 2, 100))
    screen.blit(title_text, title_rect)
    
    # Draw instructions for reloading
    reload_text = sub_font.render("Press R to reload songs", True, (180, 180, 180))
    reload_rect = reload_text.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT - 50))
    screen.blit(reload_text, reload_rect)
    
    # Create song buttons if they don't exist yet
    if not song_buttons and song_library:
        song_buttons = create_song_buttons(
            song_library, 
            DISPLAY_WIDTH // 2,  # Center x
            200,                 # Start y position 
            80,                  # Spacing between buttons
            sub_font             # Font to use
        )
    
    # Draw buttons and handle clicks if there are songs
    if song_buttons:
        mouse_pos = py.mouse.get_pos()
        mouse_pressed = py.mouse.get_pressed()[0]
        
        for btn, song in song_buttons:
            # Update button hover state
            btn.change_color(mouse_pos)
            btn.update(screen)
            
            # Handle button clicks
            if btn.check_for_input(mouse_pos) and mouse_pressed and button_cooldown == 0:
                if selected_song == song and button_cooldown == 0:
                    button_cooldown = 20  # Prevent accidental double-clicks
                    selected_song.reset_notes()
                    # Ensure audio is loaded before starting play mode
                    if not selected_song.audio_loaded:
                        selected_song.load_audio()
                    # Start play mode immediately, but delay song start
                    start_time = py.time.get_ticks()
                    song_start_delay_time = start_time + 5000  # Song starts 5 seconds later
                    game_state = "play"
                    print(f"Starting song with 5-second delay: {song.title}")
                else:
                    # Just select the song and preload its audio
                    button_cooldown = 10  # Shorter cooldown for selection
                    if selected_song != song:  # Only load if it's a different song
                        selected_song = song
                        # Preload audio in the background to prevent lag
                        if not song.audio_loaded:
                            print(f"Preloading audio for {song.title}...")
                            song.load_audio()
                        print(f"Selected song: {song.title}")
            
            # Highlight selected song
            if selected_song == song:
                py.draw.rect(screen, (235, 163, 255), btn.button_rect, 3, border_radius=10)
    else:
        # Show message if no songs are loaded
        no_songs_text = sub_font.render("No songs found. Press R to load songs.", True, (255, 100, 100))
        no_songs_rect = no_songs_text.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2))
        screen.blit(no_songs_text, no_songs_rect)
    
    # Show play instructions if a song is selected
    if selected_song:
        instructions = sub_font.render("Click again to play!", True, (200, 200, 200))
        screen.blit(instructions, (DISPLAY_WIDTH // 2 - instructions.get_width() // 2, DISPLAY_HEIGHT - 150))

    # Check for reload key
    keys = py.key.get_pressed()
    if keys[py.K_r] and not loading_songs and button_cooldown == 0:
        print("Reloading song library...")
        button_cooldown = 20  # Prevent repeated presses
        loading_songs = True
        loading_start_time = py.time.get_ticks()
        song_buttons = []  # Clear existing buttons

def play():
    global song_start_delay_time, selected_song, current_hit_rating, hit_rating_display_time
    
    screen.fill((0, 0, 0))
    
    # Update hit windows based on timing
    update_hit_windows()

    current_time = py.time.get_ticks()
    
    # Check if we're still in the 5-second delay period
    song_has_started = current_time >= song_start_delay_time
    
    # Start the song when delay period ends
    if not song_has_started and current_time >= song_start_delay_time - 100:
        if selected_song and not getattr(selected_song, '_song_started', False):
            if not selected_song.audio_loaded:
                selected_song.load_audio()
            selected_song.play_song()
            selected_song._song_started = True
            print(f"Song started: {selected_song.title}")

    # Draw play area first
    draw_play_area()
    
    # Draw countdown if song hasn't started yet
    if not song_has_started:
        remaining_time = song_start_delay_time - current_time
        countdown_seconds = max(0, remaining_time // 1000 + 1)
        
        if countdown_seconds > 0:
            countdown_text = comfortaa_font.render(str(countdown_seconds), True, (255, 100, 100))
        else:
            countdown_text = comfortaa_font.render("GO!", True, (100, 255, 100))
            
        countdown_rect = countdown_text.get_rect(center=(799, 400))
        screen.blit(countdown_text, countdown_rect)

    # Calculate total time since play mode started
    total_time = current_time - start_time

    # Update and draw all active notes
    if selected_song and hasattr(selected_song, 'notes'):
        for note in selected_song.notes:
            if note.timestamp + 5000 - 1520 <= total_time and (note.active or note.is_fading):
                if note.active:
                    note.move()
                note.draw(screen)
    
    # Display the current hit rating (only one at a time)
    if current_hit_rating and current_time - hit_rating_display_time < HIT_RATING_DURATION:
        # Calculate fade effect for hit rating
        elapsed = current_time - hit_rating_display_time
        alpha = max(255 - int((elapsed / HIT_RATING_DURATION) * 255), 0)
        
        # Choose color based on rating
        rating_colors = {
            "Max": (56, 205, 255),      # Light Blue
            "Perfect": (245, 185, 44),    # Gold
            "Great": (112, 240, 58),    # Light Green
            "Meh": (166, 64, 0),      # Brown
            "Miss": (242, 10, 2)        # Red
        }
        
        color = rating_colors.get(current_hit_rating, (200, 200, 200))
        
        # Create surface with alpha for fading effect
        hit_text = sub_font.render(current_hit_rating, True, color)
        
        # Optional: Add scaling effect (starts big, gets smaller)
        scale = 1.0 + (0.5 * (1 - elapsed / HIT_RATING_DURATION))
        if scale > 1.0:
            # Scale the text surface
            original_size = hit_text.get_size()
            new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
            hit_text = py.transform.scale(hit_text, new_size)
        
        # Apply alpha
        hit_text.set_alpha(alpha)
        
        # Position the text (centered in play area)
        text_rect = hit_text.get_rect(center=(799, 300))
        screen.blit(hit_text, text_rect)
    else:
        # Clear the rating when time expires
        if current_time - hit_rating_display_time >= HIT_RATING_DURATION:
            current_hit_rating = ""
            
    # Display song info
    if selected_song:
        song_text = sub_font.render(f"{selected_song.title}", True, (200, 200, 200))
        screen.blit(song_text, (20, 20))

def main():
    global running, game_state, start_time, mouse_pos, mouse_pressed, song_library, button_cooldown, selected_song

    button_cooldown = 0
    
    # Load keybinds at startup
    load_keybinds()
    
    # Load song library at startup
    try:
        song_library = load_song_library(get_resource_path("song_library"))
        print(f"Loaded {len(song_library)} songs")
    except Exception as e:
        print(f"Error loading song library: {e}")
        song_library = []
    
    misssound.set_volume(0.5)
    game_state = "menu"

    start_time = py.time.get_ticks()

    game_states = {
        "menu": menu,
        "opened_menu": menu,
        "song_select": song_select,
        "map_editor": map_editor,
        "play": play
    }

    # Main game loop
    while running:
        mouse_pos = py.mouse.get_pos()
        mouse_pressed = py.mouse.get_pressed()[0]

        game_states.get(game_state, lambda: None)()

        keybinds()

        for event in py.event.get():
            if event.type == py.QUIT:
                py.quit()
        
        py.display.flip()
        clock.tick(fps)
    
    py.quit()

# =========================

if __name__ == "__main__":
    main()