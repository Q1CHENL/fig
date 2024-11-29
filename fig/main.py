#!/usr/bin/env python3

import os, sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio
import fig.home, fig.editor
from fig.utils import load_css, clear_css

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
        
        self.headerbar.set_title_widget(Gtk.Label(label="Fig"))
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
            label="Right-click on the timeline handles\n" +
            "to discover more features!\n\n" +
            "Available actions:\n" +
            "• Remove frames or frame ranges\n" +
            "• Insert frames at any position\n" +
            "• Change playback speed for \n  selected frames"
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

def main():
    app = FigApplication()
    return app.run(None)

if __name__ == "__main__":
    main()