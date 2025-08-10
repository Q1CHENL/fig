from fig.utils import clear_css
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class EditorActionBar(Gtk.Box):
    """Action bar containing editing buttons (text, crop, flip, rotate, draw)"""

    def __init__(self, editor_box):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.editor_box = editor_box  # Reference to the main editor
        self.action_button_size = (30, 30)

        # Create all action buttons
        self._create_buttons()
        self._setup_layout()

    def _create_buttons(self):
        """Create all action buttons"""
        self.flip_button = Gtk.Button(icon_name="view-mirror-symbolic")
        self.flip_button.set_tooltip_text("Flip")
        self.flip_button.set_size_request(
            self.action_button_size[0], self.action_button_size[1])
        self.flip_button.connect('clicked', self.editor_box.on_flip_clicked)

        self.rotate_button = Gtk.Button(
            icon_name="object-rotate-right-symbolic")
        self.rotate_button.set_tooltip_text("Rotate")
        self.rotate_button.set_size_request(
            self.action_button_size[0], self.action_button_size[1])
        self.rotate_button.connect(
            'clicked', self.editor_box.on_rotate_clicked)

        self.text_button = Gtk.Button(icon_name="format-text-rich-symbolic")
        self.text_button.set_size_request(
            self.action_button_size[0], self.action_button_size[1])
        self.text_button.set_tooltip_text("Add Text")
        self.text_button.connect('clicked', self.editor_box.on_text_clicked)

        self.draw_button = Gtk.Button(icon_name="document-edit-symbolic")
        self.draw_button.set_tooltip_text("Draw")
        self.draw_button.set_size_request(
            self.action_button_size[0], self.action_button_size[1])
        self.draw_button.connect('clicked', self.editor_box.on_draw_clicked)

        self.crop_button = Gtk.Button(icon_name="edit-select-all-symbolic")
        self.crop_button.set_tooltip_text("Crop")
        self.crop_button.set_size_request(
            self.action_button_size[0], self.action_button_size[1])
        self.crop_button.connect('clicked', self.editor_box.on_crop_clicked)

    def _setup_layout(self):
        """Setup the layout of buttons"""
        self.append(self.text_button)
        self.append(self.crop_button)
        self.append(self.flip_button)
        self.append(self.rotate_button)
        self.append(self.draw_button)
        self.set_halign(Gtk.Align.CENTER)
        self.set_margin_bottom(10)

    def update_button_state(self, button, is_active):
        """Update CSS class for action bar button"""
        clear_css(button)
        if is_active:
            button.add_css_class(
                "action-button-dark-active" if self.editor_box.state.is_dark else "action-button-light-active")
        else:
            button.add_css_class(
                "action-button-dark" if self.editor_box.state.is_dark else "action-button-light")

    def update_theme(self, is_dark):
        """Update theme for all action buttons"""
        clear_css(self)
        self.add_css_class(
            "action-bar-dark" if is_dark else "action-bar-light")

        # Update individual button states
        clear_css(self.flip_button)
        if self.editor_box.state.flipped:
            self.flip_button.add_css_class(
                "action-button-dark-active" if is_dark else "action-button-light-active")
        else:
            self.flip_button.add_css_class(
                "action-button-dark" if is_dark else "action-button-light")

        clear_css(self.crop_button)
        if self.editor_box.state.crop_mode:
            self.crop_button.add_css_class(
                "action-button-dark-active" if is_dark else "action-button-light-active")
        else:
            self.crop_button.add_css_class(
                "action-button-dark" if is_dark else "action-button-light")

        clear_css(self.rotate_button)
        if self.editor_box.state.rotated:
            self.rotate_button.add_css_class(
                "action-button-dark-active" if is_dark else "action-button-light-active")
        else:
            self.rotate_button.add_css_class(
                "action-button-dark" if is_dark else "action-button-light")

        clear_css(self.text_button)
        if self.editor_box.state.text_mode:
            self.text_button.add_css_class(
                "action-button-dark-active" if is_dark else "action-button-light-active")
        else:
            self.text_button.add_css_class(
                "action-button-dark" if is_dark else "action-button-light")

        clear_css(self.draw_button)
        if self.editor_box.state.draw_mode:
            self.draw_button.add_css_class(
                "action-button-dark-active" if is_dark else "action-button-light-active")
        else:
            self.draw_button.add_css_class(
                "action-button-dark" if is_dark else "action-button-light")
