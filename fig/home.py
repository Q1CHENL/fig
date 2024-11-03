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
        """Open custom file chooser window for GIF selection"""
        try:
            # Create a new window
            file_chooser_window = Gtk.Window(title="Select a GIF file")
            file_chooser_window.set_default_size(800, 600)
            file_chooser_window.set_resizable(False)
            file_chooser_window.set_transient_for(self.get_root())
            file_chooser_window.set_modal(True)

            # Create main vertical box
            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            main_box.set_vexpand(True)
            file_chooser_window.set_child(main_box)

            # Create a FileChooserWidget
            file_chooser = Gtk.FileChooserWidget(action=Gtk.FileChooserAction.OPEN)
            file_chooser.set_vexpand(True)
            file_chooser.set_hexpand(True)
            
            # Initialize with home directory
            home_dir = GLib.get_home_dir()
            if os.path.exists(home_dir):
                file_chooser.set_current_folder(Gio.File.new_for_path(home_dir))

            # Set up GIF file filter
            filter_gif = Gtk.FileFilter()
            filter_gif.set_name("GIF files")
            filter_gif.add_mime_type("image/gif")
            file_chooser.add_filter(filter_gif)

            # Show all files filter
            filter_all = Gtk.FileFilter()
            filter_all.set_name("All files")
            filter_all.add_pattern("*")
            file_chooser.add_filter(filter_all)

            # Add the FileChooserWidget to the main box
            main_box.append(file_chooser)

            # Create button box
            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            button_box.set_margin_start(10)
            button_box.set_margin_end(10)
            button_box.set_margin_bottom(10)
            button_box.set_halign(Gtk.Align.END)

            # Cancel button
            cancel_button = Gtk.Button(label="Cancel")
            cancel_button.connect("clicked", lambda btn: file_chooser_window.destroy())

            # Open button
            open_button = Gtk.Button(label="Open")
            open_button.get_style_context().add_class("suggested-action")
            open_button.connect("clicked", lambda btn: self._on_open_clicked(file_chooser, file_chooser_window))

            # Add buttons to button box
            button_box.append(cancel_button)
            button_box.append(open_button)

            # Add button box to main box
            main_box.append(button_box)

            file_chooser_window.show()
        except Exception as e:
            print(f"An error occurred while opening the file chooser: {e}")

    def _on_open_clicked(self, file_chooser, file_chooser_window):
        """Handle Open button click"""
        file = file_chooser.get_file()
        if file:
            file_path = file.get_path()
            window = self.get_root()
            window.load_editor_ui()
            window.editor_box.load_gif(file_path)
            file_chooser_window.destroy()

    def show_about(self, button):
        about = Gtk.AboutDialog()
        about.set_transient_for(self.get_root())
        about.set_modal(True)
        
        about.set_program_name("Fig")
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/io.github.Q1CHENL.fig.svg"))
        icon_file = Gio.File.new_for_path(icon_path)
        about.set_logo(Gdk.Texture.new_from_file(icon_file))
        about.set_version("1.0")
        about.set_comments("A simple and usable GIF editor")
        about.set_website("https://github.com/Q1CHENL/fig")
        about.set_authors(["Qichen Liu (刘启辰)"])
        about.set_license_type(Gtk.License.MIT_X11)
        
        about.present()
