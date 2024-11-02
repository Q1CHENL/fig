#!/usr/bin/env python3

import os
import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
import fig.home, fig.editor
from fig.utils import load_css

class Fig(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_default_size(750, 650)
        self.set_resizable(False)
        load_css()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        headerbar = Adw.HeaderBar()
        headerbar.set_title_widget(Gtk.Label(label="Fig"))
        main_box.append(headerbar)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.content_box)

        self.home_box = fig.home.HomeBox()
        self.editor_box = fig.editor.EditorBox()
        self.content_box.append(self.home_box)

        self.set_content(main_box)

    def load_editor_ui(self):
        if self.content_box.get_first_child():
            self.content_box.remove(self.content_box.get_first_child())
        self.content_box.append(self.editor_box)

    def load_home_ui(self):
        if self.content_box.get_first_child():
            self.content_box.remove(self.content_box.get_first_child())
        self.content_box.append(self.home_box)

class FigApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.github.Q1CHENL.fig")

    def do_activate(self):
        win = Fig(self)
        win.present()

def main():
    app = FigApplication()
    return app.run(None)

if __name__ == "__main__":
    main()