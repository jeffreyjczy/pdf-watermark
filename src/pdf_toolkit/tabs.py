import os
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pypdf

from pdf_toolkit.paths import resource_path
from pdf_toolkit.pdf_ops import (
    build_default_merge_output_path,
    format_page_group,
    get_pdf_page_count,
    insert_pdfs_with_settings,
    parse_split_group_specs,
    split_pdf,
)
from pdf_toolkit.widgets import (
    AutoHideScrollableFrame,
    PreviewCard,
    display_path,
    set_entry_text,
)
from pdf_watermark.handler import add_watermark_to_pdf
from pdf_watermark.options import DrawingOptions, InsertOptions


class WatermarkTab:
    def __init__(self, master):
        self.selected_pdfs: list[str] = []
        self.output_folder: str | None = None
        self.font_path = "Tahoma"
        self.custom_fonts_folder = resource_path("fonts")

        self.frame = AutoHideScrollableFrame(
            master,
            corner_radius=10,
            scrollbar_button_color="#aeb8c4",
            scrollbar_button_hover_color="#8793a1",
        )
        self.frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.frame.grid_columnconfigure(0, weight=1)

        self._build()

    def _build(self):
        self._add_header("PDF Watermark", "Add watermarks to one or more PDF files.")

        input_frame = self._section("Select PDF Files", 1)
        self.input_pdf_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="No files selected...",
            height=40,
        )
        self.input_pdf_entry.grid(
            row=1, column=0, padx=(15, 10), pady=(0, 10), sticky="ew"
        )
        ctk.CTkButton(
            input_frame,
            text="Browse",
            command=self.select_pdfs,
            width=120,
            height=40,
        ).grid(row=1, column=1, padx=(0, 15), pady=(0, 10))
        self.file_count_label = ctk.CTkLabel(
            input_frame,
            text="0 file(s) selected",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.file_count_label.grid(
            row=2, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w"
        )

        output_frame = self._section("Output Folder (Optional)", 2)
        self.output_folder_entry = ctk.CTkEntry(
            output_frame,
            placeholder_text="Same as input folder...",
            height=40,
        )
        self.output_folder_entry.grid(
            row=1, column=0, padx=(15, 10), pady=(0, 15), sticky="ew"
        )
        ctk.CTkButton(
            output_frame,
            text="Browse",
            command=self.select_output_folder,
            width=120,
            height=40,
        ).grid(row=1, column=1, padx=(0, 15), pady=(0, 15))

        settings_frame = self._section("Watermark Settings", 3)
        ctk.CTkLabel(settings_frame, text="Watermark Text:", anchor="w").grid(
            row=1, column=0, columnspan=4, padx=15, pady=(0, 4), sticky="w"
        )
        self.text_entry = ctk.CTkTextbox(settings_frame, height=70, wrap="word")
        self.text_entry.grid(
            row=2, column=0, columnspan=4, padx=15, pady=(0, 10), sticky="ew"
        )

        position_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        position_frame.grid(
            row=3, column=0, columnspan=4, padx=15, pady=(0, 6), sticky="ew"
        )
        position_frame.grid_columnconfigure((0, 1), weight=1, uniform="position")
        self.x_position_entry = self._labeled_entry(position_frame, "X Offset", 0, "0")
        self.y_position_entry = self._labeled_entry(position_frame, "Y Offset", 1, "0")

        ctk.CTkLabel(
            settings_frame,
            text="Range: -5 to +5 | 0,0 = center | +X = right | +Y = up",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).grid(row=4, column=0, columnspan=4, padx=15, pady=(0, 10), sticky="w")

        self.combine_pdfs_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            settings_frame,
            text="Combine multiple PDFs into one file",
            variable=self.combine_pdfs_var,
        ).grid(row=5, column=0, columnspan=4, padx=15, pady=(0, 15), sticky="w")

        ctk.CTkButton(
            self.frame,
            text="Apply Watermark",
            command=self.apply_watermark,
            width=240,
            height=48,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#2ecc71",
            hover_color="#27ae60",
        ).grid(row=4, column=0, padx=20, pady=20)

    def _add_header(self, title: str, subtitle: str):
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            header,
            text=subtitle,
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).grid(row=1, column=0, sticky="ew")

    def _section(self, title: str, row: int):
        frame = ctk.CTkFrame(self.frame, corner_radius=8)
        frame.grid(row=row, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")
        return frame

    def _labeled_entry(self, master, label: str, column: int, default: str):
        container = ctk.CTkFrame(master, fg_color="transparent")
        container.grid(
            row=0, column=column, padx=(0, 8) if column == 0 else (8, 0), sticky="ew"
        )
        container.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(container, text=f"{label}:").grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )
        entry = ctk.CTkEntry(container, height=35)
        entry.insert(0, default)
        entry.grid(row=0, column=1, sticky="ew")
        return entry

    def select_pdfs(self):
        paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if not paths:
            return

        self.selected_pdfs = list(paths)
        file_names = [os.path.basename(path) for path in self.selected_pdfs]
        self.file_count_label.configure(
            text=f"{len(self.selected_pdfs)} file(s) selected"
        )
        set_entry_text(self.input_pdf_entry, ", ".join(file_names))

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if not folder:
            return

        self.output_folder = folder
        set_entry_text(self.output_folder_entry, folder)

    def apply_watermark(self):
        if not self.selected_pdfs:
            messagebox.showerror("Error", "Please select at least one PDF.")
            return

        watermark_text = self.text_entry.get("1.0", "end-1c").strip()
        if not watermark_text:
            messagebox.showerror("Error", "Please enter watermark text.")
            return

        try:
            x_offset = float(self.x_position_entry.get() or 0)
            y_offset = float(self.y_position_entry.get() or 0)
        except ValueError:
            messagebox.showerror("Error", "X and Y positions must be valid numbers.")
            return

        drawing_options = DrawingOptions(
            watermark=watermark_text,
            opacity=0.3,
            text_font=self.font_path,
            custom_fonts_folder=self.custom_fonts_folder,
            text_size=14,
        )
        insert_options = InsertOptions(
            x=self._convert_position_to_normalized(x_offset),
            y=self._convert_position_to_normalized(y_offset),
        )

        failed_files: list[tuple[str, str]] = []
        watermarked_files: list[str] = []

        for input_pdf in self.selected_pdfs:
            output_pdf = self._build_watermark_output_path(input_pdf)
            try:
                add_watermark_to_pdf(
                    input=input_pdf,
                    output=output_pdf,
                    drawing_options=drawing_options,
                    specific_options=insert_options,
                )
                watermarked_files.append(output_pdf)
            except Exception as exc:
                failed_files.append((input_pdf, str(exc)))

        if self.combine_pdfs_var.get() and len(watermarked_files) > 1:
            combined_output = self._combine_pdfs(watermarked_files)
            if combined_output:
                messagebox.showinfo(
                    "Success",
                    f"Watermarked and combined {len(watermarked_files)} files into:\n{combined_output}",
                )
        elif not failed_files:
            messagebox.showinfo(
                "Success",
                f"Watermark applied to {len(watermarked_files)} file(s).",
            )

        if failed_files:
            error_msg = "\n\n".join(
                f"{os.path.basename(path)}:\n{error}" for path, error in failed_files
            )
            messagebox.showerror("Some files failed", error_msg)

    def _build_watermark_output_path(self, input_pdf_path: str) -> str:
        directory, filename = os.path.split(input_pdf_path)
        name, ext = os.path.splitext(filename)
        destination = self.output_folder or directory
        return os.path.join(destination, f"{name}_watermarked{ext}")

    def _combine_pdfs(self, watermarked_files: list[str]) -> str | None:
        try:
            writer = pypdf.PdfWriter()
            for pdf_path in watermarked_files:
                reader = pypdf.PdfReader(pdf_path)
                for page in reader.pages:
                    writer.add_page(page)

            destination = self.output_folder or os.path.dirname(self.selected_pdfs[0])
            output_path = os.path.join(destination, "combined_watermarked.pdf")
            with open(output_path, "wb") as output_file:
                writer.write(output_file)

            for pdf_path in watermarked_files:
                try:
                    os.remove(pdf_path)
                except OSError:
                    pass

            return output_path
        except Exception as exc:
            messagebox.showerror(
                "Error combining PDFs", f"Failed to combine PDFs: {exc}"
            )
            return None

    def _convert_position_to_normalized(
        self, offset_value: float, max_offset: int = 10
    ) -> float:
        normalized_offset = max(-0.5, min(0.5, offset_value / max_offset))
        return 0.5 + normalized_offset


