import os
import io
from PIL import Image
from fig.utils import load_css
from fig.frameline import FrameLine
from gi.repository import Gtk, Gdk, GLib, Gio, GdkPixbuf
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')


class EditorBox(Gtk.Box):
    def __init__(self):
        super().__init__()
        self.button_height = 40

        # Main box spacing
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(0)  # Reduced from 10 to 0
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(80)
        self.set_margin_end(80)

        # Increase image display dimensions
        self.image_display_width = 600   # Increased from 400
        self.image_display_height = 450  # Increased from 300

        # Create a fixed-size container for the image
        image_container = Gtk.Box()
        image_container.set_size_request(
            self.image_display_width, self.image_display_height)
        image_container.set_halign(Gtk.Align.CENTER)
        image_container.set_valign(Gtk.Align.CENTER)
        # Allow container to expand vertically
        image_container.set_vexpand(True)

        # Image display area setup
        self.image_display = Gtk.Picture()
        self.image_display.set_can_shrink(True)
        self.image_display.set_keep_aspect_ratio(True)
        self.image_display.set_halign(Gtk.Align.CENTER)
        self.image_display.set_valign(Gtk.Align.CENTER)
        load_css(self.image_display, ["image-display"])

        # Add image display to the container
        image_container.append(self.image_display)
        # Info label
        self.info_label = Gtk.Label()
        self.info_label.set_margin_top(10)
        self.info_label.set_margin_bottom(10)
        self.info_label.set_halign(Gtk.Align.CENTER)
        load_css(self.info_label, ["info-label"])
        self.append(self.info_label)
        self.append(image_container)

        # Controls box - tighter positioning
        controls_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        controls_box.set_margin_top(15)    # Small top margin
        controls_box.set_margin_bottom(5)  # Small bottom margin
        controls_box.set_margin_start(5)
        controls_box.set_margin_end(5)
        controls_box.set_vexpand(False)

        # Frameline
        self.frameline = FrameLine(
            min_value=0, max_value=0, stride=1)  # Initialize with 0 frames
        self.frameline.set_hexpand(True)
        self.frameline.connect('frames-changed', self.on_frames_changed)
        controls_box.append(self.frameline)

        # Button container
        buttons_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        buttons_box.set_halign(Gtk.Align.END)  # Align buttons to the right

        # Add buttons
        buttons_box.append(self.play_button())
        buttons_box.append(self.save_button())

        # Add buttons to controls
        controls_box.append(buttons_box)

        # Add controls to main box
        self.append(controls_box)

        # GIF handling properties
        self.frames = []
        self.current_frame_index = 0
        self.playhead_frame_index = 0  # New variable to track playhead position
        self.is_playing = False
        self.play_timeout_id = None
        self.playback_finished = False  # Add this to track if playback reached the end

    def load_gif(self, file_path):
        """Load a GIF file using PIL for frame info and GdkPixbuf for display"""
        try:
            # Reset state before attempting to load
            self.frames = []
            self.frame_durations = []
            self.current_frame_index = 0
            self.playhead_frame_index = 0
            
            with Image.open(file_path) as gif:
                frame_count = gif.n_frames
                total_duration = 0
                self.frames = []
                self.frame_durations = []  # Store frame durations

                for frame in range(frame_count):
                    gif.seek(frame)
                    duration = gif.info.get('duration', 100) / 1000.0
                    total_duration += duration
                    pixbuf = self._pil_to_pixbuf(gif.convert('RGBA'))
                    self.frames.append(pixbuf)
                    # Store duration in milliseconds
                    self.frame_durations.append(duration * 1000)

                # Update frameline with 1-based frame range
                self.frameline.min_value = 1
                self.frameline.max_value = frame_count
                self.frameline.left_value = 1
                self.frameline.right_value = frame_count
                self.frameline.queue_draw()

                # Update info label
                self.info_label.set_text(
                    f"{frame_count} Frames • {total_duration:.2f} Seconds"
                )

                if self.frames:
                    self.display_frame(0)
        except Exception as e:
            print(f"Error loading GIF: {e}")
            # Ensure state is clean on error
            self.frames = []
            self.frame_durations = []
            self.current_frame_index = 0
            self.playhead_frame_index = 0

    def display_frame(self, frame_index):
        """Display a specific frame in the image display"""
        if not self.frames or not (0 <= frame_index < len(self.frames)):
            print(f"Frame is not displayed: {frame_index}")
            return

        try:
            self.current_frame_index = frame_index
            frame = self.frames[frame_index]
            
            if isinstance(frame, Image.Image):
                pixbuf = self._pil_to_pixbuf(frame)
            else:
                pixbuf = frame
                
            # Debug info
            if pixbuf:
                width = pixbuf.get_width()
                height = pixbuf.get_height()
                pixels = pixbuf.get_pixels()
                frame_hash = hash(pixels)
                # print(f"Frame {frame_index + 1}: type={type(frame)}, size={width}x{height}, hash={frame_hash}")
                
                scaled_pixbuf = self.scale_pixbuf_to_fit(pixbuf, self.image_display_width, self.image_display_height)
                if scaled_pixbuf:
                    self.image_display.set_pixbuf(scaled_pixbuf)
                    # Force display update
                    self.image_display.queue_draw()
                    # while Gtk.events_pending():
                    #     Gtk.main_iteration()

        except Exception as e:
            print(f"Error displaying frame: {e}")

    def scale_pixbuf_to_fit(self, pixbuf, max_width, max_height):
        """Scale pixbuf to fit within the given dimensions while maintaining aspect ratio"""
        width = pixbuf.get_width()
        height = pixbuf.get_height()

        # Calculate scale to fill the display area while maintaining aspect ratio
        scale_width = max_width / width
        scale_height = max_height / height
        # Changed from max() to min() to fit within bounds
        scale = min(scale_width, scale_height)

        new_width = int(width * scale)
        new_height = int(height * scale)

        return pixbuf.scale_simple(
            new_width,
            new_height,
            GdkPixbuf.InterpType.HYPER
        )

    def play_edited_frames(self, button):
        """Start or stop playing the edited frames"""
        if self.is_playing:
            # Just pause at current position
            self.is_playing = False
            self.update_play_button_icon(False)
            if self.play_timeout_id:
                GLib.source_remove(self.play_timeout_id)
                self.play_timeout_id = None
        else:
            # Start/resume playing
            self.is_playing = True
            self.playback_finished = False  # Reset the finished flag when starting playback
            self.update_play_button_icon(True)

            # Get current frame range
            start = int(round(self.frameline.left_value)) - 1
            end = int(round(self.frameline.right_value)) - 1
            is_reversed = start > end

            # If playhead isn't visible or playback was finished, start from left handle
            if not self.frameline.playhead_visible or self.playback_finished:
                if is_reversed:
                    self.current_frame_index = end if start <= end else start
                    self.playhead_frame_index = self.current_frame_index
                # Reverse playback
                else:
                    self.current_frame_index = start if start <= end else end
                    self.playhead_frame_index = self.current_frame_index
                    
            self.display_frame(self.current_frame_index)
            self.show_playhead()
            self.frameline.set_playhead_position(self.current_frame_index)
            self.play_next_frame()

    def play_next_frame(self):
        """Play the next frame in the sequence"""
        if not self.is_playing:
            return False

        # Get current frame range
        start = int(round(self.frameline.left_value)) - 1
        end = int(round(self.frameline.right_value)) - 1
        is_reversed = start > end

        # Calculate next frame within range
        if is_reversed:
            next_frame = self.current_frame_index - 1
            if next_frame < end:
                self.is_playing = False
                self.update_play_button_icon(False)
                self.hide_playhead()
                self.frameline.playhead_visible = False  # Explicitly set the state
                if self.play_timeout_id:
                    GLib.source_remove(self.play_timeout_id)
                    self.play_timeout_id = None
                return False
        else:
            next_frame = self.current_frame_index + 1
            if next_frame > end:
                self.is_playing = False
                self.update_play_button_icon(False)
                self.hide_playhead()
                self.frameline.playhead_visible = False  # Explicitly set the state
                if self.play_timeout_id:
                    GLib.source_remove(self.play_timeout_id)
                    self.play_timeout_id = None
                return False
            
        self.display_frame(next_frame)
        self.current_frame_index = next_frame
        self.playhead_frame_index = next_frame

        # Update playhead position
        self.frameline.set_playhead_position(self.playhead_frame_index)

        # Schedule next frame using the current frame's duration
        current_duration = self.frame_durations[next_frame]
        self.play_timeout_id = GLib.timeout_add(
            current_duration, self.play_next_frame)
        return False


    def show_playhead(self):
        """Show playhead and update state"""
        self.frameline.show_playhead()

    def hide_playhead(self):
        """Hide playhead and update state"""
        self.frameline.hide_playhead()

    def save_frames(self, button):
        """Save the selected frame range as a new GIF"""
        start_idx = int(round(self.frameline.left_value)) - 1  # Convert to 0-based index
        end_idx = int(round(self.frameline.right_value)) - 1  # Convert to 0-based index

        if 0 <= start_idx < len(self.frames) and 0 <= end_idx < len(self.frames):
            dialog = Gtk.FileChooserDialog(
                title="Save GIF as...",
                action=Gtk.FileChooserAction.SAVE,
                transient_for=self.get_root(),
                modal=True
            )
            dialog.add_buttons(
                "Cancel", Gtk.ResponseType.CANCEL,
                "Save", Gtk.ResponseType.ACCEPT
            )

            # Add file filter for .gif files
            filter_gif = Gtk.FileFilter()
            filter_gif.set_name("GIF files")
            filter_gif.add_mime_type("image/gif")
            dialog.add_filter(filter_gif)

            def on_response(dialog, response):
                if response == Gtk.ResponseType.ACCEPT:
                    save_path = dialog.get_file().get_path()
                    # Add .gif extension if not present
                    if not save_path.lower().endswith('.gif'):
                        save_path += '.gif'

                    # Check if file exists and confirm overwrite
                    if os.path.exists(save_path):
                        overwrite_dialog = Gtk.MessageDialog(
                            transient_for=self.get_root(),
                            modal=True,
                            message_type=Gtk.MessageType.QUESTION,
                            buttons=Gtk.ButtonsType.YES_NO,
                            text="File already exists. Do you want to overwrite it?"
                        )
                        overwrite_dialog.connect('response', lambda d, r: self._handle_overwrite_response(
                            d, r, save_path, start_idx, end_idx))
                        overwrite_dialog.show()
                    else:
                        self._save_gif(save_path, start_idx, end_idx)

                dialog.destroy()

            dialog.connect('response', on_response)
            dialog.show()
        else:
            dialog = Gtk.MessageDialog(
                transient_for=self.get_root(),
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Invalid Frame Range"
            )
            dialog.connect('response', lambda d, r: d.destroy())
            dialog.show()

    def _handle_overwrite_response(self, dialog, response, save_path, start_idx, end_idx):
        if response == Gtk.ResponseType.YES:
            self._save_gif(save_path, start_idx, end_idx)
        dialog.destroy()

    def _save_gif(self, save_path, start_idx, end_idx):
        # Determine if we need to reverse the frames
        is_reversed = start_idx > end_idx
        if is_reversed:
            start_idx, end_idx = end_idx, start_idx

        frames_to_save = [self._pixbuf_to_pil(
            self.frames[i]) for i in range(start_idx, end_idx + 1)]
        durations = self.frame_durations[start_idx:end_idx + 1]

        # Reverse frames and durations if needed
        if is_reversed:
            frames_to_save.reverse()
            durations.reverse()

        frames_to_save[0].save(
            save_path,
            save_all=True,
            append_images=frames_to_save[1:],
            duration=durations,
            loop=0,
            format='GIF'
        )

    def on_frames_changed(self, frameline, start, end):
        """Handle frame range changes from the frameline"""
        if not self.frames:
            return

        # Convert 1-based frame numbers to 0-based indices
        start_frame_index = int(round(start)) - 1
        end_frame_index = int(round(end)) - 1

        # Ensure we're within valid frame range
        start_frame_index = max(0, min(start_frame_index, len(self.frames) - 1))
        end_frame_index = max(0, min(end_frame_index, len(self.frames) - 1))

        # Update display during dragging if not previously playing
        if (frameline.dragging_left or frameline.dragging_right) and not frameline.playhead_visible:
            # Always use the handle being dragged for preview
            if frameline.dragging_left:
                frame_index = int(round(frameline.left_value)) - 1
            else:
                frame_index = int(round(frameline.right_value)) - 1
                
            frame_index = max(0, min(frame_index, len(self.frames) - 1))
            self.current_frame_index = frame_index
            self.display_frame(frame_index)
        
        # Update playhead visibility using min/max for reversed handles
        min_frame = min(start_frame_index, end_frame_index)
        max_frame = max(start_frame_index, end_frame_index)
        if self.playhead_frame_index < min_frame or self.playhead_frame_index > max_frame:
            self.hide_playhead()
        else:
            self.frameline.set_playhead_position(self.playhead_frame_index)

    def save_button(self):
        save_button = Gtk.Button(label="Save")
        save_button.set_size_request(80, 40)
        save_button.set_valign(Gtk.Align.CENTER)  # Center vertically
        save_button.set_halign(Gtk.Align.CENTER)
        load_css(save_button, ["save-button"])
        save_button.connect('clicked', self.save_frames)
        return save_button

    def play_button(self):
        self.play_button = Gtk.Button()
        self.update_play_button_icon(False)  # Set initial icon to play
        self.play_button.set_size_request(40, 40)
        self.play_button.set_valign(Gtk.Align.CENTER)  # Center vertically
        self.play_button.set_halign(Gtk.Align.CENTER)
        load_css(self.play_button, ["play-button"])
        self.play_button.connect('clicked', self.play_edited_frames)
        return self.play_button

    def _pil_to_pixbuf(self, pil_image):
        """Convert PIL image to GdkPixbuf"""
        # Save PIL image to buffer
        buf = io.BytesIO()
        pil_image.save(buf, 'png')
        buf.seek(0)

        # Load from buffer into GdkPixbuf
        loader = GdkPixbuf.PixbufLoader.new_with_type('png')
        loader.write(buf.read())
        loader.close()

        return loader.get_pixbuf()

    def _pixbuf_to_pil(self, pixbuf):
        """Convert GdkPixbuf to PIL Image"""
        width, height = pixbuf.get_width(), pixbuf.get_height()
        pixels = pixbuf.get_pixels()
        stride = pixbuf.get_rowstride()
        mode = "RGBA" if pixbuf.get_has_alpha() else "RGB"

        return Image.frombytes(mode, (width, height), pixels, "raw", mode, stride)

    def update_play_button_icon(self, playing):
        """Update the play button icon based on playing state"""
        icon_name = "media-playback-start-symbolic" if not playing else "media-playback-pause-symbolic"
        icon = Gio.ThemedIcon(name=icon_name)
        image = Gtk.Image.new_from_gicon(icon)
        self.play_button.set_child(image)

    def on_handle_drag(self, handle_position):
        """Called when either handle is being dragged"""
        # Update displayed frame to match handle position
        frame_index = int(round(handle_position)) - 1
        self.display_frame(frame_index)
        
        # Check if playhead should be visible
        min_val = min(self.frameline.left_value, self.frameline.right_value)
        max_val = max(self.frameline.left_value, self.frameline.right_value)
        
        # Important: handle_position is 1-based, but playhead_frame_index is 0-based
        if (self.playhead_frame_index < min_val - 1 or 
            self.playhead_frame_index > max_val - 1):
            self.frameline.playhead_visible = False
            self.hide_playhead()