import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
import cairo

class CropOverlay(Gtk.Overlay):
    def __init__(self):
        super().__init__()
        
        # Create a drawing area for the crop overlay
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_draw_func(self.draw_crop_overlay)
        
        # Make the drawing area receive events
        self.drawing_area.set_can_target(True)
        self.drawing_area.set_focusable(True)
        
        # Add event controllers
        click_controller = Gtk.GestureClick.new()
        click_controller.connect('pressed', self.on_press)
        click_controller.connect('released', self.on_release)
        self.drawing_area.add_controller(click_controller)
        
        drag_controller = Gtk.GestureDrag.new()
        drag_controller.connect('drag-begin', self.on_drag_begin)
        drag_controller.connect('drag-update', self.on_drag_update)
        drag_controller.connect('drag-end', self.on_drag_end)
        self.drawing_area.add_controller(drag_controller)
        
        # Add the drawing area as an overlay
        self.add_overlay(self.drawing_area)
        
        # Initial crop region is full size
        self.crop_rect = [0, 0, 1, 1]  # normalized coordinates
        self.handle_size = 10
        self.active_handle = None
        self.start_crop_rect = None
        self.dragging_region = False  # New flag for dragging entire region
        
    def get_handle_at_position(self, x, y, display_width, display_height, x_offset, y_offset):
        # Convert crop rect to pixel coordinates
        px = x_offset + self.crop_rect[0] * display_width
        py = y_offset + self.crop_rect[1] * display_height
        pw = self.crop_rect[2] * display_width
        ph = self.crop_rect[3] * display_height
        
        # Check each corner
        corners = [
            ('top_left', px, py),
            ('top_right', px + pw, py),
            ('bottom_left', px, py + ph),
            ('bottom_right', px + pw, py + ph)
        ]
        
        for handle, hx, hy in corners:
            if abs(x - hx) <= self.handle_size and abs(y - hy) <= self.handle_size:
                return handle
                
        # If no handle is found but point is in crop region, return 'region'
        if self.is_point_in_crop_region(x, y, display_width, display_height, x_offset, y_offset):
            return 'region'
            
        return None
        
    def is_point_in_crop_region(self, x, y, display_width, display_height, x_offset, y_offset):
        """Check if a point is within the crop region"""
        # Convert crop rect to pixel coordinates
        px = x_offset + self.crop_rect[0] * display_width
        py = y_offset + self.crop_rect[1] * display_height
        pw = self.crop_rect[2] * display_width
        ph = self.crop_rect[3] * display_height
        
        return (px <= x <= px + pw and 
                py <= y <= py + ph)

    def on_press(self, gesture, n_press, x, y):
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
        x_offset = (width - display_width) // 2
        y_offset = (height - display_height) // 2
        
        # Check if we clicked on a handle or within the region
        self.active_handle = self.get_handle_at_position(x, y, display_width, display_height, x_offset, y_offset)
        if self.active_handle:
            self.start_crop_rect = self.crop_rect.copy()
            self.dragging_region = (self.active_handle == 'region')

    def on_release(self, gesture, n_press, x, y):
        self.active_handle = None
        self.start_crop_rect = None
        self.dragging_region = False

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
        
        self.crop_rect = new_rect
        self.drawing_area.queue_draw()
    
    def on_drag_end(self, gesture, offset_x, offset_y):
        self.active_handle = None
        self.start_crop_rect = None
        self.dragging_region = False

    def draw_crop_overlay(self, area, cr, width, height, *args):
        # Get the actual image dimensions from the Picture widget
        child = self.get_child()
        if not child or not isinstance(child, Gtk.Picture):
            return
            
        paintable = child.get_paintable()
        if not paintable:
            return
            
        # Get the actual displayed image size
        img_width = paintable.get_intrinsic_width()
        img_height = paintable.get_intrinsic_height()
        
        # Calculate the scaling to fit in the display area
        scale_width = width / img_width
        scale_height = height / img_height
        scale = min(scale_width, scale_height)
        
        # Calculate the actual displayed image size
        display_width = int(img_width * scale)
        display_height = int(img_height * scale)
        
        # Calculate the position to center the image
        x_offset = (width - display_width) // 2
        y_offset = (height - display_height) // 2
        
        # Set up semi-transparent overlay for the whole area
        cr.set_source_rgba(0, 0, 0, 0.7)
        cr.rectangle(0, 0, width, height)
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
        
        # Draw crop rectangle border
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_source_rgb(1, 1, 1)
        cr.set_line_width(4)
        cr.rectangle(x, y, w, h)
        cr.stroke()
        
        # Draw corner handles
        corners = [
            (x, y), (x + w, y),
            (x, y + h), (x + w, y + h)
        ]
        
        for corner_x, corner_y in corners:
            cr.rectangle(
                corner_x - self.handle_size/2,
                corner_y - self.handle_size/2,
                self.handle_size,
                self.handle_size
            )
            cr.fill()