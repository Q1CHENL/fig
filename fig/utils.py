import os
from gi.repository import Gtk, Gdk, GLib
import gi
gi.require_version('Gtk', '4.0')

def load_css(target, css_classes=None):
    """
    Load CSS styles from individual CSS files
    
    Args:
        target: Widget to add CSS classes to, or Display to load CSS provider for
        css_classes: List of CSS classes to add to the widget
    """
    def try_load_css_files(style_dir):
        """Try to load all CSS files from style directory"""
        if not os.path.exists(style_dir):
            return None
            
        css_data = []
        css_files = [
            'headerbar.css',
            'select-gif-button.css',
            'about-fig-button.css',
            'save-button.css',
            'play-button.css',
            'menu-item.css',
            'info-label.css',
            'controls-box.css',
            'drag-and-drop.css'
        ]
        
        for css_file in css_files:
            file_path = os.path.join(style_dir, css_file)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    css_data.append(f.read())
                    
        return '\n'.join(css_data) if css_data else None

    css_provider = Gtk.CssProvider()
    
    try:
        # Try possible style directory locations
        current_dir = os.path.dirname(os.path.abspath(__file__))
        style_paths = [
            os.path.join(current_dir, 'style'),
            os.path.join(os.path.dirname(current_dir), 'style')
        ]
        
        css_data = None
        for style_dir in style_paths:
            css_data = try_load_css_files(style_dir)
            if css_data:
                break
                
        if not css_data:
            raise FileNotFoundError(f"CSS files not found in: {style_paths}")
            
        css_provider.load_from_bytes(GLib.Bytes.new(css_data.encode('utf-8')))

        # If target is a Display, add provider to display
        if isinstance(target, Gdk.Display):
            Gtk.StyleContext.add_provider_for_display(
                target,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        # If target is a widget, add provider to default display and add CSS classes
        elif isinstance(target, Gtk.Widget):
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            if css_classes:
                for css_class in css_classes:
                    target.add_css_class(css_class)

    except Exception as e:
        print(f"Error loading CSS: {e}")

def clear_css(widget):
    """
    Remove all CSS classes from a widget
    """
    if widget:
        css_classes = widget.get_css_classes()
        for css_class in css_classes:
            widget.remove_css_class(css_class)
