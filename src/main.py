import customtkinter as ctk
from tkinter import filedialog, messagebox
import sys
import os
import pypdf
from pdf_watermark.options import DrawingOptions, InsertOptions, FilesOptions
from pdf_watermark.handler import add_watermark_to_pdf

# Set appearance mode and color theme
ctk.set_appearance_mode("light")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp dir
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


font_path = "Tahoma"
custom_fonts_folder = resource_path("fonts")

selected_pdfs = []
output_folder = None


def select_pdf():
    global selected_pdfs

    paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])

    if not paths:
        return

    selected_pdfs = list(paths)

    file_names = [os.path.basename(p) for p in selected_pdfs]
    file_count_label.configure(text=f"📄 {len(selected_pdfs)} file(s) selected")
    input_pdf_entry.delete(0, "end")
    input_pdf_entry.insert(0, ", ".join(file_names))


def select_output_folder():
    global output_folder

    folder = filedialog.askdirectory(title="Select Output Folder")

    if not folder:
        return

    output_folder = folder
    output_folder_entry.delete(0, "end")
    output_folder_entry.insert(0, folder)


def build_output_path(input_pdf_path, custom_output_folder=None):
    """Build output path for a single PDF file"""
    if custom_output_folder:
        filename = os.path.basename(input_pdf_path)
        name, ext = os.path.splitext(filename)
        return os.path.join(custom_output_folder, f"{name}_watermarked{ext}")
    else:
        directory, filename = os.path.split(input_pdf_path)
        name, ext = os.path.splitext(filename)
        return os.path.join(directory, f"{name}_watermarked{ext}")


def convert_position_to_normalized(offset_value, max_offset=10):
    """
    Convert user-friendly offset (-max to +max) to normalized position (0 to 1).
    offset_value: User input offset (0 = center, positive = right/up, negative = left/down)
    max_offset: Maximum offset in points for full range
    Returns: Normalized value between 0 and 1
    """
    # Center is at 0.5
    # Normalize the offset to a proportion
    normalized_offset = offset_value / max_offset
    # Clamp to reasonable bounds
    normalized_offset = max(-0.5, min(0.5, normalized_offset))
    return 0.5 + normalized_offset


def combine_pdfs(watermarked_files):
    """
    Combine multiple PDF files into a single PDF.

    Args:
        watermarked_files: List of PDF file paths to combine

    Returns:
        Path to the combined PDF file if successful, None otherwise
    """
    global output_folder, selected_pdfs

    if len(watermarked_files) <= 1:
        return None

    try:
        # Create combined PDF
        pdf_merger = pypdf.PdfWriter()

        for pdf_path in watermarked_files:
            pdf_reader = pypdf.PdfReader(pdf_path)
            for page in pdf_reader.pages:
                pdf_merger.add_page(page)

        # Determine output path for combined PDF
        if output_folder:
            combined_output = os.path.join(output_folder, "combined_watermarked.pdf")
        else:
            # Use the directory of the first input file
            first_dir = os.path.dirname(selected_pdfs[0])
            combined_output = os.path.join(first_dir, "combined_watermarked.pdf")

        # Write combined PDF
        with open(combined_output, "wb") as output_file:
            pdf_merger.write(output_file)

        # Delete individual watermarked files
        for pdf_path in watermarked_files:
            try:
                os.remove(pdf_path)
            except:
                pass

        return combined_output

    except Exception as e:
        messagebox.showerror(
            "Error combining PDFs", f"Failed to combine PDFs: {str(e)}"
        )
        return None


