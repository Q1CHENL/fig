import os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib, Adw, Gdk


class HomeBox(Gtk.Box):
    def __init__(self):
        super().__init__()
        
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.button_box.set_spacing(10)
        self.button_box.set_margin_top(220)
        self.button_box.set_margin_bottom(220)
        self.button_box.set_margin_start(20)
        self.button_box.set_margin_end(20)
        
        self.set_orientation(Gtk.Orientation.VERTICAL)
        
        self.select_btn = self.select_button()
        self.about_btn = self.about_button()
        
        self.button_box.append(self.select_btn)
        self.button_box.append(self.about_btn)
        
        self.append(self.button_box)

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
                window.editor_box.crop_overlay.reset_crop_rect()
                window.editor_box.load_gif(file_path)
                original_file_name = os.path.basename(file_path)
                if original_file_name.endswith('.gif'):
                    window.editor_box.original_file_name = original_file_name[:-4]
                else:
                    window.editor_box.original_file_name = original_file_name
                
        except GLib.Error as e:
            print(f"Error selecting file: {e.message}")

    def show_about(self, button):
        show_about_dialog(self.get_root())

    def update_theme(self, is_dark):
        """Update theme for all buttons"""
        from fig.utils import clear_css
        
        clear_css(self.select_btn)
        self.select_btn.add_css_class("select-gif-button-dark" if is_dark else "select-gif-button-light")
        
        clear_css(self.about_btn)
        self.about_btn.add_css_class("about-fig-button-dark" if is_dark else "about-fig-button-light")


def show_about_dialog(window):
    about = Adw.AboutDialog.new()
    
    about.set_application_name("Fig")
    about.set_application_icon("io.github.Q1CHENL.fig")
    about.set_version("1.0.3")
    about.set_developer_name("Qichen Liu")
    about.set_website("https://github.com/fig")
    about.set_issue_url("https://github.com/fig/issues")

    about.set_release_notes("""
    <ul>
        <li>Extract frames</li>
        <li>Faster image loading</li>
    </ul>
    """)
    
    developers = [
        "Qichen Liu https://github.com/Q1CHENL",
    ]
    designers = ["Qichen Liu", "Homepage UI is inspired by sly"]
    artists = ["Qichen Liu"]
    
    about.set_developers(developers)
    about.set_designers(designers)
    about.set_artists(artists)

    about.set_copyright("© 2024 Qichen Liu")
    about.set_license_type(Gtk.License.MIT_X11)
    
    about.present(window)
