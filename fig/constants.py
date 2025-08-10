"""
Constants used throughout the Fig GIF editor application.

This module contains all the hardcoded values used across the application,
organized by category for better maintainability and consistency.
"""


class EditorConstants:
    """Constants used throughout the editor"""

    # UI Layout
    BUTTON_HEIGHT = 40
    MARGIN_TOP_BOTTOM = 20
    MARGIN_START_END = 80
    INFO_LABEL_MARGIN = 10
    CONTROLS_BOX_SPACING = 10
    CONTROLS_BOX_MARGIN_TOP = 15
    CONTROLS_BOX_MARGIN_BOTTOM = 5
    CONTROLS_BOX_MARGIN_SIDE = 5
    COLOR_BUTTON_SIZE = 30
    COLOR_POPOVER_MARGIN = 5

    # Frame and Animation
    MIN_FRAME_DURATION_MS = 10
    DURATION_THRESHOLD_MS = 10
    FALLBACK_DURATION_MS = 1000
    MILLISECONDS_TO_SECONDS = 1000.0

    # Rotation and Transformation
    ROTATION_DEGREES = 90
    FULL_CIRCLE_DEGREES = 360

    # Default Values
    DEFAULT_FRAME_INDEX = 0
    DEFAULT_SCALE = 1
    DEFAULT_TEXT_ROTATION = 0

    # Colors
    DEFAULT_DRAW_COLOR = '#FFFFFF'
    COLOR_WHITE = '#FFFFFF'
    COLOR_BLACK = '#000000'
    COLOR_RED = '#FF0000'
    COLOR_GREEN = '#57e389'
    COLOR_BLUE = '#3584e4'
    COLOR_YELLOW = '#FFFF00'

    # File Extensions
    GIF_EXTENSION = '.gif'
    DEFAULT_SAVE_SUFFIX = '-edited'
    DEFAULT_FILENAME = 'untitled'

    # Messages and Labels
    LOADING_MESSAGE_TEMPLATE = "Loading frames {current}/{total}"
    FRAME_INFO_TEMPLATE = "{frames} Frames • {duration:.2f} Seconds"
    ERROR_SAVING_FILE = "Error saving file"
    ERROR_LOADING_GIF = "Error loading GIF"
    ERROR_FLIPPING_FRAMES = "Error flipping frames"
    ERROR_ROTATING_FRAMES = "Error rotating frames"
    INVALID_FRAME_RANGE = "Invalid Frame Range"
    WARNING_GIF_LAG_HEADING = "Warning: GIF May Lag"
    WARNING_GIF_LAG_BODY_TEMPLATE = ("At least one frame duration is less than {min_duration}ms. "
                                     "GIF may be laggy or not play smoothly in some viewers when exported.\n\n"
                                     "Maximum applicable speedup for this GIF: {max_speedup}x")
    SAVE_DIALOG_TITLE = "Save GIF as..."
    GIF_FILTER_NAME = "GIF files"
    RESPONSE_OK = "ok"
    RESPONSE_CANCEL = "cancel"
    PROCEED_ANYWAY = "Proceed Anyway"
    CANCEL_CHANGE = "Cancel Change"

    # CSS Classes
    CSS_IMAGE_DISPLAY = "image-display"
    CSS_CONTROLS_BOX_DARK = "controls-box-dark"
    CSS_CONTROLS_BOX_LIGHT = "controls-box-light"
    CSS_INFO_LABEL_DARK = "info-label-dark"
    CSS_INFO_LABEL_LIGHT = "info-label-light"
    CSS_COLOR_BUTTON = "color-button"


class UIConstants:
    """UI-specific constants that might be used by other components"""

    # Layout spacing and sizing
    SMALL_SPACING = 5
    MEDIUM_SPACING = 10
    LARGE_SPACING = 20

    # Standard button sizes
    SMALL_BUTTON_SIZE = 24
    MEDIUM_BUTTON_SIZE = 32
    LARGE_BUTTON_SIZE = 40

    # Standard margins
    SMALL_MARGIN = 5
    MEDIUM_MARGIN = 10
    LARGE_MARGIN = 20
    XLARGE_MARGIN = 80


class AnimationConstants:
    """Animation and timing related constants"""

    # Standard frame rates (frames per second)
    FPS_24 = 24
    FPS_30 = 30
    FPS_60 = 60

    # Animation durations in milliseconds
    FAST_ANIMATION_MS = 150
    NORMAL_ANIMATION_MS = 300
    SLOW_ANIMATION_MS = 500

    # Playback constants
    MIN_PLAYBACK_SPEED = 0.1
    MAX_PLAYBACK_SPEED = 10.0
    DEFAULT_PLAYBACK_SPEED = 1.0


class ColorConstants:
    """Color palette constants"""

    # Primary colors
    PRIMARY_COLORS = [
        ('#FFFFFF', 'White'),
        ('#000000', 'Black'),
        ('#FF0000', 'Red'),
        ('#57e389', 'Green'),
        ('#3584e4', 'Blue'),
        ('#FFFF00', 'Yellow'),
    ]

    # Additional colors (commented out in original)
    SECONDARY_COLORS = [
        ('#FF00FF', 'Magenta'),
        ('#00FFFF', 'Cyan'),
        ('#FFA500', 'Orange'),
        ('#800080', 'Purple'),
    ]

    # Theme colors
    DARK_THEME_BG = '#2d2d2d'
    LIGHT_THEME_BG = '#ffffff'

    # Accent colors
    SUCCESS_COLOR = '#57e389'
    WARNING_COLOR = '#f6d32d'
    ERROR_COLOR = '#e01b24'
    INFO_COLOR = '#3584e4'


class FileConstants:
    """File handling related constants"""

    # Supported formats
    SUPPORTED_IMAGE_FORMATS = ['.gif', '.png',
                               '.jpg', '.jpeg', '.bmp', '.webp']
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.webm', '.mov', '.avi']

    # MIME types
    GIF_MIME_TYPE = "image/gif"
    PNG_MIME_TYPE = "image/png"
    JPEG_MIME_TYPE = "image/jpeg"

    # Default file naming
    DEFAULT_PROJECT_NAME = "untitled"
    BACKUP_SUFFIX = ".backup"
    TEMP_SUFFIX = ".tmp"

    # File size limits (in bytes)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_GIF_SIZE = 50 * 1024 * 1024    # 50MB

    # Quality settings
    DEFAULT_QUALITY = 85
    HIGH_QUALITY = 95
    LOW_QUALITY = 60
