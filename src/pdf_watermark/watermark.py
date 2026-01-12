import click
from dataclass_click import dataclass_click

from pdf_watermark.handler import add_watermark_from_options
from pdf_watermark.options import (
    DrawingOptions,
    FilesOptions,
    GridOptions,
    InsertOptions,
)


@click.group()
def cli():
    """
    Add a watermark to one or more PDF files.

    The watermark can be repeated in a grid pattern using the grid command, or inserted at a specific position using the insert command.
    """
    pass


@cli.command()
@dataclass_click(FilesOptions)
@dataclass_click(InsertOptions)
@dataclass_click(DrawingOptions)
def insert(
    drawing_options: DrawingOptions,
    insert_options: InsertOptions,
    files_options: FilesOptions,
):
    """
    Add a watermark at a specific position.

    Add a WATERMARK to one or more PDF files referenced by FILE.
    WATERMARK can be either a string or a path to an image file.
    FILE can be a single file or a directory, in which case all PDF files in the directory will be watermarked.
    """

    add_watermark_from_options(
        files_options,
        drawing_options,
        insert_options,
    )


@cli.command()
@dataclass_click(FilesOptions)
@dataclass_click(GridOptions)
@dataclass_click(DrawingOptions)
def grid(
    drawing_options: DrawingOptions,
    grid_options: GridOptions,
    files_options: FilesOptions,
):
    """
    Add a watermark in a grid pattern.

    Add a WATERMARK to one or more PDF files referenced by FILE.
    WATERMARK can be either a string or a path to an image file.
    FILE can be a single file or a directory, in which case all PDF files in the directory will be watermarked.
    """

    add_watermark_from_options(
        files_options,
        drawing_options,
        grid_options,
    )

def insert_watermark_gui(
    input_pdf: str,
    watermark_text: str,
    font_path: str,
    custom_fonts_folder: str,
    output_pdf: str,
):
    files_options = FilesOptions(
        file=input_pdf,
        output=output_pdf
    )

    insert_options = InsertOptions()

    drawing_options = DrawingOptions(
        watermark=watermark_text,
        opacity=0.3,
        text_font=font_path,
        custom_fonts_folder=custom_fonts_folder
    )

    add_watermark_from_options(
        files_options,
        drawing_options,
        insert_options,
    )

if __name__ == "__main__":
    cli()
