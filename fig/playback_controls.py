from fig.utils import clear_css
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio


class PlaybackControls(Gtk.Box):
    """Playback controls containing play, loop, and save buttons"""

    def __init__(self, editor_box):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.editor_box = editor_box  # Reference to the main editor
        self.BUTTON_HEIGHT = 40

        # Create all playback buttons
        self._create_buttons()
        self._setup_layout()

    def _create_buttons(self):
        """Create all playback control buttons"""
        self.play_btn = self._create_play_button()
        self.save_btn = self._create_save_button()
        self.loop_btn = self._create_loop_button()

    def _create_play_button(self):
        """Create the play/pause button"""
        play_button = Gtk.Button()
        play_button.set_size_request(40, self.BUTTON_HEIGHT)
        play_button.set_valign(Gtk.Align.CENTER)
        play_button.set_halign(Gtk.Align.CENTER)
        play_button.connect('clicked', self.editor_box.play_edited_frames)

        icon_name = "media-playback-start-symbolic"
        icon = Gio.ThemedIcon(name=icon_name)
        image = Gtk.Image.new_from_gicon(icon)
        play_button.set_child(image)

        return play_button

    def _create_save_button(self):
        """Create the save button"""
        save_button = Gtk.Button(label="Save")
        save_button.set_size_request(80, self.BUTTON_HEIGHT)
        save_button.set_valign(Gtk.Align.CENTER)
        save_button.set_halign(Gtk.Align.CENTER)
        save_button.connect('clicked', self.editor_box.save_frames)
        return save_button

    def _create_loop_button(self):
        """Create the loop toggle button"""
        loop_button = Gtk.Button()
        loop_button.set_size_request(40, self.BUTTON_HEIGHT)
        loop_button.set_valign(Gtk.Align.CENTER)
        loop_button.set_halign(Gtk.Align.CENTER)
        loop_button.connect('clicked', self.editor_box.toggle_loop)

        icon_name = "media-playlist-repeat-symbolic"
        icon = Gio.ThemedIcon(name=icon_name)
        image = Gtk.Image.new_from_gicon(icon)
        loop_button.set_child(image)

        return loop_button

    def _setup_layout(self):
        """Setup the layout of buttons"""
        self.append(self.play_btn)
        self.append(self.loop_btn)
        self.append(self.save_btn)
        self.set_halign(Gtk.Align.END)  # Align buttons to the right

    def update_play_button_icon(self, playing):
        """Update the play button icon based on playing state"""
        icon_name = "media-playback-start-symbolic" if not playing else "media-playback-pause-symbolic"
        icon = Gio.ThemedIcon(name=icon_name)
        image = Gtk.Image.new_from_gicon(icon)
        self.play_btn.set_child(image)

    def update_loop_button_state(self, is_looping):
        """Update the loop button active state"""
        if is_looping:
            self.loop_btn.add_css_class("loop-button-active")
        else:
            self.loop_btn.remove_css_class("loop-button-active")

    def update_theme(self, is_dark):
        """Update theme for all playback control buttons"""
        clear_css(self.save_btn)
        self.save_btn.add_css_class(
            "save-button-dark" if is_dark else "save-button-light")

        clear_css(self.play_btn)
        self.play_btn.add_css_class(
            "play-button-dark" if is_dark else "play-button-light")

        clear_css(self.loop_btn)
        self.loop_btn.add_css_class(
            "loop-button-dark" if is_dark else "loop-button-light")
