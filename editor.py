from gi.repository import Gtk, GdkPixbuf, GLib
from PIL import Image
import frameline, time


class EditorBox(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_homogeneous(False)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self.set_margin_right(20)
        self.button_height = 40

        self.gif_frames = []
        self.frame_durations = []

        # Image display area (main image preview) takes up the main upper space
        self.image_display = Gtk.Image()
        self.image_display.set_size_request(700, 500)
        self.info_label = Gtk.Label()


        # Bottom section container for slider, play, and save button (HORIZONTAL layout)
        self.bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.bottom_box.set_margin_start(50)
        self.bottom_box.set_margin_end(50)
        self.bottom_box.set_margin_bottom(20)

        self.pack_start(self.image_display, True, True, 0)
        self.pack_start(self.info_label, False, False, 0)
        self.pack_start(self.bottom_box, False, False, 0)        
        self.current_frame = 0
        self.is_playing = False
        self.playback_start_time = 0
        self.playback_accumulated_duration = 0


    def save_button(self):
        save_button = Gtk.Button(label="Save")
        save_button.set_size_request(60, self.button_height)
        save_button.connect("clicked", self.save_frames)
        save_button.set_halign(Gtk.Align.CENTER)
        save_button.set_sensitive(True)
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(f"""
            button {{
                border-radius: {self.button_height}px;
                /*background-color: #3584E4;*/
                background-color: white;
                color: black;
            }}
        """.encode("utf-8"))

        save_button.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        return save_button

    def play_button(self):
        play_button = Gtk.Button()
        icon = Gtk.Image.new_from_icon_name("media-playback-start", Gtk.IconSize.BUTTON)
        play_button.set_image(icon)
        play_button.set_size_request(self.button_height, self.button_height)
        play_button.connect("clicked", self.play_edited_frames)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(f"""
            button {{
                border-radius: {self.button_height}px;
                color: white;
            }}
        """.encode("utf-8"))

        play_button.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        return play_button

    def info_label():
        # Info label (hidden by default)
        info_label = Gtk.Label()
        info_label.set_margin_top(10)
        return info_label
    
    def play_edited_frames(self, widget):
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self):
        self.is_playing = True
        self.current_frame = int(self.fl.left_value)
        self.playback_start_time = time.time()
        self.playback_accumulated_duration = 0
        GLib.idle_add(self.play_next_frame)

    def stop_playback(self):
        self.is_playing = False

    def play_next_frame(self):
        if not self.is_playing or self.current_frame > int(self.fl.right_value):
            self.is_playing = False
            return False

        self.show_frame(self.current_frame)
        
        # Only update accumulated duration if we're not at the last frame
        if self.current_frame < len(self.frame_durations):
            self.playback_accumulated_duration += self.frame_durations[self.current_frame]

        self.current_frame += 1

        # Check if we've reached the end
        if self.current_frame > int(self.fl.right_value):
            self.is_playing = False
            return False

        elapsed_time = time.time() - self.playback_start_time
        delay = max(0, int((self.playback_accumulated_duration - elapsed_time) * 1000))

        GLib.timeout_add(delay, self.play_next_frame)
        return False

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
                frame_duration = gif.info.get(
                    'duration', 100) / 1000.0  # ms to seconds
                self.frame_durations.append(frame_duration)
                total_duration += frame_duration

            # Show previously hidden elements after loading a GIF
            self.info_label.set_text(f"Total frames: {gif.n_frames} | Total time: {
                                     total_duration:.2f} seconds"
                                     )
            self.fl = frameline.FrameLine(min_value=0, max_value=len(self.gif_frames), stride=1)
            self.fl.set_value_changed_callback(self.on_frameline_value_changed)
            self.bottom_box.pack_start(self.fl, True, True, 0)
            self.bottom_box.pack_start(self.play_button(), False, False, 0)
            self.bottom_box.pack_start(self.save_button(), False, False, 0)
            self.show_frame(0)
        except Exception as e:
            dialog = Gtk.MessageDialog(
                0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error")
            dialog.format_secondary_text(f"Failed to load GIF: {str(e)}")
            dialog.run()
            dialog.destroy()

    def show_frame(self, frame_index):
        if 0 <= frame_index < len(self.gif_frames):
            frame_image = self.gif_frames[frame_index]
            frame_image = frame_image.convert("RGB")
            frame_image.save("/tmp/temp_frame.png")  # Save temp image
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                "/tmp/temp_frame.png", 650, 450, True)
            self.image_display.set_from_pixbuf(pixbuf)
            self.image_display.show()
            
    def on_frameline_value_changed(self, left_value, right_value):
        # Update the image display based on the handle being dragged
        if self.fl.dragging_left:
            self.show_frame(int(round(left_value)))
        elif self.fl.dragging_right:
            self.show_frame(int(round(right_value)))

            
    def save_frames(self, widget):
        start_idx = int(self.fl.left_value)
        end_idx = int(self.fl.right_value)
        
        if 0 <= start_idx < len(self.gif_frames) and 0 <= end_idx < len(self.gif_frames) and start_idx <= end_idx:
            dialog = Gtk.FileChooserDialog(
                title="Save GIF as...", parent=self.get_parent(), action=Gtk.FileChooserAction.SAVE
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
            dialog.set_do_overwrite_confirmation(True)
            
            # Add file filter for .gif files
            filter_gif = Gtk.FileFilter()
            filter_gif.set_name("GIF files")
            filter_gif.add_mime_type("image/gif")
            dialog.add_filter(filter_gif)
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                save_path = dialog.get_filename()
                # Add .gif extension if not present
                if not save_path.lower().endswith('.gif'):
                    save_path += '.gif'
                    
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
            dialog = Gtk.MessageDialog(
                self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Invalid Frame Range")
            dialog.run()
            dialog.destroy()
