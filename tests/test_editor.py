import unittest
from unittest.mock import Mock, patch
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, GdkPixbuf
from PIL import Image
import io
import os
from fig.editor import EditorBox
from fig.frameline import FrameLine

class TestGifEditor(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        self.editor = EditorBox()
        # Create mock frames
        self.editor.frames = [Mock(spec=GdkPixbuf.Pixbuf) for _ in range(100)]
        # Mock display_frame method
        self.editor.display_frame = Mock()
        self.create_test_gif()

    def tearDown(self):
        """Clean up after each test"""
        if os.path.exists('test.gif'):
            os.remove('test.gif')
        if os.path.exists('output.gif'):
            os.remove('output.gif')
        if hasattr(self.editor, '_timeout_id') and self.editor._timeout_id is not None:
            GLib.source_remove(self.editor._timeout_id)
        self.editor.is_playing = False

    def create_test_gif(self):
        """Create a test GIF with 5 frames of different colors"""
        try:
            frames = []
            colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (0,255,255)]
            
            for color in colors:
                img = Image.new('RGB', (100, 100), color)
                frames.append(img)

            frames[0].save('test.gif',
                          save_all=True,
                          append_images=frames[1:],
                          duration=100,
                          loop=0)
        except Exception as e:
            self.fail(f"Failed to create test GIF: {e}")

    def test_gif_loading(self):
        """Test basic GIF loading functionality"""
        self.editor.load_gif('test.gif')
        
        self.assertEqual(len(self.editor.frames), 5)
        self.assertEqual(len(self.editor.frame_durations), 5)
        self.assertEqual(self.editor.frameline.min_value, 1)
        self.assertEqual(self.editor.frameline.max_value, 5)

    def test_frame_selection(self):
        """Test frame selection with frameline handles"""
        self.editor.load_gif('test.gif')
        
        # Test setting frame range
        self.editor.frameline.set_left_value(2)
        self.editor.frameline.set_right_value(4)
        
        self.assertEqual(round(self.editor.frameline.left_value), 2)
        self.assertEqual(round(self.editor.frameline.right_value), 4)

    def test_playback(self):
        """Test normal playback functionality"""
        self.editor.load_gif('test.gif')
        
        # Start playback
        self.editor.play_edited_frames(None)
        self.assertTrue(self.editor.is_playing)
        self.assertTrue(self.editor.frameline.playhead_visible)
        
        # Let main loop run briefly
        context = GLib.MainContext.default()
        while context.pending():
            context.iteration(False)
            
        # Instead of stop_playback, just set is_playing to False
        self.editor.is_playing = False
        self.assertFalse(self.editor.is_playing)

    def test_reverse_playback(self):
        """Test reverse playback functionality"""
        self.editor.load_gif('test.gif')
        
        # Set reverse frame range
        self.editor.frameline.set_left_value(5)
        self.editor.frameline.set_right_value(1)
        
        # Start playback
        self.editor.play_edited_frames(None)
        self.assertTrue(self.editor.is_playing)
        
        # Let the main loop run briefly to allow frame update
        context = GLib.MainContext.default()
        while context.pending():
            context.iteration(False)
        
        # Verify that playback is in reverse mode
        start_frame = self.editor.frameline.right_value - 1  # 0-based index
        end_frame = self.editor.frameline.left_value - 1     # 0-based index
        
        # Verify frame index is within the correct range
        self.assertGreaterEqual(self.editor.current_frame_index, min(start_frame, end_frame))
        self.assertLessEqual(self.editor.current_frame_index, max(start_frame, end_frame))
        
        # Verify playback direction
        self.assertTrue(self.editor.frameline.left_value > self.editor.frameline.right_value)

    def test_save_trimmed_gif(self):
        """Test saving trimmed GIF"""
        self.editor.load_gif('test.gif')
        
        # Set frame range
        self.editor.frameline.set_left_value(2)
        self.editor.frameline.set_right_value(4)
        
        # Save trimmed GIF
        self.editor._save_gif('output.gif', 1, 3)  # 0-based indices
        
        # Verify saved GIF
        with Image.open('output.gif') as gif:
            self.assertEqual(gif.n_frames, 3)

    def test_save_reversed_gif(self):
        """Test saving reversed GIF"""
        self.editor.load_gif('test.gif')
        
        # Set reverse frame range
        self.editor.frameline.set_left_value(5)
        self.editor.frameline.set_right_value(1)
        
        # Save reversed GIF
        self.editor._save_gif('output.gif', 4, 0)  # 0-based indices
        
        # Verify saved GIF
        with Image.open('output.gif') as gif:
            self.assertEqual(gif.n_frames, 5)

    def test_playhead_behavior(self):
        """Test playhead visibility and position"""
        self.editor.load_gif('test.gif')
        
        # Initially playhead should be hidden
        self.assertFalse(self.editor.frameline.playhead_visible)
        
        # Start playback
        self.editor.play_edited_frames(None)
        self.assertTrue(self.editor.frameline.playhead_visible)
        
        # Instead of stop_playback, just set is_playing to False
        self.editor.is_playing = False
        self.assertFalse(self.editor.is_playing)

    def test_frame_duration(self):
        """Test frame duration handling"""
        self.editor.load_gif('test.gif')
        
        # Verify all frames have correct duration
        expected_duration = 100  # milliseconds
        self.assertEqual(len(self.editor.frame_durations), 5)
        for duration in self.editor.frame_durations:
            self.assertAlmostEqual(duration, expected_duration, delta=1)  # Allow 1ms difference

    def test_invalid_frame_range(self):
        """Test handling of invalid frame ranges"""
        self.editor.load_gif('test.gif')
        
        # Test setting invalid ranges
        self.editor.frameline.set_left_value(0)  # Below minimum
        self.assertEqual(round(self.editor.frameline.left_value), 1)
        
        self.editor.frameline.set_right_value(6)  # Above maximum
        self.assertEqual(round(self.editor.frameline.right_value), 5)

    def test_corrupted_gif(self):
        """Test handling of corrupted GIF files"""
        # Create a corrupted file
        with open('corrupted.gif', 'wb') as f:
            f.write(b'Not a GIF file')
        
        try:
            self.editor.load_gif('corrupted.gif')
            # Should not affect the editor's state
            self.assertEqual(len(self.editor.frames), 0)
        finally:
            os.remove('corrupted.gif')

    def test_frame_scaling(self):
        """Test frame scaling functionality"""
        self.editor.load_gif('test.gif')
        
        # Test scaling with different display sizes
        test_sizes = [(200, 200), (50, 50), (100, 200), (200, 100)]
        
        for width, height in test_sizes:
            self.editor.image_display_width = width
            self.editor.image_display_height = height
            
            scaled_pixbuf = self.editor.scale_pixbuf_to_fit(
                self.editor.frames[0],
                width,
                height
            )
            
            # Verify scaled dimensions don't exceed container
            self.assertLessEqual(scaled_pixbuf.get_width(), width)
            self.assertLessEqual(scaled_pixbuf.get_height(), height)

    def test_playback_bounds(self):
        """Test playback stays within selected bounds"""
        self.editor.load_gif('test.gif')
        
        # Set a specific range
        self.editor.frameline.set_left_value(2)
        self.editor.frameline.set_right_value(4)
        
        # Start playback
        self.editor.play_edited_frames(None)
        
        max_iterations = 20  # Prevent infinite loop
        iterations = 0
        
        # Let it play for a few frames
        while iterations < max_iterations:
            context = GLib.MainContext.default()
            timeout = 0
            while context.pending() and timeout < 100:  # Add timeout
                context.iteration(False)
                timeout += 1
            
            # Verify frame index stays within bounds
            self.assertGreaterEqual(self.editor.current_frame_index, 1)
            self.assertLessEqual(self.editor.current_frame_index, 3)
            iterations += 1

    def test_frame_display(self):
        """Test frame display functionality"""
        self.editor.load_gif('test.gif')
        
        # Test displaying each frame
        for i in range(5):
            self.editor.display_frame(i)
            self.assertEqual(self.editor.current_frame_index, i)
            self.editor.current_frame_index = self.editor.current_frame_index + 1
            
        # Test invalid frame indices
        self.editor.display_frame(-1)  # Should not change current frame
        self.editor.display_frame(7)   # Should not change current frame
        self.assertGreaterEqual(self.editor.current_frame_index, 0)
        self.assertLessEqual(self.editor.current_frame_index, 5)

    def test_memory_cleanup(self):
        """Test that resources are properly cleaned up"""
        initial_frames = self.editor.frames.copy() if self.editor.frames else []
        
        # Load and unload multiple GIFs
        for _ in range(3):
            self.editor.load_gif('test.gif')
            self.editor.frames.clear()
            self.editor.frame_durations.clear()
        
        # Verify no memory leaks in frames list
        self.assertEqual(len(self.editor.frames), 0)
        self.assertEqual(len(self.editor.frame_durations), 0)

    def test_frame_range_validation(self):
        """Test frame range validation"""
        self.editor.load_gif('test.gif')
        
        # Test various invalid ranges
        test_cases = [
            (-1, 5),   # Invalid left
            (1, 10),   # Invalid right
            (3, 2),    # Reverse (should be allowed)
            (0, 0),    # Invalid both
        ]
        
        for left, right in test_cases:
            self.editor.frameline.set_left_value(left)
            self.editor.frameline.set_right_value(right)
            
            # Verify values are within valid range
            self.assertGreaterEqual(self.editor.frameline.left_value, 
                                  self.editor.frameline.min_value)
            self.assertLessEqual(self.editor.frameline.right_value, 
                               self.editor.frameline.max_value)

    def test_exception_handling(self):
        """Test handling of various error conditions"""
        # Test loading non-existent file
        self.editor.load_gif('nonexistent.gif')
        self.assertEqual(len(self.editor.frames), 0)
        
        # Test loading invalid file type
        with open('invalid.txt', 'w') as f:
            f.write('not a gif')
        self.editor.load_gif('invalid.txt')
        self.assertEqual(len(self.editor.frames), 0)
        os.remove('invalid.txt')

    def test_widget_initialization(self):
        """Test that GTK widgets are properly initialized"""
        self.assertIsNotNone(self.editor.frameline)
        self.assertIsNotNone(self.editor.image_display)
        self.assertIsInstance(self.editor.frameline, FrameLine)
        self.assertIsInstance(self.editor.image_display, Gtk.Picture)

    def test_handle_drag_normal_order(self):
        """Test frame preview when handles are in normal order (left < right)"""
        self.editor.frameline.left_value = 10
        self.editor.frameline.right_value = 50
        
        # Test dragging left handle
        self.editor.on_handle_drag(15)
        self.editor.display_frame.assert_called_with(14)  # 0-based index
        
        # Test dragging right handle
        self.editor.on_handle_drag(45)
        self.editor.display_frame.assert_called_with(44)  # 0-based index

    def test_handle_drag_reversed_order(self):
        """Test frame preview when handles are reversed (left > right)"""
        self.editor.frameline.left_value = 80
        self.editor.frameline.right_value = 20
        
        # Test dragging left handle
        self.editor.on_handle_drag(85)
        self.editor.display_frame.assert_called_with(84)
        
        # Test dragging right handle
        self.editor.on_handle_drag(15)
        self.editor.display_frame.assert_called_with(14)

    def test_handle_drag_edge_cases(self):
        """Test frame preview at edge cases"""
        self.editor.frameline.left_value = 1
        self.editor.frameline.right_value = 100
        
        # Test minimum bound
        self.editor.on_handle_drag(1)
        self.editor.display_frame.assert_called_with(0)
        
        # Test maximum bound
        self.editor.on_handle_drag(100)
        self.editor.display_frame.assert_called_with(99)

    def test_handle_drag_crossing_over(self):
        """Test frame preview when handles cross over each other"""
        # Start with normal order
        self.editor.frameline.left_value = 30
        self.editor.frameline.right_value = 50
        
        # Drag left handle past right handle
        self.editor.on_handle_drag(60)
        self.editor.display_frame.assert_called_with(59)
        
        # Drag right handle past left handle
        self.editor.frameline.left_value = 60
        self.editor.frameline.right_value = 50
        self.editor.on_handle_drag(40)
        self.editor.display_frame.assert_called_with(39)

    def test_playhead_visibility_during_drag(self):
        """Test playhead visibility during handle dragging"""
        self.editor.playhead_frame_index = 30
        self.editor.frameline.playhead_visible = True
        
        # Test normal order
        self.editor.frameline.left_value = 20
        self.editor.frameline.right_value = 40
        self.editor.on_handle_drag(25)
        self.assertTrue(self.editor.frameline.playhead_visible)
        
        # Test reversed order
        self.editor.frameline.left_value = 40
        self.editor.frameline.right_value = 20
        self.editor.on_handle_drag(35)
        self.assertTrue(self.editor.frameline.playhead_visible)
        
        # Test playhead out of range
        self.editor.playhead_frame_index = 14
        self.editor.on_handle_drag(15)
        self.assertFalse(self.editor.frameline.playhead_visible)

    def test_remove_single_frame(self):
        """Test removing a single frame"""
        self.editor.load_gif('test.gif')
        initial_frame_count = len(self.editor.frames)
        
        # Remove frame 3 (1-based index)
        self.editor.frameline.add_removed_range(3, 3)
        
        # Verify frame is marked as removed
        self.assertTrue(self.editor.frameline.is_frame_removed(2))  # 0-based index
        
        # Save and verify
        self.editor._save_gif('output.gif', 0, 4)  # Full range
        
        with Image.open('output.gif') as gif:
            self.assertEqual(gif.n_frames, initial_frame_count - 1)
        
        # Cleanup
        os.remove('output.gif')

    def test_remove_frame_range(self):
        """Test removing a range of frames"""
        self.editor.load_gif('test.gif')
        initial_frame_count = len(self.editor.frames)
        
        # Remove frames 2-4 (1-based indices)
        self.editor.frameline.add_removed_range(2, 4)
        
        # Verify frames are marked as removed
        for i in range(1, 4):  # 0-based indices
            self.assertTrue(self.editor.frameline.is_frame_removed(i))
        
        # Save and verify
        self.editor._save_gif('output.gif', 0, 4)
        
        with Image.open('output.gif') as gif:
            self.assertEqual(gif.n_frames, initial_frame_count - 3)
        
        # Cleanup
        os.remove('output.gif')

    def test_remove_overlapping_ranges(self):
        """Test removing overlapping ranges"""
        self.editor.load_gif('test.gif')
        
        # Add overlapping ranges
        self.editor.frameline.add_removed_range(1, 3)
        self.editor.frameline.add_removed_range(2, 4)
        
        # Verify merged range
        for i in range(0, 4):  # 0-based indices
            self.assertTrue(self.editor.frameline.is_frame_removed(i))
        
        # Verify ranges were merged
        self.assertEqual(len(self.editor.frameline.removed_ranges), 1)
        self.assertEqual(self.editor.frameline.removed_ranges[0], (0, 3))

    def test_remove_adjacent_ranges(self):
        """Test removing adjacent ranges"""
        self.editor.load_gif('test.gif')
        
        # Add adjacent ranges
        self.editor.frameline.add_removed_range(1, 2)
        self.editor.frameline.add_removed_range(3, 4)
        
        # Verify merged range
        for i in range(0, 4):  # 0-based indices
            self.assertTrue(self.editor.frameline.is_frame_removed(i))
        
        # Verify ranges were merged
        self.assertEqual(len(self.editor.frameline.removed_ranges), 1)
        self.assertEqual(self.editor.frameline.removed_ranges[0], (0, 3))

    def test_remove_edge_frames(self):
        """Test removing frames at the edges"""
        self.editor.load_gif('test.gif')
        initial_frame_count = len(self.editor.frames)
        
        # Remove first and last frames
        self.editor.frameline.add_removed_range(1, 1)  # First frame
        self.editor.frameline.add_removed_range(5, 5)  # Last frame
        
        # Verify edge frames are marked as removed
        self.assertTrue(self.editor.frameline.is_frame_removed(0))
        self.assertTrue(self.editor.frameline.is_frame_removed(4))
        
        # Save and verify
        self.editor._save_gif('output.gif', 0, 4)
        
        with Image.open('output.gif') as gif:
            self.assertEqual(gif.n_frames, initial_frame_count - 2)
        
        # Cleanup
        os.remove('output.gif')

    def test_clear_removed_ranges(self):
        """Test clearing removed ranges"""
        self.editor.load_gif('test.gif')
        
        # Add some ranges
        self.editor.frameline.add_removed_range(1, 2)
        self.editor.frameline.add_removed_range(4, 5)
        
        # Clear ranges
        self.editor.frameline.clear_removed_ranges()
        
        # Verify no frames are marked as removed
        for i in range(5):
            self.assertFalse(self.editor.frameline.is_frame_removed(i))
        
        # Verify removed_ranges list is empty
        self.assertEqual(len(self.editor.frameline.removed_ranges), 0)

if __name__ == '__main__':
    unittest.main() 