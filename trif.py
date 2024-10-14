import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class GIFCutterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Cutter")

        self.label = tk.Label(root, text="Select a GIF to cut:")
        self.label.pack(pady=10)

        self.select_button = tk.Button(root, text="Select GIF", command=self.select_gif)
        self.select_button.pack(pady=5)

        self.info_label = tk.Label(root, text="Total frames: 0 | Total time: 0.0 seconds")
        self.info_label.pack(pady=5)

        self.frame_range_label = tk.Label(root, text="Select frame range:")
        self.frame_range_label.pack(pady=5)

        self.start_frame_label = tk.Label(root, text="Start frame:")
        self.start_frame_label.pack()

        self.start_frame_number = tk.IntVar(value=0)
        self.start_frame_entry = tk.Entry(root, textvariable=self.start_frame_number)
        self.start_frame_entry.pack(pady=5)

        self.end_frame_label = tk.Label(root, text="End frame:")
        self.end_frame_label.pack()

        self.end_frame_number = tk.IntVar(value=0)
        self.end_frame_entry = tk.Entry(root, textvariable=self.end_frame_number)
        self.end_frame_entry.pack(pady=5)

        self.save_button = tk.Button(root, text="Save Frames", state=tk.DISABLED, command=self.save_frames)
        self.save_button.pack(pady=10)

        self.image_label = tk.Label(root)
        self.image_label.pack()

        self.gif_frames = []
        self.frame_durations = []

    def select_gif(self):
        file_path = filedialog.askopenfilename(filetypes=[("GIF files", "*.gif")])
        if file_path:
            try:
                gif = Image.open(file_path)
                self.gif_frames = []
                self.frame_durations = []

                total_duration = 0

                for frame in range(gif.n_frames):
                    gif.seek(frame)
                    frame_image = gif.copy().convert("RGBA")
                    self.gif_frames.append(frame_image)

                    # Store frame duration in milliseconds
                    frame_duration = gif.info.get('duration', 100) / 1000.0  # default 100 ms per frame
                    self.frame_durations.append(frame_duration)
                    total_duration += frame_duration

                self.info_label.config(text=f"Total frames: {gif.n_frames} | Total time: {total_duration:.2f} seconds")
                self.start_frame_number.set(0)
                self.end_frame_number.set(gif.n_frames - 1)
                self.show_frame(0)
                self.save_button.config(state=tk.NORMAL)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load GIF: {str(e)}")

    def show_frame(self, frame_idx):
        if 0 <= frame_idx < len(self.gif_frames):
            frame_image = self.gif_frames[frame_idx]
            frame_image_tk = ImageTk.PhotoImage(frame_image)
            self.image_label.config(image=frame_image_tk)
            self.image_label.image = frame_image_tk

    def save_frames(self):
        start_idx = self.start_frame_number.get()
        end_idx = self.end_frame_number.get()

        if 0 <= start_idx < len(self.gif_frames) and 0 <= end_idx < len(self.gif_frames) and start_idx <= end_idx:
            save_path = filedialog.asksaveasfilename(defaultextension=".gif", filetypes=[("GIF files", "*.gif")])
            if save_path:
                frames_to_save = self.gif_frames[start_idx:end_idx+1]
                frame_durations_to_save = self.frame_durations[start_idx:end_idx+1]
                frames_to_save[0].save(
                    save_path,
                    save_all=True,
                    append_images=frames_to_save[1:],
                    duration=[int(d * 1000) for d in frame_durations_to_save],
                    loop=0
                )
                messagebox.showinfo("Success", f"Frames {start_idx} to {end_idx} saved as {save_path}")
        else:
            messagebox.showerror("Error", "Invalid frame range")

if __name__ == "__main__":
    root = tk.Tk()
    app = GIFCutterApp(root)
    root.mainloop()