def apply_watermark():
    global selected_pdfs, output_folder

    if not selected_pdfs:
        messagebox.showerror("Error", "Please select at least one PDF.")
        return

    watermark_text = text_entry.get("1.0", "end-1c").strip()

    if not watermark_text:
        messagebox.showerror("Error", "Please enter watermark text.")
        return

    # Get positioning values
    try:
        x_offset = float(x_position_entry.get() or 0)
        y_offset = float(y_position_entry.get() or 0)
    except ValueError:
        messagebox.showerror("Error", "X and Y positions must be valid numbers.")
        return

    # Convert offsets to normalized positions (0-1 range)
    x_pos = convert_position_to_normalized(x_offset)
    y_pos = convert_position_to_normalized(y_offset)

    # Determine if we should combine PDFs
    should_combine = combine_pdfs_var.get()

    # Drawing options
    drawing_options = DrawingOptions(
        watermark=watermark_text,
        opacity=0.3,
        text_font=font_path,
        custom_fonts_folder=custom_fonts_folder,
        text_size=14,
        # angle=0,
    )

    # Insert options with positioning
    insert_options = InsertOptions(x=x_pos, y=y_pos)

    failed_files = []
    watermarked_files = []

    try:
        # Process each PDF
        for input_pdf in selected_pdfs:
            output_pdf = build_output_path(input_pdf, output_folder)

            try:
                add_watermark_to_pdf(
                    input=input_pdf,
                    output=output_pdf,
                    drawing_options=drawing_options,
                    specific_options=insert_options,
                )
                watermarked_files.append(output_pdf)

            except Exception as e:
                failed_files.append((input_pdf, str(e)))

        # Combine PDFs if requested and we have multiple files
        if should_combine and len(watermarked_files) > 1:
            combined_output = combine_pdfs(watermarked_files)
            if combined_output:
                messagebox.showinfo(
                    "Success",
                    f"Watermarked and combined {len(watermarked_files)} file(s) into:\n{combined_output}",
                )
        elif not failed_files:
            messagebox.showinfo(
                "Success",
                f"Watermark applied to {len(selected_pdfs)} file(s) successfully!",
            )

        if failed_files:
            error_msg = "\n\n".join(
                f"{os.path.basename(f)}:\n{err}" for f, err in failed_files
            )
            messagebox.showerror("Some files failed", error_msg)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")


# ---------------- GUI ----------------

root = ctk.CTk()
root.title("PDF Watermark Tool")
root.geometry("1000x880")
root.resizable(True, True)

# Configure grid weight for responsive design
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Main container frame
main_frame = ctk.CTkFrame(root, corner_radius=15)
main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
main_frame.grid_columnconfigure(0, weight=1)

# Title
title_label = ctk.CTkLabel(
    main_frame,
    text="✨ PDF Watermark Tool ✨",
    font=ctk.CTkFont(size=28, weight="bold"),
)
title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

subtitle_label = ctk.CTkLabel(
    main_frame,
    text="Add watermarks to your PDF files with ease",
    font=ctk.CTkFont(size=14),
    text_color="gray",
)
subtitle_label.grid(row=1, column=0, padx=20, pady=0, sticky="ew")

# Input PDF Section
input_frame = ctk.CTkFrame(main_frame, corner_radius=10)
input_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
input_frame.grid_columnconfigure(0, weight=1)

input_label = ctk.CTkLabel(
    input_frame,
    text="📂 Select PDF Files",
    font=ctk.CTkFont(size=16, weight="bold"),
    anchor="w",
)
input_label.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")

input_pdf_entry = ctk.CTkEntry(
    input_frame,
    placeholder_text="No files selected...",
    height=40,
    font=ctk.CTkFont(size=13),
)
input_pdf_entry.grid(row=1, column=0, padx=(15, 10), pady=(0, 10), sticky="ew")

browse_button = ctk.CTkButton(
    input_frame,
    text="Browse",
    command=select_pdf,
    width=120,
    height=40,
    font=ctk.CTkFont(size=13, weight="bold"),
    corner_radius=8,
)
browse_button.grid(row=1, column=1, padx=(0, 15), pady=(0, 10), sticky="e")

file_count_label = ctk.CTkLabel(
    input_frame,
    text="📄 0 file(s) selected",
    font=ctk.CTkFont(size=12),
    text_color="gray",
)
file_count_label.grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w")

# Output Folder Section
output_frame = ctk.CTkFrame(main_frame, corner_radius=10)
output_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
output_frame.grid_columnconfigure(0, weight=1)

output_label = ctk.CTkLabel(
    output_frame,
    text="📁 Output Folder (Optional)",
    font=ctk.CTkFont(size=16, weight="bold"),
    anchor="w",
)
output_label.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")

output_folder_entry = ctk.CTkEntry(
    output_frame,
    placeholder_text="Same as input folder...",
    height=40,
    font=ctk.CTkFont(size=13),
)
output_folder_entry.grid(row=1, column=0, padx=(15, 10), pady=(0, 15), sticky="ew")

output_browse_button = ctk.CTkButton(
    output_frame,
    text="Browse",
    command=select_output_folder,
    width=120,
    height=40,
    font=ctk.CTkFont(size=13, weight="bold"),
    corner_radius=8,
)
output_browse_button.grid(row=1, column=1, padx=(0, 15), pady=(0, 15), sticky="e")

