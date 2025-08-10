from fig.constants import EditorConstants


class EditorState:
    """Centralized state management for the GIF editor"""

    def __init__(self):
        # Frame and playback state
        self.frames = []
        self.frame_durations = []
        self.original_frame_durations = []
        self.current_frame_index = EditorConstants.DEFAULT_FRAME_INDEX
        self.playhead_frame_index = EditorConstants.DEFAULT_FRAME_INDEX
        self.is_playing = False
        self.play_timeout_id = None
        self.playback_finished = False
        self.loop_playback = False

        # Editing mode state
        self.crop_mode = False
        self.text_mode = False
        self.draw_mode = False
        self.drawing = False
        self.last_point = None
        self.drawings = []
        self.apply_to_all_frames = True

        # Transformation state
        self.flipped = False
        self.rotated = False
        self.text_rotation = EditorConstants.DEFAULT_TEXT_ROTATION

        # Theme and display state
        self.is_dark = True
        self.current_draw_color = EditorConstants.DEFAULT_DRAW_COLOR

        # Image properties
        self.image_display_width = EditorConstants.DEFAULT_FRAME_INDEX
        self.image_display_height = EditorConstants.DEFAULT_FRAME_INDEX
        self.container_size = EditorConstants.DEFAULT_FRAME_INDEX
        self.IMAGE_SCALE = EditorConstants.DEFAULT_SCALE
        self.original_width = EditorConstants.DEFAULT_FRAME_INDEX
        self.original_height = EditorConstants.DEFAULT_FRAME_INDEX

        # File properties
        self.original_file_path = None
        self.original_file_name = None

    def reset(self):
        """Reset all state to initial values"""
        self.frames = []
        self.frame_durations = []
        self.original_frame_durations = []
        self.current_frame_index = EditorConstants.DEFAULT_FRAME_INDEX
        self.playhead_frame_index = EditorConstants.DEFAULT_FRAME_INDEX
        self.is_playing = False
        self.play_timeout_id = None
        self.playback_finished = False

        # Reset editing states
        self.crop_mode = False
        self.text_mode = False
        self.draw_mode = False
        self.drawing = False
        self.last_point = None
        self.drawings = [[]]

        # Reset transformations
        self.flipped = False
        self.rotated = False
        self.text_rotation = EditorConstants.DEFAULT_TEXT_ROTATION

        # Keep theme and color settings
        # Keep container settings for next load

    def has_frames(self):
        """Check if frames are loaded"""
        return bool(self.frames)

    def get_frame_count(self):
        """Get total number of frames"""
        return len(self.frames)

    def is_valid_frame_index(self, index):
        """Check if frame index is valid"""
        return 0 <= index < len(self.frames)

    def set_image_dimensions(self, width, height):
        """Set image dimensions and calculate scale"""
        self.image_display_width = width
        self.image_display_height = height
        self.original_width = width
        self.original_height = height

        # Calculate scale to fit the longer dimension within reasonable bounds
        long_side = max(width, height)
        scale = EditorConstants.DEFAULT_SCALE
        self.container_size = int(long_side * scale)
        self.IMAGE_SCALE = scale
