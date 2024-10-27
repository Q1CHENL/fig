from gi.repository import Gtk, GdkPixbuf
from PIL import Image


class HomeBox(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_homogeneous(False)
        self.set_margin_top(220)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self.info_label = Gtk.Label(
            label="Please select a GIF file to start editing")
        
        # can not pack a widget twice
        self.pack_start(self.select_button(), False, False, 0)
        self.pack_start(self.about_button(), False, False, 0)


    def select_button(self):
        select_button = Gtk.Button(label="Select GIF")

        # Initial button to select GIF
        css_provider = Gtk.CssProvider()
        css = """
        button {
            background-color: white;
            color: black;
            border-radius: 25px;
        }
        """
        css_provider.load_from_data(css.encode())

        # Create a style context and add the provider
        style_context = select_button.get_style_context()
        style_context.add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        select_button.set_size_request(150, 50)  # Set specific size for button
        select_button.connect("clicked", self.select_gif)
        select_button.set_halign(Gtk.Align.CENTER)  # Center the button
        return select_button

    def about_button(self):
        about_button = Gtk.Button(label="About Fig")
        about_button.set_size_request(150, 50)
        about_button.connect("clicked", self.show_about_dialog)
        about_button.set_halign(Gtk.Align.CENTER)
        # Initial button to select GIF
        css_provider = Gtk.CssProvider()
        css = """
        button {
            border-radius: 25px;
        }
        """
        css_provider.load_from_data(css.encode())

        # Create a style context and add the provider
        style_context = about_button.get_style_context()
        style_context.add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        return about_button
    
    def show_about_dialog(self, widget):
        pass


    def select_gif(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Please choose a GIF file", 
            parent=self.get_parent(), 
            action=Gtk.FileChooserAction.OPEN
            )
        
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, 
            Gtk.ResponseType.CANCEL, 
            Gtk.STOCK_OPEN, 
            Gtk.ResponseType.OK
            )

        filter_gif = Gtk.FileFilter()
        filter_gif.set_name("GIF files")
        filter_gif.add_mime_type("image/gif")
        dialog.add_filter(filter_gif)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            gif_path = dialog.get_filename()
            self.get_parent().editor_box.load_gif(gif_path)
            self.hide()
            self.get_parent().load_editor_ui()
        dialog.destroy()

