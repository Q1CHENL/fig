#!/usr/bin/env python3

import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GdkPixbuf
import fig.home, fig.editor
from fig.utils import clear_css

class Fig(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_default_size(750, 650)
        self.set_resizable(False)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.headerbar = Adw.HeaderBar()
        
        self.style = Adw.StyleManager.get_default()
        self.style.connect("notify::dark", self.on_color_scheme_change)
        
        self.back_button = Gtk.Button()
        self.back_button.set_icon_name("go-previous-symbolic")
        self.back_button.connect("clicked", lambda _: self.load_home_ui())
        self.back_button.set_visible(False)
        self.headerbar.pack_start(self.back_button)
        
        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_icon_name("open-menu-symbolic")

        self.menu_model = Gio.Menu()
        self.menu_model.append("New Window", "app.new_window")
        self.menu_model.append("Help", "app.help")
        self.menu_button.set_menu_model(self.menu_model)

        self.headerbar.pack_end(self.menu_button)
        
        label = Gtk.Label()
        label.set_markup('<b>Fig</b>')
        self.headerbar.set_title_widget(label)
        main_box.append(self.headerbar)
        
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.content_box)

        self.home_box = fig.home.HomeBox()
        self.editor_box = fig.editor.EditorBox()
        self.content_box.append(self.home_box)

        self.set_content(main_box)
        
        self.update_theme(self.style.get_dark())
    
    def update_theme(self, is_dark):
        """Update theme for all components"""
        clear_css(self.headerbar)
        self.headerbar.add_css_class("headerbar-dark" if is_dark else "headerbar-light")
        
        self.home_box.update_theme(is_dark)
        self.editor_box.update_theme(is_dark)
    
    def on_color_scheme_change(self, style_manager, pspec):
        """Handle system color scheme changes"""
        self.update_theme(style_manager.get_dark())

    def load_editor_ui(self):
        if self.content_box.get_first_child():
            self.content_box.remove(self.content_box.get_first_child())
        self.content_box.append(self.editor_box)
        self.back_button.set_visible(True)
        self.menu_model.remove(1)
        self.menu_model.append("Extract Frames", "app.extract_frames")
        self.menu_model.append("Help", "app.help")
        self.menu_model.append("About", "app.about")

    def load_home_ui(self):
        if self.content_box.get_first_child():
            self.content_box.remove(self.content_box.get_first_child())
        self.content_box.append(self.home_box)
        self.back_button.set_visible(False)
        self.editor_box.reset()
        while self.menu_model.get_n_items() > 2:
            self.menu_model.remove(self.menu_model.get_n_items() - 1)
        
    def on_option_selected(self, action, parameter, option_name):
        print(f"Selected: {option_name}")


class FigApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.github.Q1CHENL.fig")
        
        new_window_action = Gio.SimpleAction.new("new_window", None)
        new_window_action.connect("activate", self.on_new_window)
        self.add_action(new_window_action)
        
        help_action = Gio.SimpleAction.new("help", None)
        help_action.connect("activate", self.on_help)
        self.add_action(help_action)
        
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)
        
        extract_frames_action = Gio.SimpleAction.new("extract_frames", None)
        extract_frames_action.connect("activate", self.on_extract_frames)
        self.add_action(extract_frames_action)

    def do_activate(self):
        win = Fig(self)
        win.present()
        
    def on_new_window(self, action, parameter):
        """Create a new window when New Window is selected"""
        win = Fig(self)
        win.present()
    
    def on_help(self, action, parameter):
        """Show help dialog with tips about handle functionality"""
        window = self.get_active_window()
        
        dialog = Adw.AlertDialog.new(
            "Fig - Help",
            None
        )
        
        label = Gtk.Label(
            label=
            "• Left-click on the image to activate crop.\n\n" +
            "• Right-click on the timeline handles to\n"
            "  discovery more advanced actions.\n"
            
        )
        label.set_halign(Gtk.Align.END)
        label.set_justify(Gtk.Justification.LEFT)
        
        dialog.set_extra_child(label)
        
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")
        
        dialog.present(window)

    def on_about(self, action, parameter):
        """Show about dialog when About is selected"""
        window = self.get_active_window()
        if window:
            fig.home.show_about_dialog(window)

    def on_extract_frames(self, action, parameter):
        """Extract frames from the currently loaded GIF"""
        window = self.get_active_window()
        if window and hasattr(window.editor_box, 'original_file_name'):
            try:
                output_dir = window.editor_box.original_file_path[:-4]
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                for i, frame in enumerate(window.editor_box.frames):
                    if isinstance(frame, GdkPixbuf.Pixbuf):
                        pil_image = window.editor_box._pixbuf_to_pil(frame)
                        frame_name = f"{window.editor_box.original_file_name}-{str(i+1).zfill(3)}.png"
                        frame_path = os.path.join(output_dir, frame_name)
                        pil_image.save(frame_path, 'PNG')
                
                dialog = Adw.AlertDialog.new(
                    "Frames Extracted",
                    f"{output_dir}"
                )
                dialog.add_response("ok", "OK")
                dialog.present(window)
                
            except Exception as e:
                dialog = Adw.AlertDialog.new(
                    "Error",
                    f"Failed to extract frames: {str(e)}"
                )
                dialog.add_response("ok", "OK")
                dialog.present(window)
            

def main():
    app = FigApplication()
    return app.run(None)

if __name__ == "__main__":
    main()