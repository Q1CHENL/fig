
from fig.overlay import CropTextOverlay
from fig.frameline import FrameLine
from fig.action_bar import EditorActionBar
from fig.playback_controls import PlaybackControls
from fig.utils import load_css, clear_css
from fig.image_converter import ImageConverter
from fig.gif_loader import GifLoader, LoadProgress, LoadResult
from fig.frame_processor import FrameProcessor, ProcessingOptions
from fig.constants import EditorConstants
from fig.state import EditorState
from fig.colorpicker import ColorPicker
import os
from PIL import Image
import gi
gi.require_version('Adw', '1')
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, GLib, Gio, Adw


class EditorBox(Gtk.Box):
    def __init__(self):
        super().__init__()
        self.BUTTON_HEIGHT = EditorConstants.BUTTON_HEIGHT

        # Initialize state management
        self.state = EditorState()

        # Initialize GIF loader and frame processor
        self.gif_loader = GifLoader()
        self.frame_processor = FrameProcessor()

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(0)
        self.set_margin_top(EditorConstants.MARGIN_TOP_BOTTOM)
        self.set_margin_bottom(EditorConstants.MARGIN_TOP_BOTTOM)
        self.set_margin_start(EditorConstants.MARGIN_START_END)
        self.set_margin_end(EditorConstants.MARGIN_START_END)

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
        load_css(self.image_display, [EditorConstants.CSS_IMAGE_DISPLAY])

        self.overlay = CropTextOverlay(self)
        self.image_container.append(self.overlay)
        self.overlay.set_child(self.image_display)

        self.info_label = Gtk.Label()
        self.info_label.set_margin_top(EditorConstants.INFO_LABEL_MARGIN)
        self.info_label.set_margin_bottom(EditorConstants.INFO_LABEL_MARGIN)
        self.info_label.set_halign(Gtk.Align.CENTER)
        self.append(self.info_label)

        # Create action bar with all editing buttons
        self.action_bar = EditorActionBar(self)

        # Keep references to individual buttons for compatibility
        self.flip_button = self.action_bar.flip_button
        self.rotate_button = self.action_bar.rotate_button
        self.text_button = self.action_bar.text_button
        self.draw_button = self.action_bar.draw_button
        self.crop_button = self.action_bar.crop_button

        self.append(self.action_bar)
        self.append(self.image_container)

        self.controls_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=EditorConstants.CONTROLS_BOX_SPACING)
        self.controls_box.set_margin_top(
            EditorConstants.CONTROLS_BOX_MARGIN_TOP)
        self.controls_box.set_margin_bottom(
            EditorConstants.CONTROLS_BOX_MARGIN_BOTTOM)
        self.controls_box.set_margin_start(
            EditorConstants.CONTROLS_BOX_MARGIN_SIDE)
        self.controls_box.set_margin_end(
            EditorConstants.CONTROLS_BOX_MARGIN_SIDE)
        self.controls_box.set_vexpand(False)
        # Initial dark theme
        load_css(self.controls_box, [EditorConstants.CSS_CONTROLS_BOX_DARK])

        self.frameline = FrameLine(self)
        self.frameline.set_hexpand(True)
        self.frameline.connect('frames-changed', self.on_frames_changed)
        self.frameline.connect('insert-frames', self.on_insert_frames)
        self.frameline.connect('speed-changed', self.on_speed_changed)
        self.controls_box.append(self.frameline)

        # Create playback controls
        self.playback_controls = PlaybackControls(self)

        # Keep references to individual buttons for compatibility
        self.play_btn = self.playback_controls.play_btn
        self.save_btn = self.playback_controls.save_btn
        self.loop_btn = self.playback_controls.loop_btn

        self.controls_box.append(self.playback_controls)

        self.append(self.controls_box)

        # Initialize color picker for drawing
        self.color_picker = ColorPicker(
            parent_widget=self.draw_button,
            on_color_selected_callback=self.on_color_selected
        )
        # Set initial color in state
        self.state.current_draw_color = self.color_picker.get_current_color()

        # Initialize theme
        self.update_theme(is_dark=True)

    def calculate_image_scale(self, image_width, image_height):
        """Set up a fixed square container based on the longer dimension"""
        # Use the state method to set dimensions and calculate scale
        self.state.set_image_dimensions(image_width, image_height)

    def load_gif(self, file_path):
        """Load a GIF file using the new GifLoader class"""
        try:
            # Reset state
            self.state.frames = []
            self.state.frame_durations = []
            self.state.original_frame_durations = []
            self.state.current_frame_index = EditorConstants.DEFAULT_FRAME_INDEX
            self.state.playhead_frame_index = EditorConstants.DEFAULT_FRAME_INDEX
            self.overlay.reset_crop_rect()

            # Get image info for initial setup
            width, height, frame_count = GifLoader.get_image_info(file_path)

            # Store the original dimensions and calculate scale
            self.calculate_image_scale(width, height)

            # Set all containers to the fixed square size
            self.image_container.set_size_request(
                self.state.container_size,
                self.state.container_size)
            self.overlay.drawing_area.set_size_request(
                self.state.container_size,
                self.state.container_size)
            self.overlay.set_size_request(
                self.state.container_size,
                self.state.container_size)

            # Start loading
            self.info_label.set_text(
                EditorConstants.LOADING_MESSAGE_TEMPLATE.format(current=0, total=frame_count))

            self.gif_loader.load_gif_async(
                file_path=file_path,
                progress_callback=self._on_loading_progress,
                completion_callback=self._on_loading_complete
            )

        except Exception as e:
            print(f"Error loading GIF: {e}")
            self._reset_loading_state()

    def _on_loading_progress(self, progress: LoadProgress):
        """Handle loading progress updates"""
        self.state.frames = progress.frames
        self.state.frame_durations = progress.durations
        self.state.original_frame_durations = progress.durations.copy()

        self.info_label.set_text(
            EditorConstants.LOADING_MESSAGE_TEMPLATE.format(current=progress.current_frame, total=progress.total_frames))

        # If this is the final update
        if progress.total_duration is not None:
            # Update frameline with 1-based frame range
            self.frameline.min_value = 1
            self.frameline.max_value = progress.total_frames
            self.frameline.left_value = 1
            self.frameline.right_value = progress.total_frames
            self.frameline.queue_draw()

            self.info_label.set_text(
                EditorConstants.FRAME_INFO_TEMPLATE.format(
                    frames=progress.total_frames, duration=progress.total_duration)
            )

            if self.state.frames:
                self.display_frame(EditorConstants.DEFAULT_FRAME_INDEX)
                self.overlay.drawing_area.queue_resize()
                self.overlay.drawing_area.queue_draw()

    def _on_loading_complete(self, result: LoadResult = None, error: Exception = None):
        """Handle loading completion"""
        if error:
            print(f"Error loading GIF: {error}")
            self._reset_loading_state()

            # Show error dialog
            error_dialog = Gtk.AlertDialog()
            error_dialog.set_message(EditorConstants.ERROR_LOADING_GIF)
            error_dialog.set_detail(str(error))
            error_dialog.show(self.get_root())
        elif result:
            # Store file information
            self.state.original_file_path = result.file_path
            # Extract filename without extension for saving
            filename = os.path.basename(result.file_path)
            self.state.original_file_name = os.path.splitext(filename)[0]

    def _reset_loading_state(self):
        """Reset loading state on error"""
        self.state.frames = []
        self.state.frame_durations = []
        self.state.original_frame_durations = []
        self.state.current_frame_index = EditorConstants.DEFAULT_FRAME_INDEX
        self.state.playhead_frame_index = EditorConstants.DEFAULT_FRAME_INDEX

    def display_frame(self, frame_index):
        """Display a specific frame in the image display"""
        if not self.state.frames or not (0 <= frame_index < len(self.state.frames)):
            print(f"Frame is not displayed: {frame_index}")
            return

        try:
            self.state.current_frame_index = frame_index
            frame = self.state.frames[frame_index]

            if isinstance(frame, Image.Image):
                pixbuf = ImageConverter.pil_to_pixbuf(frame)
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
        if self.state.is_playing:
            # Just pause at current position
            self.state.is_playing = False
            self.update_play_button_icon(False)
            if self.state.play_timeout_id:
                GLib.source_remove(self.state.play_timeout_id)
                self.state.play_timeout_id = None
        else:
            # Start/resume playing
            self.state.is_playing = True
            # Reset the finished flag when starting playback
            self.state.playback_finished = False
            self.update_play_button_icon(True)

            # Get current frame range
            start = int(round(self.frameline.left_value)) - 1

            # Always start from the left handle when starting new playback
            if not self.frameline.playhead_visible or self.state.playback_finished:
                self.state.current_frame_index = start
                self.state.playhead_frame_index = start

            self.display_frame(self.state.current_frame_index)
            self.show_playhead()
            self.frameline.set_playhead_pos(self.state.current_frame_index)
            self.play_next_frame()

    def play_next_frame(self):
        """Play the next frame in the sequence, with loop support."""
        if not self.state.is_playing:
            return False

        start = int(round(self.frameline.left_value)) - 1
        end = int(round(self.frameline.right_value)) - 1
        is_reversed = start > end
        direction = -1 if is_reversed else 1

        # Get next valid frame, skipping removed ranges
        next_frame = self.frameline.get_next_valid_frame(
            self.state.current_frame_index,
            direction
        )

        # Check if we've reached the end
        if next_frame == -1 or (direction > 0 and next_frame > end) or (direction < 0 and next_frame < end):
            if self.state.loop_playback:
                # Loop to the start
                self.state.current_frame_index = start
                self.state.playhead_frame_index = start
                self.display_frame(self.state.current_frame_index)
                self.show_playhead()
                self.frameline.set_playhead_pos(
                    self.state.current_frame_index + 1)
                current_duration = self.state.frame_durations[self.state.current_frame_index]
                self.state.play_timeout_id = GLib.timeout_add(
                    current_duration, self.play_next_frame)
                return False
            else:
                self.state.is_playing = False
                self.update_play_button_icon(False)
                self.hide_playhead()
                self.frameline.playhead_visible = False
                if self.state.play_timeout_id:
                    GLib.source_remove(self.state.play_timeout_id)
                    self.state.play_timeout_id = None
                return False

        self.display_frame(next_frame)
        self.state.current_frame_index = next_frame
        self.state.playhead_frame_index = next_frame
        self.frameline.set_playhead_pos(self.state.playhead_frame_index)

        # Schedule next frame
        current_duration = self.state.frame_durations[next_frame]
        self.state.play_timeout_id = GLib.timeout_add(
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

        if 0 <= start_idx < len(self.state.frames) and 0 <= end_idx < len(self.state.frames):
            dialog = Gtk.FileDialog()
            dialog.set_title(EditorConstants.SAVE_DIALOG_TITLE)

            filter_gif = Gtk.FileFilter()
            filter_gif.set_name(EditorConstants.GIF_FILTER_NAME)
            filter_gif.add_mime_type("image/gif")
            filters = Gio.ListStore.new(Gtk.FileFilter)
            filters.append(filter_gif)
            dialog.set_filters(filters)
            dialog.set_default_filter(filter_gif)

            original_file_name = self.state.original_file_name if hasattr(
                self.state, 'original_file_name') else EditorConstants.DEFAULT_FILENAME
            dialog.set_initial_name(
                f"{original_file_name}{EditorConstants.DEFAULT_SAVE_SUFFIX}{EditorConstants.GIF_EXTENSION}")

            def save_callback(dialog, result):
                try:
                    file = dialog.save_finish(result)
                    if file:
                        save_path = file.get_path()
                        # Add .gif extension if not present
                        if not save_path.lower().endswith(EditorConstants.GIF_EXTENSION):
                            save_path += EditorConstants.GIF_EXTENSION

                        self._save_gif(save_path, start_idx, end_idx)

                except GLib.Error as e:
                    # Only show error dialog if it's not a user dismissal
                    if "Dismissed by user" not in str(e):
                        print(f"Error saving file: {e}")
                        error_dialog = Gtk.AlertDialog()
                        error_dialog.set_message(
                            EditorConstants.ERROR_SAVING_FILE)
                        error_dialog.set_detail(str(e))
                        error_dialog.show(self.get_root())

            dialog.save(self.get_root(), None, save_callback)
        else:
            error_dialog = Gtk.AlertDialog()
            error_dialog.set_message(EditorConstants.INVALID_FRAME_RANGE)
            error_dialog.show(self.get_root())

    def _handle_overwrite_response(self, dialog, response, save_path, start_idx, end_idx):
        if response == Gtk.ResponseType.YES:
            self._save_gif(save_path, start_idx, end_idx)
        dialog.destroy()

    def _save_gif(self, save_path, start_idx, end_idx):
        """Save GIF using FrameProcessor for consistent processing"""
        try:
            # Prepare processing options
            processing_options = ProcessingOptions(
                crop_rect=self.overlay.crop_rect,
                container_size=self.state.container_size,
                text_rotation=getattr(self.state, 'text_rotation', 0)
            )

            # Prepare excluded ranges (removed frames)
            excluded_ranges = []
            for i, frame in enumerate(self.state.frames):
                if self.frameline.is_frame_removed(i):
                    excluded_ranges.append((i, i))

            # Prepare text entries for processing
            text_entries = []
            if hasattr(self.overlay, 'text_entries'):
                for text_entry in self.overlay.text_entries:
                    if 'entry' in text_entry and text_entry['entry']:
                        text_entries.append({
                            'x': text_entry.get('x', 0),
                            'y': text_entry.get('y', 0),
                            'text': text_entry['entry'].get_text()
                        })

            # Use FrameProcessor to handle the entire save operation
            self.frame_processor.process_and_save_gif(
                frames=self.state.frames,
                durations=self.state.frame_durations,
                save_path=save_path,
                start_idx=start_idx,
                end_idx=end_idx,
                excluded_ranges=excluded_ranges,
                inserted_ranges=getattr(self.frameline, 'inserted_ranges', []),
                drawings=getattr(self.state, 'drawings', None),
                text_entries=text_entries,
                processing_options=processing_options
            )

        except Exception as e:
            print(f"Error saving GIF: {e}")
            import traceback
            traceback.print_exc()
            # Re-raise to allow calling code to handle
            raise

    def on_frames_changed(self, frameline, start, end):
        """Handle frame range changes from the frameline"""
        if not self.state.frames:
            return

        # Convert 1-based frame numbers to 0-based indices
        start_frame_index = int(round(start)) - 1
        end_frame_index = int(round(end)) - 1

        # Ensure we're within valid frame range
        start_frame_index = max(
            0, min(start_frame_index, len(self.state.frames) - 1))
        end_frame_index = max(
            0, min(end_frame_index, len(self.state.frames) - 1))

        # Update display during dragging if not previously playing
        if (frameline.dragging_left or frameline.dragging_right) and not frameline.playhead_visible:
            if frameline.dragging_left:
                frame_index = int(round(frameline.left_value)) - 1
            else:
                frame_index = int(round(frameline.right_value)) - 1

            frame_index = max(0, min(frame_index, len(self.state.frames) - 1))

            if not frameline.is_frame_removed(frame_index):
                self.state.current_frame_index = frame_index
                self.display_frame(frame_index)
        self.update_info_label()

    def update_action_bar_button(self, set, button):
        """Update CSS class for action bar button"""
        self.action_bar.update_button_state(button, set)

    def on_flip_clicked(self, button):
        """Flip all frames horizontally"""
        # Reset any active editing modes
        if self.state.text_mode:
            self.state.text_mode = False
            self.overlay.text_mode = False
            self.update_action_bar_button(False, self.text_button)

        if self.state.draw_mode:
            self.state.draw_mode = False
            self.overlay.draw_mode = False
            self.update_action_bar_button(False, self.draw_button)

        if self.state.crop_mode:
            self.state.crop_mode = False
            self.overlay.handles_visible = False
            self.update_action_bar_button(False, self.crop_button)

        self.state.flipped = not self.state.flipped
        self.update_action_bar_button(self.state.flipped, button)

        if not self.state.frames:
            return
        try:
            # Use FrameProcessor to flip frames
            self.state.frames = self.frame_processor.flip_frames_horizontal(
                self.state.frames)
            self.display_frame(self.state.current_frame_index)

        except Exception as e:
            print(f"Error flipping frames: {e}")
            error_dialog = Gtk.AlertDialog()
            error_dialog.set_message(EditorConstants.ERROR_FLIPPING_FRAMES)
            error_dialog.set_detail(str(e))
            error_dialog.show(self.get_root())

    def on_rotate_clicked(self, button):
        """Rotate all frames 90 degrees clockwise"""
        # Reset any active editing modes
        if self.state.text_mode:
            self.state.text_mode = False
            self.overlay.text_mode = False
            self.update_action_bar_button(False, self.text_button)

        if self.state.draw_mode:
            self.state.draw_mode = False
            self.overlay.draw_mode = False
            self.update_action_bar_button(False, self.draw_button)

        if self.state.crop_mode:
            self.state.crop_mode = False
            self.overlay.handles_visible = False
            self.update_action_bar_button(False, self.crop_button)

        if not self.state.frames:
            return

        # Toggle the rotated state
        self.state.rotated = not self.state.rotated
        self.update_action_bar_button(self.state.rotated, button)

        try:
            # Swap dimensions (logical dimensions only, container stays the same)
            self.state.image_display_width, self.state.image_display_height = self.state.image_display_height, self.state.image_display_width

            # Use FrameProcessor to rotate frames
            self.state.frames = self.frame_processor.rotate_frames_90(
                self.state.frames)

            # Rotate all drawings if they exist
            if hasattr(self.state, 'drawings'):
                self.state.drawings = self.frame_processor.rotate_drawings(
                    self.state.drawings, self.state.container_size)

            # Handle text rotation
            self.state.text_rotation = (
                self.state.text_rotation + EditorConstants.ROTATION_DEGREES) % EditorConstants.FULL_CIRCLE_DEGREES

            if hasattr(self.overlay, 'text_entries'):
                rotated_entries, rotation_increment = self.frame_processor.rotate_text_entries(
                    self.overlay.text_entries, self.state.container_size)

                # Update the entries
                for i, rotated_entry in enumerate(rotated_entries):
                    if i < len(self.overlay.text_entries):
                        self.overlay.text_entries[i].update(rotated_entry)

                        # Update the actual widget position if it exists
                        if 'entry' in self.overlay.text_entries[i] and self.overlay.text_entries[i]['entry']:
                            entry_widget = self.overlay.text_entries[i]['entry']
                            entry_widget.set_margin_start(
                                int(rotated_entry['x']))
                            entry_widget.set_margin_top(
                                int(rotated_entry['y']))

                            # Apply rotation transform via CSS
                            css_provider = Gtk.CssProvider()
                            css_data = f"""
                                entry {{
                                    transform: rotate({self.state.text_rotation}deg);
                                    transform-origin: 0 0;
                                }}
                            """
                            css_provider.load_from_data(
                                css_data.encode('utf-8'))

                            style_context = entry_widget.get_style_context()

                            if hasattr(entry_widget, 'rotation_provider'):
                                style_context.remove_provider(
                                    entry_widget.rotation_provider)

                            style_context.add_provider(
                                css_provider,
                                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                            )
                            entry_widget.rotation_provider = css_provider
                            entry_widget.rotation_angle = self.state.text_rotation

            # Update display
            self.display_frame(self.state.current_frame_index)
            self.overlay.drawing_area.queue_draw()

        except Exception as e:
            print(f"Error rotating frames: {e}")
            import traceback
            traceback.print_exc()
            error_dialog = Gtk.AlertDialog()
            error_dialog.set_message(EditorConstants.ERROR_ROTATING_FRAMES)
            error_dialog.set_detail(str(e))
            error_dialog.show(self.get_root())

    def update_theme(self, is_dark):
        """Update theme for all buttons"""
        self.state.is_dark = is_dark

        # Update playback controls theme
        self.playback_controls.update_theme(is_dark)

        clear_css(self.info_label)
        self.info_label.add_css_class(
            EditorConstants.CSS_INFO_LABEL_DARK if is_dark else EditorConstants.CSS_INFO_LABEL_LIGHT)

        clear_css(self.controls_box)
        self.controls_box.add_css_class(
            EditorConstants.CSS_CONTROLS_BOX_DARK if is_dark else EditorConstants.CSS_CONTROLS_BOX_LIGHT)

        # Update action bar theme
        self.action_bar.update_theme(is_dark)

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
        if (self.state.playhead_frame_index < min_val - 1 or
                self.state.playhead_frame_index > max_val - 1):
            self.frameline.playhead_visible = False
            self.hide_playhead()

    def on_insert_frames(self, frameline, position, file_paths):
        try:
            # Use the GifLoader to load frames for insertion
            new_frames, new_durations = self.gif_loader.load_images_for_insertion(
                file_paths)

            if new_frames:
                insert_idx = max(0, position - 1)
                num_new_frames = len(new_frames)

                # Adjust speed ranges before inserting new frames
                updated_speed_ranges = []
                for start, end, speed in self.frameline.speed_ranges:
                    if insert_idx <= start:
                        # Speed range is after insertion point - shift it
                        updated_speed_ranges.append(
                            (start + num_new_frames, end + num_new_frames, speed))
                    elif insert_idx > end:
                        # Speed range is before insertion point - keep it unchanged
                        updated_speed_ranges.append((start, end, speed))
                    else:
                        # Speed range contains insertion point - split it into two parts
                        if start < insert_idx:
                            # Keep the part before insertion
                            updated_speed_ranges.append(
                                (start, insert_idx - 1, speed))
                        # Keep the part after insertion (shifted by the number of new frames)
                        updated_speed_ranges.append(
                            (insert_idx + num_new_frames, end + num_new_frames, speed))

                self.frameline.speed_ranges = updated_speed_ranges
                self.state.frames[insert_idx:insert_idx] = new_frames
                self.state.frame_durations[insert_idx:insert_idx] = new_durations
                new_max = len(self.state.frames)
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
                        updated_inserted_ranges.append(
                            (start + num_new_frames, end + num_new_frames))
                    elif end < insert_idx:
                        # Range is before insertion point - keep it unchanged
                        updated_inserted_ranges.append((start, end))
                    else:
                        # Range overlaps insertion point - split or shift as needed
                        # For simplicity, shift the part after insertion
                        if start < insert_idx:
                            updated_inserted_ranges.append(
                                (start, insert_idx - 1))
                        updated_inserted_ranges.append(
                            (insert_idx + num_new_frames, end + num_new_frames))

                self.frameline.inserted_ranges = updated_inserted_ranges
                # Append the new inserted range
                self.frameline.inserted_ranges.append(
                    (position, position + len(new_frames) - 1))

                for i, r in enumerate(self.frameline.removed_ranges):
                    # Shift removed ranges after insertion point
                    if r[0] >= insert_idx:
                        self.frameline.removed_ranges[i] = (
                            r[0] + num_new_frames, r[1] + num_new_frames)

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
            if not hasattr(self.state, 'original_frame_durations'):
                self.state.original_frame_durations = self.state.frame_durations.copy()
            elif len(self.state.original_frame_durations) != len(self.state.frames):
                # Extend original_frame_durations for inserted frames
                inserted_count = len(self.state.frames) - \
                    len(self.state.original_frame_durations)
                self.state.original_frame_durations.extend(
                    self.state.frame_durations[-inserted_count:])

            # Verify we have valid frames and durations
            if not self.state.frames or not self.state.frame_durations:
                print("Invalid frame data state")
                return

            # Adjust frame durations for the selected range
            for i in range(start_idx, end_idx + 1):
                if i < len(self.state.original_frame_durations):
                    self.state.frame_durations[i] = int(
                        self.state.original_frame_durations[i] / speed_factor)

            # Warn if any frame duration in the affected range is < 10ms
            min_duration = min(
                self.state.frame_durations[start_idx:end_idx+1]) if self.state.frame_durations[start_idx:end_idx+1] else EditorConstants.FALLBACK_DURATION_MS
            if min_duration < EditorConstants.MIN_FRAME_DURATION_MS:
                # Compute the maximum applicable speedup for this range
                if hasattr(self.state, 'original_frame_durations') and self.state.original_frame_durations:
                    min_orig = min(self.state.original_frame_durations[i] for i in range(
                        start_idx, end_idx+1))
                    max_speedup = round(
                        min_orig / EditorConstants.DURATION_THRESHOLD_MS, 2)
                else:
                    max_speedup = 'N/A'
                alert = Adw.AlertDialog()
                alert.set_heading(EditorConstants.WARNING_GIF_LAG_HEADING)
                alert.set_body(
                    EditorConstants.WARNING_GIF_LAG_BODY_TEMPLATE.format(
                        min_duration=EditorConstants.MIN_FRAME_DURATION_MS,
                        max_speedup=max_speedup
                    )
                )
                alert.add_response(EditorConstants.RESPONSE_OK,
                                   EditorConstants.PROCEED_ANYWAY)
                alert.add_response(
                    EditorConstants.RESPONSE_CANCEL, EditorConstants.CANCEL_CHANGE)
                alert.set_default_response(EditorConstants.RESPONSE_OK)
                alert.set_close_response(EditorConstants.RESPONSE_CANCEL)

                def on_response(dialog, response_id):
                    if response_id == EditorConstants.RESPONSE_CANCEL:
                        # Revert the frame durations in the affected range
                        for i in range(start_idx, end_idx + 1):
                            if i < len(self.state.original_frame_durations):
                                self.state.frame_durations[i] = self.state.original_frame_durations[i]
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
                    self.frameline.add_speed_range(
                        start_idx, end_idx, speed_factor)

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
                if self.state.is_playing:
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
        self.state.is_playing = False
        self.update_play_button_icon(False)
        if self.state.play_timeout_id:
            GLib.source_remove(self.state.play_timeout_id)
            self.state.play_timeout_id = None

    def reset(self):
        """Reset editor state"""
        # Use the state's reset method
        self.state.reset()

        # Reset overlays
        self.overlay.text_mode = False
        self.overlay.draw_mode = False
        self.overlay.handles_visible = False
        self.overlay.remove_all_text_entries()
        self.overlay.reset_crop_rect()

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

    def update_play_button_icon(self, playing):
        """Update the play button icon based on playing state"""
        self.playback_controls.update_play_button_icon(playing)

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
                self.state.frame_durations[i] for i in range(left_value, right_value + 1)
                if not self.frameline.is_frame_removed(i)
            ) / EditorConstants.MILLISECONDS_TO_SECONDS  # Convert to seconds

            self.info_label.set_text(
                EditorConstants.FRAME_INFO_TEMPLATE.format(
                    frames=valid_frame_count, duration=total_duration)
            )
        except Exception as e:
            print(f"Error updating info label: {e}")

    def on_crop_clicked(self, button):
        # Reset other modes first
        if self.state.text_mode:
            self.state.text_mode = False
            self.overlay.text_mode = False
            self.update_action_bar_button(False, self.text_button)

        if self.state.draw_mode:
            self.state.draw_mode = False
            self.overlay.draw_mode = False
            self.update_action_bar_button(False, self.draw_button)

        # Now toggle crop mode
        if self.state.crop_mode:
            self.state.crop_mode = False
            self.overlay.reset_crop_rect()
        else:
            self.state.crop_mode = True
            self.overlay.handles_visible = True
        self.update_action_bar_button(self.state.crop_mode, button)
        self.overlay.drawing_area.queue_draw()

    def on_text_clicked(self, button):
        """Toggle text editing mode"""
        if self.state.draw_mode:
            self.state.draw_mode = False
            self.overlay.draw_mode = False
            self.update_action_bar_button(False, self.draw_button)

        self.state.text_mode = not self.state.text_mode
        self.update_action_bar_button(self.state.text_mode, button)

        if self.state.text_mode:
            self.state.crop_mode = False
            self.overlay.handles_visible = False
            self.overlay.text_mode = True
            self.overlay.drawing_area.queue_draw()
        else:
            self.overlay.handles_visible = False
            self.overlay.text_mode = False
            self.overlay.drawing_area.queue_draw()

    def on_draw_clicked(self, button):
        """Toggle drawing mode and show color popover"""
        if self.state.text_mode:
            self.state.text_mode = False
            self.overlay.text_mode = False
            self.update_action_bar_button(False, self.text_button)

        if not self.state.draw_mode:
            self.color_picker.show()

        self.state.draw_mode = not self.state.draw_mode
        self.update_action_bar_button(self.state.draw_mode, button)

        if self.state.draw_mode:
            self.state.crop_mode = False
            self.overlay.handles_visible = False
            self.overlay.draw_mode = True

            if not hasattr(self.state, 'drawings'):
                # Start with empty list for first frame
                self.state.drawings = [[]]
        else:
            self.overlay.draw_mode = False

        self.overlay.drawing_area.queue_draw()

    def on_color_selected(self, color_hex, color_name):
        """Handle color selection from color picker"""
        self.state.current_draw_color = color_hex

    def toggle_loop(self, button):
        """Toggle looping playback on/off."""
        self.state.loop_playback = not self.state.loop_playback
        self.playback_controls.update_loop_button_state(
            self.state.loop_playback)
