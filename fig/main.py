#!/usr/bin/env python3

import os
import gi
import threading
import time
import tempfile

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GdkPixbuf, Gdk, GLib
import fig.home, fig.editor
from fig.utils import clear_css, load_css
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip

class Fig(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_default_size(750, 650)
        self.set_resizable(False)
        
        drop_target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        drop_target.connect('drop', self.on_drop)
        drop_target.connect('enter', self.on_drag_enter)
        drop_target.connect('leave', self.on_drag_leave)
        drop_target.connect('motion', self.on_drag_motion)
        self.add_controller(drop_target)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.headerbar = Adw.HeaderBar()
        
        self.style = Adw.StyleManager.get_default()
        self.style.connect("notify::dark", self.on_color_scheme_change)
        
        self.back_button = Gtk.Button()
        self.back_button.set_icon_name("go-previous-symbolic")
        self.back_button.connect("clicked", lambda _: self.load_home_ui())
        self.back_button.set_visible(False)
        self.headerbar.pack_start(self.back_button)
        
        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_icon_name("open-menu-symbolic")

        self.menu_model = Gio.Menu()
        self.menu_model.append("New Window", "app.new_window")
        self.menu_model.append("Help", "app.help")
        self.menu_button.set_menu_model(self.menu_model)

        self.headerbar.pack_end(self.menu_button)
        
        label = Gtk.Label()
        label.set_markup('<b>Fig</b>')
        self.headerbar.set_title_widget(label)
        main_box.append(self.headerbar)
        
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.content_box)

        self.home_box = fig.home.HomeBox()
        self.editor_box = fig.editor.EditorBox()
        self.content_box.append(self.home_box)

        self.set_content(main_box)
        
        self.update_theme(self.style.get_dark())
        
        self.on_editor = False
    
    def update_theme(self, is_dark):
        """Update theme for all components"""
        clear_css(self.headerbar)
        self.headerbar.add_css_class("headerbar-dark" if is_dark else "headerbar-light")
        
        self.home_box.update_theme(is_dark)
        self.editor_box.update_theme(is_dark)
    
    def on_color_scheme_change(self, style_manager, pspec):
        """Handle system color scheme changes"""
        self.update_theme(style_manager.get_dark())

    def load_editor_ui(self):
        if self.on_editor:
            return
        self.on_editor = True
        if self.content_box.get_first_child():
            self.content_box.remove(self.content_box.get_first_child())
        self.content_box.append(self.editor_box)
        self.back_button.set_visible(True)
        self.clear_menu()
        self.menu_model.append("New Window", "app.new_window")
        self.menu_model.append("Extract Frames", "app.extract_frames")
        self.menu_model.append("Export to Video", "app.export_to_video")
        self.menu_model.append("Help", "app.help")
        self.menu_model.append("About", "app.about")

    def load_home_ui(self):
        self.on_editor = False
        if self.content_box.get_first_child():
            self.content_box.remove(self.content_box.get_first_child())
        self.content_box.append(self.home_box)
        self.back_button.set_visible(False)
        self.editor_box.reset()
        self.clear_menu()
        self.menu_model.append("New Window", "app.new_window")
        self.menu_model.append("Help", "app.help")
        
    def clear_menu(self):
        while self.menu_model.get_n_items() > 0:
            self.menu_model.remove(self.menu_model.get_n_items() - 1)
        
    def on_option_selected(self, action, parameter, option_name):
        print(f"Selected: {option_name}")

    def on_drop(self, drop_target, value, x, y):
        self.remove_css_class('drag-and-drop')
        if isinstance(value, Gio.File):
            file_path = value.get_path()
            if file_path.lower().endswith('.gif'):
                self.load_editor_ui()
                self.editor_box.overlay.reset_crop_rect()
                self.editor_box.load_gif(file_path)
                original_file_name = os.path.basename(file_path)
                if original_file_name.endswith('.gif'):
                    self.editor_box.original_file_name = original_file_name[:-4]
                else:
                    self.editor_box.original_file_name = original_file_name
                return True
            
        return False

    def on_drag_enter(self, drop_target, x, y):
        load_css(self.get_display(), [])
        self.add_css_class('drag-and-drop')
        return Gdk.DragAction.COPY

    def on_drag_leave(self, drop_target):
        self.remove_css_class('drag-and-drop')

    def on_drag_motion(self, drop_target, x, y):
        return Gdk.DragAction.COPY

class FigApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.github.Q1CHENL.fig")
        
        new_window_action = Gio.SimpleAction.new("new_window", None)
        new_window_action.connect("activate", self.on_new_window)
        self.add_action(new_window_action)
        
        help_action = Gio.SimpleAction.new("help", None)
        help_action.connect("activate", self.on_help)
        self.add_action(help_action)
        
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)
        
        extract_frames_action = Gio.SimpleAction.new("extract_frames", None)
        extract_frames_action.connect("activate", self.on_extract_frames)
        self.add_action(extract_frames_action)
        
        export_to_video_action = Gio.SimpleAction.new("export_to_video", None)
        export_to_video_action.connect("activate", self.on_export_to_video)
        self.add_action(export_to_video_action)

    def do_activate(self):
        win = Fig(self)
        win.present()
        
    def on_new_window(self, action, parameter):
        """Create a new window when New Window is selected"""
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
            label=
            "• You can drag and drop a GIF file to start editing.\n\n" + 
            "• Left-click on the image to activate crop.\n\n" +
            "• Right-click on the timeline handles to\n"
            "  discovery more advanced actions.\n"
            
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
        # Prompt user to choose output folder instead of writing to read-only source location
        window = self.get_active_window()
        if not window or not hasattr(window.editor_box, 'original_file_path'):
            return

        try:
            dialog = Gtk.FileDialog.new()
            dialog.set_title("Extract Frames")
            original_dir = os.path.dirname(window.editor_box.original_file_path)
            initial_folder = Gio.File.new_for_path(original_dir)
            dialog.set_initial_folder(initial_folder)

            if hasattr(window.editor_box, 'original_file_name'):
                dialog.set_initial_name(window.editor_box.original_file_name)
            def save_callback(dialog, result):
                try:
                    folder = dialog.save_finish(result)
                    if folder:
                        output_dir = folder.get_path()
                        os.makedirs(output_dir, exist_ok=True)

                        frames = window.editor_box.frames
                        total_frames = len(frames)
                        BATCH_SIZE = self.compute_batch_size(total_frames)

                        progress_dialog = Adw.AlertDialog.new(
                            "0%",
                            f"{output_dir}"
                        )
                        GLib.idle_add(progress_dialog.present, window)

                        def extraction_thread():
                            try:
                                extracted = 0
                                def process_batch(batch_info):
                                    nonlocal extracted
                                    start_idx, end_idx = batch_info
                                    for i in range(start_idx, end_idx):
                                        if isinstance(frames[i], GdkPixbuf.Pixbuf):
                                            pil_image = window.editor_box._pixbuf_to_pil(frames[i])
                                            frame_name = f"{window.editor_box.original_file_name}-{str(i+1).zfill(3)}.png"
                                            frame_path = os.path.join(output_dir, frame_name)
                                            pil_image.save(frame_path, 'PNG')
                                        extracted += 1
                                    GLib.idle_add(
                                        progress_dialog.set_heading,
                                        f"{int((extracted / total_frames) * 100)}%"
                                    )
                                    return end_idx

                                batches = [
                                    (i, min(i + BATCH_SIZE, total_frames))
                                    for i in range(0, total_frames, BATCH_SIZE)
                                ]

                                import concurrent.futures
                                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                                    for batch in batches:
                                        executor.submit(process_batch, batch)
                                    executor.shutdown(wait=True)
                                
                                # Extraction complete
                                GLib.idle_add(progress_dialog.set_heading, "Frames Extracted")
                                GLib.idle_add(progress_dialog.set_body, f"{output_dir}")
                                GLib.idle_add(progress_dialog.add_response, "ok", "OK")
                                GLib.idle_add(progress_dialog.set_response_enabled, "OK", True)

                            except Exception as e:
                                error_dialog = Adw.AlertDialog.new(
                                    "Error",
                                    f"Failed to extract frames: {str(e)}"
                                )
                                error_dialog.add_response("ok", "OK")
                                GLib.idle_add(error_dialog.present, window)
                        threading.Thread(target=extraction_thread).start()
                except GLib.Error:
                    # user cancelled or error opening dialog
                    pass

            dialog.save(window, None, save_callback)
        except Exception as e:
            error_dialog = Adw.AlertDialog.new(
                "Error",
                f"Failed to extract frames: {str(e)}"
            )
            error_dialog.add_response("ok", "OK")
            error_dialog.present(window)

    def on_export_to_video(self, action, parameter):
        """Export the current GIF frames to a video file"""
        window = self.get_active_window()
        if window and hasattr(window.editor_box, 'original_file_path'):
            try:
                dialog = Gtk.FileDialog.new()
                dialog.set_title("Export to Video")
                original_dir = os.path.dirname(window.editor_box.original_file_path)
                initial_folder = Gio.File.new_for_path(original_dir)
                dialog.set_initial_folder(initial_folder)
                
                if hasattr(window.editor_box, 'original_file_name'):
                    dialog.set_initial_name(f"{window.editor_box.original_file_name}.mp4")
                else:
                    dialog.set_initial_name("output.mp4")
                
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
                
            except Exception as e:
                error_dialog = Adw.AlertDialog.new(
                    "Error",
                    f"Failed to export video: {str(e)}"
                )
                error_dialog.add_response("ok", "OK")
                error_dialog.present(window)

    def _export_video(self, window, editor_box, output_path):
        """Handle the actual video export process with a progress dialog and cancellation support."""
        try:
            cancel_event = threading.Event()

            progress_dialog = Adw.AlertDialog.new("Exporting Video...", output_path)
            progress_dialog.add_response("cancel", "Cancel")
            progress_dialog.set_default_response("cancel")
            progress_dialog.set_close_response("cancel")

            def on_response(dialog, response_id):
                if response_id == "cancel":
                    cancel_event.set()
                    dialog.set_heading("Cancelling...")
                    dialog.set_body("Please wait while the export is being cancelled.")

            progress_dialog.connect("response", on_response)
            GLib.idle_add(progress_dialog.present, window)

            def export_thread():
                try:
                    durations = [d / 1000.0 for d in editor_box.frame_durations]  # Convert ms to seconds

                    with tempfile.TemporaryDirectory() as temp_dir:
                        frame_paths = []
                        total_frames = len(editor_box.frames)
                        processed_frames = 0

                        for i, frame in enumerate(editor_box.frames):
                            if cancel_event.is_set():
                                raise Exception("Export cancelled by user.")
                            if not editor_box.frameline.is_frame_removed(i):
                                frame_path = os.path.join(temp_dir, f"frame_{i}.png")
                                pil_image = editor_box._pixbuf_to_pil(frame)
                                pil_image.save(frame_path, 'PNG')
                                frame_paths.append(frame_path)
                            processed_frames += 1

                        if cancel_event.is_set():
                            raise Exception("Export cancelled by user.")

                        clip = ImageSequenceClip(frame_paths, durations=durations)
                        clip.write_videofile(
                            output_path,
                            fps=30,
                            codec='libvpx-vp9',
                            audio=False,
                            logger=None
                        )

                    if cancel_event.is_set():
                        raise Exception("Export cancelled by user.")

                    GLib.idle_add(progress_dialog.set_heading, "Video Exported")
                    GLib.idle_add(progress_dialog.set_body, output_path)
                    GLib.idle_add(progress_dialog.add_response, "ok", "OK")
                    GLib.idle_add(progress_dialog.set_default_response, "ok")
                    GLib.idle_add(progress_dialog.set_close_response, "ok")

                except Exception as e:
                    if os.path.exists(output_path):
                        try:
                            os.remove(output_path)
                            print("removed partial file")
                        except Exception as remove_error:
                            print(f"Failed to remove partial file: {remove_error}")

                    GLib.idle_add(progress_dialog.set_heading, "Export Failed")
                    GLib.idle_add(progress_dialog.set_body, str(e))
                    GLib.idle_add(progress_dialog.add_response, "ok", "OK")
                    GLib.idle_add(progress_dialog.set_default_response, "ok")
                    GLib.idle_add(progress_dialog.set_close_response, "ok")

            threading.Thread(target=export_thread).start()

        except Exception as e:
            error_dialog = Adw.AlertDialog.new("Error", f"Failed to initialize export: {str(e)}")
            error_dialog.add_response("ok", "OK")
            error_dialog.set_default_response("ok")
            error_dialog.set_close_response("ok")
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

def main():
    app = FigApplication()
    return app.run(None)
