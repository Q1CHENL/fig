import os
from gi.repository import Gtk, Gdk
import gi
gi.require_version('Gtk', '4.0')


def load_css(widget=None, css_classes=None):
    """
    Load CSS styles from style.css file

    Args:
        widget: Optional widget to add CSS classes to
        css_classes: List of CSS classes to add to the widget
    """
    css_provider = Gtk.CssProvider()

    # Get the directory containing the script
    try:
        # css_file = pkg_resources.resource_filename('fig', 'style/style.css')

        current_dir = os.path.dirname(os.path.abspath(__file__))
        css_file = os.path.join(current_dir, 'style/style.css')

        with open(css_file, 'r', encoding='utf-8') as f:
            css_data = f.read()
            css_provider.load_from_data(css_data.encode('utf-8'))

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Add CSS classes to widget if provided
        if widget and css_classes:
            for css_class in css_classes:
                widget.get_style_context().add_class(css_class)

    except Exception as e:
        try:
            # Fallback for development environment
            current_dir = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))
            css_file = os.path.join(current_dir, 'style/style.css')
            with open(css_file, 'r', encoding='utf-8') as f:
                css_data = f.read()
                css_provider.load_from_data(css_data.encode('utf-8'))

            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

            # Add CSS classes to widget if provided
            if widget and css_classes:
                for css_class in css_classes:
                    widget.get_style_context().add_class(css_class)
        except Exception as e:
            print(f"Error loading CSS: {e}")
