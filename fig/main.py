#!/usr/bin/env python3

import os
import sys

# Add the package directory to Python path
package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, Gio, GLib, Adw
from PIL import Image
import fig.home, fig.editor
from fig.utils import load_css


class Fig(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        
        self.set_default_size(750, 650)
        self.set_resizable(False)
        
        # Load global CSS once
        load_css()
        
        # Create main structure
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Setup header bar
        headerbar = Adw.HeaderBar()
        headerbar.set_title_widget(Gtk.Label(label="Fig"))
        
        # Add headerbar to main box
        main_box.append(headerbar)
        
        # Create content box for switching between home and editor
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.content_box)
        
        # Main content
        self.home_box = fig.home.HomeBox()
        self.editor_box = fig.editor.EditorBox()
        self.content_box.append(self.home_box)
        
        # Set the main box as content
        self.set_content(main_box)
        
    def load_editor_ui(self):
        # Remove current content
        if self.content_box.get_first_child():
            self.content_box.remove(self.content_box.get_first_child())
        # Add editor
        self.content_box.append(self.editor_box)
        
    def load_home_ui(self):
        # Remove current content
        if self.content_box.get_first_child():
            self.content_box.remove(self.content_box.get_first_child())
        # Add home
        self.content_box.append(self.home_box)

class FigApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.flatpak.fig")
        
    def do_activate(self):
        win = Fig(self)  # Just pass self directly
        win.present()

def main():
    app = FigApplication()
    return app.run(None)

if __name__ == "__main__":
    main()
