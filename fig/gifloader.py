"""
GIF and image loading functionality for the Fig editor.

This module provides the GifLoader class which handles loading GIF files,
static images, and inserting frames with proper progress reporting and
error handling.
"""

import os
import threading
from dataclasses import dataclass
from typing import List, Tuple, Callable, Optional
from fig.imagecvt import ImageConverter
from PIL import Image
import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib


@dataclass
class LoadResult:
    """Result of a GIF/image loading operation."""
    frames: List
    durations: List[float]
    total_duration: float
    width: int
    height: int
    frame_count: int
    file_path: str


@dataclass
class LoadProgress:
    """Progress information during loading."""
    current_frame: int
    total_frames: int
    frames: List
    durations: List[float]
    total_duration: Optional[float] = None


class GifLoaderError(Exception):
    """Custom exception for GIF loading errors."""
    pass


class GifLoader:
    """
    Handles loading of GIF files and static images with progress reporting.

    This class provides asynchronous loading of animated GIFs and static images,
    with support for progress callbacks and proper error handling.
    """

    def __init__(self):
        self._loading = False
        self._load_thread = None

    @property
    def is_loading(self) -> bool:
        """Check if a loading operation is currently in progress."""
        return self._loading

    def load_gif_async(
        self,
        file_path: str,
        progress_callback: Callable[[LoadProgress], None],
        completion_callback: Callable[[Optional[LoadResult], Optional[Exception]], None],
        batch_size: Optional[int] = None
    ) -> None:
        """
        Load a GIF file asynchronously with progress reporting.

        Args:
            file_path: Path to the GIF file to load
            progress_callback: Called periodically with loading progress
            completion_callback: Called when loading completes (success or failure)
            batch_size: Number of frames to process before reporting progress

        Raises:
            GifLoaderError: If already loading or file doesn't exist
        """
        if self._loading:
            raise GifLoaderError("Already loading a file")

        if not os.path.exists(file_path):
            raise GifLoaderError(f"File not found: {file_path}")

        self._loading = True

        # Calculate batch size if not provided
        if batch_size is None:
            try:
                with Image.open(file_path) as img:
                    frame_count = getattr(img, 'n_frames', 1)
                    batch_size = self._calculate_batch_size(frame_count)
            except Exception:
                batch_size = 10  # Fallback

        # Start loading thread
        self._load_thread = threading.Thread(
            target=self._load_gif_thread,
            args=(file_path, progress_callback,
                  completion_callback, batch_size),
            daemon=True
        )
        self._load_thread.start()

    def load_images_for_insertion(
        self,
        file_paths: List[str]
    ) -> Tuple[List, List[float]]:
        """
        Load multiple images/GIFs for frame insertion.

        Args:
            file_paths: List of file paths to load

        Returns:
            Tuple of (frames, durations) lists

        Raises:
            GifLoaderError: If any file cannot be loaded
        """
        all_frames = []
        all_durations = []

        for path in file_paths:
            if not os.path.exists(path):
                raise GifLoaderError(f"File not found: {path}")

            try:
                frames, durations = self._load_single_file(path)
                all_frames.extend(frames)
                all_durations.extend(durations)
            except Exception as e:
                raise GifLoaderError(f"Error loading {path}: {str(e)}") from e

        return all_frames, all_durations

    def cancel_loading(self) -> None:
        """Cancel the current loading operation if one is in progress."""
        if self._loading and self._load_thread:
            # Note: Python threading doesn't support cancellation directly
            # This sets a flag that the thread should check
            self._loading = False

    def _load_gif_thread(
        self,
        file_path: str,
        progress_callback: Callable[[LoadProgress], None],
        completion_callback: Callable[[Optional[LoadResult], Optional[Exception]], None],
        batch_size: int
    ) -> None:
        """Thread function for loading GIF files."""
        try:
            result = self._load_gif_file(
                file_path, progress_callback, batch_size)
            GLib.idle_add(lambda: completion_callback(result, None))
        except Exception as ex:
            GLib.idle_add(lambda e=ex: completion_callback(None, e))
        finally:
            self._loading = False

    def _load_gif_file(
        self,
        file_path: str,
        progress_callback: Callable[[LoadProgress], None],
        batch_size: int
    ) -> LoadResult:
        """Load a GIF file and report progress."""
        frames = []
        durations = []
        total_duration = 0.0

        with Image.open(file_path) as gif:
            width, height = gif.size
            frame_count = getattr(gif, 'n_frames', 1)

            # Report initial progress
            progress = LoadProgress(0, frame_count, [], [])
            GLib.idle_add(lambda: progress_callback(progress))

            update_batch = []

            for frame_idx in range(frame_count):
                if not self._loading:  # Check for cancellation
                    raise GifLoaderError("Loading cancelled")

                gif.seek(frame_idx)

                # Get frame duration (convert from ms to seconds, then back to ms)
                duration_ms = gif.info.get('duration', 100)
                duration_seconds = duration_ms / 1000.0
                total_duration += duration_seconds

                # Convert frame to RGBA if needed
                if gif.mode != 'RGBA':
                    frame_image = gif.convert('RGBA')
                else:
                    frame_image = gif.copy()

                # Convert to pixbuf
                pixbuf = ImageConverter.pil_to_pixbuf(frame_image)
                frames.append(pixbuf)
                durations.append(duration_ms)  # Store in milliseconds

                # Report progress in batches
                if len(update_batch) < batch_size and frame_idx < frame_count - 1:
                    update_batch.append(frame_idx)
                else:
                    progress = LoadProgress(
                        current_frame=frame_idx + 1,
                        total_frames=frame_count,
                        frames=frames.copy(),
                        durations=durations.copy(),
                        total_duration=total_duration if frame_idx == frame_count - 1 else None
                    )
                    GLib.idle_add(lambda p=progress: progress_callback(p))
                    update_batch = []

        return LoadResult(
            frames=frames,
            durations=durations,
            total_duration=total_duration,
            width=width,
            height=height,
            frame_count=frame_count,
            file_path=file_path
        )

    def _load_single_file(self, file_path: str) -> Tuple[List, List[float]]:
        """Load a single image or GIF file."""
        frames = []
        durations = []

        with Image.open(file_path) as img:
            if getattr(img, 'is_animated', False):
                # Handle animated GIFs
                for frame_idx in range(img.n_frames):
                    img.seek(frame_idx)
                    frame_image = img.convert('RGBA')
                    pixbuf = ImageConverter.pil_to_pixbuf(frame_image)
                    frames.append(pixbuf)
                    durations.append(img.info.get('duration', 100))
            else:
                # Handle static images
                frame_image = img.convert('RGBA')
                pixbuf = ImageConverter.pil_to_pixbuf(frame_image)
                frames.append(pixbuf)
                durations.append(100.0)  # Default 100ms duration

        return frames, durations

    def _calculate_batch_size(self, frame_count: int) -> int:
        """Calculate optimal batch size based on frame count."""
        if frame_count <= 40:
            return max(1, frame_count // 4)
        elif frame_count <= 200:
            return 10
        else:
            return 20

    @staticmethod
    def get_image_info(file_path: str) -> Tuple[int, int, int]:
        """
        Get basic information about an image file.

        Args:
            file_path: Path to the image file

        Returns:
            Tuple of (width, height, frame_count)

        Raises:
            GifLoaderError: If file cannot be read
        """
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                frame_count = getattr(img, 'n_frames', 1)
                return width, height, frame_count
        except Exception as e:
            raise GifLoaderError(
                f"Cannot read image info from {file_path}: {str(e)}") from e
