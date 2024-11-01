import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, Gio, GLib
from PIL import Image
import fig.home, fig.editor
from fig.utils import load_css

class Fig(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        
        self.set_default_size(750, 650)
        self.set_resizable(False)
        
        # Load global CSS once
        load_css()
        window_handle = Gtk.WindowHandle()
        self.set_child(window_handle)
        
        
        # Setup header bar
        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Fig"))  # GTK4 way to set title
        self.set_titlebar(header)
        
        # Settings button
        settings_button = Gtk.Button()
        settings_icon = Gio.ThemedIcon(name="open-menu-symbolic")
        settings_image = Gtk.Image.new_from_gicon(settings_icon)
        settings_button.set_child(settings_image)
        load_css(settings_button, ["menu-button"])  # Add specific class
        settings_button.connect("clicked", self.show_menu)
        # header.pack_end(settings_button)
        
        # Main content
        self.home_box = fig.home.HomeBox()
        self.editor_box = fig.editor.EditorBox()
        window_handle.set_child(self.home_box)
        
        # Define and connect actions
        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self.show_preferences)
        self.add_action(preferences_action)
        
        import_frames_action = Gio.SimpleAction.new("import_frames", None)
        import_frames_action.connect("activate", self.import_frames)
        self.add_action(import_frames_action)
        
    def load_editor_ui(self):
        self.set_child(self.editor_box)
        
    def load_home_ui(self):
        self.set_child(self.home_box)

    def show_menu(self, button):
        popover = Gtk.PopoverMenu()
        popover.set_parent(button)
        
        menu = Gio.Menu()
        menu.append("Preferences", "win.preferences")
        menu.append("Import frames", "win.import_frames")
        
        popover.set_menu_model(menu)
        popover.popup()

    def show_preferences(self, action, param):
        # Create a preferences window with similar styling to main window
        preferences_window = Gtk.Window(transient_for=self, modal=True)
        preferences_window.set_default_size(400, 300)
        
        # Create and style headerbar
        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Preferences"))
        preferences_window.set_titlebar(header)
        
        # Apply the same CSS classes as main window
        load_css(preferences_window)
        load_css(header)
        
        # Add content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_box.set_margin_top(20)
        content_box.set_margin_bottom(20)
        content_box.set_margin_start(20)
        content_box.set_margin_end(20)
        
        label = Gtk.Label(label="")
        content_box.append(label)
        
        preferences_window.set_child(content_box)
        preferences_window.present()

    def import_frames(self, action, param):
        # Placeholder for import frames functionality
        print("Import frames clicked")

class FigApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.github.fig")
        
    def do_activate(self):
        win = Fig(self)
        win.present()

def main():
    app = FigApplication()
    return app.run(None)

if __name__ == "__main__":
    main()
