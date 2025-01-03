import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import cairo

class CropTextOverlay(Gtk.Overlay):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.text_mode = False
        self.text_entries = []  # Initialize empty list for text entries
        self.current_entry = None  # Track current entry
        
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_draw_func(self.draw_crop_overlay)
        self.drawing_area.set_can_target(True)
        self.drawing_area.set_focusable(True)

        click_controller = Gtk.GestureClick.new()
        click_controller.connect('pressed', self.on_press)
        click_controller.connect('released', self.on_release)
        self.drawing_area.add_controller(click_controller)
        
        drag_controller = Gtk.GestureDrag.new()
        drag_controller.connect('drag-begin', self.on_drag_begin)
        drag_controller.connect('drag-update', self.on_drag_update)
        drag_controller.connect('drag-end', self.on_drag_end)
        self.drawing_area.add_controller(drag_controller)
        
        self.add_overlay(self.drawing_area)
        
        self.crop_rect = [0, 0, 1, 1]  # normalized coordinates
        self.rect_handle_width = 5
        self.rect_handle_height = 20
        self.active_handle = None
        self.start_crop_rect = None
        self.dragging_region = False
        self.show_grid_lines = False
        self.handles_visible = False


    def get_handle_at_position(self, x, y, display_width, display_height, x_offset, y_offset):
        # Convert crop rect to pixel coordinates
        px = x_offset + self.crop_rect[0] * display_width
        py = y_offset + self.crop_rect[1] * display_height
        pw = self.crop_rect[2] * display_width
        ph = self.crop_rect[3] * display_height
        
        corners = [
            ('top_left', px, py, 1, 1),          
            ('top_right', px + pw, py, -1, 1),    
            ('bottom_left', px, py + ph, 1, -1),  
            ('bottom_right', px + pw, py + ph, -1, -1)
        ]
        
        for handle, corner_x, corner_y, dx, dy in corners:
            # Check horizontal line of L handle
            h_x1 = corner_x
            h_x2 = corner_x + self.rect_handle_height * dx
            h_y = corner_y + self.rect_handle_width/2 * dy
            
            # Check vertical line of L handle
            v_x = corner_x + self.rect_handle_width/2 * dx
            v_y1 = corner_y
            v_y2 = corner_y + self.rect_handle_height * dy
            
            # Check if click is near either line of the L
            near_horizontal = (abs(y - h_y) <= self.rect_handle_width and 
                             min(h_x1, h_x2) <= x <= max(h_x1, h_x2))
            near_vertical = (abs(x - v_x) <= self.rect_handle_width and 
                           min(v_y1, v_y2) <= y <= max(v_y1, v_y2))
            
            if near_horizontal or near_vertical:
                return handle
                
        # Middle points of each side
        middle_handles = [
            ('top', px + pw/2 - self.rect_handle_height/2, py),
            ('right', px + pw - self.rect_handle_width, py + ph/2 - self.rect_handle_height/2),
            ('bottom', px + pw/2 - self.rect_handle_height/2, py + ph - self.rect_handle_width),
            ('left', px, py + ph/2 - self.rect_handle_height/2)
        ]

        for pos, mx, my in middle_handles:
            w_rect = self.rect_handle_height if pos == 'top' or pos == 'bottom' else self.rect_handle_width
            h_rect = self.rect_handle_width if pos == 'top' or pos == 'bottom' else self.rect_handle_height
            if (mx <= x <= mx + w_rect and my <= y <= my + h_rect):
                return pos
                
        # If no handle is found but point is in crop region, return 'region'
        if (px <= x <= px + pw and py <= y <= py + ph):
            return 'region'
            
        return None

    def on_press(self, gesture, n_press, x, y):
        if self.text_mode:
            self._show_text_entry(x, y)
            return
            
        # Get image dimensions and scaling
        child = self.get_child()
        if not child or not isinstance(child, Gtk.Picture):
            self.handles_visible = False
            self.drawing_area.queue_draw()
            return
            
        paintable = child.get_paintable()
        if not paintable:
            self.handles_visible = False
            self.drawing_area.queue_draw()
            return
            
        width = self.drawing_area.get_width()
        height = self.drawing_area.get_height()
        img_width = paintable.get_intrinsic_width()
        img_height = paintable.get_intrinsic_height()
        
        scale_width = width / img_width
        scale_height = height / img_height
        scale = min(scale_width, scale_height)
        
        display_width = int(img_width * scale)
        display_height = int(img_height * scale)
        x_offset = (width - display_width) // 2
        y_offset = (height - display_height) // 2
        
        if self.editor.crop_mode:
            self.handles_visible = True
            # Check if we clicked on a handle or within the region
            self.active_handle = self.get_handle_at_position(x, y, display_width, display_height, x_offset, y_offset)
            if self.active_handle:
                self.start_crop_rect = self.crop_rect.copy()
                self.dragging_region = (self.active_handle == 'region')
                self.show_grid_lines = True
        else:
            # Hide handles when clicking outside the image
            self.handles_visible = False
            self.active_handle = None
            self.start_crop_rect = None
            self.dragging_region = False
            self.show_grid_lines = False
        
        self.drawing_area.queue_draw()

    def on_release(self, gesture, n_press, x, y):
        self.active_handle = None
        self.start_crop_rect = None
        self.dragging_region = False
        self.show_grid_lines = False
        self.drawing_area.queue_draw()

    def on_drag_begin(self, gesture, start_x, start_y):
        # Already handled in on_press
        pass
    
    def on_drag_update(self, gesture, offset_x, offset_y):
        if not self.active_handle or not self.start_crop_rect:
            return
            
        # Get image dimensions and scaling
        child = self.get_child()
        if not child or not isinstance(child, Gtk.Picture):
            return
            
        paintable = child.get_paintable()
        if not paintable:
            return
            
        width = self.drawing_area.get_width()
        height = self.drawing_area.get_height()
        img_width = paintable.get_intrinsic_width()
        img_height = paintable.get_intrinsic_height()
        
        scale_width = width / img_width
        scale_height = height / img_height
        scale = min(scale_width, scale_height)
        
        display_width = int(img_width * scale)
        display_height = int(img_height * scale)
        
        # Convert offset to normalized coordinates
        dx = offset_x / display_width
        dy = offset_y / display_height
        
        # Update crop rectangle based on which handle is being dragged
        new_rect = self.start_crop_rect.copy()
        
        if self.dragging_region:
            # Move the entire region while keeping size constant
            new_x = max(0, min(new_rect[0] + dx, 1 - new_rect[2]))
            new_y = max(0, min(new_rect[1] + dy, 1 - new_rect[3]))
            new_rect[0] = new_x
            new_rect[1] = new_y
        elif self.active_handle == 'top_left':
            new_rect[0] = max(0, min(new_rect[0] + dx, new_rect[0] + new_rect[2] - 0.1))
            new_rect[1] = max(0, min(new_rect[1] + dy, new_rect[1] + new_rect[3] - 0.1))
            new_rect[2] -= (new_rect[0] - self.start_crop_rect[0])
            new_rect[3] -= (new_rect[1] - self.start_crop_rect[1])
        elif self.active_handle == 'top_right':
            new_rect[1] = max(0, min(new_rect[1] + dy, new_rect[1] + new_rect[3] - 0.1))
            new_rect[2] = max(0.1, min(new_rect[2] + dx, 1 - new_rect[0]))
            new_rect[3] -= (new_rect[1] - self.start_crop_rect[1])
        elif self.active_handle == 'bottom_left':
            new_rect[0] = max(0, min(new_rect[0] + dx, new_rect[0] + new_rect[2] - 0.1))
            new_rect[2] -= (new_rect[0] - self.start_crop_rect[0])
            new_rect[3] = max(0.1, min(new_rect[3] + dy, 1 - new_rect[1]))
        elif self.active_handle == 'bottom_right':
            new_rect[2] = max(0.1, min(new_rect[2] + dx, 1 - new_rect[0]))
            new_rect[3] = max(0.1, min(new_rect[3] + dy, 1 - new_rect[1]))
        elif self.active_handle == 'top':
            new_rect[1] = max(0, min(new_rect[1] + dy, new_rect[1] + new_rect[3] - 0.1))
            new_rect[3] -= (new_rect[1] - self.start_crop_rect[1])
        elif self.active_handle == 'right':
            new_rect[2] = max(0.1, min(new_rect[2] + dx, 1 - new_rect[0]))
        elif self.active_handle == 'bottom':
            new_rect[3] = max(0.1, min(new_rect[3] + dy, 1 - new_rect[1]))
        elif self.active_handle == 'left':
            new_rect[0] = max(0, min(new_rect[0] + dx, new_rect[0] + new_rect[2] - 0.1))
            new_rect[2] -= (new_rect[0] - self.start_crop_rect[0])

        self.crop_rect = new_rect
        self.drawing_area.queue_draw()
    
    def on_drag_end(self, gesture, offset_x, offset_y):
        self.active_handle = None
        self.start_crop_rect = None
        self.dragging_region = False

    def draw_crop_overlay(self, area, cr, da_width, da_height, *args):
        """
        Draw the crop overlay with proper scaling for both normal and rotated images
        da_width: width of the drawing area
        da_height: height of the drawing area
        """
        # Get the actual image dimensions from the Picture widget
        child = self.get_child()
        if not child or not isinstance(child, Gtk.Picture):
            return
            
        paintable = child.get_paintable()
        if not paintable:
            return

        img_width = paintable.get_intrinsic_width()
        img_height = paintable.get_intrinsic_height()
        
        # Calculate the scaling to fit in the display area
        scale_width = da_width / img_width
        scale_height = da_height / img_height
        scale = min(scale_width, scale_height)
        
        # Calculate the actual displayed image size
        display_width = int(img_width * scale)
        display_height = int(img_height * scale)
        
        # Calculate the position to center the image
        x_offset = (da_width - display_width) // 2
        y_offset = (da_height - display_height) // 2
        
        # Set up semi-transparent overlay for the whole area
        cr.set_source_rgba(self.overlay_bkg[0], self.overlay_bkg[1], self.overlay_bkg[2], self.overlay_bkg[3])
        cr.rectangle(0, 0, da_width, da_height)
        cr.fill()
        
        # Calculate crop rectangle in pixels, relative to the actual image display area
        x = x_offset + self.crop_rect[0] * display_width
        y = y_offset + self.crop_rect[1] * display_height
        w = self.crop_rect[2] * display_width
        h = self.crop_rect[3] * display_height
        
        # Clear the crop region
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.rectangle(x, y, w, h)
        cr.fill()
        
        if self.handles_visible:
            cr.set_operator(cairo.OPERATOR_OVER)
            # Draw crop rectangle border
            cr.set_source_rgb(1, 1, 1)
            cr.set_line_width(1)
            cr.rectangle(x, y, w, h)
            cr.stroke()
            
            if self.show_grid_lines:
                cr.set_line_width(1)
                cr.set_source_rgba(1, 1, 1, 0.8)
                
                for i in range(1, 3):
                    line_x = x + (w * i / 3)
                    cr.move_to(line_x, y)
                    cr.line_to(line_x, y + h)
                    cr.stroke()
                
                for i in range(1, 3):
                    line_y = y + (h * i / 3)
                    cr.move_to(x, line_y)
                    cr.line_to(x + w, line_y)
                    cr.stroke()
            
            # Draw dragging handles
            cr.set_line_width(self.rect_handle_width)
            corners = [
                ('top_left', x, y, 1, 1),          
                ('top_right', x + w, y, -1, 1),    
                ('bottom_left', x, y + h, 1, -1),  
                ('bottom_right', x + w, y + h, -1, -1)
            ]

            for pos, corner_x, corner_y, dx, dy in corners:
                # Draw horizontal handles
                cr.move_to(corner_x, corner_y + self.rect_handle_width/2 * dy)
                cr.line_to(corner_x + self.rect_handle_height * dx, corner_y + self.rect_handle_width/2 * dy)

                # Draw vertical handles
                cr.move_to(corner_x + self.rect_handle_width/2 * dx, corner_y)
                cr.line_to(corner_x + self.rect_handle_width/2 * dx, corner_y + self.rect_handle_height * dy)

                cr.stroke()
            
            middle_handles = [
                ('top', x + w/2 - self.rect_handle_height/2, y),
                ('right', x + w - self.rect_handle_width, y + h/2 - self.rect_handle_height/2),
                ('bottom', x + w/2 - self.rect_handle_height/2, y + h - self.rect_handle_width),
                ('left', x, y + h/2 - self.rect_handle_height/2)
            ]

            cr.set_line_width(1)
            for pos, mx, my in middle_handles:
                w_rect = self.rect_handle_height if pos == 'top' or pos == 'bottom' else self.rect_handle_width
                h_rect = self.rect_handle_width if pos == 'top' or pos == 'bottom' else self.rect_handle_height
                cr.rectangle(mx, my, w_rect, h_rect)
                cr.fill()

    def update_theme(self, is_dark):
        if is_dark:
            self.overlay_bkg = (36/255, 36/255, 36/255, 0.85)
        else:
            self.overlay_bkg = (250/255, 250/255, 250/255, 0.85)

    def reset_crop_rect(self):
        self.crop_rect = [0, 0, 1, 1]
        self.active_handle = None
        self.start_crop_rect = None
        self.dragging_region = False
        self.show_grid_lines = False
        self.handles_visible = False
        self.remove_all_text_entries()
        self.drawing_area.queue_draw()

    def _show_text_entry(self, x, y):
        """Show text entry at mouse click position"""
        if self.current_entry:
            # If there's an existing entry, save it first
            text = self.current_entry.get_text()
            if text:
                self.text_entries.append({
                    'text': text,
                    'x': self.current_entry.get_margin_start(),
                    'y': self.current_entry.get_margin_top()
                })
            self.remove_overlay(self.current_entry)

        entry = Gtk.Entry()
        entry.set_has_frame(False)
        
        # Prevent expansion
        entry.set_hexpand(False)
        entry.set_vexpand(False)
        entry.set_halign(Gtk.Align.START)
        entry.set_valign(Gtk.Align.START)
        
        entry.add_css_class('text-entry')
        
        # Position the entry at click coordinates
        entry.set_margin_start(int(x))
        entry.set_margin_top(int(y))

        # Connect to the "activate" signal (triggered by Enter key)
        entry.connect('activate', self._on_entry_activated)
        
        # Handle key events (for Escape)
        key_controller = Gtk.EventControllerKey()
        key_controller.connect('key-pressed', self._on_text_key_pressed, entry)
        entry.add_controller(key_controller)
        
        self.add_overlay(entry)
        entry.grab_focus()
        self.current_entry = entry

    def _on_entry_activated(self, entry: Gtk.Entry):
        """Handle Enter key press"""
        text = entry.get_text()
        if text:
            # Remove focus
            entry.remove_css_class('focused') 
            entry.grab_focus_without_selecting()
            self.get_root().set_focus(None)
            
            text_entry = {
                'entry': entry,
                'x': entry.get_margin_start(),
                'y': entry.get_margin_top()
            }
            self.text_entries.append(text_entry)
        self.current_entry = None


    def _on_text_key_pressed(self, controller, keyval, keycode, state, entry):
        """Handle only Escape key now"""
        if keyval == Gdk.KEY_Escape:
            self.remove_overlay(entry)
            self.current_entry = None
            return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE
    
    def remove_all_text_entries(self):
        for entry in self.text_entries:
            self.remove_overlay(entry['entry'])
        self.text_entries = []
        self.current_entry = None

