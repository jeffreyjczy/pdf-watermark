import tkinter as tk
from tkinter import filedialog, messagebox
import sys
import os
from pdf_watermark.watermark import insert_watermark_gui

selected_pdfs = []

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp dir
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def select_pdf():
    global selected_pdfs

    paths = filedialog.askopenfilenames(
        filetypes=[("PDF Files", "*.pdf")]
    )

    if not paths:
        return

    selected_pdfs = list(paths)

    file_names = [os.path.basename(p) for p in selected_pdfs]
    input_pdf_var.set(", ".join(file_names))

def build_output_path(input_pdf_path):
    directory, filename = os.path.split(input_pdf_path)
    name, ext = os.path.splitext(filename)

    return os.path.join(
        directory,
        f"{name}_watermarked{ext}"
    )

def apply_watermark():
    if not selected_pdfs:
        messagebox.showerror("Error", "Please select at least one PDF.")
        return

    font_path = "NotoSansThai-Regular"
    custom_fonts_folder = resource_path("fonts")
    watermark_text = text_entry.get("1.0", tk.END).strip()

    if not watermark_text:
        messagebox.showerror("Error", "Please enter watermark text.")
        return

    failed_files = []

    for input_pdf in selected_pdfs:
        output_pdf = build_output_path(input_pdf)

        try:
            insert_watermark_gui(
                input_pdf=input_pdf,
                watermark_text=watermark_text,
                font_path=font_path,
                custom_fonts_folder=custom_fonts_folder,
                output_pdf=output_pdf,
            )

        except Exception as e:
            failed_files.append((input_pdf, str(e)))

    if not failed_files:
        messagebox.showinfo(
            "Success",
            f"Watermark applied to {len(selected_pdfs)} file(s) successfully!"
        )
    else:
        error_msg = "\n\n".join(
            f"{os.path.basename(f)}:\n{err}"
            for f, err in failed_files
        )
        messagebox.showerror(
            "Some files failed",
            error_msg
        )

# ---------------- GUI ----------------

root = tk.Tk()
root.title("PDF Watermark Tool")
root.geometry("550x420")
root.resizable(True, True)

input_pdf_var = tk.StringVar()
output_pdf_var = tk.StringVar()
font_path_var = tk.StringVar()

# Input PDF
tk.Label(root, text="Input PDF:").pack(anchor="w", padx=10, pady=(10, 0))

input_row = tk.Frame(root)
input_row.pack(fill="x", padx=10, pady=5)

tk.Entry(
    input_row,
    textvariable=input_pdf_var
).pack(side="left", fill="x", expand=True)

tk.Button(
    input_row,
    text="Browse",
    command=select_pdf,
    width=10
).pack(side="left", padx=(5, 0))

# Watermark Text
tk.Label(root, text="Watermark Text:").pack(anchor="w", padx=10)
text_entry = tk.Text(root, height=4, width=60)
text_entry.pack(padx=10, pady=5)

# Apply Button
tk.Button(
    root,
    text="Apply Watermark",
    command=apply_watermark,
    bg="#FFFFFF",
    fg="black",
    width=25
).pack(pady=15)

root.mainloop()

# BUILD script
# pyinstaller --onefile --windowed --add-data "fonts;fonts" main.py


