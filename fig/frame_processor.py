"""
Frame processing functionality for the Fig editor.

This module provides the FrameProcessor class which handles all frame manipulation
operations including transformations, drawing, text rendering, cropping, and export.
"""

import traceback
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from PIL import Image, ImageDraw
from fig.image_converter import ImageConverter


@dataclass
class ProcessingOptions:
    """Options for frame processing operations."""
    crop_rect: Tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)  # x, y, width, height (normalized)
    container_size: int = 500
    text_rotation: int = 0
    

@dataclass 
class DrawingData:
    """Data structure for drawing information."""
    points: List[Tuple[float, float]]
    color: str = '#FFFFFF'
    width: int = 2


@dataclass
class TextData:
    """Data structure for text information."""
    x: int
    y: int
    text: str
    color: str = 'white'
    font_size: int = 24


class FrameProcessorError(Exception):
    """Custom exception for frame processing errors."""
    pass


class FrameProcessor:
    """
    Handles all frame processing operations for the GIF editor.
    
    This class provides methods for transforming frames, applying drawings,
    rendering text, cropping, and exporting processed frames to GIF format.
    """
    
    def __init__(self):
        pass
    
    def flip_frames_horizontal(self, frames: List) -> List:
        """
        Flip all frames horizontally.
        
        Args:
            frames: List of GdkPixbuf frames to flip
            
        Returns:
            List of flipped frames
            
        Raises:
            FrameProcessorError: If frame processing fails
        """
        if not frames:
            return frames
            
        try:
            flipped_frames = []
            for frame in frames:
                if frame:
                    pil_image = ImageConverter.pixbuf_to_pil(frame)
                    flipped = pil_image.transpose(Image.FLIP_LEFT_RIGHT)
                    flipped_frames.append(ImageConverter.pil_to_pixbuf(flipped))
                else:
                    flipped_frames.append(frame)
            return flipped_frames
        except Exception as e:
            raise FrameProcessorError(f"Error flipping frames: {str(e)}") from e
    
    def rotate_frames_90(self, frames: List) -> List:
        """
        Rotate all frames 90 degrees clockwise.
        
        Args:
            frames: List of GdkPixbuf frames to rotate
            
        Returns:
            List of rotated frames
            
        Raises:
            FrameProcessorError: If frame processing fails
        """
        if not frames:
            return frames
            
        try:
            rotated_frames = []
            for frame in frames:
                if frame:
                    pil_image = ImageConverter.pixbuf_to_pil(frame)
                    rotated = pil_image.transpose(Image.ROTATE_270)
                    rotated_frames.append(ImageConverter.pil_to_pixbuf(rotated))
                else:
                    rotated_frames.append(frame)
            return rotated_frames
        except Exception as e:
            raise FrameProcessorError(f"Error rotating frames: {str(e)}") from e
    
    def rotate_drawings(
        self, 
        drawings: List[List[Dict]], 
        container_size: int
    ) -> List[List[Dict]]:
        """
        Rotate drawing coordinates for a 90-degree clockwise rotation.
        
        Args:
            drawings: List of frame drawings (each frame contains list of drawing objects)
            container_size: Size of the container for coordinate transformation
            
        Returns:
            Rotated drawings with updated coordinates
        """
        rotated_drawings = []
        for frame_drawings in drawings:
            rotated_frame_drawings = []
            for drawing in frame_drawings:
                rotated_drawing = drawing.copy()
                if 'points' in drawing:
                    rotated_points = []
                    for point in drawing['points']:
                        x, y = point
                        final_x = container_size - y
                        final_y = x
                        rotated_points.append((final_x, final_y))
                    rotated_drawing['points'] = rotated_points
                rotated_frame_drawings.append(rotated_drawing)
            rotated_drawings.append(rotated_frame_drawings)
        return rotated_drawings
    
    def rotate_text_entries(
        self, 
        text_entries: List[Dict], 
        container_size: int
    ) -> Tuple[List[Dict], int]:
        """
        Rotate text entry positions for a 90-degree clockwise rotation.
        
        Args:
            text_entries: List of text entry dictionaries
            container_size: Size of the container for coordinate transformation
            
        Returns:
            Tuple of (updated text entries, new rotation angle)
        """
        rotated_entries = []
        for text_entry in text_entries:
            rotated_entry = text_entry.copy()
            x = text_entry.get('x', 0)
            y = text_entry.get('y', 0)
            
            # Apply rotation transformation for position
            final_y = x
            final_x = container_size - y
            
            rotated_entry['x'] = final_x
            rotated_entry['y'] = final_y
            rotated_entries.append(rotated_entry)
        
        return rotated_entries, 90  # Return new rotation increment
    
    def apply_drawings_to_frame(
        self,
        frame: Image.Image,
        drawings: List[Dict],
        processing_options: ProcessingOptions
    ) -> Image.Image:
        """
        Apply drawing lines to a frame.
        
        Args:
            frame: PIL Image to draw on
            drawings: List of drawing data dictionaries
            processing_options: Processing options for coordinate transformation
            
        Returns:
            Frame with drawings applied
        """
        if not drawings:
            return frame
        
        draw = ImageDraw.Draw(frame)
        orig_width, orig_height = frame.size
        long_side = max(orig_width, orig_height)
        
        for line in drawings:
            if len(line.get('points', [])) > 1:
                # Convert coordinates to image space
                scaled_points = []
                for point in line['points']:
                    if isinstance(point, (list, tuple)) and len(point) >= 2:
                        x, y = point[0], point[1]
                        if long_side == orig_width:
                            y = y - (processing_options.container_size - orig_height) / 2
                        else:
                            x = x - (processing_options.container_size - orig_width) / 2
                        scaled_points.append((x, y))
                
                color = line.get('color', '#FFFFFF')
                width = line.get('width', 2)
                
                # Draw line segments
                for j in range(len(scaled_points) - 1):
                    draw.line([scaled_points[j], scaled_points[j + 1]],
                             fill=color, width=width)
        
        return frame
    
    def apply_text_to_frame(
        self,
        frame: Image.Image,
        text_entries: List[Dict],
        processing_options: ProcessingOptions
    ) -> Image.Image:
        """
        Apply text overlays to a frame.
        
        Args:
            frame: PIL Image to draw text on
            text_entries: List of text entry dictionaries
            processing_options: Processing options including rotation
            
        Returns:
            Frame with text applied
        """
        if not text_entries:
            return frame
        
        orig_width, orig_height = frame.size
        long_side = max(orig_width, orig_height)
        
        for text_entry in text_entries:
            try:
                x = int(text_entry.get('x', 0))
                y = int(text_entry.get('y', 0))
                text = text_entry.get('text', '')
                
                if not text:
                    continue
                
                # Check if we need to apply rotation
                if processing_options.text_rotation != 0:
                    # Create rotated text
                    font_size = 24
                    text_width = len(text) * font_size
                    text_height = font_size * 1.5
                    
                    # Create transparent image for the text
                    text_img = Image.new('RGBA',
                                        (int(max(text_width, text_height) * 3),
                                         int(max(text_width, text_height) * 3)),
                                        (0, 0, 0, 0))
                    
                    # Draw text at center
                    text_draw = ImageDraw.Draw(text_img)
                    text_draw.text((text_img.width//2, text_img.height//2),
                                  text,
                                  fill='white',
                                  anchor='mm')
                    
                    # Rotate the text image
                    rotated_text = text_img.rotate(-processing_options.text_rotation,
                                                  resample=Image.BICUBIC,
                                                  expand=True)
                    
                    # Calculate paste coordinates
                    paste_x = x
                    paste_y = y
                    
                    # Adjust for container padding
                    if long_side == orig_width:
                        paste_y -= (processing_options.container_size - orig_height) // 2
                    else:
                        paste_x -= (processing_options.container_size - orig_width) // 2
                    
                    # Center the rotated text at the specified point
                    paste_x -= rotated_text.width // 2
                    paste_y -= rotated_text.height // 2
                    
                    # Paste using alpha channel as mask
                    frame.paste(rotated_text, (paste_x, paste_y), rotated_text)
                else:
                    # No rotation - draw text directly
                    if long_side == orig_width:
                        y = y - (processing_options.container_size - orig_height) // 2
                    else:
                        x = x - (processing_options.container_size - orig_width) // 2
                    
                    draw = ImageDraw.Draw(frame)
                    draw.text((x, y), text, fill='white')
                    
            except Exception as e:
                print(f"Error applying text to frame: {e}")
                traceback.print_exc()
        
        return frame
    
    def crop_frame(
        self,
        frame: Image.Image,
        crop_rect: Tuple[float, float, float, float]
    ) -> Image.Image:
        """
        Crop a frame using normalized coordinates.
        
        Args:
            frame: PIL Image to crop
            crop_rect: Tuple of (x, y, width, height) in normalized coordinates (0.0-1.0)
            
        Returns:
            Cropped frame
        """
        orig_width, orig_height = frame.size
        left = int(crop_rect[0] * orig_width)
        top = int(crop_rect[1] * orig_height)
        right = int((crop_rect[0] + crop_rect[2]) * orig_width)
        bottom = int((crop_rect[1] + crop_rect[3]) * orig_height)
        
        crop_box = (left, top, right, bottom)
        return frame.crop(crop_box)
    
    def process_and_save_gif(
        self,
        frames: List,
        durations: List[float],
        save_path: str,
        start_idx: int,
        end_idx: int,
        excluded_ranges: List[Tuple[int, int]],
        inserted_ranges: List[Tuple[int, int]],
        drawings: Optional[List[List[Dict]]] = None,
        text_entries: Optional[List[Dict]] = None,
        processing_options: Optional[ProcessingOptions] = None
    ) -> None:
        """
        Process frames and save as GIF with all transformations applied.
        
        Args:
            frames: List of GdkPixbuf frames
            durations: List of frame durations in milliseconds
            save_path: Path to save the GIF
            start_idx: Start index for frame range
            end_idx: End index for frame range
            excluded_ranges: List of (start, end) tuples for excluded frame ranges
            inserted_ranges: List of (start, end) tuples for inserted frame ranges
            drawings: Optional list of drawings to apply
            text_entries: Optional list of text entries to apply
            processing_options: Optional processing options
            
        Raises:
            FrameProcessorError: If processing or saving fails
        """
        if processing_options is None:
            processing_options = ProcessingOptions()
        
        try:
            # Handle reversed range
            is_reversed = start_idx > end_idx
            if is_reversed:
                start_idx, end_idx = end_idx, start_idx
            
            frames_to_save = []
            durations_to_save = []
            
            # Get reference frame for dimensions
            ref_frame = None
            for frame in frames:
                if frame:
                    ref_frame = ImageConverter.pixbuf_to_pil(frame)
                    break
            
            if not ref_frame:
                raise FrameProcessorError("No valid frames to save")
            
            orig_width, orig_height = ref_frame.size
            
            # Process each frame in range
            for i in range(start_idx, end_idx + 1):
                # Skip excluded frames
                if any(start <= i <= end for start, end in excluded_ranges):
                    continue
                if i < 0 or i >= len(frames):
                    continue
                if not frames[i]:
                    continue
                
                # Get frame and duration
                frame = ImageConverter.pixbuf_to_pil(frames[i])
                duration = durations[i]
                
                # Check if this is an inserted frame and resize if needed
                is_inserted = any(start <= i <= end for start, end in inserted_ranges)
                if is_inserted and frame.size != (orig_width, orig_height):
                    frame = frame.resize((orig_width, orig_height), Image.Resampling.LANCZOS)
                
                # Apply drawings if provided
                if drawings and drawings[0]:  # Assuming single frame drawing for now
                    frame = self.apply_drawings_to_frame(
                        frame, drawings[0], processing_options)
                
                # Apply text if provided
                if text_entries:
                    frame = self.apply_text_to_frame(
                        frame, text_entries, processing_options)
                
                # Apply cropping
                frame = self.crop_frame(frame, processing_options.crop_rect)
                
                frames_to_save.append(frame)
                durations_to_save.append(duration)
            
            # Reverse if needed
            if is_reversed:
                frames_to_save.reverse()
                durations_to_save.reverse()
            
            # Save GIF
            if frames_to_save:
                frames_to_save[0].save(
                    save_path,
                    save_all=True,
                    append_images=frames_to_save[1:],
                    duration=durations_to_save,
                    loop=0,
                    format='GIF'
                )
            else:
                raise FrameProcessorError("No frames to save after processing")
                
        except Exception as e:
            if isinstance(e, FrameProcessorError):
                raise
            raise FrameProcessorError(f"Error processing and saving GIF: {str(e)}") from e
    
    def resize_frames_to_match(
        self,
        frames: List,
        target_size: Tuple[int, int]
    ) -> List:
        """
        Resize all frames to match a target size.
        
        Args:
            frames: List of GdkPixbuf frames to resize
            target_size: Target (width, height) tuple
            
        Returns:
            List of resized frames
        """
        if not frames:
            return frames
        
        try:
            resized_frames = []
            for frame in frames:
                if frame:
                    pil_image = ImageConverter.pixbuf_to_pil(frame)
                    if pil_image.size != target_size:
                        resized = pil_image.resize(target_size, Image.Resampling.LANCZOS)
                        resized_frames.append(ImageConverter.pil_to_pixbuf(resized))
                    else:
                        resized_frames.append(frame)
                else:
                    resized_frames.append(frame)
            return resized_frames
        except Exception as e:
            raise FrameProcessorError(f"Error resizing frames: {str(e)}") from e
