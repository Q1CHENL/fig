#!/usr/bin/env python3

import fig.io
import fig.home
import os
import threading
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib


class FigApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.github.Q1CHENL.fig")
        self._setup_actions()

    def _setup_actions(self):
        """Setup all application actions"""
        actions = [
            ("new_window", self.on_new_window),
            ("help", self.on_help),
            ("about", self.on_about),
            ("extract_frames", self.on_extract_frames),
            ("export_to_video", self.on_export_to_video)
        ]

        for action_name, callback in actions:
            action = Gio.SimpleAction.new(action_name, None)
            action.connect("activate", callback)
            self.add_action(action)

    def do_activate(self):
        from fig.window import Fig
        win = Fig(self)
        win.present()

    def on_new_window(self, action, parameter):
        """Create a new window when New Window is selected"""
        from fig.window import Fig
        win = Fig(self)
        win.present()

    def on_help(self, action, parameter):
        """Show help dialog with tips about handle functionality"""
        window = self.get_active_window()

        dialog = Adw.AlertDialog.new(
            "Help",
            None
        )

        label = Gtk.Label(
            label="• You can drag and drop a GIF file to start editing.\n\n" +
            "• Right-click on the timeline handles for more advanced actions.\n\n"
            "• Press Left/Right arrow keys to move handles\n"
        )
        label.set_halign(Gtk.Align.END)
        label.set_justify(Gtk.Justification.LEFT)

        dialog.set_extra_child(label)

        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")

        dialog.present(window)

    def on_about(self, action, parameter):
        """Show about dialog when About is selected"""
        window = self.get_active_window()
        if window:
            fig.home.show_about_dialog(window)

    def on_extract_frames(self, action, parameter):
        """Extract frames with user-selected output directory"""
        window = self.get_active_window()
        if not window or not hasattr(window.editor_box, 'original_file_path'):
            return

        try:
            self._show_extract_frames_dialog(window)
        except Exception as e:
            self._show_error_dialog(
                window, "Failed to extract frames", str(e))

    def _show_extract_frames_dialog(self, window):
        """Show file dialog for frame extraction"""
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Extract Frames")

        # Set initial directory and name
        original_dir = os.path.dirname(window.editor_box.original_file_path)
        initial_folder = Gio.File.new_for_path(original_dir)
        dialog.set_initial_folder(initial_folder)

        if hasattr(window.editor_box, 'original_file_name'):
            dialog.set_initial_name(window.editor_box.original_file_name)

        dialog.save(window, None, lambda d, r: self._handle_extract_frames_response(
            d, r, window))

    def _handle_extract_frames_response(self, dialog, result, window):
        """Handle the response from extract frames dialog"""
        try:
            folder = dialog.save_finish(result)
            if folder:
                output_dir = folder.get_path()
                os.makedirs(output_dir, exist_ok=True)
                self._start_frame_extraction(window, output_dir)
        except GLib.Error:
            # User cancelled or error opening dialog
            pass

    def _start_frame_extraction(self, window, output_dir):
        """Start the frame extraction process"""
        frames = window.editor_box.frames
        total_frames = len(frames)
        batch_size = self.compute_batch_size(total_frames)

        progress_dialog = Adw.AlertDialog.new("0%", f"{output_dir}")
        GLib.idle_add(progress_dialog.present, window)

        def extraction_thread():
            fig.io.extract_frames(
                window, frames, total_frames, batch_size, output_dir, progress_dialog)

        threading.Thread(target=extraction_thread).start()

    def on_export_to_video(self, action, parameter):
        """Export the current GIF frames to a video file"""
        window = self.get_active_window()
        if not window or not hasattr(window.editor_box, 'original_file_path'):
            return

        try:
            self._show_export_video_dialog(window)
        except Exception as e:
            self._show_error_dialog(window, "Failed to export video", str(e))

    def _show_export_video_dialog(self, window):
        """Show file dialog for video export"""
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Export to Video")

        # Set initial directory and name
        original_dir = os.path.dirname(window.editor_box.original_file_path)
        initial_folder = Gio.File.new_for_path(original_dir)
        dialog.set_initial_folder(initial_folder)

        if hasattr(window.editor_box, 'original_file_name'):
            dialog.set_initial_name(
                f"{window.editor_box.original_file_name}.mp4")
        else:
            dialog.set_initial_name("output.mp4")

        # Setup file filter
        filter_mp4 = Gtk.FileFilter()
        filter_mp4.set_name("MP4 files")
        filter_mp4.add_pattern("*.mp4")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_mp4)
        dialog.set_filters(filters)

        def save_callback(dialog, result):
            try:
                file = dialog.save_finish(result)
                if file:
                    output_path = file.get_path()
                    self._export_video(window, window.editor_box, output_path)
            except GLib.Error as e:
                print(f"Error in save dialog: {e}")

        dialog.save(window, None, save_callback)

    def _export_video(self, window, editor_box, output_path):
        """Handle the actual video export process with a progress dialog and cancellation support."""
        try:
            cancel_event = threading.Event()

            progress_dialog = Adw.AlertDialog.new(
                "Exporting Video...", output_path)
            progress_dialog.add_response("cancel", "Cancel")
            progress_dialog.set_default_response("cancel")
            progress_dialog.set_close_response("cancel")

            def on_response(dialog, response_id):
                if response_id == "cancel":
                    cancel_event.set()
                    dialog.set_heading("Cancelling...")
                    dialog.set_body(
                        "Please wait while the export is being cancelled.")

            progress_dialog.connect("response", on_response)
            GLib.idle_add(progress_dialog.present, window)

            def export_thread():
                fig.io.export_video(
                    window, editor_box, output_path, cancel_event, progress_dialog)

            threading.Thread(target=export_thread).start()

        except Exception as e:
            error_dialog = Adw.AlertDialog.new(
                "Error", f"Failed to initialize export: {str(e)}")
            error_dialog.add_response("ok", "OK")
            error_dialog.set_default_response("ok")
            error_dialog.set_close_response("ok")
            error_dialog.present(window)

    def _show_error_dialog(self, window, title, message):
        """Show a generic error dialog"""
        error_dialog = Adw.AlertDialog.new(title, message)
        error_dialog.add_response("ok", "OK")
        error_dialog.present(window)

    def compute_batch_size(self, total_frames):
        if total_frames < 20:
            return total_frames
        return total_frames // 20

    def show_extraction_complete_dialog(self, window, output_dir):
        dialog = Adw.AlertDialog.new(
            "Frames Extracted",
            f"{output_dir}"
        )
        dialog.add_response("ok", "OK")
        dialog.present(window)
