#!/usr/bin/env python3

import os
import gi
import fig.editor
import fig.home
from fig.utils import clear_css, load_css

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, Gdk


class Fig(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self._setup_window_properties()
        self._setup_drag_and_drop()
        self._setup_header_bar()
        self._setup_content_area()
        self._setup_theme()
        self.on_editor = False

    def _setup_window_properties(self):
        """Configure basic window properties"""
        self.set_default_size(750, 650)
        self.set_resizable(False)

    def _setup_drag_and_drop(self):
        """Setup drag and drop functionality"""
        drop_target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        drop_target.connect('drop', self.on_drop)
        drop_target.connect('enter', self.on_drag_enter)
        drop_target.connect('leave', self.on_drag_leave)
        drop_target.connect('motion', self.on_drag_motion)
        self.add_controller(drop_target)

    def _setup_header_bar(self):
        """Setup the header bar with navigation and menu"""
        self.headerbar = Adw.HeaderBar()

        # Setup back button
        self.back_button = Gtk.Button()
        self.back_button.set_icon_name("go-previous-symbolic")
        self.back_button.connect("clicked", lambda _: self.load_home_ui())
        self.back_button.set_visible(False)
        self.headerbar.pack_start(self.back_button)

        # Setup menu button
        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_icon_name("open-menu-symbolic")

        self.menu_model = Gio.Menu()
        self.menu_model.append("New Window", "app.new_window")
        self.menu_model.append("Help", "app.help")
        self.menu_button.set_menu_model(self.menu_model)

        self.headerbar.pack_end(self.menu_button)

        # Setup title
        label = Gtk.Label()
        label.set_markup('<b>Fig</b>')
        self.headerbar.set_title_widget(label)

    def _setup_content_area(self):
        """Setup the main content area with home and editor boxes"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.headerbar)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.content_box)

        self.home_box = fig.home.HomeBox()
        self.editor_box = fig.editor.EditorBox()
        self.content_box.append(self.home_box)

        self.set_content(main_box)

    def _setup_theme(self):
        """Setup theme management"""
        self.style = Adw.StyleManager.get_default()
        self.style.connect("notify::dark", self.on_color_scheme_change)
        self.update_theme(self.style.get_dark())

    def update_theme(self, is_dark):
        """Update theme for all components"""
        clear_css(self.headerbar)
        self.headerbar.add_css_class(
            "headerbar-dark" if is_dark else "headerbar-light")

        self.home_box.update_theme(is_dark)
        self.editor_box.update_theme(is_dark)

    def on_color_scheme_change(self, style_manager, pspec):
        """Handle system color scheme changes"""
        self.update_theme(style_manager.get_dark())

    def load_editor_ui(self):
        if self.on_editor:
            return
        self.on_editor = True
        if self.content_box.get_first_child():
            self.content_box.remove(self.content_box.get_first_child())
        self.content_box.append(self.editor_box)
        self.back_button.set_visible(True)
        self.clear_menu()
        self.menu_model.append("New Window", "app.new_window")
        self.menu_model.append("Extract Frames", "app.extract_frames")
        self.menu_model.append("Export to Video", "app.export_to_video")
        self.menu_model.append("Help", "app.help")
        self.menu_model.append("About", "app.about")

    def load_home_ui(self):
        self.on_editor = False
        if self.content_box.get_first_child():
            self.content_box.remove(self.content_box.get_first_child())
        self.content_box.append(self.home_box)
        self.back_button.set_visible(False)
        self.editor_box.reset()
        self.clear_menu()
        self.menu_model.append("New Window", "app.new_window")
        self.menu_model.append("Help", "app.help")

    def clear_menu(self):
        while self.menu_model.get_n_items() > 0:
            self.menu_model.remove(self.menu_model.get_n_items() - 1)

    def on_option_selected(self, action, parameter, option_name):
        print(f"Selected: {option_name}")

    def on_drop(self, drop_target, value, x, y):
        self.remove_css_class('drag-and-drop')
        if isinstance(value, Gio.File):
            file_path = value.get_path()
            if file_path.lower().endswith('.gif'):
                self.load_editor_ui()
                self.editor_box.overlay.reset_crop_rect()
                self.editor_box.load_gif(file_path)
                original_file_name = os.path.basename(file_path)
                if original_file_name.endswith('.gif'):
                    self.editor_box.original_file_name = original_file_name[:-4]
                else:
                    self.editor_box.original_file_name = original_file_name
                return True

        return False

    def on_drag_enter(self, drop_target, x, y):
        load_css(self.get_display(), [])
        self.add_css_class('drag-and-drop')
        return Gdk.DragAction.COPY

    def on_drag_leave(self, drop_target):
        self.remove_css_class('drag-and-drop')

    def on_drag_motion(self, drop_target, x, y):
        return Gdk.DragAction.COPY
