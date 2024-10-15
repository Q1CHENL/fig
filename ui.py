from gi.repository import Gtk, GdkPixbuf


def header_bar():
    header_bar = Gtk.HeaderBar()
    header_bar.set_show_close_button(True)
    header_bar.props.title = "Trif"
    header_bar.props.subtitle = "Trim your GIF by frames"
    return header_bar


def editor_box():
    editor_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    editor_box.set_homogeneous(False)
    editor_box.set_margin_top(20)
    editor_box.set_margin_bottom(20)
    editor_box.set_margin_start(20)
    editor_box.set_margin_end(20)
    return editor_box


def home_box():
    home_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    home_box.set_homogeneous(False)
    home_box.set_margin_top(140)
    home_box.set_margin_bottom(20)
    home_box.set_margin_start(20)
    home_box.set_margin_end(20)
    return home_box


def save_button(trif):
    save_button = Gtk.Button(label="Save Frames")
    save_button.set_size_request(150, 50)
    save_button.connect("clicked", trif.save_frames)
    save_button.set_halign(Gtk.Align.CENTER)
    save_button.set_sensitive(False)
    return save_button


def info_label():
    # Info label (hidden by default)
    info_label = Gtk.Label(label="Total frames: 0 | Total time: 0.0 seconds")
    info_label.set_margin_top(10)
    return info_label


def select_button(trif):
    # Initial button to select GIF
    select_button = Gtk.Button(label="Select GIF")
    select_button.set_size_request(150, 50)  # Set specific size for button
    select_button.connect("clicked", trif.select_gif)
    select_button.set_halign(Gtk.Align.CENTER)  # Center the button
    return select_button


def about_button(trif):
    about_button = Gtk.Button(label="About Trif")
    about_button.set_size_request(150, 50)  # Set specific size for button
    about_button.connect("clicked", trif.show_about_dialog)
    about_button.set_halign(Gtk.Align.CENTER)  # Center the button
    return about_button


def frame_grid(trif):
    # Frame range entry fields (hidden by default)
    frame_grid = Gtk.Grid()
    frame_grid.set_row_spacing(10)
    frame_grid.set_column_spacing(10)
    frame_grid.set_margin_top(20)
    trif.start_frame_entry = Gtk.Entry()
    trif.start_frame_entry.set_placeholder_text("Start frame")
    trif.end_frame_entry = Gtk.Entry()
    trif.end_frame_entry.set_placeholder_text("End frame")
    frame_grid.attach(trif.start_frame_entry, 1, 0, 1, 1)
    frame_grid.attach(trif.end_frame_entry, 1, 1, 1, 1)
    return frame_grid
