import gi
import cairo
import math
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

class FrameLine(Gtk.DrawingArea):
    def __init__(self, min_value=0, max_value=100, stride=1):
        super().__init__()
        
        # Slider properties
        self.min_value = min_value
        self.max_value = max_value
        self.left_value = min_value
        self.right_value = max_value
        self.stride = stride  # Step size for the slider

        self.handle_radius = 20  # Changed from width/height to radius
        self.track_height = 4   # Very thin track
        self.track_radius = 2   # Adjusted for the thin track
        self.dragging_left = False
        self.dragging_right = False
        self.drag_offset = 0
        
        # Enable events
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK)

        # Connect event handlers
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion_notify)

        self.value_changed_callback = None

    def set_value_changed_callback(self, callback):
        self.value_changed_callback = callback
        
    def on_draw(self, widget, cr):
        width = self.get_allocated_width()
        height = self.get_allocated_height()
     
        # Calculate positions for the left and right handles
        left_handle_x = max(self.handle_radius, self.value_to_position(self.left_value, width))
        right_handle_x = min(width - self.handle_radius, self.value_to_position(self.right_value, width))
     
        # Draw full grey track from edge to edge
        cr.set_source_rgb(0.7, 0.7, 0.7)  # Gray for unselected track
        self.draw_rounded_rectangle(cr, self.handle_radius, (height - self.track_height) / 2, 
                                    width - 2 * self.handle_radius, self.track_height, self.track_radius)
        cr.fill()
     
        # Draw selected portion of the track (white)
        cr.set_source_rgb(1, 1, 1)  # White for the selected track
        cr.rectangle(left_handle_x, (height - self.track_height) / 2, 
                     right_handle_x - left_handle_x, self.track_height)
        cr.fill()

        # Draw handles with white color
        cr.set_source_rgb(1, 1, 1)  # White color for handles
        
        # Left handle
        cr.new_path()
        cr.arc(left_handle_x, height / 2, self.handle_radius, 0, 2 * math.pi)
        cr.fill()
        
        # Right handle
        cr.new_path()
        cr.arc(right_handle_x, height / 2, self.handle_radius, 0, 2 * math.pi)
        cr.fill()

        # Draw text on handles
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(self.handle_radius * 0.6)  # Adjust font size as needed
        cr.set_source_rgb(0, 0, 0)  # Black color for text

        # Left handle text
        text = str(round(self.left_value))
        (x, y, text_width, text_height, dx, dy) = cr.text_extents(text)
        cr.move_to(left_handle_x - text_width / 2, height / 2 + text_height / 2)
        cr.show_text(text)

        # Right handle text
        text = str(round(self.right_value))
        (x, y, text_width, text_height, dx, dy) = cr.text_extents(text)
        cr.move_to(right_handle_x - text_width / 2, height / 2 + text_height / 2)
        cr.show_text(text)

    def draw_rounded_rectangle(self, cr, x, y, width, height, radius):
        # Adjust the drawing of rounded rectangle to handle very short tracks
        if width < 2 * radius:
            radius = width / 2
        cr.new_path()
        cr.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
        cr.arc(x + width - radius, y + radius, radius, 3 * math.pi / 2, 0)
        cr.arc(x + width - radius, y + height - radius, radius, 0, math.pi / 2)
        cr.arc(x + radius, y + height - radius, radius, math.pi / 2, math.pi)
        cr.close_path()

    def on_button_press(self, widget, event):
        width = self.get_allocated_width()
        left_handle_x = self.value_to_position(self.left_value, width)
        right_handle_x = self.value_to_position(self.right_value, width)

        if abs(event.x - left_handle_x) <= self.handle_radius:
            self.dragging_left = True
            self.drag_offset = left_handle_x - event.x
        elif abs(event.x - right_handle_x) <= self.handle_radius:
            self.dragging_right = True
            self.drag_offset = right_handle_x - event.x
        return True

    def on_button_release(self, widget, event):
        self.dragging_left = False
        self.dragging_right = False
        self.drag_offset = 0
        return True
    
    def on_motion_notify(self, widget, event):
        # Check if either handle is being dragged
        if self.dragging_left or self.dragging_right:
            # Get the width of the widget
            width = self.get_allocated_width()
            # Calculate new x position, accounting for drag offset
            new_x = event.x + self.drag_offset
            # Convert pixel position to slider value
            new_value = self.position_to_value(new_x, width)

            # Update the appropriate handle value
            if self.dragging_left:
                self.set_left_value(new_value)
            else:  # dragging right
                self.set_right_value(new_value)

            # Redraw the widget to reflect changes
            self.queue_draw()
            # Call the callback if it's set
            if self.value_changed_callback:
                self.value_changed_callback(self.left_value, self.right_value)
            
            return True
        return False

    def value_to_position(self, value, width):
        """Convert a value to a pixel position on the slider."""
        usable_width = width - 2 * self.handle_radius
        position = (value - self.min_value) / (self.max_value - self.min_value) * usable_width
        return position + self.handle_radius

    def position_to_value(self, x, width):
        """Convert a pixel position to a value on the slider."""
        usable_width = width - 2 * self.handle_radius
        clamped_x = max(self.handle_radius, min(x, width - self.handle_radius))
        return self.min_value + (clamped_x - self.handle_radius) / usable_width * (self.max_value - self.min_value)

    def round_to_stride(self, value):
        """Round the given value to the nearest stride increment."""
        return self.min_value + round((value - self.min_value) / self.stride) * self.stride

    def set_left_value(self, value):
        """Set the left handle value, respecting stride and boundaries."""
        rounded_value = self.round_to_stride(value)
        self.left_value = max(self.min_value, min(rounded_value, self.right_value - self.stride))

    def set_right_value(self, value):
        """Set the right handle value, respecting stride and boundaries."""
        rounded_value = self.round_to_stride(value)
        self.right_value = min(self.max_value, max(rounded_value, self.left_value + self.stride))

