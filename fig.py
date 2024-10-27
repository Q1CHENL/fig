import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
from PIL import Image
import home, editor

class Fig(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)
        # self.set_border_width(100)
        self.set_default_size(800, 600)
        self.round_radius = 15
        
        # CSS to round the bottom corners
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(f"""
            window {{
                border-radius: 0 0 {self.round_radius}px {self.round_radius}px; /* Rounding bottom left and right corners */
            }}
            decoration {{
                border-radius: {self.round_radius}px;
            }}
            window.background {{
                    border-radius: 0 0 {self.round_radius}px {self.round_radius}px;
            }}
        """)
    
        # Apply the CSS to the window
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Toggle light/dark mode
        settings = Gtk.Settings.get_default()
        # settings.set_property("gtk-application-prefer-dark-theme", False)

        self.set_titlebar(self.header_bar())
        self.set_resizable(False)

        # This sets the window the parent of the homebox and editorbox
        self.home_box = home.HomeBox()
        self.editor_box = editor.EditorBox()
        self.add(self.home_box)

    def load_editor_ui(self):
        self.remove(self.home_box)
        self.add(self.editor_box)
        self.editor_box.show_all()

    def load_home_ui(self):
        self.remove(self.editor_box)
        self.add(self.home_box)
        self.home_box.show_all()

    def header_bar(self):
        hb = Gtk.HeaderBar()
        hb.set_name("mw_hb")
        hb.set_show_close_button(True)
        hb.props.title = "Fig"

        # CSS to change the background color of the HeaderBar
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
        #mw_hb {
            border-width: 0;
            background-image: none; /* Clear inherited styles */
            background-image: linear-gradient(to bottom, #242424, #242424); /* Solid color */
            color: white; /* Text color */
        }
        """)
        # Apply the CSS to the header bar
        hb.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        # Add settings button on the left side of minimize
        settings_button = Gtk.Button()
        settings_icon = Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON)
        settings_button.set_image(settings_icon)
        settings_button.connect("clicked", self.show_menu)
        
        # Add CSS for circular hover effect
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data("""
            button {
                border-radius: 9999px;
            }
        """.encode())
        
        settings_button.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        
        # Add the button to the header bar
        hb.pack_end(settings_button)
        
        return hb

    def show_menu(self, button):
        # Create a popup menu
        menu = Gtk.PopoverMenu.new()
        menu.set_relative_to(button)
        
        # CSS to remove border
        # css_provider = Gtk.CssProvider()
        # css_provider.load_from_data("""
        #     popover * {
        #         box-shadow: none;
        #         border-style: hidden;
        #         margin: 0px;
        #         border-radius: 0px;
        #     }
        #         .window-frame {
        #         box-shadow: none;
        #         margin: 1px;
        #     }
        #     .suggestions {
        #         padding-top: 0px;
        #     }
        # """.encode())
        
        # menu.get_style_context().add_provider(
        #     css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        # )
        
        # Create a box to hold menu items
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # box.set_margin_top(5)
        # box.set_margin_bottom(5)
        
        # Add Preferences button
        preferences_button = Gtk.ModelButton()
        preferences_button.set_label("Preferences")
        preferences_button.set_alignment(0.0, 0.5)  # Left align text
        preferences_button.connect("clicked", self.show_preferences)
        box.pack_start(preferences_button, False, False, 0)
        
        # Add Import frames button
        import_button = Gtk.ModelButton()
        import_button.set_label("Import frames")
        import_button.set_alignment(0.0, 0.5)  # Left align text
        import_button.connect("clicked", self.import_frames)
        box.pack_start(import_button, False, False, 0)
        
        # Add the box to the menu and show it
        menu.add(box)
        box.show_all()
        menu.popup()

    def show_preferences(self, button):
        # TODO: Implement preferences dialog
        pass

    def import_frames(self, button):
        # TODO: Implement frame import functionality
        pass

    def show_settings(self, widget):
        # TODO: Implement settings dialog
        pass


if __name__ == "__main__":
    app = Fig()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
