import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, GLib, Gio, GdkPixbuf
import frameline
import time
from utils import load_css
from PIL import Image
import io
import os


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
        image_container.set_size_request(self.image_display_width, self.image_display_height)
        image_container.set_halign(Gtk.Align.CENTER)
        image_container.set_valign(Gtk.Align.CENTER)
        image_container.set_vexpand(True)  # Allow container to expand vertically
        
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
        self.append(self.info_label)
        self.append(image_container)
        
        # Controls box - tighter positioning
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        controls_box.set_margin_top(15)    # Small top margin
        controls_box.set_margin_bottom(5) # Small bottom margin
        controls_box.set_margin_start(5)
        controls_box.set_margin_end(5)
        controls_box.set_vexpand(False)
        
        # Frameline
        self.frameline = frameline.FrameLine(min_value=0, max_value=0, stride=1)  # Initialize with 0 frames
        self.frameline.set_hexpand(True)
        self.frameline.connect('frames-changed', self.on_frames_changed)
        controls_box.append(self.frameline)
        
        # Button container
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
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
        self.current_frame = 0
        self.is_playing = False
        self.play_timeout_id = None

    def load_gif(self, file_path):
        """Load a GIF file using PIL for frame info and GdkPixbuf for display"""
        try:
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
                    self.frame_durations.append(duration * 1000)  # Store duration in milliseconds
                
                # Update frameline with 1-based frame range
                self.frameline.min_value = 1
                self.frameline.max_value = frame_count
                self.frameline.left_value = 1
                self.frameline.right_value = frame_count
                self.frameline.queue_draw()
                
                # Update info label
                self.info_label.set_text(
                    f"Total Frames: {frame_count} • Duration: {total_duration:.2f}s"
                )
                
                if self.frames:
                    self.display_frame(0)
                    print(f"Loaded GIF with {frame_count} frames, {total_duration:.2f}s duration")
            
        except Exception as e:
            print(f"Error loading GIF: {e}")

    def display_frame(self, frame_index):
        """Display a specific frame in the image display"""
        if not self.frames or not (0 <= frame_index < len(self.frames)):
            return
            
        try:
            pixbuf = self.frames[frame_index]
            scaled_pixbuf = self.scale_pixbuf_to_fit(
                pixbuf, 
                self.image_display_width, 
                self.image_display_height
            )
            self.image_display.set_pixbuf(scaled_pixbuf)
            self.current_frame = frame_index
            
        except Exception as e:
            print(f"Error displaying frame: {e}")

    def scale_pixbuf_to_fit(self, pixbuf, max_width, max_height):
        """Scale pixbuf to fit within the given dimensions while maintaining aspect ratio"""
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        
        # Calculate scale to fill the display area while maintaining aspect ratio
        scale_width = max_width / width
        scale_height = max_height / height
        scale = min(scale_width, scale_height)  # Changed from max() to min() to fit within bounds
        
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
            # Stop playing
            self.is_playing = False
            self.update_play_button_icon(False)
            if self.play_timeout_id:
                GLib.source_remove(self.play_timeout_id)
                self.play_timeout_id = None
        else:
            # Start playing
            self.is_playing = True
            self.update_play_button_icon(True)
            
            # Reset to start frame
            start = int(round(self.frameline.left_value)) - 1  # Convert to 0-based index
            self.current_frame = start
            self.display_frame(self.current_frame)
            
            # Schedule the first frame
            self.play_next_frame()

    def play_next_frame(self):
        """Play the next frame in the sequence"""
        if not self.is_playing:
            return False
            
        # Get current frame range
        start = int(round(self.frameline.left_value)) - 1  # Convert to 0-based index
        end = int(round(self.frameline.right_value)) - 1  # Convert to 0-based index
        
        # Calculate next frame within range
        next_frame = self.current_frame + 1
        
        if next_frame > end:
            # Stop playing when reaching the end frame
            self.is_playing = False
            self.update_play_button_icon(False)  # Update icon to play
            return False
        
        self.display_frame(next_frame)
        self.current_frame = next_frame
        
        # Schedule next frame
        self.play_timeout_id = GLib.timeout_add(100, self.play_next_frame)
        return False

    def save_frames(self, button):
        """Save the selected frame range as a new GIF"""
        start_idx = int(round(self.frameline.left_value)) - 1  # Convert to 0-based index
        end_idx = int(round(self.frameline.right_value)) - 1  # Convert to 0-based index
        
        if 0 <= start_idx < len(self.frames) and 0 <= end_idx < len(self.frames) and start_idx <= end_idx:
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
                        overwrite_dialog.connect('response', lambda d, r: self._handle_overwrite_response(d, r, save_path, start_idx, end_idx))
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
        frames_to_save = [self._pixbuf_to_pil(self.frames[i]) for i in range(start_idx, end_idx + 1)]
        durations = self.frame_durations[start_idx:end_idx + 1]
        
        frames_to_save[0].save(
            save_path,
            save_all=True,
            append_images=frames_to_save[1:],
            duration=durations,
            loop=0,
            format='GIF'
        )
        print(f"Saved GIF to {save_path}")

    def on_frames_changed(self, frameline, start, end):
        """Handle frame range changes from the frameline"""
        if self.frames:
            # Convert 1-based frame numbers to 0-based indices
            start_frame = int(round(start)) - 1  # Subtract 1 to convert to 0-based index
            end_frame = int(round(end)) - 1  # Subtract 1 to convert to 0-based index
            
            # Ensure we're within valid frame range
            start_frame = max(0, min(start_frame, len(self.frames) - 1))
            end_frame = max(0, min(end_frame, len(self.frames) - 1))
            
            # Determine which handle was moved and update the frame
            if frameline.dragging_left:
                self.display_frame(start_frame)
            elif frameline.dragging_right:
                self.display_frame(end_frame)
            
            print(f"Frame range changed: {int(round(start))} to {int(round(end))}")

    def save_button(self):
        save_button = Gtk.Button(label="Save")
        # Force the button size
        save_button.set_size_request(80, 40)  # Increased width for better text fit
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
        pil_image.save(buf, 'ppm')
        buf.seek(0)
        
        # Load from buffer into GdkPixbuf
        loader = GdkPixbuf.PixbufLoader.new_with_type('pnm')
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










