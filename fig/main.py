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
        
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")

        menu_model = Gio.Menu()
        menu_model.append("New Window", "app.new_window")
        menu_model.append("Option 2", "app.option2")
        menu_model.append("Option 3", "app.option3")
        menu_model.append("Option 4", "app.option4")
        menu_button.set_menu_model(menu_model)

        action2 = Gio.SimpleAction.new("option2", None)
        action2.connect("activate", self.on_option_selected, "Option 2")
        self.add_action(action2)

        action3 = Gio.SimpleAction.new("option3", None)
        action3.connect("activate", self.on_option_selected, "Option 3")
        self.add_action(action3)

        action4 = Gio.SimpleAction.new("option4", None)
        action4.connect("activate", self.on_option_selected, "Option 4")
        self.add_action(action4)

        self.headerbar.pack_end(menu_button)
        
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

    def load_home_ui(self):
        if self.content_box.get_first_child():
            self.content_box.remove(self.content_box.get_first_child())
        self.content_box.append(self.home_box)
        self.back_button.set_visible(False)
        self.editor_box.reset()
        
    def on_option_selected(self, action, parameter, option_name):
        print(f"Selected: {option_name}")


class FigApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.github.Q1CHENL.fig")
        
        new_window_action = Gio.SimpleAction.new("new_window", None)
        new_window_action.connect("activate", self.on_new_window)
        self.add_action(new_window_action)

    def do_activate(self):
        win = Fig(self)
        win.present()
        
    def on_new_window(self, action, parameter):
        """Create a new window when New Window is selected"""
        win = Fig(self)
        win.present()

def main():
    app = FigApplication()
    return app.run(None)

if __name__ == "__main__":
    main()