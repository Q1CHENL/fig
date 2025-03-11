import os
import cairo
import math
from gi.repository import Gtk, Gdk, GLib, Graphene, GObject, Gio
import gi
gi.require_version('Gtk', '4.0')


class FrameLine(Gtk.Widget):
    __gtype_name__ = 'FrameLine'

    __gsignals__ = {
        'frames-changed': (GObject.SignalFlags.RUN_LAST, None, (float, float)),
        'insert-frames': (GObject.SignalFlags.RUN_LAST, None, (int, object)),
        'speed-changed': (GObject.SignalFlags.RUN_LAST, None, (float, float, float))  # start, end, speed_factor
    }

    def __init__(self, editor=None):
        super().__init__()
        
        self.editor = editor

        self.stride = 1
        self.min_value = 0
        self.max_value = 1

        # Handle properties
        self.left_value = self.min_value
        self.right_value = self.max_value - 1

        # Visual properties (updated to match button height)
        self.handle_radius = 20  # Diameter will be 40px to match button height
        self.track_height = 4
        self.track_radius = 2

        # Theme colors
        self.track_color = (0, 0, 0, 0.1)
        self.handle_color = (0, 0, 0, 1)  
        self.text_color = (0, 0, 0, 1)
        self.playhead_color = (0, 0, 0, 1)
        self.selected_track_color = (1, 1, 1, 1)

        self.dragging_left = False
        self.dragging_right = False
        self.drag_offset = 0  # prevent jump when press handle

        # Enable interaction
        self.set_can_target(True)
        self.set_focusable(True)

        # Setup gesture controllers
        self.click_gesture = Gtk.GestureClick.new()
        self.click_gesture.connect('pressed', self.on_handle_pressed)
        self.click_gesture.connect('released', self.on_handle_released)
        self.add_controller(self.click_gesture)

        self.motion_controller = Gtk.EventControllerMotion.new()
        self.motion_controller.connect('motion', self.on_motion)
        self.add_controller(self.motion_controller)

        self.playhead_visible = False
        self.playhead_pos = 1

        self.left_handle_hover = False
        self.right_handle_hover = False

        # Add motion controller for hover effects
        self.motion_controller = Gtk.EventControllerMotion.new()
        self.motion_controller.connect('enter', self.on_enter)
        self.motion_controller.connect('leave', self.on_leave)
        self.motion_controller.connect('motion', self.on_motion)
        self.add_controller(self.motion_controller)

        # Keep these for red highlight feature
        self.menu_active = False
        self.active_handle = None
        self.hover_action = None  # Track which menu item is being hovered

        # Add right click gesture (add this near other gesture controllers)
        self.right_click_gesture = Gtk.GestureClick.new()
        self.right_click_gesture.set_button(3)  # 3 is right click
        self.right_click_gesture.connect('pressed', self.on_right_click)
        self.add_controller(self.right_click_gesture)

        self.popup_menu = Gtk.Popover()
        self.popup_menu.set_has_arrow(False)
        self.popup_menu.set_parent(self)
        self.popup_menu.set_autohide(True)

        # Add key controller for escape key
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect('key-pressed', self.on_key_pressed)
        self.popup_menu.add_controller(key_controller)

        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        remove_range_btn = Gtk.Button(label="Remove Range")
        remove_range_btn.connect('clicked', self.on_remove_range_clicked)

        remove_frame_btn = Gtk.Button(label="Remove Frame")
        remove_frame_btn.connect('clicked', self.on_remove_frame_clicked)
        
        insert_frames_btn = Gtk.Button(label="Insert Frames")
        insert_frames_btn.connect('clicked', self.on_insert_frames_clicked)

        changespeed_frames_btn = Gtk.Button(label="Change Speed...")
        changespeed_frames_btn.connect('clicked', self.on_changespeed_frames_clicked)

        # Add CSS classes and set alignment
        remove_range_btn.set_halign(Gtk.Align.START)
        remove_frame_btn.set_halign(Gtk.Align.START)
        insert_frames_btn.set_halign(Gtk.Align.START)
        changespeed_frames_btn.set_halign(Gtk.Align.START)

        remove_range_btn.add_css_class('menu-item')
        remove_frame_btn.add_css_class('menu-item')
        insert_frames_btn.add_css_class('menu-item')
        changespeed_frames_btn.add_css_class('menu-item')

        # Add hover controllers
        range_motion = Gtk.EventControllerMotion.new()
        range_motion.connect('enter', self.on_remove_range_hover_enter)
        range_motion.connect('leave', self.on_menu_item_hover_leave)
        remove_range_btn.add_controller(range_motion)

        frame_motion = Gtk.EventControllerMotion.new()
        frame_motion.connect('enter', self.on_remove_frame_hover_enter)
        frame_motion.connect('leave', self.on_menu_item_hover_leave)
        remove_frame_btn.add_controller(frame_motion)

        insert_motion = Gtk.EventControllerMotion.new()
        insert_motion.connect('enter', self.on_insert_frames_hover_enter)
        insert_motion.connect('leave', self.on_menu_item_hover_leave)
        insert_frames_btn.add_controller(insert_motion)

        changespeed_motion = Gtk.EventControllerMotion.new()
        changespeed_motion.connect('enter', self.on_changespeed_frames_hover_enter)
        changespeed_motion.connect('leave', self.on_menu_item_hover_leave)
        changespeed_frames_btn.add_controller(changespeed_motion)

        menu_box.append(remove_range_btn)
        menu_box.append(remove_frame_btn)
        menu_box.append(insert_frames_btn)
        menu_box.append(changespeed_frames_btn)

        self.popup_menu.set_child(menu_box)
        self.popup_menu.connect('closed', self.on_popup_closed)

        # Modified 0-based Ranges (start, end)
        self.removed_ranges = [] 
        self.inserted_ranges = []
        self.speed_ranges = []


    # Handle Hover
    def on_remove_range_hover_enter(self, controller, x, y):
        self.hover_action = 'range'
        self.queue_draw()

    def on_remove_frame_hover_enter(self, controller, x, y):
        self.hover_action = 'frame'
        self.queue_draw()

    def on_insert_frames_hover_enter(self, controller, x, y):
        self.hover_action = 'insert'
        self.queue_draw()

    def on_changespeed_frames_hover_enter(self, controller, x, y):
        self.hover_action = 'changespeed'
        self.queue_draw()

    def on_menu_item_hover_leave(self, controller, *args):
        self.hover_action = None
        self.queue_draw()


    # Called internally by Gtk Layout System
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

        cr = snapshot.append_cairo(
            Graphene.Rect().init(-padding, -padding,
                                 width + 2*padding, height + 2*padding)
        )

        # 1. Draw base track first
        cr.set_source_rgba(self.track_color[0], self.track_color[1], 
                          self.track_color[2], self.track_color[3])
        self.draw_rounded_rectangle(cr, self.handle_radius, (height - self.track_height) / 2,
                                    width - 2 * self.handle_radius, self.track_height, self.track_radius)
        cr.fill()

        self.draw_selected_track(cr, left_handle_x, right_handle_x, width, height)
        self.draw_inserted_ranges(cr, width, height)
        self.draw_speed_ranges(cr, width, height)
        self.draw_removed_ranges(cr, width, height)
        self.draw_playhead(cr, width, height)
        self.draw_handles(cr, left_handle_x, right_handle_x, height)

    def draw_handles(self, cr, left_handle_x, right_handle_x, height):
        for handle_x, is_left_handle in [(left_handle_x, True), (right_handle_x, False)]:
            # Determine handle color based on hover state and active handle
            if self.hover_action == 'frame' and (
                (is_left_handle and self.active_handle == 'left') or
                (not is_left_handle and self.active_handle == 'right')
            ):
                cr.set_source_rgb(0xed/255, 0x33/255, 0x3b/255)  # Red for active handle on frame hover
            elif self.hover_action == 'range':
                cr.set_source_rgb(0xed/255, 0x33/255, 0x3b/255)  # Red for both handles on range hover
            elif self.hover_action == 'changespeed' or self.handle_within_speed_range(handle_x):
                cr.set_source_rgb(0x62/255, 0xa0/255, 0xea/255)  # Blue
            elif (self.hover_action == 'insert' and (
                (is_left_handle and self.active_handle == 'left') or
                (not is_left_handle and self.active_handle == 'right')) or
                self.handle_within_insert_range(handle_x)):
                cr.set_source_rgb(0x57/255, 0xe3/255, 0x89/255)  # Green for active handle on insert hover
            else:
                cr.set_source_rgba(self.handle_color[0], self.handle_color[1],
                             self.handle_color[2], self.handle_color[3])  # White

            self.draw_handle(cr, handle_x, height)
    
    def draw_playhead(self, cr, width, height):
        if self.playhead_visible and self.playhead_pos > 0:
            playhead_x = self.value_to_position(self.playhead_pos, width)
            
            # Get and apply the appropriate color based on frame state
            color = self.get_playhead_color(self.playhead_pos)
            cr.set_source_rgb(color[0], color[1], color[2])
            self.draw_handle(cr, playhead_x, height)
        
        # Restore default handle color
        cr.set_source_rgba(self.handle_color[0], self.handle_color[1],
                          self.handle_color[2], self.handle_color[3])
    
    def draw_selected_track(self, cr, left_handle_x, right_handle_x, width, height):
        if self.hover_action == 'range':
            cr.set_source_rgb(0xed/255, 0x33/255, 0x3b/255)  # Red
        elif self.hover_action == 'changespeed':
            cr.set_source_rgb(0x62/255, 0xa0/255, 0xea/255)  # Blue
        elif self.left_value <= self.right_value:
            cr.set_source_rgba(self.selected_track_color[0], self.selected_track_color[1],
                             self.selected_track_color[2], self.selected_track_color[3])
        else:
            cr.set_source_rgb(1, 0.4, 0.4)  # Light red

        cr.rectangle(min(left_handle_x, right_handle_x), (height - self.track_height) / 2,
                    abs(right_handle_x - left_handle_x), self.track_height)
        cr.fill()
            
    def handle_within_insert_range(self, handle_x):
        # Convert handle_x screen position to frame value
        handle_value = self.position_to_value(handle_x, self.get_width())
        for start, end in self.inserted_ranges:
            # Compare using frame values (ranges are stored as 1-based indices)
            if start <= handle_value <= end:
                return True
        return False
    
    def handle_within_speed_range(self, handle_x):
        # Convert handle_x screen position to frame value
        handle_value = self.position_to_value(handle_x, self.get_width())
        for start, end, _ in self.speed_ranges:
            # Add 1 to convert from 0-based to 1-based indices
            if (start + 1) <= handle_value <= (end + 1):
                return True
        return False
    
    def get_playhead_color(self, position):
        for range_start, range_end, _ in self.speed_ranges:
            if range_start <= position <= range_end:
                return (0x62/255, 0xa0/255, 0xea/255)  # Blue
        for range_start, range_end in self.inserted_ranges:
            if range_start <= position <= range_end:
                return (0x57/255, 0xe3/255, 0x89/255)  # Green
        return self.playhead_color

    def draw_rounded_rectangle(self, cr, x, y, width, height, radius):
        if width < 2 * radius:
            radius = width / 2
        cr.new_path()
        cr.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
        cr.arc(x + width - radius, y + radius, radius, 3 * math.pi / 2, 0)
        cr.arc(x + width - radius, y + height - radius, radius, 0, math.pi / 2)
        cr.arc(x + radius, y + height - radius, radius, math.pi / 2, math.pi)
        cr.close_path()

    def on_handle_pressed(self, gesture, n_press, x, y):
        """Handle mouse press on the widget"""
        if not self.editor:
            return
        
        # Hide crop overlay when interacting with frameline
        self.editor.overlay.handles_visible = False
        self.editor.overlay.drawing_area.queue_draw()
        
        width = self.get_width()
        left_handle_x = self.value_to_position(self.left_value, width)
        right_handle_x = self.value_to_position(self.right_value, width)
        
        # Only handle dragging for left click
        if abs(x - left_handle_x) <= self.handle_radius:
            self.dragging_left = True
            self.drag_offset = left_handle_x - x
            gesture.set_state(Gtk.EventSequenceState.CLAIMED)
        elif abs(x - right_handle_x) <= self.handle_radius:
            self.dragging_right = True
            self.drag_offset = right_handle_x - x
            gesture.set_state(Gtk.EventSequenceState.CLAIMED)

        # Clear any existing menu state
        self.menu_active = False
        self.active_handle = None
        self.popup_menu.popdown()

        self.queue_draw()

    def on_handle_released(self, gesture, n_press, x, y):
        self.dragging_left = False
        self.dragging_right = False
        self.drag_offset = 0

    def on_motion(self, controller, x, y):
        if self.dragging_left or self.dragging_right:
            width = self.get_width()
            new_x = x + self.drag_offset
            new_value = self.position_to_value(new_x, width)
            
            # Find next valid frame position
            frame_index = int(round(new_value)) - 1
            if self.is_frame_removed(frame_index):
                # Get direction based on drag movement
                direction = 1 if new_value > (self.left_value if self.dragging_left else self.right_value) else -1
                next_valid = self.get_next_valid_frame(frame_index, direction)
                if next_valid != -1:
                    new_value = next_valid + 1  # Convert back to 1-based value

            if self.dragging_left:
                self.set_left_value(new_value)
            else:
                self.set_right_value(new_value)

            self.queue_draw()
            if self.left_value <= self.right_value:
                self.emit('frames-changed', self.left_value, self.right_value)
            else:
                self.emit('frames-changed', self.right_value, self.left_value)
            self.editor.update_info_label()
        else:
            # Handle hover effects when not dragging
            self.check_handle_hover(x, y)
            self.queue_draw()

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

    def on_right_click(self, gesture, n_press, x, y):
        if self.popup_menu.get_visible():
            self.popup_menu.popdown()

        width = self.get_width()
        left_handle_x = self.value_to_position(self.left_value, width)
        right_handle_x = self.value_to_position(self.right_value, width)

        # Check if click is on handles
        if abs(x - left_handle_x) <= self.handle_radius:
            self.active_handle = 'left'
            rect = Gdk.Rectangle()
            rect.x = int(x)
            rect.y = int(y)
            rect.width = 1
            rect.height = 1
            self.popup_menu.set_pointing_to(rect)
            self.popup_menu.popup()
        elif abs(x - right_handle_x) <= self.handle_radius:
            self.active_handle = 'right'
            rect = Gdk.Rectangle()
            rect.x = int(x)
            rect.y = int(y)
            rect.width = 1
            rect.height = 1
            self.popup_menu.set_pointing_to(rect)
            self.popup_menu.popup()
        else:
            self.active_handle = None
            self.hover_action = None
            self.popup_menu.popdown()

        self.queue_draw()

    def draw_handle(self, cr, handle_x, height):
        """Helper method to draw a handle"""
        cr.new_path()
        
        # Draw handle circle with scaling if hovered
        if (self.left_handle_hover and handle_x == self.value_to_position(self.left_value, self.get_width())) or \
           (self.right_handle_hover and handle_x == self.value_to_position(self.right_value, self.get_width())):
            cr.save()
            cr.translate(handle_x, height / 2)
            cr.scale(1.05, 1.05)
            cr.translate(-handle_x, -height / 2)
            cr.arc(handle_x, height / 2, self.handle_radius, 0, 2 * math.pi)
            cr.restore()
        else:
            cr.arc(handle_x, height / 2, self.handle_radius, 0, 2 * math.pi)
        cr.fill()

        # Draw frame number text
        width = self.get_width()
        left_pos = self.value_to_position(self.left_value, width)
        right_pos = self.value_to_position(self.right_value, width)
        playhead_pos = self.value_to_position(self.playhead_pos, width) if self.playhead_visible else -1

        text = ""        
        # More robust position comparison that handles edge cases
        if abs(handle_x - left_pos) < 1 or (handle_x <= self.handle_radius + 1 and left_pos <= self.handle_radius + 1):
            text = str(int(self.left_value))
        elif abs(handle_x - right_pos) < 1 or (handle_x >= width - self.handle_radius - 1 and right_pos >= width - self.handle_radius - 1):
            text = str(int(self.right_value))
        elif self.playhead_visible and (abs(handle_x - playhead_pos) < 1):
            text = str(int(self.playhead_pos))
        
        if text:  # Only draw text if we have a value to display
            cr.set_source_rgba(self.text_color[0], self.text_color[1],
                              self.text_color[2], self.text_color[3])
            
            # Center text in handle
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(12)
            
            # Get text extents for centering
            extents = cr.text_extents(text)
            text_x = handle_x - extents.width / 2
            text_y = height / 2 + extents.height / 2
            
            cr.move_to(text_x, text_y)
            cr.show_text(text)

    def on_popup_closed(self, popover):
        """Reset states when popup menu is closed"""
        self.menu_active = False
        self.active_handle = None
        self.hover_action = None
        self.queue_draw()

    def on_key_pressed(self, controller, keyval, keycode, state):
        """Handle escape key to close popover"""
        if keyval == Gdk.KEY_Escape:
            self.popup_menu.popdown()
            return True
        return False

    def on_changespeed_frames_hover_enter(self, controller, x, y):
        self.hover_action = 'changespeed'
        self.queue_draw()

    def on_remove_range_clicked(self, button):
        # Get current range values (1-based)
        start = min(self.left_value, self.right_value)
        end = max(self.left_value, self.right_value)
        self.add_removed_range(start, end)
        self.popup_menu.popdown()

    def on_remove_frame_clicked(self, button):
        """Remove a single frame at the handle position"""
        # Get the frame to remove based on which handle was right-clicked
        if self.active_handle == 'left':
            frame = int(self.left_value)
        else:
            frame = int(self.right_value)
        self.add_removed_range(frame, frame)
        self.popup_menu.popdown()

    def add_removed_range(self, start, end):
        """Add a range of frames to be removed"""
        # Convert to 0-based indices for internal storage
        start_idx = int(start) - 1
        end_idx = int(end) - 1
        
        # Add to removed ranges
        self.removed_ranges.append((start_idx, end_idx))
        
        # Sort and merge overlapping ranges
        self.removed_ranges.sort()
        merged = []
        for range_start, range_end in self.removed_ranges:
            if not merged or merged[-1][1] + 1 < range_start:
                merged.append([range_start, range_end])
            else:
                merged[-1][1] = max(merged[-1][1], range_end)
        self.removed_ranges = [tuple(x) for x in merged]
        
        # Update speed ranges to exclude removed frames
        new_speed_ranges = []
        for speed_start, speed_end, speed in self.speed_ranges:
            # Keep ranges that don't overlap with removed range
            if not (speed_start <= end_idx and speed_end >= start_idx):
                new_speed_ranges.append((speed_start, speed_end, speed))
            else:
                # Split range if necessary
                if speed_start < start_idx:
                    new_speed_ranges.append((speed_start, start_idx - 1, speed))
                if speed_end > end_idx:
                    new_speed_ranges.append((end_idx + 1, speed_end, speed))
        self.speed_ranges = new_speed_ranges
        
        # Reset handles and emit signal
        self.left_value = self.min_value
        self.right_value = self.max_value
        self.emit('frames-changed', self.left_value, self.right_value)
        
        self.queue_draw()

    def is_frame_removed(self, frame_index):
        """Check if a frame index is within any removed range"""
        frame_index = int(frame_index)
        for start, end in self.removed_ranges:
            if start <= frame_index <= end:
                return True
        return False

    def get_next_valid_frame(self, current_frame, direction=1):
        """Get next valid frame index, skipping removed ranges
        direction: 1 for forward, -1 for reverse"""
        next_frame = current_frame + direction
        while 0 <= next_frame < self.max_value and self.is_frame_removed(next_frame):
            next_frame += direction
        return next_frame if 0 <= next_frame < self.max_value else -1


    def on_insert_frames_clicked(self, button):
        """Handle insert frames button click"""
        try:
            # Store the active handle before closing the popover
            insert_at_handle = self.active_handle

            self.popup_menu.popdown()
            
            dialog = Gtk.FileDialog.new()
            dialog.set_title("Select Images to Insert")
            dialog.set_modal(True)

            # Set up file filters
            filter_images = Gtk.FileFilter()
            filter_images.set_name("Images")
            filter_images.add_mime_type("image/gif")
            filter_images.add_mime_type("image/png")
            filter_images.add_mime_type("image/jpeg")
            
            filter_all = Gtk.FileFilter()
            filter_all.set_name("All files")
            filter_all.add_pattern("*")
            
            filters = Gio.ListStore.new(Gtk.FileFilter)
            filters.append(filter_images)
            filters.append(filter_all)
            dialog.set_filters(filters)
            dialog.set_default_filter(filter_images)

            # Initialize with home directory
            home_dir = GLib.get_home_dir()
            if os.path.exists(home_dir):
                dialog.set_initial_folder(Gio.File.new_for_path(home_dir))

            # Pass the stored handle to the response callback
            dialog.open_multiple(
                parent=self.get_root(),
                callback=lambda d, r: self._on_insert_dialog_response(d, r, insert_at_handle)
            )

        except Exception as e:
            print(f"Error opening file dialog: {e}")

    def _on_insert_dialog_response(self, dialog, result, insert_at_handle):
        """Handle insert file dialog response"""
        try:
            files = dialog.open_multiple_finish(result)
            if files and files.get_n_items() > 0:
                # Determine the insert point based on the active handle
                insert_point = int(self.left_value if insert_at_handle == 'left' else self.right_value)

                # Add 1 to insert after the current frame
                insert_point += 1

                # Convert files to list of paths
                file_paths = [files.get_item(i).get_path() 
                             for i in range(files.get_n_items())]

                # Emit custom signal with insert information
                self.emit('insert-frames', insert_point, file_paths)

        except GLib.Error as e:
            print(f"Error selecting files: {e.message}")

    def draw_inserted_ranges(self, cr, width, height):
        """Draw inserted ranges in green"""
        track_y = (height - self.track_height) / 2
        
        for start_idx, end_idx in self.inserted_ranges:
            # Convert indices to positions (fix the off-by-one issue)
            start_pos = self.value_to_position(start_idx, width)  # Removed +1
            end_pos = self.value_to_position(end_idx + 1, width)  # Changed from +2 to +1
            
            # Draw green highlight
            cr.set_source_rgb(0x2d/255, 0xc6/255, 0x53/255)  # Green color
            cr.rectangle(start_pos, track_y, end_pos - start_pos, self.track_height)
            cr.fill()

    def on_changespeed_frames_clicked(self, button):
        # Close the main context menu
        self.popup_menu.popdown()
        
        # Create speed selection popover
        speed_popover = Gtk.Popover()
        speed_popover.set_has_arrow(False)
        speed_popover.set_parent(self)
        speed_popover.set_autohide(True)
        
        # Create box for speed options
        speed_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        # Speed options
        speeds = [
            ("2.0x", 2.0),
            ("1.5x", 1.5),
            ("1.2x", 1.2),
            ("1.0x", 1.0),
            ("0.75x", 0.75),
            ("0.5x", 0.5)
        ]
        
        for label, speed in speeds:
            speed_btn = Gtk.Button(label=label)
            speed_btn.add_css_class('menu-item')
            speed_btn.set_halign(Gtk.Align.START)
            speed_btn.connect('clicked', self.on_speed_selected, speed)
            speed_box.append(speed_btn)
        
        speed_popover.set_child(speed_box)
        
        # Position the popover near the clicked handle
        if self.active_handle == 'left':
            x = self.value_to_position(self.left_value, self.get_width())
        else:
            x = self.value_to_position(self.right_value, self.get_width())
        
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(self.get_height() / 2)
        rect.width = 1
        rect.height = 1
        
        speed_popover.set_pointing_to(rect)
        speed_popover.popup()

    def on_speed_selected(self, button, speed_factor):
        # Get the current range
        start = min(self.left_value, self.right_value)
        end = max(self.left_value, self.right_value)
        
        # Add to speed ranges
        self.speed_ranges.append((int(start) - 1, int(end) - 1, speed_factor))
        
        # Sort and merge overlapping ranges
        self.speed_ranges.sort()
        merged = []
        for range_start, range_end, speed in self.speed_ranges:
            if not merged or merged[-1][1] + 1 < range_start:
                merged.append([range_start, range_end, speed])
            else:
                merged[-1][1] = max(merged[-1][1], range_end)
                merged[-1][2] = speed  # Use the most recent speed for overlapping ranges
        self.speed_ranges = [tuple(x) for x in merged]
        
        # Emit the speed-changed signal
        self.emit('speed-changed', start, end, speed_factor)
        
        # Close the speed selection popover
        widget = button
        while widget and not isinstance(widget, Gtk.Popover):
            widget = widget.get_parent()
        if widget:
            widget.popdown()
        
        # Redraw to show the speed range
        self.queue_draw()

    def draw_removed_ranges(self, cr, width, height):
        """Draw removed ranges in red"""
        cr.set_source_rgb(0xed/255, 0x33/255, 0x3b/255)  # Red
        for start, end in self.removed_ranges:
            start_x = self.value_to_position(start + 1, width)
            end_x = self.value_to_position(end + 1, width)
            cr.rectangle(start_x, (height - self.track_height) / 2,
                        end_x - start_x + (width - 2 * self.handle_radius) / (self.max_value - self.min_value),
                        self.track_height)
            cr.fill()

    def draw_speed_ranges(self, cr, width, height):
        """Draw speed-modified ranges in blue"""
        track_y = (height - self.track_height) / 2
        
        for start_idx, end_idx, _ in self.speed_ranges:
            # Convert indices to positions (use same logic as inserted_ranges)
            start_pos = self.value_to_position(start_idx + 1, width)
            end_pos = self.value_to_position(end_idx + 2, width)  # +2 to include the full range
            
            # Draw blue highlight
            cr.set_source_rgb(0x62/255, 0xa0/255, 0xea/255)  # Blue color
            cr.rectangle(start_pos, track_y, end_pos - start_pos, self.track_height)
            cr.fill()

    def add_speed_range(self, start, end, speed):
        """Add a speed range"""
        self.speed_ranges.append((start, end, speed))

    def update_theme(self, is_dark):
        """Update theme colors"""
        from fig.utils import clear_css
        
        clear_css(self)
        
        self.add_css_class("frameline-dark" if is_dark else "frameline-light")
        
        if is_dark:
            self.track_color = (1, 1, 1, 0.1)    
            self.handle_color = (1, 1, 1, 1)
            self.text_color = (0, 0, 0, 1)       
            self.playhead_color = (1, 1, 1, 1)
            self.selected_track_color = (1, 1, 1, 1)
        else:
            self.track_color = (0, 0, 0, 0.1)  
            self.handle_color = (0.141, 0.141, 0.141, 1)     
            self.text_color = (1, 1, 1, 1)
            self.playhead_color = (0.141, 0.141, 0.141, 1)
            self.selected_track_color = (0.141, 0.141, 0.141, 1)

        self.queue_draw()

    def reset(self):
        """Reset framline state"""
        self.min_value = 0
        self.max_value = 1
        self.left_value = 0
        self.right_value = 0
        self.removed_ranges = []
        self.inserted_ranges = []
        self.speed_ranges = []
        self.playhead_pos = 1
        self.playhead_visible = False
        self.dragging_left = False
        self.dragging_right = False
        self.drag_offset = 0
        self.left_handle_hover = False
        self.right_handle_hover = False
        self.menu_active = False
        self.active_handle = None
        self.hover_action = None
        self.queue_draw()

    #
    # Test and Internal Methods
    #
    
    def clear_removed_ranges(self):
        self.removed_ranges = []
        self.queue_draw()
    
    def set_left_value(self, value):
        """Internal method to set left handle value"""
        rounded_value = self.round_to_stride(value)
        self.left_value = max(self.min_value, min(rounded_value, self.max_value))

    def set_right_value(self, value):
        """Internal method to set right handle value"""
        rounded_value = self.round_to_stride(value)
        self.right_value = max(self.min_value, min(rounded_value, self.max_value))

    def round_to_stride(self, value):
        """Internal method to round value to nearest stride"""
        return round(value / self.stride) * self.stride

    def value_to_position(self, value, width):
        """Internal method to convert value to screen position"""
        usable_width = width - 2 * self.handle_radius
        normalized_value = (value - self.min_value) / (self.max_value - self.min_value)
        return self.handle_radius + normalized_value * usable_width

    def position_to_value(self, position, width):
        """Internal method to convert screen position to value"""
        usable_width = width - 2 * self.handle_radius
        normalized_pos = max(0, min(1, (position - self.handle_radius) / usable_width))
        return self.min_value + normalized_pos * (self.max_value - self.min_value)

    def is_frame_removed(self, frame_index):
        """Internal method to check if a frame is in a removed range"""
        for start, end in self.removed_ranges:
            if start <= frame_index <= end:
                return True
        return False

    def show_playhead(self):
        """Show the playhead"""
        self.playhead_visible = True
        self.queue_draw()

    def hide_playhead(self):
        """Hide the playhead"""
        self.playhead_visible = False
        self.queue_draw()
        
    def set_playhead_pos(self, position):
        """Set playhead position"""
        self.playhead_pos = position
        # If position is -1, hide the playhead
        if position == -1:
            self.playhead_visible = False
        self.queue_draw()