import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib, Graphene, GObject
import math
import cairo

class FrameLine(Gtk.Widget):
    __gtype_name__ = 'FrameLine'
    
    # Define the custom signal
    __gsignals__ = {
        'frames-changed': (GObject.SignalFlags.RUN_LAST, None, (float, float))
    }

    def __init__(self, min_value=0, max_value=100, stride=1):
        super().__init__()
        
        # Slider properties
        self.min_value = min_value
        self.max_value = max_value
        self.left_value = min_value
        self.right_value = max_value
        self.stride = stride
        
        # Visual properties (updated to match button height)
        self.handle_radius = 20  # Diameter will be 40px to match button height
        self.track_height = 4
        self.track_radius = 2
        
        # Dragging state
        self.dragging_left = False
        self.dragging_right = False
        self.drag_offset = 0 # prevent jump when press handle
        
        # Enable input
        self.set_can_target(True)
        self.set_focusable(True)
        
        # Setup gesture controllers
        self.click_gesture = Gtk.GestureClick.new()
        self.click_gesture.connect('pressed', self.on_pressed)
        self.click_gesture.connect('released', self.on_released)
        self.add_controller(self.click_gesture)
        
        self.motion_controller = Gtk.EventControllerMotion.new()
        self.motion_controller.connect('motion', self.on_motion)
        self.add_controller(self.motion_controller)
        
        self.value_changed_callback = None
        self.playhead_visible = False
        self.playhead_position = 0
        
        # Add hover state tracking
        self.left_handle_hover = False
        self.right_handle_hover = False
        
        # Add motion controller for hover effects
        self.motion_controller = Gtk.EventControllerMotion.new()
        self.motion_controller.connect('enter', self.on_enter)
        self.motion_controller.connect('leave', self.on_leave)
        self.motion_controller.connect('motion', self.on_motion)
        self.add_controller(self.motion_controller)

    def do_measure(self, orientation, for_size):
        if orientation == Gtk.Orientation.VERTICAL:
            # Fixed height that accommodates the handles
            return 50, 50, -1, -1
        else:
            # Minimum width should accommodate both handles
            return 100, 400, -1, -1

    def do_snapshot(self, snapshot):
        width = self.get_width()
        height = self.get_height()
        
        # Calculate padding needed for scaled handles
        scale_factor = 1.05
        padding = self.handle_radius * (scale_factor - 1)
        
        # Adjust positions to account for padding
        left_handle_x = max(self.handle_radius + padding, 
                           self.value_to_position(self.left_value, width))
        right_handle_x = min(width - self.handle_radius - padding, 
                            self.value_to_position(self.right_value, width))
        
        # Create Cairo context with adjusted area
        cr = snapshot.append_cairo(
            Graphene.Rect().init(-padding, -padding, 
                                width + 2*padding, height + 2*padding)
        )
        
        # Draw full grey track
        cr.set_source_rgb(0, 0, 0)
        self.draw_rounded_rectangle(cr, self.handle_radius, (height - self.track_height) / 2,
                                  width - 2 * self.handle_radius, self.track_height, self.track_radius)
        cr.fill()
        
        # Draw selected portion (white or red depending on handle positions)
        if self.left_value <= self.right_value:
            cr.set_source_rgb(1, 1, 1)  # White for normal order
        else:
            cr.set_source_rgb(1, 0.4, 0.4)  # Light red for reverse order
        
        cr.rectangle(min(left_handle_x, right_handle_x), (height - self.track_height) / 2,
                    abs(right_handle_x - left_handle_x), self.track_height)
        cr.fill()
        
        # Draw handles
        cr.set_source_rgb(1, 1, 1)
        
        # Left handle
        cr.new_path()
        if self.left_handle_hover or self.dragging_left:
            cr.save()
            cr.translate(left_handle_x, height / 2)
            cr.scale(1.05, 1.05)
            cr.translate(-left_handle_x, -height / 2)
            cr.arc(left_handle_x, height / 2, self.handle_radius, 0, 2 * math.pi)
            cr.restore()
        else:
            cr.arc(left_handle_x, height / 2, self.handle_radius, 0, 2 * math.pi)
        cr.fill()
        
        # Right handle
        cr.new_path()
        if self.right_handle_hover or self.dragging_right:
            cr.save()
            cr.translate(right_handle_x, height / 2)
            cr.scale(1.05, 1.05)
            cr.translate(-right_handle_x, -height / 2)
            cr.arc(right_handle_x, height / 2, self.handle_radius, 0, 2 * math.pi)
            cr.restore()
        else:
            cr.arc(right_handle_x, height / 2, self.handle_radius, 0, 2 * math.pi)
        cr.fill()
        
        # Draw text on handles
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(self.handle_radius * 0.6)
        cr.set_source_rgb(0, 0, 0)
        
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
        
        # Draw playhead if visible
        if self.playhead_visible:
            playhead_x = self.value_to_position(self.playhead_position + 1, width)
            vertical_center = height / 2
            
            # Draw playhead circle
            cr.set_source_rgb(1, 1, 1)
            cr.arc(playhead_x, vertical_center, self.handle_radius, 0, 2 * math.pi)
            cr.fill()
            
            # Draw frame number inside playhead (exactly like handles)
            frame_text = str(int(self.playhead_position + 1))
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(11)
            
            # Get text dimensions
            text_extents = cr.text_extents(frame_text)
            text_x = playhead_x - text_extents.width / 2
            text_y = vertical_center + text_extents.height / 2 - 1
            
            # Draw text
            cr.set_source_rgb(0.2, 0.2, 0.2)
            cr.move_to(text_x, text_y)
            cr.show_text(frame_text)

    def draw_rounded_rectangle(self, cr, x, y, width, height, radius):
        if width < 2 * radius:
            radius = width / 2
        cr.new_path()
        cr.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
        cr.arc(x + width - radius, y + radius, radius, 3 * math.pi / 2, 0)
        cr.arc(x + width - radius, y + height - radius, radius, 0, math.pi / 2)
        cr.arc(x + radius, y + height - radius, radius, math.pi / 2, math.pi)
        cr.close_path()

    def on_pressed(self, gesture, n_press, x, y):
        width = self.get_width()
        left_handle_x = self.value_to_position(self.left_value, width)
        right_handle_x = self.value_to_position(self.right_value, width)
        
        if abs(x - left_handle_x) <= self.handle_radius:
            self.dragging_left = True
            self.drag_offset = left_handle_x - x
            gesture.set_state(Gtk.EventSequenceState.CLAIMED)
        elif abs(x - right_handle_x) <= self.handle_radius:
            self.dragging_right = True
            self.drag_offset = right_handle_x - x
            gesture.set_state(Gtk.EventSequenceState.CLAIMED)

    def on_released(self, gesture, n_press, x, y):
        self.dragging_left = False
        self.dragging_right = False
        self.drag_offset = 0

    def on_motion(self, controller, x, y):
        if self.dragging_left or self.dragging_right:
            width = self.get_width()
            new_x = x + self.drag_offset
            new_value = self.position_to_value(new_x, width)
            
            if self.dragging_left:
                self.set_left_value(new_value)
            else:
                self.set_right_value(new_value)
            
            self.queue_draw()
            if self.left_value <= self.right_value:
                self.emit('frames-changed', self.left_value, self.right_value)
            else:
                self.emit('frames-changed', self.right_value, self.left_value)
        else:
            # Handle hover effects when not dragging
            self.check_handle_hover(x, y)
            self.queue_draw()

    # Helper methods remain the same
    def value_to_position(self, value, width):
        usable_width = width - 2 * self.handle_radius
        position = (value - self.min_value) / (self.max_value - self.min_value) * usable_width
        return position + self.handle_radius

    def position_to_value(self, x, width):
        usable_width = width - 2 * self.handle_radius
        clamped_x = max(self.handle_radius, min(x, width - self.handle_radius))
        return self.min_value + (clamped_x - self.handle_radius) / usable_width * (self.max_value - self.min_value)

    def round_to_stride(self, value):
        return self.min_value + round((value - self.min_value) / self.stride) * self.stride

    def set_left_value(self, value):
        rounded_value = self.round_to_stride(value)
        self.left_value = max(self.min_value, min(rounded_value, self.max_value))

    def set_right_value(self, value):
        rounded_value = self.round_to_stride(value)
        self.right_value = max(self.min_value, min(rounded_value, self.max_value))

    def set_value_changed_callback(self, callback):
        self.value_changed_callback = callback

    def set_playhead_position(self, position):
        """Set playhead position"""
        self.playhead_position = position
        # If position is -1, hide the playhead
        if position == -1:
            self.playhead_visible = False
        self.queue_draw()

    def show_playhead(self):
        """Show the playhead"""
        self.playhead_visible = True
        self.queue_draw()

    def hide_playhead(self):
        """Hide the playhead"""
        self.playhead_visible = False
        self.queue_draw()

    def on_handle_drag_begin(self):
        """Called when handle drag begins"""
        self.dragging = True
        # Store current playhead state if not playing
        self.playhead_position_before_drag = self.playhead_position

    def on_handle_drag_end(self):
        """Called when handle drag ends"""
        self.dragging = False
        # Restore playhead position if not playing
        if not self.editor.is_playing:
            self.set_playhead_position(self.playhead_position_before_drag)

    def on_enter(self, controller, x, y):
        self.check_handle_hover(x, y)
        self.queue_draw()

    def on_leave(self, controller):
        self.left_handle_hover = False
        self.right_handle_hover = False
        self.queue_draw()

    def check_handle_hover(self, x, y):
        width = self.get_width()
        left_handle_x = self.value_to_position(self.left_value, width)
        right_handle_x = self.value_to_position(self.right_value, width)
        
        # Check if mouse is over either handle
        self.left_handle_hover = abs(x - left_handle_x) <= self.handle_radius and not self.dragging_right
        self.right_handle_hover = abs(x - right_handle_x) <= self.handle_radius and not self.dragging_left
