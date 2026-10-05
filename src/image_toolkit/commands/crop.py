from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageTk
from rich.console import Console

from .. import constants
from ..core import files, images

console = Console()


class AutoCropAppPortrait:
    def __init__(self, root, file_list: list[str]) -> None:
        self.root = root
        self.root.title("9:16 Portrait Crop Tool (Cat Auto-Centering)")
        self.root.geometry("1280x800")

        self.file_list = file_list
        self.current_idx = 0
        self.is_cropped = False
        self.tk_img = None
        self.orig_img = None
        self.preview_cropped_img = None

        console.print("Loading YOLO model for cat detection...")
        try:
            from ultralytics import YOLO

            self.model = YOLO(constants.YOLO_MODEL)
        except (OSError, RuntimeError, ImportError):
            self.model = None

        import tkinter as tk

        self.canvas = tk.Canvas(root, bg="#222222", cursor="cross")
        self.canvas.pack(fill="both", expand=True)

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
        self.info_label.pack(fill="x", side="bottom")

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        self.canvas.bind("<Button-4>", lambda e: self.zoom_box(1.05))
        self.canvas.bind("<Button-5>", lambda e: self.zoom_box(0.95))

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

    def load_next_image(self) -> None:
        if self.current_idx >= len(self.file_list):
            console.print("All non-portrait images processed!")
            self.root.destroy()
            return
        self.is_cropped = False
        self.current_file = self.file_list[self.current_idx]
        self.img_path = constants.TARGET_DIR / self.current_file
        try:
            with images.open_with_exif(self.img_path) as img:
                self.orig_img = img.copy().convert("RGB")
        except Exception:
            self.skip_image()
            return
        self.refresh_display_and_box()

    def refresh_display_and_box(self) -> None:
        if self.orig_img is None:
            return
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
        resized = self.orig_img.resize((self.display_w, self.display_h), Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(resized)
        self.canvas.delete("all")
        self.canvas.create_image(self.offset_x, self.offset_y, anchor="nw", image=self.tk_img)
        if not self.is_cropped:
            center_x, center_y = self.detect_cat_center()
            self.init_crop_box(center_x, center_y)
        self.update_info_label()

    def rotate_image_cw(self) -> None:
        if self.is_cropped or self.orig_img is None:
            return
        self.orig_img = self.orig_img.transpose(Image.Transpose.ROTATE_270)
        self.refresh_display_and_box()

    def detect_cat_center(self) -> tuple[float, float]:
        if self.model is None or self.orig_img is None:
            return self.img_w / 2.0, self.img_h / 2.0
        try:
            try:
                results_iter = self.model(self.orig_img, verbose=False)
                results = next(iter(results_iter), None)
            except Exception:
                results = None
            if results is None:
                return self.img_w / 2.0, self.img_h / 2.0
            boxes_obj = getattr(results, "boxes", None)
            if boxes_obj is None:
                return self.img_w / 2.0, self.img_h / 2.0
            try:
                for box in boxes_obj:
                    try:
                        cls_list = getattr(box, "cls", [])
                        if not cls_list:
                            continue
                        if int(cls_list[0]) == constants.CAT_CLASS_ID:
                            xyxy = getattr(box, "xyxy", [])
                            if not xyxy:
                                continue
                            first = xyxy[0]
                            vals = first.tolist() if hasattr(first, "tolist") else []
                            if len(vals) >= 4:
                                x1, y1, x2, y2 = vals[0], vals[1], vals[2], vals[3]
                                return (x1 + x2) / 2.0, (y1 + y2) / 2.0
                    except (ValueError, AttributeError, IndexError):
                        continue
            except (TypeError, AttributeError):
                pass
        except Exception as e:
            console.print(f"Detection note for {self.current_file}: {e}")
        return self.img_w / 2.0, self.img_h / 2.0

    def init_crop_box(self, center_x: float, center_y: float) -> None:
        ratio = constants.PORTRAIT_ASPECT
        if self.img_w / self.img_h > ratio:
            crop_h = self.img_h
            crop_w = crop_h * ratio
        else:
            crop_w = self.img_w
            crop_h = crop_w / ratio
        left = max(0.0, min(self.img_w - crop_w, center_x - (crop_w / 2.0)))
        top = max(0.0, min(self.img_h - crop_h, center_y - (crop_h / 2.0)))
        self.box_x1 = self.offset_x + (left * self.scale)
        self.box_y1 = self.offset_y + (top * self.scale)
        self.box_x2 = self.box_x1 + (crop_w * self.scale)
        self.box_y2 = self.box_y1 + (crop_h * self.scale)
        self.draw_crop_box()

    def draw_crop_box(self) -> None:
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

    def on_mouse_down(self, event) -> None:
        if self.is_cropped:
            return
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_mouse_drag(self, event) -> None:
        if self.is_cropped:
            return
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        box_w = self.box_x2 - self.box_x1
        box_h = self.box_y2 - self.box_y1
        min_x = self.offset_x
        max_x = self.offset_x + self.display_w - box_w
        min_y = self.offset_y
        max_y = self.offset_y + self.display_h - box_h
        new_x1 = max(min_x, min(max_x, self.box_x1 + dx))
        new_y1 = max(min_y, min(max_y, self.box_y1 + dy))
        self.box_x1, self.box_y1 = new_x1, new_y1
        self.box_x2, self.box_y2 = new_x1 + box_w, new_y1 + box_h
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.draw_crop_box()

    def on_scroll(self, event) -> None:
        if event.delta > 0:
            self.zoom_box(1.05)
        elif event.delta < 0:
            self.zoom_box(0.95)

    def zoom_box(self, factor: float) -> None:
        if self.is_cropped:
            return
        center_x = (self.box_x1 + self.box_x2) / 2.0
        center_y = (self.box_y1 + self.box_y2) / 2.0
        curr_w = self.box_x2 - self.box_x1
        new_w = curr_w * factor
        new_h = new_w / constants.PORTRAIT_ASPECT
        max_w = self.display_w
        max_h = self.display_h
        if new_w > max_w or new_h > max_h:
            new_w = max_w
            new_h = new_w / constants.PORTRAIT_ASPECT
        elif new_w < 50:
            new_w = 50
            new_h = new_w / constants.PORTRAIT_ASPECT
        new_x1 = center_x - (new_w / 2.0)
        new_y1 = center_y - (new_h / 2.0)
        min_x = self.offset_x
        max_x = self.offset_x + self.display_w - new_w
        min_y = self.offset_y
        max_y = self.offset_y + self.display_h - new_h
        self.box_x1 = max(min_x, min(max_x, new_x1))
        self.box_y1 = max(min_y, min(max_y, new_y1))
        self.box_x2 = self.box_x1 + new_w
        self.box_y2 = self.box_y1 + new_h
        self.draw_crop_box()

    def apply_crop_preview(self) -> None:
        if self.is_cropped or self.orig_img is None:
            return
        crop_x1 = max(0, int((self.box_x1 - self.offset_x) / self.scale))
        crop_y1 = max(0, int((self.box_y1 - self.offset_y) / self.scale))
        crop_x2 = min(self.img_w, int((self.box_x2 - self.offset_x) / self.scale))
        crop_y2 = min(self.img_h, int((self.box_y2 - self.offset_y) / self.scale))
        self.preview_cropped_img = self.orig_img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
        self.is_cropped = True

        raw_w = self.canvas.winfo_width() or 1280
        raw_h = self.canvas.winfo_height() or 750
        pw, ph = self.preview_cropped_img.size
        scale = min(raw_w / pw, raw_h / ph) * 0.9
        disp_w, disp_h = max(1, int(pw * scale)), max(1, int(ph * scale))
        off_x, off_y = (raw_w - disp_w) // 2, (raw_h - disp_h) // 2
        resized = self.preview_cropped_img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(resized)
        self.canvas.delete("all")
        self.canvas.create_image(off_x, off_y, anchor="nw", image=self.tk_img)
        self.update_info_label()

    def reset_crop_preview(self) -> None:
        if not self.is_cropped:
            return
        self.is_cropped = False
        self.refresh_display_and_box()

    def save_crop(self) -> None:
        if not self.is_cropped:
            self.apply_crop_preview()
        if self.preview_cropped_img is None:
            return
        final_img = self.preview_cropped_img.resize(
            (constants.CROP_SAVE_W, constants.CROP_SAVE_H),
            Image.Resampling.LANCZOS,
        )
        backup_dir = constants.backup_dir()
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / self.current_file
        out_path = constants.TARGET_DIR / (Path(self.current_file).stem + ".jpg")
        if self.orig_img is not None:
            try:
                self.orig_img.close()
            except Exception:
                pass
        if self.img_path.exists():
            shutil.move(str(self.img_path), str(backup_path))
        final_img.save(
            out_path,
            "JPEG",
            quality=constants.CROP_SAVE_QUALITY,
            optimize=True,
        )
        console.print(f"Saved portrait crop: {self.current_file} -> 1080x1920")
        self.current_idx += 1
        self.load_next_image()

    def skip_image(self) -> None:
        console.print(f"Skipped {self.current_file}")
        if self.orig_img is not None:
            try:
                self.orig_img.close()
            except Exception:
                pass
        self.current_idx += 1
        self.load_next_image()

    def update_info_label(self) -> None:
        status = "CROPPED PREVIEW" if self.is_cropped else "SELECTING FRAME"

        self.info_label.config(
            text=(
                f"[{self.current_idx + 1}/{len(self.file_list)}] {self.current_file} | Status: {status} | "
                f"Controls: Scroll/Up/Down=Zoom, 'C'=Crop, 'Z'=Reset, Enter/Space=Save, 'R'=Rotate, 'S'=Skip"
            )
        )


def crop_portrait() -> None:
    files_to_process: list[str] = []
    for p in files.list_files(constants.TARGET_DIR):
        name = p.name
        if not files.is_image_file(name):
            continue
        if images.is_non_portrait_9x16(p):
            files_to_process.append(name)
    if not files_to_process:
        console.print("No images found that require portrait cropping.")
        return
    console.print(f"Found {len(files_to_process)} non-portrait images to crop.")
    import tkinter as tk

    root = tk.Tk()
    _ = AutoCropAppPortrait(root, files_to_process)
    root.mainloop()
