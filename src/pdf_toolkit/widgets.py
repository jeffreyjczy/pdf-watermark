import os
from collections.abc import Callable

import customtkinter as ctk

from pdf_toolkit.pdf_ops import render_pdf_page


class AutoHideScrollableFrame(ctk.CTkScrollableFrame):
    """Scrollable frame that only shows its scrollbar when content overflows."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scrollbar_visible = True

        if self._orientation == "vertical":
            self._parent_canvas.configure(yscrollcommand=self._update_scrollbar)
        else:
            self._parent_canvas.configure(xscrollcommand=self._update_scrollbar)

        self._parent_canvas.bind("<Configure>", self._handle_canvas_configure, add="+")
        self.bind("<Configure>", self._handle_content_configure, add="+")
        self.after_idle(self._refresh_scrollbar_visibility)

    def _update_scrollbar(self, first, last):
        first = float(first)
        last = float(last)
        self._scrollbar.set(first, last)

        should_show = first > 0.0 or last < 1.0
        if should_show and not self._scrollbar_visible:
            self._scrollbar.grid()
            self._scrollbar_visible = True
        elif not should_show and self._scrollbar_visible:
            self._scrollbar.grid_remove()
            self._scrollbar_visible = False

    def _handle_canvas_configure(self, _event):
        self._refresh_scrollbar_visibility()

    def _handle_content_configure(self, _event):
        self._refresh_scrollbar_visibility()

    def _refresh_scrollbar_visibility(self):
        if self._orientation == "vertical":
            self._update_scrollbar(*self._parent_canvas.yview())
        else:
            self._update_scrollbar(*self._parent_canvas.xview())


class PreviewCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        pdf_path: str,
        page_number: int,
        min_page: int,
        max_page: int,
        page_label: str,
        on_jump: Callable[[int], None] | None = None,
        page_label_builder: Callable[[int], str] | None = None,
        **kwargs,
    ):
        super().__init__(master, corner_radius=8, **kwargs)
        self.pdf_path = pdf_path
        self.page_number = page_number
        self.min_page = min_page
        self.max_page = max_page
        self.on_jump = on_jump
        self.page_label_builder = page_label_builder
        self.image = None

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="center",
        ).grid(row=0, column=0, padx=10, pady=(10, 2), sticky="ew")

        self.page_label = ctk.CTkLabel(
            self,
            text=page_label,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="center",
        )
        self.page_label.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")

        self.image_label = ctk.CTkLabel(self, text="")
        self.image_label.grid(row=2, column=0, padx=10, pady=(0, 8))
        self._load_image()

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=3, column=0, padx=10, pady=(0, 10))
        controls.grid_columnconfigure(1, weight=1)

        self.previous_button = ctk.CTkButton(
            controls,
            text="<",
            width=36,
            height=30,
            command=lambda: self._change_page(-1),
        )
        self.previous_button.grid(row=0, column=0, padx=(0, 4), sticky="w")

        self.control_page_label = ctk.CTkLabel(
            controls,
            text="",
            font=ctk.CTkFont(size=11),
            anchor="center",
        )
        self.control_page_label.grid(row=0, column=1, padx=4)

        self.next_button = ctk.CTkButton(
            controls,
            text=">",
            width=36,
            height=30,
            command=lambda: self._change_page(1),
        )
        self.next_button.grid(row=0, column=2, padx=(4, 0), sticky="e")
        self._refresh_controls()

    def _load_image(self):
        try:
            pil_image = render_pdf_page(self.pdf_path, self.page_number, (220, 300))
        except Exception as exc:
            self.image_label.configure(text=f"Preview unavailable:\n{exc}")
            return

        self.image = ctk.CTkImage(
            light_image=pil_image,
            dark_image=pil_image,
            size=pil_image.size,
        )
        self.image_label.configure(image=self.image, text="")

    def _change_page(self, delta: int):
        next_page_number = self.page_number + delta
        if next_page_number < self.min_page or next_page_number > self.max_page:
            return

        self.page_number = next_page_number
        if self.page_label_builder is not None:
            self.page_label.configure(text=self.page_label_builder(next_page_number))
        self._load_image()
        self._refresh_controls()
        if self.on_jump is not None:
            self.on_jump(next_page_number)

    def _refresh_controls(self):
        self.control_page_label.configure(text=f"Page {self.page_number}")
        self.previous_button.configure(
            state="normal" if self.page_number > self.min_page else "disabled"
        )
        self.next_button.configure(
            state="normal" if self.page_number < self.max_page else "disabled"
        )


def set_entry_text(entry: ctk.CTkEntry, value: str):
    entry.delete(0, "end")
    entry.insert(0, value)


def display_path(path: str | None) -> str:
    if not path:
        return ""
    return os.path.basename(path)
