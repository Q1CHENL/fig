import os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib, Gdk, Adw
from fig.utils import load_css, clear_css


class HomeBox(Gtk.Box):
    def __init__(self):
        super().__init__()
        
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(10)
        
        self.set_margin_top(220)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        
        # Create buttons
        self.select_btn = self.select_button()
        self.about_btn = self.about_button()
        
        self.append(self.select_btn)
        self.append(self.about_btn)

    def select_button(self):
        select_button = Gtk.Button(label="Select GIF")
        select_button.set_size_request(150, 50)
        select_button.set_halign(Gtk.Align.CENTER)
        select_button.connect('clicked', self.select_gif)
        return select_button

    def about_button(self):
        about_button = Gtk.Button(label="About Fig")
        about_button.set_size_request(150, 50)
        about_button.set_halign(Gtk.Align.CENTER)
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
        show_about_dialog(self.get_root())

    def update_theme(self, is_dark):
        """Update theme for all buttons"""
        from fig.utils import clear_css
        
        # Update Select GIF button
        clear_css(self.select_btn)
        self.select_btn.add_css_class("select-gif-button-dark" if is_dark else "select-gif-button-light")
        
        # Update About Fig button
        clear_css(self.about_btn)
        self.about_btn.add_css_class("about-fig-button-dark" if is_dark else "about-fig-button-light")


def show_about_dialog(window):
    about = Adw.AboutDialog.new()
    
    about.set_application_name("Fig")
    about.set_application_icon("io.github.Q1CHENL.fig")
    about.set_version("1.0.1")
    about.set_developer_name("Qichen Liu")
    about.set_website("https://github.com/fig")
    about.set_issue_url("https://github.com/fig/issues")

    about.set_comments("Sleek GIF editor.")
    about.set_release_notes("""
    <ul>
        <li>Remove certain frames</li>
        <li>Insert frame(s) at any position</li>
        <li>Speed up/slow down certain frames</li>
        <li>Light/Dark mode switch</li>
        <li>New About page</li>
        <li>New window option</li>
        <li>Help page</li>
        <li>Return to home from editor</li>
        <li>Bug fixes and improvements</li>
    </ul>
    """)
    
    developers = [
        "Qichen Liu https://github.com/Q1CHENL",
    ]
    designers = ["Qichen Liu"]
    artists = ["Qichen Liu"]
    
    about.set_developers(developers)
    about.set_designers(designers)
    about.set_artists(artists)

    about.set_copyright("© 2024 Qichen Liu")
    about.set_license_type(Gtk.License.MIT_X11)
    
    about.set_debug_info("Version: 1.0.1\nPlatform: Linux\nGTK: 4.0")
    about.set_debug_info_filename("debug-info.txt")

    about.present(window)