class SplitterTab:
    def __init__(self, master):
        self.input_pdf: str | None = None
        self.output_folder: str | None = None
        self.page_count = 0
        self.group_preview_pages: dict[int, int] = {}
        self.split_rows: list[dict] = []

        self.frame = AutoHideScrollableFrame(
            master,
            corner_radius=10,
            scrollbar_button_color="#aeb8c4",
            scrollbar_button_hover_color="#8793a1",
        )
        self.frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.frame.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        self._add_header(
            "PDF Splitter",
            "Create one output PDF per semicolon-separated page group.",
        )

        input_frame = self._section("Source PDF", 1)
        self.input_entry = ctk.CTkEntry(
            input_frame, placeholder_text="No PDF selected...", height=40
        )
        self.input_entry.grid(row=1, column=0, padx=(15, 10), pady=(0, 10), sticky="ew")
        ctk.CTkButton(
            input_frame, text="Browse", width=120, height=40, command=self.select_pdf
        ).grid(row=1, column=1, padx=(0, 15), pady=(0, 10))
        self.source_info_label = ctk.CTkLabel(
            input_frame,
            text="Select a PDF to populate the default 1-N range.",
            text_color="gray",
            font=ctk.CTkFont(size=12),
        )
        self.source_info_label.grid(
            row=2, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w"
        )

        range_frame = self._section("Split Ranges", 2)
        self.range_rows_frame = ctk.CTkFrame(range_frame, fg_color="transparent")
        self.range_rows_frame.grid(
            row=1, column=0, columnspan=2, padx=15, pady=(0, 8), sticky="ew"
        )
        self.range_rows_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(
            range_frame,
            text="Add Split Range",
            width=150,
            height=36,
            command=self.add_split_row,
        ).grid(row=2, column=0, padx=15, pady=(0, 10), sticky="w")
        ctk.CTkLabel(
            range_frame,
            text="Each row creates one output PDF. Overlapping pages are allowed, for example 1-3 and 2-4.",
            text_color="gray",
            font=ctk.CTkFont(size=12),
        ).grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w")

        output_frame = self._section("Output Folder (Optional)", 3)
        self.output_entry = ctk.CTkEntry(
            output_frame,
            placeholder_text="Same as input folder...",
            height=40,
        )
        self.output_entry.grid(
            row=1, column=0, padx=(15, 10), pady=(0, 15), sticky="ew"
        )
        ctk.CTkButton(
            output_frame,
            text="Browse",
            width=120,
            height=40,
            command=self.select_output_folder,
        ).grid(row=1, column=1, padx=(0, 15), pady=(0, 15))

        preview_section = self._section("Split Preview", 4)
        self.preview_status_label = ctk.CTkLabel(
            preview_section,
            text="No preview yet.",
            text_color="gray",
        )
        self.preview_status_label.grid(
            row=1, column=0, padx=15, pady=(0, 10), sticky="w"
        )
        self.preview_grid = ctk.CTkFrame(preview_section, fg_color="transparent")
        self.preview_grid.grid(
            row=2, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew"
        )
        self.preview_grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="preview")

        ctk.CTkButton(
            self.frame,
            text="Split PDF",
            command=self.split_pdf,
            width=220,
            height=48,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#2f80ed",
            hover_color="#1f6fd0",
        ).grid(row=5, column=0, padx=20, pady=20)
        self.add_split_row(refresh=False)

    def _add_header(self, title: str, subtitle: str):
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=title, font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, sticky="ew"
        )
        ctk.CTkLabel(header, text=subtitle, text_color="gray").grid(
            row=1, column=0, sticky="ew"
        )

    def _section(self, title: str, row: int):
        frame = ctk.CTkFrame(self.frame, corner_radius=8)
        frame.grid(row=row, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")
        return frame

    def select_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not path:
            return

        try:
            self.page_count = get_pdf_page_count(path)
        except Exception as exc:
            messagebox.showerror("Error", f"Could not read PDF: {exc}")
            return

        self.input_pdf = path
        self.group_preview_pages.clear()
        set_entry_text(self.input_entry, path)
        self._reset_split_rows()
        set_entry_text(self.split_rows[0]["entry"], f"1-{self.page_count}")
        self.source_info_label.configure(
            text=f"{display_path(path)} has {self.page_count} page(s)."
        )
        self.refresh_preview()

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if not folder:
            return
        self.output_folder = folder
        set_entry_text(self.output_entry, folder)

    def _handle_ranges_changed(self, _event=None):
        self.refresh_preview()

    def add_split_row(self, refresh: bool = True):
        row_state: dict = {}
        row_frame = ctk.CTkFrame(self.range_rows_frame, fg_color="transparent")
        row_frame.grid_columnconfigure(1, weight=1)
        row_state["frame"] = row_frame

        label = ctk.CTkLabel(row_frame, text="", anchor="w")
        label.grid(row=0, column=0, padx=(0, 8), sticky="w")
        row_state["label"] = label

        entry = ctk.CTkEntry(
            row_frame,
            placeholder_text="Example: 1-4",
            height=36,
        )
        if not self.split_rows and self.page_count:
            entry.insert(0, f"1-{self.page_count}")
        entry.grid(row=0, column=1, padx=(0, 8), sticky="ew")
        entry.bind("<KeyRelease>", self._handle_ranges_changed)
        row_state["entry"] = entry

        remove_button = ctk.CTkButton(
            row_frame,
            text="Remove",
            width=86,
            height=34,
            fg_color="#d9534f",
            hover_color="#c03d39",
            command=lambda row=row_state: self.remove_split_row(row),
        )
        remove_button.grid(row=0, column=2, sticky="e")
        row_state["remove_button"] = remove_button

        self.split_rows.append(row_state)
        self._layout_split_rows()
        if refresh:
            self.refresh_preview()

    def remove_split_row(self, row_state: dict):
        if len(self.split_rows) == 1:
            set_entry_text(row_state["entry"], "")
        else:
            self.split_rows.remove(row_state)
            row_state["frame"].destroy()
        self._layout_split_rows()
        self.refresh_preview()

    def _reset_split_rows(self):
        for row_state in self.split_rows[1:]:
            row_state["frame"].destroy()
        self.split_rows = self.split_rows[:1]
        if not self.split_rows:
            self.add_split_row(refresh=False)
        set_entry_text(self.split_rows[0]["entry"], "")
        self._layout_split_rows()

    def _layout_split_rows(self):
        for index, row_state in enumerate(self.split_rows):
            row_state["frame"].grid(row=index, column=0, pady=(0, 8), sticky="ew")
            row_state["label"].configure(text=f"Output {index + 1} range:")
            if index == 0:
                row_state["remove_button"].grid_remove()
            else:
                row_state["remove_button"].grid()
        self.group_preview_pages = {
            index: page
            for index, page in self.group_preview_pages.items()
            if index < len(self.split_rows)
        }

    def _read_split_groups(self) -> list[list[int]]:
        specs = [row["entry"].get() for row in self.split_rows]
        return parse_split_group_specs(specs, self.page_count)

    def refresh_preview(self):
        self._clear_preview_grid()
        if not self.input_pdf:
            self.preview_status_label.configure(
                text="Select a PDF to preview split groups."
            )
            return

        try:
            groups = self._read_split_groups()
        except ValueError as exc:
            self.preview_status_label.configure(text=f"Range error: {exc}")
            return

        self.preview_status_label.configure(
            text=f"{len(groups)} output group(s) will be created."
        )
        for index, pages in enumerate(groups):
            preview_page = self.group_preview_pages.get(index, pages[0])
            if preview_page not in pages:
                preview_page = pages[0]
            self.group_preview_pages[index] = preview_page

            card = PreviewCard(
                self.preview_grid,
                title=f"Group {index + 1}",
                pdf_path=self.input_pdf,
                page_number=preview_page,
                min_page=pages[0],
                max_page=pages[-1],
                page_label=(
                    f"Pages {format_page_group(pages)} | Preview page {preview_page}"
                ),
                on_jump=lambda page_number, group_index=index: self._set_group_preview_page(
                    group_index,
                    page_number,
                ),
                page_label_builder=lambda page_number, group_pages=pages: (
                    f"Pages {format_page_group(group_pages)} | Preview page {page_number}"
                ),
            )
            card.grid(row=index // 3, column=index % 3, padx=8, pady=8, sticky="nsew")

    def _set_group_preview_page(self, group_index: int, page_number: int):
        self.group_preview_pages[group_index] = page_number

    def _clear_preview_grid(self):
        for child in self.preview_grid.winfo_children():
            child.destroy()

    def split_pdf(self):
        if not self.input_pdf:
            messagebox.showerror("Error", "Please select a source PDF.")
            return

        try:
            groups = self._read_split_groups()
            output_paths = split_pdf(self.input_pdf, groups, self.output_folder)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        messagebox.showinfo(
            "Success",
            "Created split PDFs:\n" + "\n".join(output_paths),
        )


class MergerTab:
    def __init__(self, master):
        self.original_pdf: str | None = None
        self.output_folder: str | None = None
        self.original_page_count = 0
        self.insert_rows: list[dict] = []

        self.frame = AutoHideScrollableFrame(
            master,
            corner_radius=10,
            scrollbar_button_color="#aeb8c4",
            scrollbar_button_hover_color="#8793a1",
        )
        self.frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.frame.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        self._add_header(
            "PDF Merger",
            "Add insert rows, each with its own PDF and insertion position.",
        )

        original_frame = self._section("Original PDF", 1)
        self.original_entry = ctk.CTkEntry(
            original_frame, placeholder_text="No PDF selected...", height=40
        )
        self.original_entry.grid(
            row=1, column=0, padx=(15, 10), pady=(0, 10), sticky="ew"
        )
        ctk.CTkButton(
            original_frame,
            text="Browse",
            width=120,
            height=40,
            command=self.select_original_pdf,
        ).grid(row=1, column=1, padx=(0, 15), pady=(0, 10))
        self.original_info_label = ctk.CTkLabel(
            original_frame,
            text="Select the PDF that receives inserted pages.",
            text_color="gray",
            font=ctk.CTkFont(size=12),
        )
        self.original_info_label.grid(
            row=2, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w"
        )

        insert_section = self._section("Insert PDFs", 2)
        self.insert_rows_frame = ctk.CTkFrame(insert_section, fg_color="transparent")
        self.insert_rows_frame.grid(
            row=1, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="ew"
        )
        self.insert_rows_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(
            insert_section,
            text="Add Insert PDF",
            width=160,
            height=38,
            command=self.add_insert_row,
        ).grid(row=2, column=0, padx=15, pady=(0, 10), sticky="w")
        ctk.CTkLabel(
            insert_section,
            text="Each row is inserted independently. Rows with the same page position keep the order shown here.",
            text_color="gray",
            font=ctk.CTkFont(size=12),
        ).grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w")
        self.add_insert_row()

        output_frame = self._section("Output Folder (Optional)", 3)
        self.output_entry = ctk.CTkEntry(
            output_frame,
            placeholder_text="Same as original PDF folder...",
            height=40,
        )
        self.output_entry.grid(
            row=1, column=0, padx=(15, 10), pady=(0, 15), sticky="ew"
        )
        ctk.CTkButton(
            output_frame,
            text="Browse",
            width=120,
            height=40,
            command=self.select_output_folder,
        ).grid(row=1, column=1, padx=(0, 15), pady=(0, 15))

        preview_section = self._section("Merge Preview", 4)
        self.preview_status_label = ctk.CTkLabel(
            preview_section,
            text="Select an original PDF and at least one insert PDF to preview.",
            text_color="gray",
        )
        self.preview_status_label.grid(
            row=1, column=0, padx=15, pady=(0, 10), sticky="w"
        )
        self.preview_grid = ctk.CTkFrame(preview_section, fg_color="transparent")
        self.preview_grid.grid(
            row=2, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew"
        )
        self.preview_grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="preview")

        ctk.CTkButton(
            self.frame,
            text="Merge PDF",
            command=self.merge_pdf,
            width=220,
            height=48,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#9b51e0",
            hover_color="#7f3dc0",
        ).grid(row=5, column=0, padx=20, pady=20)

    def _add_header(self, title: str, subtitle: str):
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=title, font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, sticky="ew"
        )
        ctk.CTkLabel(header, text=subtitle, text_color="gray").grid(
            row=1, column=0, sticky="ew"
        )

    def _section(self, title: str, row: int):
        frame = ctk.CTkFrame(self.frame, corner_radius=8)
        frame.grid(row=row, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")
        return frame

    def add_insert_row(self):
        row_state: dict = {
            "path": None,
            "page_count": 0,
            "preview_page": 1,
        }
        row_frame = ctk.CTkFrame(self.insert_rows_frame, corner_radius=8)
        row_state["frame"] = row_frame

        title_row = ctk.CTkFrame(row_frame, fg_color="transparent")
        title_row.grid(row=0, column=0, columnspan=3, padx=12, pady=(12, 8), sticky="ew")
        title_row.grid_columnconfigure(0, weight=1)
        title_label = ctk.CTkLabel(
            title_row,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        title_label.grid(row=0, column=0, sticky="w")
        row_state["title_label"] = title_label
        remove_button = ctk.CTkButton(
            title_row,
            text="Remove",
            width=86,
            height=30,
            fg_color="#d9534f",
            hover_color="#c03d39",
            command=lambda row=row_state: self.remove_insert_row(row),
        )
        remove_button.grid(row=0, column=1, sticky="e")
        row_state["remove_button"] = remove_button

        path_entry = ctk.CTkEntry(
            row_frame,
            placeholder_text="No insert PDF selected...",
            height=38,
        )
        path_entry.grid(row=1, column=0, padx=(12, 8), pady=(0, 8), sticky="ew")
        row_state["path_entry"] = path_entry
        ctk.CTkButton(
            row_frame,
            text="Browse",
            width=100,
            height=38,
            command=lambda row=row_state: self.select_insert_pdf(row),
        ).grid(row=1, column=1, padx=(0, 12), pady=(0, 8), sticky="e")

        settings_row = ctk.CTkFrame(row_frame, fg_color="transparent")
        settings_row.grid(row=2, column=0, columnspan=2, padx=12, pady=(0, 8), sticky="ew")
        settings_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(settings_row, text="Insert after page:").grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )
        position_entry = ctk.CTkEntry(settings_row, width=120, height=34)
        position_entry.insert(0, "0")
        position_entry.grid(row=0, column=1, sticky="w")
        position_entry.bind("<KeyRelease>", self._handle_position_changed)
        row_state["position_entry"] = position_entry

        info_label = ctk.CTkLabel(
            row_frame,
            text="Use 0 to insert before original page 1.",
            text_color="gray",
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        info_label.grid(row=3, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="w")
        row_state["info_label"] = info_label

        row_frame.grid_columnconfigure(0, weight=1)
        self.insert_rows.append(row_state)
        self._layout_insert_rows()
        if hasattr(self, "preview_grid"):
            self.refresh_preview()

    def remove_insert_row(self, row_state: dict):
        if len(self.insert_rows) == 1:
            row_state["path"] = None
            row_state["page_count"] = 0
            row_state["preview_page"] = 1
            set_entry_text(row_state["path_entry"], "")
            set_entry_text(row_state["position_entry"], "0")
            row_state["info_label"].configure(
                text="Use 0 to insert before original page 1."
            )
        else:
            self.insert_rows.remove(row_state)
            row_state["frame"].destroy()

        self._layout_insert_rows()
        self.refresh_preview()

    def _layout_insert_rows(self):
        for index, row_state in enumerate(self.insert_rows):
            row_state["frame"].grid(row=index, column=0, pady=(0, 10), sticky="ew")
            row_state["title_label"].configure(text=f"Insert PDF {index + 1}")
            if index == 0:
                row_state["remove_button"].grid_remove()
            else:
                row_state["remove_button"].grid()

    def select_original_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not path:
            return
        try:
            self.original_page_count = get_pdf_page_count(path)
        except Exception as exc:
            messagebox.showerror("Error", f"Could not read original PDF: {exc}")
            return
        self.original_pdf = path
        set_entry_text(self.original_entry, path)
        self.original_info_label.configure(
            text=f"{display_path(path)} has {self.original_page_count} page(s)."
        )
        self.refresh_preview()

    def select_insert_pdf(self, row_state: dict):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not path:
            return

        try:
            page_count = get_pdf_page_count(path)
        except Exception as exc:
            messagebox.showerror("Error", f"Could not read insert PDF: {exc}")
            return

        row_state["path"] = path
        row_state["page_count"] = page_count
        row_state["preview_page"] = 1
        set_entry_text(row_state["path_entry"], path)
        row_state["info_label"].configure(
            text=f"{display_path(path)} has {page_count} page(s)."
        )
        self.refresh_preview()

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if not folder:
            return
        self.output_folder = folder
        set_entry_text(self.output_entry, folder)

    def _handle_position_changed(self, _event=None):
        self.refresh_preview()

    def refresh_preview(self):
        self._clear_preview_grid()
        if not self.original_pdf:
            self.preview_status_label.configure(text="Select an original PDF to preview.")
            return

        complete_rows = [row for row in self.insert_rows if row["path"]]
        if not complete_rows:
            self.preview_status_label.configure(
                text="Add at least one insert PDF to preview."
            )
            return

        try:
            specs = self._read_insert_specs(require_all_rows=False)
        except ValueError as exc:
            self.preview_status_label.configure(text=f"Merge setting error: {exc}")
            return

        grouped_specs: dict[int, list[tuple[int, dict]]] = {}
        for row_index, (row_state, after_page) in enumerate(specs, start=1):
            grouped_specs.setdefault(after_page, []).append((row_index, row_state))

        cards = []
        sorted_positions = sorted(grouped_specs)
        previous_position = 0
        for after_page in sorted_positions:
            segment_start = previous_position + 1
            segment_end = after_page
            if segment_start <= segment_end:
                cards.append(
                    (
                        f"Original pages {segment_start}-{segment_end}",
                        self.original_pdf,
                        segment_end,
                        segment_start,
                        segment_end,
                        f"Original page {segment_end}",
                        lambda page_number: None,
                        lambda page_number: f"Original page {page_number}",
                    )
                )

            insert_rows = grouped_specs[after_page]
            for row_index, row_state in insert_rows:
                preview_page = min(row_state["preview_page"], row_state["page_count"])
                row_state["preview_page"] = preview_page
                cards.append(
                    (
                        f"Insert PDF {row_index}",
                        row_state["path"],
                        preview_page,
                        1,
                        row_state["page_count"],
                        f"{display_path(row_state['path'])} | Page {preview_page}",
                        lambda page_number, row=row_state: self._set_insert_preview_page(
                            row,
                            page_number,
                        ),
                        lambda page_number, row=row_state: (
                            f"{display_path(row['path'])} | Page {page_number}"
                        ),
                    )
                )

            previous_position = after_page

        final_segment_start = previous_position + 1
        if final_segment_start <= self.original_page_count:
            cards.append(
                (
                    f"Original pages {final_segment_start}-{self.original_page_count}",
                    self.original_pdf,
                    final_segment_start,
                    final_segment_start,
                    self.original_page_count,
                    f"Original page {final_segment_start}",
                    lambda page_number: None,
                    lambda page_number: f"Original page {page_number}",
                )
            )

        total_pages = sum(row["page_count"] for row, _after_page in specs)
        self.preview_status_label.configure(
            text=f"{len(specs)} insert row(s), {total_pages} page(s), will be merged."
        )
        for index, card_args in enumerate(cards):
            (
                title,
                pdf_path,
                page_number,
                min_page,
                max_page,
                label,
                callback,
                label_builder,
            ) = card_args
            card = PreviewCard(
                self.preview_grid,
                title=title,
                pdf_path=pdf_path,
                page_number=page_number,
                min_page=min_page,
                max_page=max_page,
                page_label=label,
                on_jump=callback,
                page_label_builder=label_builder,
            )
            card.grid(row=index // 3, column=index % 3, padx=8, pady=8)

    def _read_insert_specs(self, require_all_rows: bool) -> list[tuple[dict, int]]:
        specs: list[tuple[dict, int]] = []
        for index, row_state in enumerate(self.insert_rows, start=1):
            if not row_state["path"]:
                continue

            raw_value = row_state["position_entry"].get().strip()
            if not raw_value.isdigit():
                raise ValueError(f"Insert row {index} position must be a whole number.")

            after_page = int(raw_value)
            if after_page < 0 or after_page > self.original_page_count:
                raise ValueError(
                    f"Insert row {index} position must be from 0 to {self.original_page_count}."
                )
            specs.append((row_state, after_page))

        if require_all_rows and not specs:
            raise ValueError("Add at least one insert PDF.")
        return specs

    def _set_row_after_page(self, row_state: dict, page_number: int):
        page_number = max(0, min(page_number, self.original_page_count))
        scroll_position = self.frame._parent_canvas.yview()[0]
        set_entry_text(row_state["position_entry"], str(page_number))
        self.refresh_preview()
        self.frame.after_idle(
            lambda: self.frame._parent_canvas.yview_moveto(scroll_position)
        )

    def _set_insert_preview_page(self, row_state: dict, page_number: int):
        row_state["preview_page"] = max(1, min(page_number, row_state["page_count"]))

    def _clear_preview_grid(self):
        for child in self.preview_grid.winfo_children():
            child.destroy()

    def merge_pdf(self):
        if not self.original_pdf:
            messagebox.showerror("Error", "Please select an original PDF.")
            return

        try:
            specs = self._read_insert_specs(require_all_rows=True)
            output_path = build_default_merge_output_path(
                self.original_pdf,
                self.output_folder,
            )
            insert_pdfs_with_settings(
                self.original_pdf,
                [(row["path"], after_page) for row, after_page in specs],
                output_path,
            )
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        messagebox.showinfo("Success", f"Merged PDF created:\n{output_path}")
