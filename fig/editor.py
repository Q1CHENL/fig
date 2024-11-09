import os
import io
from PIL import Image
from fig.utils import load_css
from fig.frameline import FrameLine
from gi.repository import Gtk, Gdk, GLib, Gio, GdkPixbuf
import gi
import time
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

        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        controls_box.set_margin_top(15)  
        controls_box.set_margin_bottom(5)
        controls_box.set_margin_start(5)
        controls_box.set_margin_end(5)
        controls_box.set_vexpand(False)

        # Frameline
        self.frameline = FrameLine(
            min_value=0, max_value=0, stride=1)  # Initialize with 0 frames
        self.frameline.set_hexpand(True)
        self.frameline.connect('frames-changed', self.on_frames_changed)
        self.frameline.connect('insert-frames', self.on_insert_frames)
        self.frameline.connect('speed-changed', self.on_speed_changed)
        controls_box.append(self.frameline)

        # Button container
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        buttons_box.set_halign(Gtk.Align.END)  # Align buttons to the right
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
            self.original_frame_durations = []  # Store original durations
            self.current_frame_index = 0
            self.playhead_frame_index = 0
            
            with Image.open(file_path) as gif:
                frame_count = gif.n_frames
                total_duration = 0
                self.frames = []
                self.frame_durations = []  # Store frame durations
                self.original_frame_durations = []  # Keep original durations
                
                context = GLib.MainContext.default()
                for frame in range(frame_count):
                    # Update loading label
                    self.info_label.set_text(f"Loading frames {frame + 1}/{frame_count}")
                    # Process pending events
                    while context.pending():
                        context.iteration(False)
                    
                    gif.seek(frame)
                    duration = gif.info.get('duration', 100) / 1000.0
                    total_duration += duration
                    pixbuf = self._pil_to_pixbuf(gif.convert('RGBA'))
                    self.frames.append(pixbuf)
                    # Store duration in milliseconds
                    self.frame_durations.append(duration * 1000)
                    self.original_frame_durations.append(duration * 1000)  # Keep original
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
            self.original_frame_durations = []
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
                
                scaled_pixbuf = self.scale_pixbuf_to_fit(pixbuf, self.image_display_width, self.image_display_height)
                if scaled_pixbuf:
                    self.image_display.set_pixbuf(scaled_pixbuf)
                    # Force display update
                    self.image_display.queue_draw()

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

        start = int(round(self.frameline.left_value)) - 1
        end = int(round(self.frameline.right_value)) - 1
        is_reversed = start > end
        direction = -1 if is_reversed else 1

        # Get next valid frame, skipping removed ranges
        next_frame = self.frameline.get_next_valid_frame(
            self.current_frame_index, 
            direction
        )

        # Check if we've reached the end
        if next_frame == -1 or (direction > 0 and next_frame > end) or (direction < 0 and next_frame < end):
            self.is_playing = False
            self.update_play_button_icon(False)
            self.hide_playhead()
            self.frameline.playhead_visible = False
            if self.play_timeout_id:
                GLib.source_remove(self.play_timeout_id)
                self.play_timeout_id = None
            return False

        self.display_frame(next_frame)
        self.current_frame_index = next_frame
        self.playhead_frame_index = next_frame
        self.frameline.set_playhead_position(self.playhead_frame_index)

        # Schedule next frame
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
            dialog = Gtk.FileDialog()
            dialog.set_title("Save GIF as...")
            dialog.set_initial_name("untitled.gif")

            # Add file filter for .gif files
            filter_gif = Gtk.FileFilter()
            filter_gif.set_name("GIF files")
            filter_gif.add_mime_type("image/gif")
            filters = Gio.ListStore.new(Gtk.FileFilter)
            filters.append(filter_gif)
            dialog.set_filters(filters)
            dialog.set_default_filter(filter_gif)

            def save_callback(dialog, result):
                try:
                    file = dialog.save_finish(result)
                    if file:
                        save_path = file.get_path()
                        # Add .gif extension if not present
                        if not save_path.lower().endswith('.gif'):
                            save_path += '.gif'

                        # Check if file exists
                        if os.path.exists(save_path):
                            confirm_dialog = Gtk.AlertDialog()
                            confirm_dialog.set_message("File already exists. Do you want to overwrite it?")
                            confirm_dialog.set_modal(True)
                            confirm_dialog.set_buttons(["Cancel", "Overwrite"])
                            confirm_dialog.set_default_button(0)
                            confirm_dialog.set_cancel_button(0)

                            def confirm_callback(dialog, result):
                                try:
                                    response = dialog.choose_finish(result)
                                    if response == 1:  # "Overwrite" was chosen
                                        self._save_gif(save_path, start_idx, end_idx)
                                except GLib.Error as e:
                                    print(f"Error in confirmation dialog: {e}")

                            confirm_dialog.choose(
                                self.get_root(),
                                None,
                                confirm_callback
                            )
                        else:
                            self._save_gif(save_path, start_idx, end_idx)

                except GLib.Error as e:
                    # Only show error dialog if it's not a user dismissal
                    if not "Dismissed by user" in str(e):
                        print(f"Error saving file: {e}")
                        error_dialog = Gtk.AlertDialog()
                        error_dialog.set_message("Error saving file")
                        error_dialog.set_detail(str(e))
                        error_dialog.show(self.get_root())

            dialog.save(self.get_root(), None, save_callback)
        else:
            error_dialog = Gtk.AlertDialog()
            error_dialog.set_message("Invalid Frame Range")
            error_dialog.show(self.get_root())

    def _handle_overwrite_response(self, dialog, response, save_path, start_idx, end_idx):
        if response == Gtk.ResponseType.YES:
            self._save_gif(save_path, start_idx, end_idx)
        dialog.destroy()

    def _save_gif(self, save_path, start_idx, end_idx):
        """Save GIF including inserted frames and excluding removed ranges"""
        # Determine if we need to reverse the frames
        is_reversed = start_idx > end_idx
        if is_reversed:
            start_idx, end_idx = end_idx, start_idx

        # Get valid frames (excluding removed ranges)
        frames_to_save = []
        durations = []
        
        # Get reference dimensions from the first non-removed frame
        ref_frame = None
        for frame in self.frames:
            if frame:
                ref_frame = self._pixbuf_to_pil(frame)
                break
        
        if not ref_frame:
            return  # No valid frames to save
        
        ref_size = ref_frame.size
        
        for i in range(start_idx, end_idx + 1):
            # Skip if frame is removed
            if self.frameline.is_frame_removed(i):
                continue
                
            # Skip if index is out of bounds
            if i < 0 or i >= len(self.frames):
                continue
                
            # Skip if frame is None
            if not self.frames[i]:
                continue
            
            # Check if this frame is part of an inserted range
            is_inserted = any(start <= i <= end for start, end in self.frameline.inserted_ranges)
            
            # Get the frame and its duration
            frame = self._pixbuf_to_pil(self.frames[i])
            duration = self.frame_durations[i]
            
            # Resize inserted frames if needed
            if is_inserted and frame.size != ref_size:
                frame = frame.resize(ref_size, Image.Resampling.LANCZOS)
            
            frames_to_save.append(frame)
            durations.append(duration)

        # Reverse frames and durations if needed
        if is_reversed:
            frames_to_save.reverse()
            durations.reverse()

        if frames_to_save:  # Only save if we have valid frames
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
            
            # Only update display if frame is not removed
            if not frameline.is_frame_removed(frame_index):
                self.current_frame_index = frame_index
                self.display_frame(frame_index)

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

    def on_insert_frames(self, frameline, position, file_paths):
        try:
            new_frames = []
            new_durations = []
            
            # Load each image and get number of new frames
            for path in file_paths:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"File not found: {path}")
                
                with Image.open(path) as img:
                    if getattr(img, 'is_animated', False):
                        # Handle animated GIFs
                        for frame in range(img.n_frames):
                            img.seek(frame)
                            pixbuf = self._pil_to_pixbuf(img.convert('RGBA'))
                            new_frames.append(pixbuf)
                            new_durations.append(img.info.get('duration', 100))
                    else:
                        # Handle static images
                        pixbuf = self._pil_to_pixbuf(img.convert('RGBA'))
                        new_frames.append(pixbuf)
                        new_durations.append(100)  # Default 100ms duration
            
            if new_frames:
                insert_idx = max(0, position - 1)
                num_new_frames = len(new_frames)
                
                # Adjust speed ranges before inserting new frames
                updated_speed_ranges = []
                for start, end, speed in self.frameline.speed_ranges:
                    if insert_idx <= start:
                        # Speed range is after insertion point - shift it
                        updated_speed_ranges.append((start + num_new_frames, end + num_new_frames, speed))
                    elif insert_idx > end:
                        # Speed range is before insertion point - keep it unchanged
                        updated_speed_ranges.append((start, end, speed))
                    else:
                        # Speed range contains insertion point - split it into two parts
                        if start < insert_idx:
                            # Keep the part before insertion
                            updated_speed_ranges.append((start, insert_idx - 1, speed))
                        # Keep the part after insertion (shifted by the number of new frames)
                        updated_speed_ranges.append((insert_idx + num_new_frames, end + num_new_frames, speed))
                
                # Update speed ranges with adjusted positions
                self.frameline.speed_ranges = updated_speed_ranges
                
                # Insert new frames and durations
                self.frames[insert_idx:insert_idx] = new_frames
                self.frame_durations[insert_idx:insert_idx] = new_durations
                
                # Update frameline max value
                new_max = len(self.frames)
                self.frameline.max_value = new_max
                
                # If inserting at left handle, adjust right handle position
                if self.frameline.active_handle == 'left':
                    new_right = self.frameline.right_value + len(new_frames)
                    self.frameline.right_value = min(new_right, new_max)
                
                # Add to inserted ranges
                self.frameline.inserted_ranges.append((position, position + len(new_frames) - 1))
                
                # Update display
                self.frameline.queue_draw()
                self.display_frame(insert_idx)
                
                # Update info label
                total_duration = sum(self.frame_durations) / 1000.0
                self.info_label.set_text(
                    f"{len(self.frames)} Frames • {total_duration:.2f} Seconds"
                )
                
        except Exception as e:
            print(f"Error inserting frames: {e}")
            raise

    def on_speed_changed(self, frameline, start, end, speed_factor):
        """Handle speed change for the selected frame range"""
        try:
            # Convert from 1-based to 0-based indices
            start_idx = int(start) - 1
            end_idx = int(end) - 1
            
            # Ensure valid range and handle reversed ranges
            if start_idx > end_idx:
                start_idx, end_idx = end_idx, start_idx
                
            # Clamp indices to valid range
            start_idx = max(0, min(start_idx, len(self.frames) - 1))
            end_idx = max(0, min(end_idx, len(self.frames) - 1))
            
            # Initialize original_frame_durations if not already set
            if not hasattr(self, 'original_frame_durations'):
                self.original_frame_durations = self.frame_durations.copy()
            elif len(self.original_frame_durations) != len(self.frames):
                # Extend original_frame_durations for inserted frames
                inserted_count = len(self.frames) - len(self.original_frame_durations)
                self.original_frame_durations.extend(self.frame_durations[-inserted_count:])
            
            # Verify we have valid frames and durations
            if not self.frames or not self.frame_durations:
                print("Invalid frame data state")
                return
                
            # Adjust frame durations for the selected range
            for i in range(start_idx, end_idx + 1):
                if i < len(self.original_frame_durations):
                    self.frame_durations[i] = int(self.original_frame_durations[i] / speed_factor)
            
            # Add to frameline's speed ranges
            self.frameline.add_speed_range(start_idx, end_idx, speed_factor)
            
            # Sort ranges by start index
            self.frameline.speed_ranges.sort()
            
            # Merge only adjacent (not overlapping) ranges with same speed
            merged = []
            for range_start, range_end, speed in self.frameline.speed_ranges:
                if not merged or merged[-1][1] + 1 < range_start or merged[-1][2] != speed:
                    merged.append([range_start, range_end, speed])
                elif merged[-1][2] == speed:  # Only merge if speeds match
                    merged[-1][1] = max(merged[-1][1], range_end)
            self.frameline.speed_ranges = [tuple(x) for x in merged]
            
            # Update info label with new total duration
            total_duration = sum(self.frame_durations) / 1000.0
            self.info_label.set_text(
                f"{len(self.frames)} Frames • {total_duration:.2f} Seconds"
            )
            
            # If currently playing, restart playback to apply new speeds immediately
            if self.is_playing:
                self.stop_playback()
                self.play_edited_frames(None)
                
            # Trigger redraw of frameline
            self.frameline.queue_draw()
            
        except Exception as e:
            print(f"Error changing speed: {e}")
            import traceback
            traceback.print_exc()

    def stop_playback(self):
        """Stop current playback"""
        self.is_playing = False
        self.update_play_button_icon(False)
        if self.play_timeout_id:
            GLib.source_remove(self.play_timeout_id)
            self.play_timeout_id = None