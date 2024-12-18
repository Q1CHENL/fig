import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
import cairo

class CropOverlay(Gtk.Overlay):
    def __init__(self):
        super().__init__()
        
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

        self.connect('realize', self.on_realize)

    def on_realize(self, widget):
        # Add the click controller to the root window after widget is realized
        root = self.get_root()
        if root:
            # Create a controller for both left and right clicks on root
            root_click_controller = Gtk.GestureClick.new()
            root_click_controller.set_button(0)  # 0 means listen to any mouse button
            root_click_controller.connect('pressed', self.on_click_outside)
            root.add_controller(root_click_controller)
            
            # Add another controller to the drawing area itself
            drawing_click_controller = Gtk.GestureClick.new()
            drawing_click_controller.set_button(0)
            drawing_click_controller.connect('pressed', self.on_click_outside)
            self.drawing_area.add_controller(drawing_click_controller)

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
        
        # Check if click is within image bounds
        if (x_offset <= x <= x_offset + display_width and 
            y_offset <= y <= y_offset + display_height):
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

    def draw_crop_overlay(self, area, cr, width, height, *args):
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
        cr.set_source_rgba(self.overlay_bkg[0], self.overlay_bkg[1], self.overlay_bkg[2], self.overlay_bkg[3])
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
        self.drawing_area.queue_draw()

    def on_click_outside(self, gesture, n_press, x, y):
        # Check if click is within our widget bounds
        native = gesture.get_widget().get_native()
        if native:
            # Get the bounds of our widget relative to the native window
            bounds = self.compute_bounds(native)[1]
            if not (bounds.get_x() <= x <= bounds.get_x() + bounds.get_width() and
                    bounds.get_y() <= y <= bounds.get_y() + bounds.get_height()):
                self.handles_visible = False
                self.active_handle = None
                self.start_crop_rect = None
                self.dragging_region = False
                self.show_grid_lines = False
                self.drawing_area.queue_draw()
