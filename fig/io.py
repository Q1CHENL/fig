#!/usr/bin/env python3

import os
import tempfile
import concurrent.futures
from gi.repository import GdkPixbuf, GLib, Adw
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip


def extract_frames(window, frames, total_frames, batch_size, output_dir, progress_dialog):
    """Worker thread for frame extraction"""
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
            (i, min(i + batch_size, total_frames))
            for i in range(0, total_frames, batch_size)
        ]

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
        error_dialog = Adw.AlertDialog.new("Error", f"Failed to extract frames: {str(e)}")
        error_dialog.add_response("ok", "OK")
        GLib.idle_add(error_dialog.present, window)


def export_video(window, editor_box, output_path, cancel_event, progress_dialog):
    """Handle the actual video export process"""
    try:
        # Convert ms to seconds
        durations = [
            d / 1000.0 for d in editor_box.frame_durations]

        with tempfile.TemporaryDirectory() as temp_dir:
            frame_paths = []
            processed_frames = 0

            for i, frame in enumerate(editor_box.frames):
                if cancel_event.is_set():
                    raise Exception("Export cancelled by user.")
                if not editor_box.frameline.is_frame_removed(i):
                    frame_path = os.path.join(
                        temp_dir, f"frame_{i}.png")
                    pil_image = editor_box._pixbuf_to_pil(frame)
                    pil_image.save(frame_path, 'PNG')
                    frame_paths.append(frame_path)
                processed_frames += 1

            if cancel_event.is_set():
                raise Exception("Export cancelled by user.")

            clip = ImageSequenceClip(
                frame_paths, durations=durations)
            clip.write_videofile(
                output_path,
                fps=30,
                codec='libvpx-vp9',
                audio=False,
                logger=None
            )

        if cancel_event.is_set():
            raise Exception("Export cancelled by user.")

        GLib.idle_add(progress_dialog.set_heading,
                      "Video Exported")
        GLib.idle_add(progress_dialog.set_body, output_path)
        GLib.idle_add(progress_dialog.add_response, "ok", "OK")
        GLib.idle_add(progress_dialog.set_default_response, "ok")
        GLib.idle_add(progress_dialog.set_close_response, "ok")
        GLib.idle_add(progress_dialog.remove_response, "cancel")

    except Exception as e:
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                print("removed partial file")
            except Exception as remove_error:
                print(
                    f"Failed to remove partial file: {remove_error}")

        GLib.idle_add(progress_dialog.set_heading, "Export Failed")
        GLib.idle_add(progress_dialog.set_body, str(e))
        GLib.idle_add(progress_dialog.add_response, "ok", "OK")
        GLib.idle_add(progress_dialog.set_default_response, "ok")
        GLib.idle_add(progress_dialog.set_close_response, "ok")