# Watermark Settings Section (Combined: Text, Position, Options)
settings_frame = ctk.CTkFrame(main_frame, corner_radius=10)
settings_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
settings_frame.grid_columnconfigure(0, weight=1)

settings_label = ctk.CTkLabel(
    settings_frame,
    text="⚙️ Watermark Settings",
    font=ctk.CTkFont(size=16, weight="bold"),
    anchor="w",
)
settings_label.grid(row=0, column=0, columnspan=4, padx=15, pady=(15, 0), sticky="w")

# Watermark Text
text_label = ctk.CTkLabel(
    settings_frame,
    text="✏️ Watermark Text:",
    font=ctk.CTkFont(size=13),
    anchor="w",
)
text_label.grid(row=1, column=0, columnspan=4, padx=15, pady=3, sticky="w")

text_entry = ctk.CTkTextbox(
    settings_frame, height=60, font=ctk.CTkFont(size=13), corner_radius=8, wrap="word"
)
text_entry.grid(row=2, column=0, columnspan=4, padx=15, pady=(0, 8), sticky="ew")

# Position Section
position_label = ctk.CTkLabel(
    settings_frame,
    text="📍 Position:",
    font=ctk.CTkFont(size=13),
    anchor="w",
)
position_label.grid(row=3, column=0, columnspan=4, padx=15, pady=(5, 3), sticky="w")

# X and Y Position in same row
settings_frame.grid_columnconfigure(1, weight=1)
settings_frame.grid_columnconfigure(3, weight=1)

x_label = ctk.CTkLabel(
    settings_frame,
    text="X Offset:",
    font=ctk.CTkFont(size=12),
    anchor="w",
)
x_label.grid(row=4, column=0, padx=15, pady=(0, 3), sticky="w")

x_position_entry = ctk.CTkEntry(
    settings_frame,
    placeholder_text="0",
    height=35,
    width=100,
    font=ctk.CTkFont(size=13),
)
x_position_entry.insert(0, "0")
x_position_entry.grid(row=4, column=0, padx=70, pady=(0, 3), sticky="w")

y_label = ctk.CTkLabel(
    settings_frame,
    text="Y Offset:",
    font=ctk.CTkFont(size=12),
    anchor="w",
)
y_label.grid(row=4, column=1, padx=(5, 10), pady=(0, 3), sticky="w")

y_position_entry = ctk.CTkEntry(
    settings_frame,
    placeholder_text="0",
    height=35,
    width=100,
    font=ctk.CTkFont(size=13),
)
y_position_entry.insert(0, "0")
y_position_entry.grid(row=4, column=1, padx=70, pady=(0, 3), sticky="w")

# Position instructions
position_info = ctk.CTkLabel(
    settings_frame,
    text="💡 Range: -5 to +5 | 0,0 = center | +X = right, -X = left | +Y = up, -Y = down",
    font=ctk.CTkFont(size=11),
    text_color="gray",
)
position_info.grid(row=5, column=0, columnspan=4, padx=15, pady=(3, 8), sticky="w")

# Options
options_label = ctk.CTkLabel(
    settings_frame,
    text="🔧 Options:",
    font=ctk.CTkFont(size=13),
    anchor="w",
)
options_label.grid(row=6, column=0, columnspan=4, padx=5, pady=(3, 3), sticky="w")

# Combine PDFs checkbox
combine_pdfs_var = ctk.BooleanVar(value=False)
combine_checkbox = ctk.CTkCheckBox(
    settings_frame,
    text="Combine multiple PDFs into one file",
    variable=combine_pdfs_var,
    font=ctk.CTkFont(size=13),
)
combine_checkbox.grid(row=7, column=0, columnspan=4, padx=15, pady=(0, 15), sticky="w")

# Apply Button
apply_button = ctk.CTkButton(
    main_frame,
    text="🎨 Apply Watermark",
    command=apply_watermark,
    width=250,
    height=50,
    font=ctk.CTkFont(size=16, weight="bold"),
    corner_radius=10,
    fg_color="#2ecc71",
    hover_color="#27ae60",
)
apply_button.grid(row=5, column=0, padx=20, pady=20)

root.mainloop()

# BUILD script
# pyinstaller --onefile --windowed --add-data "fonts;fonts" main.py
