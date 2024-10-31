import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, Gio, GLib
from PIL import Image
from utils import load_css


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
        # GTK4 file chooser dialog
        dialog = Gtk.FileChooserDialog(
            title="Select a GIF file",
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.set_modal(True)
        dialog.set_transient_for(self.get_root())
        
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Open", Gtk.ResponseType.ACCEPT)
        
        # File filter for GIF files
        filter_gif = Gtk.FileFilter()
        filter_gif.set_name("GIF files")
        filter_gif.add_mime_type("image/gif")
        dialog.add_filter(filter_gif)
        
        dialog.connect('response', self._on_file_dialog_response)
        dialog.present()

    def _on_file_dialog_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            file_path = file.get_path()
            # Get the parent Fig window and trigger the editor UI
            window = self.get_root()
            window.load_editor_ui()
            # Load the selected GIF into editor
            window.editor_box.load_gif(file_path)
        dialog.destroy()

    def show_about(self, button):
        about = Gtk.AboutDialog()
        about.set_transient_for(self.get_root())
        about.set_modal(True)
        
        about.set_program_name("Fig")
        about.set_version("1.0")
        about.set_comments("A simple and usable GIF editor")
        about.set_website("https://github.com/Q1CHENL/fig")
        about.set_authors(["Qichen Liu (刘启辰)"])
        about.set_license_type(Gtk.License.MIT_X11)
        
        about.present()
