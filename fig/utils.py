import os
from gi.repository import Gtk, Gdk, GLib
import gi
gi.require_version('Gtk', '4.0')

def load_css(widget=None, css_classes=None):
    """
    Load CSS styles from style.css file

    Args:
        widget: Optional widget to add CSS classes to
        css_classes: List of CSS classes to add to the widget
    """
    def try_load_css_file(path):
        """Try to load CSS from given path"""
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    css_provider = Gtk.CssProvider()
    
    try:
        # Try possible CSS file locations
        current_dir = os.path.dirname(os.path.abspath(__file__))
        css_paths = [
            os.path.join(current_dir, 'style/style.css'),
            os.path.join(os.path.dirname(current_dir), 'style/style.css')
        ]
        
        css_data = None
        for path in css_paths:
            css_data = try_load_css_file(path)
            if css_data:
                break
                
        if not css_data:
            raise FileNotFoundError(f"CSS file not found in: {css_paths}")
            
        css_provider.load_from_bytes(GLib.Bytes.new(css_data.encode('utf-8')))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        if widget and css_classes:
            for css_class in css_classes:
                widget.add_css_class(css_class)

    except Exception as e:
        print(f"Error loading CSS: {e}")
