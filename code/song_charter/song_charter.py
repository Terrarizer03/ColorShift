import pygame as py
import json, os, time

py.init()
py.mixer.init()

width, height = 800, 800
screen = py.display.set_mode((width, height))
py.display.set_caption("Song Charter")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 100, 100)
BLUE = (100, 100, 255)
GREEN = (100, 255, 100)
YELLOW = (255, 255, 100)
GRAY = (128, 128, 128)

# Game state
recording = False
start_time = 0
press_times = []
current_song = None
visual_effects = []

# Key mappings for charting
chart_keys = {
    py.K_q: {"name": "Q", "color": RED, "pos": (150, 400)},
    py.K_w: {"name": "W", "color": BLUE, "pos": (250, 400)},
    py.K_o: {"name": "O", "color": GREEN, "pos": (350, 400)},
    py.K_p: {"name": "P", "color": YELLOW, "pos": (450, 400)}
}

class VisualEffect:
    def __init__(self, key_name, color, pos, timestamp):
        self.key_name = key_name
        self.color = color
        self.pos = pos
        self.timestamp = timestamp
        self.creation_time = py.time.get_ticks()
        self.duration = 1000  # Effect lasts 1 second
        
    def update(self):
        elapsed = py.time.get_ticks() - self.creation_time
        return elapsed < self.duration
        
    def draw(self, screen, font):
        elapsed = py.time.get_ticks() - self.creation_time
        alpha = max(0, 255 - (elapsed * 255 // self.duration))
        
        # Create surface for text with alpha
        text_surface = font.render(f"{self.key_name}: {self.timestamp}ms", True, self.color)
        text_rect = text_surface.get_rect(center=self.pos)
        
        # Draw with fading effect
        if alpha > 0:
            fade_surface = py.Surface(text_surface.get_size())
            fade_surface.set_alpha(alpha)
            fade_surface.blit(text_surface, (0, 0))
            screen.blit(fade_surface, text_rect)

song = os.path.join("Rhythm Game", "code", "song_charter", "best_beat_ever (1).mp3") # Default song file
song2 = os.path.join("Rhythm Game", "code", "song_charter", "eazybeat 2.mp3") # Default song file
music_files = [song, song2]
current_song_index = 0  # Track the index of the current song
current_song = None     # Will hold the path to the current song

def load_music(index=None):
    """Load a music file by index."""
    global current_song_index, current_song
    if index is not None:
        current_song_index = index % len(music_files)
    try:
        file = music_files[current_song_index]
        if os.path.exists(file):
            py.mixer.music.load(file)
            current_song = file
            return file
        else:
            print(f"Music file not found: {file}")
            current_song = None
            return None
    except Exception as e:
        print(f"Error loading music: {e}")
        current_song = None
        return None

def save_chart_data():
    """Save recorded keypress times to JSON file"""
    if not press_times:
        print("No keypress data recorded!")
        return
        
    chart_data = {
        "song_file": current_song,
        "total_time": py.time.get_ticks() - start_time if recording else 0,
        "keypresses": press_times,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        os.makedirs("charts", exist_ok=True)
        filename = f"charts/chart_{int(time.time())}.json"
        
        with open(filename, "w") as f:
            json.dump(chart_data, f, indent=2)
        print(f"Chart saved to {filename}")
        print(f"Total keypresses recorded: {len(press_times)}")
    except Exception as e:
        print(f"Error saving chart: {e}")

def handle_keypress(key, current_time):
    """Handle chart key presses during recording"""
    if key in chart_keys and recording:
        relative_time = current_time - start_time
        key_data = {
            "key": chart_keys[key]["name"],
            "time": relative_time
        }
        press_times.append(key_data)
        
        # Add visual effect
        effect = VisualEffect(
            chart_keys[key]["name"],
            chart_keys[key]["color"],
            (chart_keys[key]["pos"][0], chart_keys[key]["pos"][1] - 50),
            relative_time
        )
        visual_effects.append(effect)
        
        print(f"Recorded: {chart_keys[key]['name']} at {relative_time}ms")

def draw_interface(screen, font, large_font):
    """Draw the user interface"""
    # Title
    title = large_font.render("Song Charter", True, WHITE)
    screen.blit(title, (width//2 - title.get_width()//2, 50))
    
    # Instructions
    if not recording:
        instructions = [
            "Press SPACEBAR to start recording and play music",
            "Press Q, W, O, P to record notes while music plays",
            "Press SPACEBAR again to stop and save chart"
        ]
    else:
        elapsed_time = py.time.get_ticks() - start_time
        instructions = [
            "RECORDING...",
            f"Time: {elapsed_time}ms",
            f"Notes recorded: {len(press_times)}",
            "Press SPACEBAR to stop recording"
        ]
    
    for i, instruction in enumerate(instructions):
        color = GREEN if recording and i == 0 else WHITE
        text = font.render(instruction, True, color)
        screen.blit(text, (width//2 - text.get_width()//2, 150 + i * 30))
    
    # Draw key positions
    for key_data in chart_keys.values():
        py.draw.circle(screen, key_data["color"], key_data["pos"], 30, 3)
        key_text = font.render(key_data["name"], True, WHITE)
        key_rect = key_text.get_rect(center=key_data["pos"])
        screen.blit(key_text, key_rect)
    
    # Status
    status_color = GREEN if current_song else RED
    status_text = f"Music: {current_song if current_song else 'No music file loaded'}"
    status = font.render(status_text, True, status_color)
    screen.blit(status, (20, height - 40))

def main():
    global recording, start_time, press_times, current_song, visual_effects, current_song_index

    clock = py.time.Clock()
    font = py.font.Font(None, 24)
    large_font = py.font.Font(None, 48)

    # Try to load music
    load_music(current_song_index)

    running = True
    while running:
        current_time = py.time.get_ticks()

        for event in py.event.get():
            if event.type == py.QUIT:
                running = False

            elif event.type == py.KEYDOWN:
                if event.key == py.K_SPACE:
                    if not recording and current_song:
                        # Start recording
                        recording = True
                        start_time = current_time
                        press_times = []
                        visual_effects = []
                        py.mixer.music.play()
                        print("Recording started!")
                    elif recording:
                        # Stop recording
                        recording = False
                        py.mixer.music.stop()
                        save_chart_data()
                        print("Recording stopped!")

                elif event.key == py.K_RIGHT:
                    if not recording:
                        # Next song
                        py.mixer.music.stop()
                        current_song_index = (current_song_index + 1) % len(music_files)
                        load_music(current_song_index)
                        print(f"Switched to: {current_song}")

                elif event.key == py.K_LEFT:
                    if not recording:
                        # Previous song
                        py.mixer.music.stop()
                        current_song_index = (current_song_index - 1) % len(music_files)
                        load_music(current_song_index)
                        print(f"Switched to: {current_song}")

                # Handle chart key presses
                handle_keypress(event.key, current_time)

        # Clear screen
        screen.fill(BLACK)

        # Update and draw visual effects
        visual_effects = [effect for effect in visual_effects if effect.update()]
        for effect in visual_effects:
            effect.draw(screen, font)

        # Draw interface
        draw_interface(screen, font, large_font)

        py.display.flip()
        clock.tick(60)

    # Cleanup
    py.mixer.music.stop()
    py.quit()

if __name__ == "__main__":
    main()