# /// script
# dependencies = [
#   "pillow",
#   "ultralytics",
# ]
# ///

import os
import shutil
import tkinter as tk
from PIL import Image, ImageTk
from ultralytics import YOLO

# Configuration Parameters (Locked to 9:16 Portrait)
TARGET_DIR = os.getcwd()
BACKUP_DIR = "_backup_originals"
TARGET_ASPECT_RATIO = 9 / 16
TOLERANCE = 0.02
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class AutoCropAppPortrait:
    def __init__(self, root, file_list):
        self.root = root
        self.root.title("9:16 Portrait Crop Tool (Cat Auto-Centering)")
        self.root.geometry("1280x800")

        self.file_list = file_list
        self.current_idx = 0
        self.is_cropped = False

        print("Loading YOLO model for cat detection...")
        self.model = YOLO("yolov8n.pt")

        self.canvas = tk.Canvas(root, bg="#222222", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.info_label = tk.Label(
            root,
            text="",
            fg="white",
            bg="#111111",
            font=("Arial", 12),
            anchor="w",
            padx=5,
            pady=5,
        )
        self.info_label.pack(fill=tk.X, side=tk.BOTTOM)

        # Bind Mouse & Key Events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        self.canvas.bind("<Button-4>", lambda e: self.zoom_box(1.05))  # Linux scroll up
        self.canvas.bind(
            "<Button-5>", lambda e: self.zoom_box(0.95)
        )  # Linux scroll down

        self.root.bind("<Up>", lambda e: self.zoom_box(1.05))
        self.root.bind("<Down>", lambda e: self.zoom_box(0.95))
        self.root.bind("c", lambda e: self.apply_crop_preview())
        self.root.bind("z", lambda e: self.reset_crop_preview())
        self.root.bind("<Return>", lambda e: self.save_crop())
        self.root.bind("<space>", lambda e: self.save_crop())
        self.root.bind("r", lambda e: self.rotate_image_cw())
        self.root.bind("s", lambda e: self.skip_image())
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        self.load_next_image()

    def load_next_image(self):
        if self.current_idx >= len(self.file_list):
            print("All non-portrait images processed!")
            self.root.destroy()
            return

        self.is_cropped = False
        self.current_file = self.file_list[self.current_idx]
        self.img_path = os.path.join(TARGET_DIR, self.current_file)

        img = Image.open(self.img_path).convert("RGB")
        self.orig_img = Image.ops.exif_transpose(img) if hasattr(Image, "ops") else img

        self.refresh_display_and_box()

    def refresh_display_and_box(self):
        self.img_w, self.img_h = self.orig_img.size

        raw_w = self.canvas.winfo_width()
        raw_h = self.canvas.winfo_height()
        canvas_w = raw_w if raw_w > 1 else 1280
        canvas_h = raw_h if raw_h > 1 else 750

        self.scale = min(canvas_w / self.img_w, canvas_h / self.img_h) * 0.9
        self.display_w = max(1, int(self.img_w * self.scale))
        self.display_h = max(1, int(self.img_h * self.scale))
        self.offset_x = (canvas_w - self.display_w) // 2
        self.offset_y = (canvas_h - self.display_h) // 2

        resized = self.orig_img.resize(
            (self.display_w, self.display_h), Image.Resampling.LANCZOS
        )
        self.tk_img = ImageTk.PhotoImage(resized)

        self.canvas.delete("all")
        self.canvas.create_image(
            self.offset_x, self.offset_y, anchor=tk.NW, image=self.tk_img
        )

        if not self.is_cropped:
            center_x, center_y = self.detect_cat_center()
            self.init_crop_box(center_x, center_y)
        self.update_info_label()

    def rotate_image_cw(self):
        if self.is_cropped:
            return
        self.orig_img = self.orig_img.transpose(Image.Transpose.ROTATE_270)
        self.refresh_display_and_box()

    def detect_cat_center(self):
        try:
            results = self.model(self.orig_img, verbose=False)[0]
            for box in results.boxes:
                if int(box.cls[0]) == 15:  # Class ID 15 = Cat
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    return (x1 + x2) / 2, (y1 + y2) / 2
        except Exception as e:
            print(f"Detection note for {self.current_file}: {e}")

        return self.img_w / 2, self.img_h / 2

    def init_crop_box(self, center_x, center_y):
        ratio = TARGET_ASPECT_RATIO

        if self.img_w / self.img_h > ratio:
            crop_h = self.img_h
            crop_w = crop_h * ratio
        else:
            crop_w = self.img_w
            crop_h = crop_w / ratio

        left = max(0, min(self.img_w - crop_w, center_x - (crop_w / 2)))
        top = max(0, min(self.img_h - crop_h, center_y - (crop_h / 2)))

        self.box_x1 = self.offset_x + (left * self.scale)
        self.box_y1 = self.offset_y + (top * self.scale)
        self.box_x2 = self.box_x1 + (crop_w * self.scale)
        self.box_y2 = self.box_y1 + (crop_h * self.scale)

        self.draw_crop_box()

    def draw_crop_box(self):
        self.canvas.delete("crop_rect")
        if not self.is_cropped:
            self.canvas.create_rectangle(
                self.box_x1,
                self.box_y1,
                self.box_x2,
                self.box_y2,
                outline="#00FF00",
                width=3,
                tags="crop_rect",
            )

    def on_mouse_down(self, event):
        if self.is_cropped:
            return
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_mouse_drag(self, event):
        if self.is_cropped:
            return
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        box_w = self.box_x2 - self.box_x1
        box_h = self.box_y2 - self.box_y1

        min_x, max_x = self.offset_x, self.offset_x + self.display_w - box_w
        min_y, max_y = self.offset_y, self.offset_y + self.display_h - box_h

        new_x1 = max(min_x, min(max_x, self.box_x1 + dx))
        new_y1 = max(min_y, min(max_y, self.box_y1 + dy))

        self.box_x1, self.box_y1 = new_x1, new_y1
        self.box_x2, self.box_y2 = new_x1 + box_w, new_y1 + box_h

        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.draw_crop_box()

    def on_scroll(self, event):
        if event.delta > 0:
            self.zoom_box(1.05)
        elif event.delta < 0:
            self.zoom_box(0.95)

    def zoom_box(self, factor):
        if self.is_cropped:
            return

        center_x = (self.box_x1 + self.box_x2) / 2
        center_y = (self.box_y1 + self.box_y2) / 2

        curr_w = self.box_x2 - self.box_x1
        curr_h = self.box_y2 - self.box_y1

        new_w = curr_w * factor
        new_h = new_w / TARGET_ASPECT_RATIO

        max_w = self.display_w
        max_h = self.display_h

        if new_w > max_w or new_h > max_h:
            new_w = max_w
            new_h = new_w / TARGET_ASPECT_RATIO
        elif new_w < 50:
            new_w = 50
            new_h = new_w / TARGET_ASPECT_RATIO

        new_x1 = center_x - (new_w / 2)
        new_y1 = center_y - (new_h / 2)

        min_x, max_x = self.offset_x, self.offset_x + self.display_w - new_w
        min_y, max_y = self.offset_y, self.offset_y + self.display_h - new_h

        self.box_x1 = max(min_x, min(max_x, new_x1))
        self.box_y1 = max(min_y, min(max_y, new_y1))
        self.box_x2 = self.box_x1 + new_w
        self.box_y2 = self.box_y1 + new_h

        self.draw_crop_box()

    def apply_crop_preview(self):
        """Action 'C': Crop the preview window to show final result before save."""
        if self.is_cropped:
            return

        crop_x1 = max(0, int((self.box_x1 - self.offset_x) / self.scale))
        crop_y1 = max(0, int((self.box_y1 - self.offset_y) / self.scale))
        crop_x2 = min(self.img_w, int((self.box_x2 - self.offset_x) / self.scale))
        crop_y2 = min(self.img_h, int((self.box_y2 - self.offset_y) / self.scale))

        self.preview_cropped_img = self.orig_img.crop(
            (crop_x1, crop_y1, crop_x2, crop_y2)
        )
        self.is_cropped = True

        raw_w = self.canvas.winfo_width() or 1280
        raw_h = self.canvas.winfo_height() or 750

        pw, ph = self.preview_cropped_img.size
        scale = min(raw_w / pw, raw_h / ph) * 0.9
        disp_w, disp_h = max(1, int(pw * scale)), max(1, int(ph * scale))
        off_x, off_y = (raw_w - disp_w) // 2, (raw_h - disp_h) // 2

        resized = self.preview_cropped_img.resize(
            (disp_w, disp_h), Image.Resampling.LANCZOS
        )
        self.tk_img = ImageTk.PhotoImage(resized)

        self.canvas.delete("all")
        self.canvas.create_image(off_x, off_y, anchor=tk.NW, image=self.tk_img)
        self.update_info_label()

    def reset_crop_preview(self):
        """Action 'Z': Reset crop preview back to full image edit mode."""
        if not self.is_cropped:
            return
        self.is_cropped = False
        self.refresh_display_and_box()

    def save_crop(self):
        """Action 'Enter' / 'Space': Write crop to disk and advance."""
        if not self.is_cropped:
            self.apply_crop_preview()

        final_img = self.preview_cropped_img.resize(
            (1080, 1920), Image.Resampling.LANCZOS
        )

        os.makedirs(BACKUP_DIR, exist_ok=True)
        backup_path = os.path.join(BACKUP_DIR, self.current_file)
        out_path = os.path.join(
            TARGET_DIR, os.path.splitext(self.current_file)[0] + ".jpg"
        )

        self.orig_img.close()
        shutil.move(self.img_path, backup_path)
        final_img.save(out_path, "JPEG", quality=90, optimize=True)

        print(f"Saved portrait crop: {self.current_file} -> 1080x1920")
        self.current_idx += 1
        self.load_next_image()

    def skip_image(self):
        print(f"Skipped {self.current_file}")
        self.orig_img.close()
        self.current_idx += 1
        self.load_next_image()

    def update_info_label(self):
        status = "CROPPED PREVIEW" if self.is_cropped else "SELECTING FRAME"
        self.info_label.config(
            text=f"[{self.current_idx + 1}/{len(self.file_list)}] {self.current_file} | Status: {status} | "
            f"Controls: Scroll/Up/Down = Zoom, 'C' = Crop, 'Z' = Reset, Enter/Space = Save, 'R' = Rotate, 'S' = Skip"
        )


def get_non_portrait_images():
    files_to_process = []
    for f in os.listdir(TARGET_DIR):
        if not os.path.isfile(os.path.join(TARGET_DIR, f)):
            continue
        ext = os.path.splitext(f)[1].lower()
        if ext not in IMAGE_EXTS:
            continue

        try:
            with Image.open(os.path.join(TARGET_DIR, f)) as img:
                w, h = img.size
                ratio = w / h
                if abs(ratio - TARGET_ASPECT_RATIO) >= TOLERANCE:
                    files_to_process.append(f)
        except Exception:
            continue
    return files_to_process


def main():
    files = get_non_portrait_images()
    if not files:
        print("No images found that require portrait cropping.")
        return

    print(f"Found {len(files)} non-portrait images to crop.")
    root = tk.Tk()
    app = AutoCropAppPortrait(root, files)
    root.mainloop()


if __name__ == "__main__":
    main()
