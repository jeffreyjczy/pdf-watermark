import customtkinter as ctk

from pdf_toolkit.tabs import MergerTab, SplitterTab, WatermarkTab


class PdfToolkitApp:
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("PDF Toolkit")
        self.root.geometry("1180x920")
        self.root.minsize(760, 560)
        self.root.resizable(True, True)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self.root, corner_radius=8)
        self.tabview.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        self.tabview.add("Watermark")
        self.tabview.add("Splitter")
        self.tabview.add("Merger")

        WatermarkTab(self.tabview.tab("Watermark"))
        SplitterTab(self.tabview.tab("Splitter"))
        MergerTab(self.tabview.tab("Merger"))

    def run(self):
        self.root.mainloop()


def main():
    PdfToolkitApp().run()
