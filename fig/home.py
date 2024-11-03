import os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib, Gdk
from fig.utils import load_css


class HomeBox(Gtk.Box):
    def __init__(self):
        super().__init__()
        
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(10)
        
        self.set_margin_top(220)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        
        self.append(self.select_button())
        self.append(self.about_button())

    def select_button(self):
        select_button = Gtk.Button(label="Select GIF")
        select_button.set_size_request(150, 50)
        select_button.set_halign(Gtk.Align.CENTER)
        load_css(select_button, ["select-gif-button"])
        select_button.connect('clicked', self.select_gif)
        return select_button

    def about_button(self):
        about_button = Gtk.Button(label="About Fig")
        about_button.set_size_request(150, 50)
        about_button.set_halign(Gtk.Align.CENTER)
        load_css(about_button, ["about-fig-button"])
        about_button.connect('clicked', self.show_about)
        return about_button
    
    def select_gif(self, button):
        """Open native file chooser dialog for GIF selection"""
        try:
            dialog = Gtk.FileDialog.new()
            dialog.set_title("Select a GIF")
            dialog.set_modal(True)

            # Set up GIF file filter
            filter_gif = Gtk.FileFilter()
            filter_gif.set_name("GIF files")
            filter_gif.add_mime_type("image/gif")
            
            filter_all = Gtk.FileFilter()
            filter_all.set_name("All files")
            filter_all.add_pattern("*")
            
            filters = Gio.ListStore.new(Gtk.FileFilter)
            filters.append(filter_gif)
            filters.append(filter_all)
            dialog.set_filters(filters)
            dialog.set_default_filter(filter_gif)

            # Initialize with home directory
            home_dir = GLib.get_home_dir()
            if os.path.exists(home_dir):
                dialog.set_initial_folder(Gio.File.new_for_path(home_dir))

            dialog.open(
                parent=self.get_root(),
                callback=self._on_file_dialog_response
            )

        except Exception as e:
            print(f"An error occurred while opening the file chooser: {e}")

    def _on_file_dialog_response(self, dialog, result):
        """Handle file chooser dialog response"""
        try:
            file = dialog.open_finish(result)
            if file:
                file_path = file.get_path()
                window = self.get_root()
                window.load_editor_ui()
                window.editor_box.load_gif(file_path)
        except GLib.Error as e:
            print(f"Error selecting file: {e.message}")

    def show_about(self, button):
        about = Gtk.AboutDialog()
        about.set_transient_for(self.get_root())
        about.set_modal(True)
        
        about.set_program_name("Fig")
        # Try multiple possible locations for the icon
        icon_paths = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/io.github.Q1CHENL.fig.svg")),
            os.path.join(os.path.dirname(__file__), "assets/io.github.Q1CHENL.fig.svg"),
            "/app/share/icons/hicolor/scalable/apps/io.github.Q1CHENL.fig.svg"  # Flatpak location
        ]

        icon_file = None
        for path in icon_paths:
            if os.path.exists(path):
                icon_file = Gio.File.new_for_path(path)
                break

        if icon_file:
            about.set_logo(Gdk.Texture.new_from_file(icon_file))
        about.set_version("1.0")
        about.set_comments("A simple and usable GIF editor")
        about.set_website("https://github.com/Q1CHENL/fig")
        about.set_authors(["Qichen Liu (刘启辰)"])
        about.set_license_type(Gtk.License.MIT_X11)
        
        about.present()
