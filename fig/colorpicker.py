import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from fig.constants import EditorConstants


class ColorPicker:
    """A color picker widget with predefined color options"""

    def __init__(self, parent_widget, on_color_selected_callback):
        """
        Initialize the color picker
        
        Args:
            parent_widget: The widget to attach the popover to
            on_color_selected_callback: Callback function when a color is selected
        """
        self.parent_widget = parent_widget
        self.on_color_selected_callback = on_color_selected_callback
        
        # Default colors available in the picker
        self.colors = [
            (EditorConstants.COLOR_WHITE, 'White'),
            (EditorConstants.COLOR_BLACK, 'Black'),
            (EditorConstants.COLOR_RED, 'Red'),
            (EditorConstants.COLOR_GREEN, 'Green'),
            (EditorConstants.COLOR_BLUE, 'Blue'),
            (EditorConstants.COLOR_YELLOW, 'Yellow'),
            # ('#FF00FF', 'Magenta'),
            # ('#00FFFF', 'Cyan'),
        ]
        
        self.current_color = self.colors[0][0]  # Default to first color (white)
        
        # Create the popover widget
        self._create_popover()

    def _create_popover(self):
        """Create the color picker popover"""
        self.popover = Gtk.Popover()
        self.popover.set_parent(self.parent_widget)

        # Create container box for color buttons
        color_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=EditorConstants.COLOR_POPOVER_MARGIN
        )
        color_box.set_margin_top(EditorConstants.COLOR_POPOVER_MARGIN)
        color_box.set_margin_bottom(EditorConstants.COLOR_POPOVER_MARGIN)
        color_box.set_margin_start(EditorConstants.COLOR_POPOVER_MARGIN)
        color_box.set_margin_end(EditorConstants.COLOR_POPOVER_MARGIN)

        # Create color buttons
        for color_info in self.colors:
            color_button = self._create_color_button(color_info)
            color_box.append(color_button)

        self.popover.set_child(color_box)

    def _create_color_button(self, color_info):
        """
        Create a color button for the picker
        
        Args:
            color_info: Tuple of (color_hex, color_name)
            
        Returns:
            Gtk.Button: The created color button
        """
        color_hex, color_name = color_info
        
        color_button = Gtk.Button()
        color_button.set_size_request(
            EditorConstants.COLOR_BUTTON_SIZE, 
            EditorConstants.COLOR_BUTTON_SIZE
        )
        color_button.add_css_class(EditorConstants.CSS_COLOR_BUTTON)
        color_button.set_tooltip_text(color_name)

        # Apply color styling
        css_provider = Gtk.CssProvider()
        css_data = f"""
            .{EditorConstants.CSS_COLOR_BUTTON} {{
                background: {color_hex};
            }}
        """
        css_provider.load_from_data(css_data.encode('utf-8'))
        color_button.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Connect button click event
        color_button.connect('clicked', self._on_color_button_clicked, color_info)
        
        return color_button

    def _on_color_button_clicked(self, button, color_info):
        """Handle color button click"""
        color_hex, color_name = color_info
        self.current_color = color_hex
        
        # Call the provided callback
        if self.on_color_selected_callback:
            self.on_color_selected_callback(color_hex, color_name)
        
        # Close the popover
        self.popover.popdown()

    def show(self):
        """Show the color picker popover"""
        self.popover.popup()

    def hide(self):
        """Hide the color picker popover"""
        self.popover.popdown()

    def get_current_color(self):
        """Get the currently selected color"""
        return self.current_color

    def set_current_color(self, color_hex):
        """Set the current color"""
        self.current_color = color_hex

    def add_color(self, color_hex, color_name):
        """
        Add a new color to the picker
        
        Args:
            color_hex: The color in hex format (e.g., '#FF0000')
            color_name: Human-readable name for the color
        """
        self.colors.append((color_hex, color_name))
        # Recreate the popover to include the new color
        self._create_popover()

    def remove_color(self, color_hex):
        """
        Remove a color from the picker
        
        Args:
            color_hex: The color to remove
        """
        self.colors = [color for color in self.colors if color[0] != color_hex]
        # Recreate the popover without the removed color
        self._create_popover()

    def set_parent(self, parent_widget):
        """
        Change the parent widget for the popover
        
        Args:
            parent_widget: The new parent widget
        """
        self.parent_widget = parent_widget
        self.popover.set_parent(parent_widget)
