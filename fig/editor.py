import os

from PIL import Image, ImageDraw
import gi

gi.require_version('Adw', '1')
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, GLib, Gio, GdkPixbuf, Adw

from fig.utils import clear_css, load_css
from fig.frameline import FrameLine
from fig.overlay import CropTextOverlay

class EditorBox(Gtk.Box):
    def __init__(self):
        super().__init__()
        self.BUTTON_HEIGHT = 40

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(0)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(80)
        self.set_margin_end(80)

        self.image_container = Gtk.Box()
        self.image_container.set_halign(Gtk.Align.CENTER)
        self.image_container.set_valign(Gtk.Align.CENTER)
        self.image_container.set_vexpand(True)

        self.image_display = Gtk.Picture()
        self.image_display.set_can_shrink(True)
        self.image_display.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.image_display.set_halign(Gtk.Align.CENTER)
        self.image_display.set_valign(Gtk.Align.CENTER)
        self.image_display.set_hexpand(True)
        load_css(self.image_display, ["image-display"])

        self.overlay = CropTextOverlay(self)
        self.image_container.append(self.overlay)
        self.overlay.set_child(self.image_display)

        self.info_label = Gtk.Label()
        self.info_label.set_margin_top(10)
        self.info_label.set_margin_bottom(10)
        self.info_label.set_halign(Gtk.Align.CENTER)
        self.append(self.info_label)

        action_button_size = (30, 30)

        self.flip_button = Gtk.Button(icon_name="view-mirror-symbolic")
        self.flip_button.set_tooltip_text("Flip")
        self.flip_button.set_size_request(action_button_size[0], action_button_size[1])
        self.flip_button.connect('clicked', self.on_flip_clicked)

        self.rotate_button = Gtk.Button(icon_name="object-rotate-right-symbolic")
        self.rotate_button.set_tooltip_text("Rotate")
        self.rotate_button.set_size_request(action_button_size[0], action_button_size[1])
        self.rotate_button.connect('clicked', self.on_rotate_clicked)

        self.text_button = Gtk.Button(icon_name="format-text-rich-symbolic")
        self.text_button.set_size_request(action_button_size[0], action_button_size[1])
        self.text_button.set_tooltip_text("Add Text")
        self.text_button.connect('clicked', self.on_text_clicked)

        # todo colors
        self.draw_button = Gtk.Button(icon_name="document-edit-symbolic")
        self.draw_button.set_tooltip_text("Draw")
        self.draw_button.set_size_request(action_button_size[0], action_button_size[1])
        self.draw_button.connect('clicked', self.on_draw_clicked)

        self.crop_button = Gtk.Button(icon_name="edit-select-all-symbolic")
        self.crop_button.set_tooltip_text("Crop")
        self.crop_button.set_size_request(action_button_size[0], action_button_size[1])
        self.crop_button.connect('clicked', self.on_crop_clicked)

        self.action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.action_bar.append(self.text_button)
        self.action_bar.append(self.crop_button)
        self.action_bar.append(self.flip_button)
        self.action_bar.append(self.rotate_button)
        self.action_bar.append(self.draw_button)
        self.action_bar.set_halign(Gtk.Align.CENTER)
        self.action_bar.set_margin_bottom(10)

        self.append(self.action_bar)
        self.append(self.image_container)

        self.controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.controls_box.set_margin_top(15)
        self.controls_box.set_margin_bottom(5)
        self.controls_box.set_margin_start(5)
        self.controls_box.set_margin_end(5)
        self.controls_box.set_vexpand(False)
        load_css(self.controls_box, ["controls-box-dark"])  # Initial dark theme

        self.frameline = FrameLine(self)
        self.frameline.set_hexpand(True)
        self.frameline.connect('frames-changed', self.on_frames_changed)
        self.frameline.connect('insert-frames', self.on_insert_frames)
        self.frameline.connect('speed-changed', self.on_speed_changed)
        self.controls_box.append(self.frameline)

        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        buttons_box.set_halign(Gtk.Align.END)  # Align buttons to the right

        self.play_btn = self.play_button()
        self.save_btn = self.save_button()
        self.loop_btn = self.loop_button()
        buttons_box.append(self.play_btn)
        buttons_box.append(self.loop_btn)
        buttons_box.append(self.save_btn)

        self.controls_box.append(buttons_box)

        self.append(self.controls_box)

        self.frames = []
        self.current_frame_index = 0
        self.playhead_frame_index = 0
        self.is_playing = False
        self.play_timeout_id = None
        self.playback_finished = False

        self.crop_mode = False
        self.text_mode = False
        self.draw_mode = False
        self.drawing = False
        self.last_point = None
        self.drawings = []
        self.apply_to_all_frames = True

        self.flipped = False
        self.is_dark = True
        self.rotated = False

        self.update_theme(is_dark=True)

        self.color_popover = Gtk.Popover()
        self.color_popover.set_parent(self.draw_button)

        color_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        color_box.set_margin_top(5)
        color_box.set_margin_bottom(5)
        color_box.set_margin_start(5)
        color_box.set_margin_end(5)

        colors = [
            ('#FFFFFF', 'White'),
            ('#000000', 'Black'),
            ('#FF0000', 'Red'),
            ('#57e389', 'Green'),
            ('#3584e4', 'Blue'),
            ('#FFFF00', 'Yellow'),
            # ('#FF00FF', 'Magenta'),
            # ('#00FFFF', 'Cyan'),
        ]

        self.current_draw_color = colors[0][0]
        for color_hex in colors:
            color_button = Gtk.Button()
            color_button.set_size_request(30, 30)
            color_button.add_css_class("color-button")

            css_provider = Gtk.CssProvider()
            css_data = f"""
                .color-button {{
                    background: {color_hex[0]};
                }}
            """
            css_provider.load_from_data(css_data.encode('utf-8'))
            color_button.get_style_context().add_provider(
                css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

            color_button.connect('clicked', self.on_color_selected, color_hex)
            color_box.append(color_button)

        self.color_popover.set_child(color_box)

        self.loop_playback = False

    def calculate_image_scale(self, image_width, image_height):
        """Set up a fixed square container based on the longer dimension"""
        # Determine the longer side of the image
        long_side = max(image_width, image_height)
        
        # Calculate scale to fit the longer dimension within reasonable bounds
        # Use the same logic as before, but apply it to the square container
        scale = 1
        
        # Set the square container size to the scaled longest dimension
        self.container_size = int(long_side * scale)
        
        # Store scale factor for drawings and text positioning
        self.IMAGE_SCALE = scale
        
        # Store original dimensions for reference
        self.original_width = image_width
        self.original_height = image_height

    def load_gif(self, file_path):
        """Load a GIF file using PIL for frame info and GdkPixbuf for display"""
        try:
            self.frames = []
            self.frame_durations = []
            self.original_frame_durations = []
            self.current_frame_index = 0
            self.playhead_frame_index = 0
            self.overlay.reset_crop_rect()

            # Get dimensions from the first frame
            with Image.open(file_path) as gif:
                # Store the original dimensions
                self.image_display_width, self.image_display_height = gif.size
                self.calculate_image_scale(self.image_display_width, self.image_display_height)
                
                # Set all containers to the fixed square size
                self.image_container.set_size_request(
                    self.container_size,
                    self.container_size)
                self.overlay.drawing_area.set_size_request(
                    self.container_size,
                    self.container_size)
                self.overlay.set_size_request(
                    self.container_size,
                    self.container_size)
                
                frame_count = gif.n_frames

            def load_frames_thread(batch_size=10):
                frames = []
                durations = []
                total_duration = 0
                update_batch = []

                with Image.open(file_path) as gif:
                    self.original_file_path = file_path
                    for frame in range(frame_count):
                        gif.seek(frame)
                        duration = gif.info.get('duration', 100) / 1000.0
                        total_duration += duration

                        # Convert to RGBA only if needed
                        if gif.mode != 'RGBA':
                            frame_image = gif.convert('RGBA')
                        else:
                            frame_image = gif

                        pixbuf = self._pil_to_pixbuf(frame_image)
                        frames.append(pixbuf)
                        durations.append(duration * 1000)

                        if len(update_batch) < batch_size and frame < frame_count - 1:
                            update_batch.append(frame)
                        else:
                            GLib.idle_add(
                                self.update_loading_progress,
                                frame + 1,
                                frame_count,
                                frames[:],
                                durations[:],
                                total_duration if frame == frame_count - 1 else None
                            )
                            update_batch = []

            self.info_label.set_text(f"Loading frames 0/{frame_count}")
            import threading
            thread = threading.Thread(target=load_frames_thread, args=(self.compute_batch_size(frame_count),))
            thread.daemon = True
            thread.start()

        except Exception as e:
            print(f"Error loading GIF: {e}")
            self.frames = []
            self.frame_durations = []
            self.original_frame_durations = []
            self.current_frame_index = 0
            self.playhead_frame_index = 0

    def compute_batch_size(self, frame_count):
        return frame_count // 4

    def update_loading_progress(self, current_frame, total_frames, frames, durations, total_duration=None):
        """Update loading progress from background thread"""
        self.frames = frames
        self.frame_durations = durations
        self.original_frame_durations = durations.copy()

        self.info_label.set_text(f"Loading frames {current_frame}/{total_frames}")

        # If this is the final update
        if total_duration is not None:
            # Update frameline with 1-based frame range
            self.frameline.min_value = 1
            self.frameline.max_value = total_frames
            self.frameline.left_value = 1
            self.frameline.right_value = total_frames
            self.frameline.queue_draw()

            self.info_label.set_text(
                f"{total_frames} Frames • {total_duration:.2f} Seconds"
            )

            if self.frames:
                self.display_frame(0)
                self.overlay.drawing_area.queue_resize()
                self.overlay.drawing_area.queue_draw()

        return False  # Required for GLib.idle_add

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

            if pixbuf:
                # Display the frame directly without scaling
                self.image_display.set_pixbuf(pixbuf)
                self.image_display.queue_draw()

        except Exception as e:
            print(f"Error displaying frame: {e}")

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

            # Always start from the left handle when starting new playback
            if not self.frameline.playhead_visible or self.playback_finished:
                self.current_frame_index = start
                self.playhead_frame_index = start

            self.display_frame(self.current_frame_index)
            self.show_playhead()
            self.frameline.set_playhead_pos(self.current_frame_index)
            self.play_next_frame()

    def play_next_frame(self):
        """Play the next frame in the sequence, with loop support."""
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
            if self.loop_playback:
                # Loop to the start
                self.current_frame_index = start
                self.playhead_frame_index = start
                self.display_frame(self.current_frame_index)
                self.show_playhead()
                self.frameline.set_playhead_pos(self.current_frame_index + 1)
                current_duration = self.frame_durations[self.current_frame_index]
                self.play_timeout_id = GLib.timeout_add(
                    current_duration, self.play_next_frame)
                return False
            else:
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
        self.frameline.set_playhead_pos(self.playhead_frame_index)

        # Schedule next frame
        current_duration = self.frame_durations[next_frame]
        self.play_timeout_id = GLib.timeout_add(
            current_duration, self.play_next_frame)
        return False


    def show_playhead(self):
        self.frameline.show_playhead()

    def hide_playhead(self):
        self.frameline.hide_playhead()

    def save_frames(self, button):
        """Save the selected frame range as a new GIF"""
        # Convert to 0-based index
        start_idx = int(round(self.frameline.left_value)) - 1
        end_idx = int(round(self.frameline.right_value)) - 1

        if 0 <= start_idx < len(self.frames) and 0 <= end_idx < len(self.frames):
            dialog = Gtk.FileDialog()
            dialog.set_title("Save GIF as...")

            filter_gif = Gtk.FileFilter()
            filter_gif.set_name("GIF files")
            filter_gif.add_mime_type("image/gif")
            filters = Gio.ListStore.new(Gtk.FileFilter)
            filters.append(filter_gif)
            dialog.set_filters(filters)
            dialog.set_default_filter(filter_gif)

            original_file_name = self.original_file_name if hasattr(self, 'original_file_name') else "untitled"  # Remove .fig
            dialog.set_initial_name(f"{original_file_name}-edited.gif")

            def save_callback(dialog, result):
                try:
                    file = dialog.save_finish(result)
                    if file:
                        save_path = file.get_path()
                        # Add .gif extension if not present
                        if not save_path.lower().endswith('.gif'):
                            save_path += '.gif'

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
        """Save GIF including inserted frames, drawings, and excluding removed ranges"""
        import traceback
        from PIL import Image, ImageDraw, ImageFont  # Move imports to the top of the method
        
        is_reversed = start_idx > end_idx
        if is_reversed:
            start_idx, end_idx = end_idx, start_idx

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

        # Calculate crop box in absolute pixels
        crop_rect = self.overlay.crop_rect
        orig_width, orig_height = ref_frame.size
        left = int(crop_rect[0] * orig_width)
        top = int(crop_rect[1] * orig_height)
        right = int((crop_rect[0] + crop_rect[2]) * orig_width)
        bottom = int((crop_rect[1] + crop_rect[3]) * orig_height)
        crop_box = (left, top, right, bottom)

        for i in range(start_idx, end_idx + 1):
            if self.frameline.is_frame_removed(i):
                continue
            if i < 0 or i >= len(self.frames):
                continue
            if not self.frames[i]:
                continue
            # Get the frame and its duration
            frame = self._pixbuf_to_pil(self.frames[i])
            duration = self.frame_durations[i]
            is_inserted = any(start <= i <= end for start, end in self.frameline.inserted_ranges)

            # For inserted frames, resize to match original size before cropping
            if is_inserted and frame.size != (orig_width, orig_height):
                frame = frame.resize((orig_width, orig_height), Image.Resampling.LANCZOS)

            draw = ImageDraw.Draw(frame)
            long_side = max(orig_width, orig_height)

            if self.drawings and self.drawings[0]:
                for line in self.drawings[0]:
                    if len(line['points']) > 1:
                        # Convert coordinates to image space
                        scaled_points = []
                        for point in line['points']:
                            if isinstance(point, (list, tuple)) and len(point) >= 2:
                                x, y = point[0], point[1]
                                if long_side == orig_width:
                                    y = y - (self.container_size - orig_height)/2
                                else:
                                    x = x - (self.container_size - orig_width)/2
                                scaled_points.append((x, y))

                        color = line.get('color', '#FFFFFF')
                        for j in range(len(scaled_points) - 1):  # Changed i to j to avoid variable shadowing
                            draw.line([scaled_points[j], scaled_points[j + 1]],
                                    fill=color, width=2)

            # Handle text with rotation
            for text_entry in self.overlay.text_entries:
                try:
                    x = int(text_entry['x'])
                    y = int(text_entry['y'])
                    text = text_entry['entry'].get_text()
                    
                    # Check if we need to apply rotation
                    if hasattr(self, 'text_rotation') and self.text_rotation != 0:
                        # Estimate text size - you might want to use a font that supports size measurement
                        # This is an approximation
                        font_size = 24  # Increased font size for better visibility
                        text_width = len(text) * font_size
                        text_height = font_size * 1.5
                        
                        # Create transparent image large enough for the rotated text
                        text_img = Image.new('RGBA', 
                                            (int(max(text_width, text_height) * 3), 
                                             int(max(text_width, text_height) * 3)), 
                                            (0, 0, 0, 0))
                        
                        # Draw text at the center of this new image
                        text_draw = ImageDraw.Draw(text_img)
                        text_draw.text((text_img.width//2, text_img.height//2), 
                                       text, 
                                       fill='white',
                                       anchor='mm')  # Center alignment
                        
                        # Rotate the text image
                        rotated_text = text_img.rotate(-self.text_rotation, 
                                                      resample=Image.BICUBIC, 
                                                      expand=True)
                        
                        # Calculate paste coordinates
                        paste_x = x
                        paste_y = y
                        
                        # Adjust for container padding
                        if long_side == orig_width:
                            paste_y -= (self.container_size - orig_height)//2
                        else:
                            paste_x -= (self.container_size - orig_width)//2
                        
                        # Adjust paste position to center the rotated text at the specified point
                        paste_x -= rotated_text.width//2
                        paste_y -= rotated_text.height//2
                        
                        # Paste using the alpha channel as mask
                        frame.paste(rotated_text, (paste_x, paste_y), rotated_text)
                    else:
                        if long_side == orig_width:
                            y = y - (self.container_size - orig_height)//2
                        else:
                            x = x - (self.container_size - orig_width)//2
                        # No rotation - draw text directly
                        draw.text((x, y), text, fill='white')
                except Exception as e:
                    print(f"Error drawing text: {e}")
                    traceback.print_exc()

            frame = frame.crop(crop_box)
            frames_to_save.append(frame)
            durations.append(duration)

        if is_reversed:
            frames_to_save.reverse()
            durations.reverse()

        if frames_to_save:
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
            if frameline.dragging_left:
                frame_index = int(round(frameline.left_value)) - 1
            else:
                frame_index = int(round(frameline.right_value)) - 1

            frame_index = max(0, min(frame_index, len(self.frames) - 1))

            if not frameline.is_frame_removed(frame_index):
                self.current_frame_index = frame_index
                self.display_frame(frame_index)
        self.update_info_label()


    def update_action_bar_button(self, set, button):
        """Update CSS class for action bar button"""
        from fig.utils import clear_css
        clear_css(button)
        if set:
            button.add_css_class("action-button-dark-active" if self.is_dark else "action-button-light-active")
        else:
            button.add_css_class("action-button-dark" if self.is_dark else "action-button-light")

    def on_flip_clicked(self, button):
        """Flip all frames horizontally"""
        # Reset any active editing modes
        if self.text_mode:
            self.text_mode = False
            self.overlay.text_mode = False
            self.update_action_bar_button(False, self.text_button)
            
        if self.draw_mode:
            self.draw_mode = False
            self.overlay.draw_mode = False
            self.update_action_bar_button(False, self.draw_button)
            
        if self.crop_mode:
            self.crop_mode = False
            self.overlay.handles_visible = False
            self.update_action_bar_button(False, self.crop_button)
        
        self.flipped = not self.flipped
        self.update_action_bar_button(self.flipped, button)

        if not self.frames:
            return
        try:
            for i, frame in enumerate(self.frames):
                if frame:
                    pil_image = self._pixbuf_to_pil(frame)
                    flipped = pil_image.transpose(Image.FLIP_LEFT_RIGHT)
                    self.frames[i] = self._pil_to_pixbuf(flipped)

            self.display_frame(self.current_frame_index)

        except Exception as e:
            print(f"Error flipping frames: {e}")
            error_dialog = Gtk.AlertDialog()
            error_dialog.set_message("Error flipping frames")
            error_dialog.set_detail(str(e))
            error_dialog.show(self.get_root())

    def on_rotate_clicked(self, button):
        """Rotate all frames 90 degrees clockwise"""
        # Reset any active editing modes
        if self.text_mode:
            self.text_mode = False
            self.overlay.text_mode = False
            self.update_action_bar_button(False, self.text_button)
            
        if self.draw_mode:
            self.draw_mode = False
            self.overlay.draw_mode = False
            self.update_action_bar_button(False, self.draw_button)
            
        if self.crop_mode:
            self.crop_mode = False
            self.overlay.handles_visible = False
            self.update_action_bar_button(False, self.crop_button)
            
        if not self.frames:
            return
        
        # Toggle the rotated state
        self.rotated = not self.rotated
        self.update_action_bar_button(self.rotated, button)
        
        try:
            # Swap dimensions (logical dimensions only, container stays the same)
            self.image_display_width, self.image_display_height = self.image_display_height, self.image_display_width
            
            # Rotate the frames' content
            for i, frame in enumerate(self.frames):
                if frame:
                    pil_image = self._pixbuf_to_pil(frame)
                    rotated = pil_image.transpose(Image.ROTATE_270)
                    self.frames[i] = self._pil_to_pixbuf(rotated)
            
            # Rotate all drawings if they exist
            if hasattr(self, 'drawings'):
                for frame_drawings in self.drawings:
                    for line in frame_drawings:
                        rotated_points = []
                        for point in line['points']:
                            x, y = point
                            final_x = self.container_size - y
                            final_y = x
                            rotated_points.append((final_x, final_y))
                        line['points'] = rotated_points
            
            # Handle text rotation
            if not hasattr(self, 'text_rotation'):
                self.text_rotation = 0
            
            self.text_rotation = (self.text_rotation + 90) % 360
            
            if hasattr(self.overlay, 'text_entries'):
                for text_entry in self.overlay.text_entries:
                    # Get current coordinates
                    x = text_entry['x']
                    y = text_entry['y']
                    
                    # Apply the same rotation transformation for position
                    final_y = x
                    final_x = self.container_size - y
                    
                    # Update the text entry coordinates
                    text_entry['x'] = final_x
                    text_entry['y'] = final_y
                    
                    # Update the actual widget position if it exists
                    if 'entry' in text_entry and text_entry['entry']:
                        entry_widget = text_entry['entry']
                        entry_widget.set_margin_start(int(final_x))
                        entry_widget.set_margin_top(int(final_y))
                        
                        # Apply rotation transform via CSS
                        css_provider = Gtk.CssProvider()
                        css_data = f"""
                            entry {{
                                transform: rotate({self.text_rotation}deg);
                                transform-origin: 0 0;
                            }}
                        """
                        css_provider.load_from_data(css_data.encode('utf-8'))
                        
                        style_context = entry_widget.get_style_context()
                        
                        if hasattr(entry_widget, 'rotation_provider'):
                            style_context.remove_provider(entry_widget.rotation_provider)
                        
                        style_context.add_provider(
                            css_provider,
                            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                        )
                        entry_widget.rotation_provider = css_provider
                        entry_widget.rotation_angle = self.text_rotation
            
            # Update display
            self.display_frame(self.current_frame_index)
            self.overlay.drawing_area.queue_draw()
            
        except Exception as e:
            print(f"Error rotating frames: {e}")
            import traceback
            traceback.print_exc()
            error_dialog = Gtk.AlertDialog()
            error_dialog.set_message("Error rotating frames")
            error_dialog.set_detail(str(e))
            error_dialog.show(self.get_root())

    def save_button(self):
        save_button = Gtk.Button(label="Save")
        save_button.set_size_request(80, self.BUTTON_HEIGHT)
        save_button.set_valign(Gtk.Align.CENTER)
        save_button.set_halign(Gtk.Align.CENTER)
        save_button.connect('clicked', self.save_frames)
        return save_button

    def play_button(self):
        play_button = Gtk.Button()
        play_button.set_size_request(40, self.BUTTON_HEIGHT)
        play_button.set_valign(Gtk.Align.CENTER)
        play_button.set_halign(Gtk.Align.CENTER)
        play_button.connect('clicked', self.play_edited_frames)

        icon_name = "media-playback-start-symbolic"
        icon = Gio.ThemedIcon(name=icon_name)
        image = Gtk.Image.new_from_gicon(icon)
        play_button.set_child(image)

        return play_button

    def loop_button(self):
        loop_button = Gtk.Button()
        loop_button.set_size_request(40, self.BUTTON_HEIGHT)
        loop_button.set_valign(Gtk.Align.CENTER)
        loop_button.set_halign(Gtk.Align.CENTER)
        loop_button.connect('clicked', self.toggle_loop)

        icon_name = "media-playlist-repeat-symbolic"
        icon = Gio.ThemedIcon(name=icon_name)
        image = Gtk.Image.new_from_gicon(icon)
        loop_button.set_child(image)

        return loop_button

    def update_theme(self, is_dark):
        """Update theme for all buttons"""
        self.is_dark = is_dark
        from fig.utils import clear_css

        clear_css(self.save_btn)
        self.save_btn.add_css_class("save-button-dark" if is_dark else "save-button-light")

        clear_css(self.play_btn)
        self.play_btn.add_css_class("play-button-dark" if is_dark else "play-button-light")

        clear_css(self.loop_btn)
        self.loop_btn.add_css_class("loop-button-dark" if is_dark else "loop-button-light")

        clear_css(self.info_label)
        self.info_label.add_css_class("info-label-dark" if is_dark else "info-label-light")

        clear_css(self.controls_box)
        self.controls_box.add_css_class("controls-box-dark" if is_dark else "controls-box-light")

        clear_css(self.action_bar)
        self.action_bar.add_css_class("action-bar-dark" if is_dark else "action-bar-light")

        clear_css(self.flip_button)
        if self.flipped:
            self.flip_button.add_css_class("action-button-dark-active" if is_dark else "action-button-light-active")
        else:
            self.flip_button.add_css_class("action-button-dark" if is_dark else "action-button-light")

        clear_css(self.crop_button)
        if self.crop_mode:
            self.crop_button.add_css_class("action-button-dark-active" if is_dark else "action-button-light-active")
        else:
            self.crop_button.add_css_class("action-button-dark" if is_dark else "action-button-light")

        clear_css(self.rotate_button)
        if self.rotated:
            self.rotate_button.add_css_class("action-button-dark-active" if is_dark else "action-button-light-active")
        else:
            self.rotate_button.add_css_class("action-button-dark" if is_dark else "action-button-light")

        clear_css(self.text_button)
        if self.text_mode:
            self.text_button.add_css_class("action-button-dark-active" if is_dark else "action-button-light-active")
        else:
            self.text_button.add_css_class("action-button-dark" if is_dark else "action-button-light")

        clear_css(self.draw_button)
        if self.draw_mode:
            self.draw_button.add_css_class("action-button-dark-active" if is_dark else "action-button-light-active")
        else:
            self.draw_button.add_css_class("action-button-dark" if is_dark else "action-button-light")

        self.frameline.update_theme(is_dark)
        self.overlay.update_theme(is_dark)

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

                self.frameline.speed_ranges = updated_speed_ranges
                self.frames[insert_idx:insert_idx] = new_frames
                self.frame_durations[insert_idx:insert_idx] = new_durations
                new_max = len(self.frames)
                self.frameline.max_value = new_max

                # If inserting at left handle, adjust right handle position
                if self.frameline.active_handle == 'left':
                    new_right = self.frameline.right_value + len(new_frames)
                    self.frameline.right_value = min(new_right, new_max)

                # --- Update inserted_ranges (shift ranges after insertion) ---
                updated_inserted_ranges = []
                for start, end in self.frameline.inserted_ranges:
                    if start > insert_idx:
                        # Range is after insertion point - shift it
                        updated_inserted_ranges.append((start + num_new_frames, end + num_new_frames))
                    elif end < insert_idx:
                        # Range is before insertion point - keep it unchanged
                        updated_inserted_ranges.append((start, end))
                    else:
                        # Range overlaps insertion point - split or shift as needed
                        # For simplicity, shift the part after insertion
                        if start < insert_idx:
                            updated_inserted_ranges.append((start, insert_idx - 1))
                        updated_inserted_ranges.append((insert_idx + num_new_frames, end + num_new_frames))

                self.frameline.inserted_ranges = updated_inserted_ranges
                # Append the new inserted range
                self.frameline.inserted_ranges.append((position, position + len(new_frames) - 1))
                
                for i, r in enumerate(self.frameline.removed_ranges):
                    # Shift removed ranges after insertion point
                    if r[0] >= insert_idx:
                        self.frameline.removed_ranges[i] = (r[0] + num_new_frames, r[1] + num_new_frames)

                self.frameline.queue_draw()
                self.display_frame(insert_idx)
                self.update_info_label()

        except Exception as e:
            print(f"Error inserting frames: {e}")
            raise

    def on_speed_changed(self, frameline, start, end, speed_factor):
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

            # Warn if any frame duration in the affected range is < 10ms
            min_duration = min(self.frame_durations[start_idx:end_idx+1]) if self.frame_durations[start_idx:end_idx+1] else 1000
            if min_duration < 10:
                # Compute the maximum applicable speedup for this range
                if hasattr(self, 'original_frame_durations') and self.original_frame_durations:
                    min_orig = min(self.original_frame_durations[i] for i in range(start_idx, end_idx+1))
                    max_speedup = round(min_orig / 10.0, 2)
                else:
                    max_speedup = 'N/A'
                alert = Adw.AlertDialog()
                alert.set_heading("Warning: GIF May Lag")
                alert.set_body(
                    f"At least one frame duration is less than 10ms. "
                    f"GIF may be laggy or not play smoothly in some viewers when exported.\n\n"
                    f"Maximum applicable speedup for this GIF: {max_speedup}x"
                )
                alert.add_response("ok", "Proceed Anyway")
                alert.add_response("cancel", "Cancel Change")
                alert.set_default_response("ok")
                alert.set_close_response("cancel")
                def on_response(dialog, response_id):
                    if response_id == "cancel":
                        # Revert the frame durations in the affected range
                        for i in range(start_idx, end_idx + 1):
                            if i < len(self.original_frame_durations):
                                self.frame_durations[i] = self.original_frame_durations[i]
                        # Remove the speed range for the affected region
                        self.frameline.speed_ranges = [
                            (s, e, spd) for s, e, spd in self.frameline.speed_ranges
                            if not (s == start_idx and e == end_idx)
                        ]
                        self.update_info_label()
                        self.frameline.queue_draw()
                alert.connect("response", on_response)
                alert.present(self.get_root())
            else:
                # Remove speed range if speed factor is 1.0
                if speed_factor == 1.0:
                    self.frameline.speed_ranges = [
                        (s, e, spd) for s, e, spd in self.frameline.speed_ranges
                        if not (s == start_idx and e == end_idx)
                    ]
                else:
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
                self.update_info_label()

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

    def reset(self):
        """Reset editor state"""
        self.frames = []
        self.frame_durations = []
        self.original_frame_durations = []
        self.current_frame_index = 0
        self.playhead_frame_index = 0
        self.is_playing = False
        self.play_timeout_id = None
        self.playback_finished = False
        
        # Reset editing states
        self.crop_mode = False
        self.text_mode = False
        self.draw_mode = False
        self.drawing = False
        self.last_point = None
        
        # Reset overlays
        self.overlay.text_mode = False
        self.overlay.draw_mode = False
        self.overlay.handles_visible = False
        self.overlay.remove_all_text_entries()
        self.overlay.reset_crop_rect()
        
        # Clear drawings
        self.drawings = [[]]
        
        # Reset transformations
        self.flipped = False
        self.rotated = False
        if hasattr(self, 'text_rotation'):
            self.text_rotation = 0
            
        # Reset UI button states
        self.update_action_bar_button(False, self.crop_button)
        self.update_action_bar_button(False, self.text_button)
        self.update_action_bar_button(False, self.draw_button) 
        self.update_action_bar_button(False, self.flip_button)
        self.update_action_bar_button(False, self.rotate_button)
        
        # Reset frameline and display
        self.frameline.reset()
        self.info_label.set_text("")
        self.image_display.set_pixbuf(None)
        self.image_display.queue_draw()
        self.overlay.drawing_area.queue_draw()
        self.queue_draw()

    def _pil_to_pixbuf(self, pil_image):
        """Convert PIL image to GdkPixbuf more efficiently"""
        # Get image data
        width, height = pil_image.size
        data = pil_image.tobytes()

        # Create pixbuf directly from data
        has_alpha = pil_image.mode == 'RGBA'
        colorspace = GdkPixbuf.Colorspace.RGB
        bps = 8
        rowstride = width * (4 if has_alpha else 3)

        return GdkPixbuf.Pixbuf.new_from_data(
            data,
            colorspace,
            has_alpha,
            bps,
            width,
            height,
            rowstride
        )

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
        self.play_btn.set_child(image)

    def update_info_label(self):
        """Update info label with current frame count and total duration"""
        try:
            # Only include frames from left handle to right handle
            left_value = int(round(self.frameline.left_value)) - 1
            right_value = int(round(self.frameline.right_value)) - 1

            valid_frame_count = sum(
                not self.frameline.is_frame_removed(i) for i in range(left_value, right_value + 1)
            )

            # Calculate total duration from current frame durations
            total_duration = sum(
                self.frame_durations[i] for i in range(left_value, right_value + 1)
                if not self.frameline.is_frame_removed(i)
            ) / 1000.0  # Convert to seconds

            self.info_label.set_text(
                f"{valid_frame_count} Frames • {total_duration:.2f} Seconds"
            )
        except Exception as e:
            print(f"Error updating info label: {e}")

    def on_crop_clicked(self, button):
        # Reset other modes first
        if self.text_mode:
            self.text_mode = False
            self.overlay.text_mode = False
            self.update_action_bar_button(False, self.text_button)
        
        if self.draw_mode:
            self.draw_mode = False
            self.overlay.draw_mode = False
            self.update_action_bar_button(False, self.draw_button)
            
        # Now toggle crop mode
        if self.crop_mode:
            self.crop_mode = False
            self.overlay.reset_crop_rect()
        else:
            self.crop_mode = True
            self.overlay.handles_visible = True
        self.update_action_bar_button(self.crop_mode, button)
        self.overlay.drawing_area.queue_draw()

    def on_text_clicked(self, button):
        """Toggle text editing mode"""
        if self.draw_mode:
            self.draw_mode = False
            self.overlay.draw_mode = False
            self.update_action_bar_button(False, self.draw_button)

        self.text_mode = not self.text_mode
        self.update_action_bar_button(self.text_mode, button)

        if self.text_mode:
            self.crop_mode = False
            self.overlay.handles_visible = False
            self.overlay.text_mode = True
            self.overlay.drawing_area.queue_draw()
        else:
            self.overlay.handles_visible = False
            self.overlay.text_mode = False
            self.overlay.drawing_area.queue_draw()

    def on_draw_clicked(self, button):
        """Toggle drawing mode and show color popover"""
        if self.text_mode:
            self.text_mode = False
            self.overlay.text_mode = False
            self.update_action_bar_button(False, self.text_button)

        if not self.draw_mode:
            self.color_popover.popup()

        self.draw_mode = not self.draw_mode
        self.update_action_bar_button(self.draw_mode, button)

        if self.draw_mode:
            self.crop_mode = False
            self.overlay.handles_visible = False
            self.overlay.draw_mode = True
            
            if not hasattr(self, 'drawings'):
                self.drawings = [[]]  # Start with empty list for first frame
        else:
            self.overlay.draw_mode = False

        self.overlay.drawing_area.queue_draw()

    def on_color_selected(self, button, color):
        """Handle color selection"""
        self.current_draw_color = color[0]
        self.color_popover.popdown()

    def toggle_loop(self, button):
        """Toggle looping playback on/off."""
        self.loop_playback = not self.loop_playback
        if self.loop_playback:
            self.loop_btn.add_css_class("loop-button-active")
        else:
            self.loop_btn.remove_css_class("loop-button-active")
