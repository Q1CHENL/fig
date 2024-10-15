import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
from PIL import Image
import ui

class Trif(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Trif - GIF Trimmer")
        self.set_border_width(10)
        self.set_default_size(400, 400)

        self.header_bar = ui.header_bar()
        self.set_titlebar(self.header_bar)
        
        self.home_box = ui.home_box()
        self.editor_box = ui.editor_box()
        self.add(self.home_box)
        
        self.frame_grid = ui.frame_grid(self)
        self.select_button = ui.select_button(self)
        self.info_label = ui.info_label()
        self.save_button = ui.save_button(self)
        self.about_button = ui.about_button(self)

        self.home_box.pack_start(self.select_button, False, False, 0) # can not pack a widget twice
        self.home_box.pack_start(self.about_button, False, False, 0)
        # Separator between sections
        # self.separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        # self.separator.set_margin_top(20)

        # Image display (hidden by default)
        self.image = Gtk.Image()
        self.image.set_margin_top(20)

        self.gif_frames = []
        self.frame_durations = []
    
    def load_editor_ui(self):
        self.remove(self.home_box)
        self.add(self.editor_box)
        self.editor_box.pack_start(self.info_label, False, False, 0)
        self.editor_box.pack_start(self.frame_grid, False, False, 0)
        self.editor_box.pack_start(self.save_button, False, False, 0)
        self.editor_box.pack_start(self.image, True, True, 0)
        self.editor_box.show_all()
        
    
    def show_about_dialog(self, widget):
        pass

    def select_gif(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Please choose a GIF file", parent=self, action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        filter_gif = Gtk.FileFilter()
        filter_gif.set_name("GIF files")
        filter_gif.add_mime_type("image/gif")
        dialog.add_filter(filter_gif)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            gif_path = dialog.get_filename()
            self.load_gif(gif_path)
        dialog.destroy()
        self.home_box.hide()
        self.load_editor_ui()

    def load_gif(self, gif_path):
        try:
            gif = Image.open(gif_path)
            self.gif_frames = []
            self.frame_durations = []
            total_duration = 0

            for frame in range(gif.n_frames):
                gif.seek(frame)
                frame_image = gif.copy().convert("RGBA")
                self.gif_frames.append(frame_image)
                frame_duration = gif.info.get('duration', 100) / 1000.0  # ms to seconds
                self.frame_durations.append(frame_duration)
                total_duration += frame_duration

            # Show previously hidden elements after loading a GIF
            # self.separator.show()
            self.info_label.set_text(f"Total frames: {gif.n_frames} | Total time: {total_duration:.2f} seconds")
            self.info_label.show()
            self.frame_grid.show()
            self.start_frame_entry.set_text("0")
            self.end_frame_entry.set_text(str(gif.n_frames - 1))
            self.save_button.set_sensitive(True)
            self.save_button.show()
            self.show_frame(0)
            self.image.show()

        except Exception as e:
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error")
            dialog.format_secondary_text(f"Failed to load GIF: {str(e)}")
            dialog.run()
            dialog.destroy()

    def show_frame(self, frame_idx):
        if 0 <= frame_idx < len(self.gif_frames):
            frame_image = self.gif_frames[frame_idx]
            frame_image = frame_image.convert("RGB")
            frame_image.save("/tmp/temp_frame.png")  # Save temp image
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale("/tmp/temp_frame.png", 300, 300, True)
            self.image.set_from_pixbuf(pixbuf)

    def save_frames(self, widget):
        start_idx = int(self.start_frame_entry.get_text())
        end_idx = int(self.end_frame_entry.get_text())

        if 0 <= start_idx < len(self.gif_frames) and 0 <= end_idx < len(self.gif_frames) and start_idx <= end_idx:
            dialog = Gtk.FileChooserDialog(
                title="Save GIF as...", parent=self, action=Gtk.FileChooserAction.SAVE
            )
            dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
            dialog.set_do_overwrite_confirmation(True)

            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                save_path = dialog.get_filename()
                frames_to_save = self.gif_frames[start_idx:end_idx + 1]
                frame_durations_to_save = self.frame_durations[start_idx:end_idx + 1]
                frames_to_save[0].save(
                    save_path,
                    save_all=True,
                    append_images=frames_to_save[1:],
                    duration=[int(d * 1000) for d in frame_durations_to_save],
                    loop=0
                )
            dialog.destroy()
        else:
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Invalid Frame Range")
            dialog.run()
            dialog.destroy()

if __name__ == "__main__":
    app = Trif()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
