import pygame as py
import os

py.mixer.init()

click_sound = py.mixer.Sound(os.path.join("Rhythm Game", "assets", "sounds", "click-sound.wav"))
click_sound.set_volume(0.2)

class Button:
    def __init__(self, audio, pos, current_pos, text_input, font, base_color="white", hovering_color="green", scale=1.0, padding=(20, 10), has_audio=None):
        self.x_pos, self.y_pos = pos 
        self.font = font
        self.base_color = base_color
        self.hovering_color = hovering_color
        self.text_input = text_input
        self.scale = scale
        self.padding = padding  # (horizontal, vertical) padding
        self.text = self.font.render(self.text_input, True, self.base_color)
        self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))
        self.button_rect = None
        self.is_hovering = False
        self.target_scale = self.scale
        self.scale_speed = 0.05
        self.clicking = False
        self.has_audio = has_audio
        self.audio = audio
        
        self.target_x = self.x_pos
        self.current_x = current_pos
        self.animation_speed = 30
        self.original_x = current_pos  # Store the initial offscreen position

        
        self.x_pos = self.current_x
        self.text_rect.center = (self.x_pos, self.y_pos)
        self._update_button_rect()
    
    def _update_button_rect(self):
        """Update the button's rectangle based on text size, padding and scale"""
        width = self.text_rect.width + (self.padding[0] * 2)
        height = self.text_rect.height + (self.padding[1] * 2)
        
        # Apply scaling
        scaled_width = int(width * self.scale)
        scaled_height = int(height * self.scale)
        
        # Create the button rect centered on the text position
        self.button_rect = py.Rect(
            self.x_pos - scaled_width // 2,
            self.y_pos - scaled_height // 2,
            scaled_width, 
            scaled_height
        )
    
    def slide_in(self):
        """Slide towards the target_x using ease in-out."""
        distance = self.target_x - self.current_x

        if abs(distance) > 1:
            # Easing factor (between 0 and 1) — tweak to control smoothness
            easing_factor = 0.07  
            self.current_x += distance * easing_factor
        else:
            self.current_x = self.target_x  # Snap to target if very close

        # Update actual position and hitboxes
        self.x_pos = self.current_x
        self.text_rect.center = (self.x_pos, self.y_pos)
        self._update_button_rect()

	
    def slide_out(self):
        """Slide back to the start_x using ease in-out."""
        distance = self.original_x - self.current_x

        if abs(distance) > 1:
            easing_factor = 0.07
            self.current_x += distance * easing_factor
        else:
            self.current_x = self.original_x

        self.x_pos = self.current_x
        self.text_rect.center = (self.x_pos, self.y_pos)
        self._update_button_rect()
    
    def update(self, screen):
        """Render the button on the screen"""
        self.smooth_resize()
        # Draw button background
        py.draw.rect(screen, self.base_color if not self.is_hovering else self.hovering_color, 
                     self.button_rect, 0, border_radius=12)
        
        # Draw button border
        border_color = self.hovering_color if not self.is_hovering else self.base_color
        py.draw.rect(screen, border_color, self.button_rect, 2, border_radius=12)
        
        # Draw button text in opposite color when hovering
        text_color = self.hovering_color if not self.is_hovering else self.base_color
        self.text = self.font.render(self.text_input, True, text_color)
        screen.blit(self.text, self.text_rect)
    
    def check_for_input(self, position):
        """Check if position is within button area. Return True if clicked."""
        if self.button_rect.collidepoint(position):
            if not self.is_hovering and self.has_audio:
                self.audio.play()
            return True
        return False
    
    def change_color(self, position):
        """Update hover state based on mouse position"""
        old_hover_state = self.is_hovering
        self.is_hovering = self.check_for_input(position)
        
        if self.is_hovering:
            self.resize(1.07)
        else:
            self.resize(1.0)
        
        # Return True if hover state changed
        return self.is_hovering != old_hover_state
    
    def smooth_resize(self):
        if abs(self.scale - self.target_scale) > 0.01:
            # Move scale closer to target_scale
            self.scale += (self.target_scale - self.scale) * self.scale_speed

            # Rerender text at new scale
            self.text = self.font.render(self.text_input, True, self.base_color)
            scaled_text = py.transform.smoothscale(
                self.text,
                (
                    int(self.text.get_width() * self.scale),
                    int(self.text.get_height() * self.scale)
                )
            )
            self.text = scaled_text
            self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))

            self._update_button_rect()


    def resize(self, new_scale):
        self.target_scale = new_scale
     
    def set_position(self, new_pos):
        """Move the button to a new position"""
        self.x_pos, self.y_pos = new_pos
        self.text_rect.center = new_pos
        self._update_button_rect()
    
    def set_text(self, new_text):
        """Change the button text"""
        self.text_input = new_text
        self.text = self.font.render(self.text_input, True, self.base_color)
        self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))
        self._update_button_rect()

    def is_clicked(self, position, mouse_pressed):
        """Check if the button is being clicked at the given position"""
        if self.button_rect.collidepoint(position) and mouse_pressed:
            if not self.clicking:  # Only trigger once when first pressed
                self.clicking = True
                if self.has_audio:
                    self.audio.play()
                return True
        elif not mouse_pressed:
            self.clicking = False  # Reset clicking state when mouse released
        return False