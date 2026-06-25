import os
from functools import lru_cache
from typing import Iterable

import fitz
from PIL import Image
import pypdf


def get_pdf_page_count(pdf_path: str) -> int:
    reader = pypdf.PdfReader(pdf_path)
    return len(reader.pages)


def parse_split_groups(spec: str, page_count: int) -> list[list[int]]:
    if page_count < 1:
        raise ValueError("PDF has no pages.")

    spec = spec.strip()
    if not spec:
        raise ValueError("Enter at least one split range.")

    groups: list[list[int]] = []
    seen_groups: set[tuple[int, ...]] = set()
    seen_pages: set[int] = set()

    for raw_group in spec.split(";"):
        token = raw_group.strip()
        if not token:
            raise ValueError("Split groups cannot be empty.")

        pages = _parse_page_token(token, page_count)
        group_key = tuple(pages)
        if group_key in seen_groups:
            raise ValueError(f"Duplicate split group: {format_page_group(pages)}.")
        duplicated_pages = seen_pages.intersection(pages)
        if duplicated_pages:
            repeated = ", ".join(str(page) for page in sorted(duplicated_pages))
            raise ValueError(f"Duplicate page(s) across groups: {repeated}.")

        seen_groups.add(group_key)
        seen_pages.update(pages)
        groups.append(pages)

    return groups


def parse_split_group_specs(specs: list[str], page_count: int) -> list[list[int]]:
    if page_count < 1:
        raise ValueError("PDF has no pages.")
    if not specs:
        raise ValueError("Add at least one output range.")

    groups: list[list[int]] = []

    for index, raw_spec in enumerate(specs, start=1):
        token = raw_spec.strip()
        if not token:
            raise ValueError(f"Output {index} range cannot be empty.")
        if ";" in token:
            raise ValueError(f"Output {index} range cannot contain semicolons.")

        groups.append(_parse_page_token(token, page_count))

    return groups


def _parse_page_token(token: str, page_count: int) -> list[int]:
    normalized = token.upper().replace("N", str(page_count))

    if "-" in normalized:
        parts = [part.strip() for part in normalized.split("-")]
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(f"Invalid range: {token}.")
        start = _parse_page_number(parts[0], page_count, token)
        end = _parse_page_number(parts[1], page_count, token)
        if start > end:
            raise ValueError(f"Range starts after it ends: {token}.")
        return list(range(start, end + 1))

    return [_parse_page_number(normalized, page_count, token)]


def _parse_page_number(value: str, page_count: int, original_token: str) -> int:
    if not value.isdigit():
        raise ValueError(f"Invalid page number: {original_token}.")

    page_number = int(value)
    if page_number < 1:
        raise ValueError("Page numbers must be 1 or greater.")
    if page_number > page_count:
        raise ValueError(
            f"Page {page_number} is outside the PDF page count ({page_count})."
        )
    return page_number


def format_page_group(pages: Iterable[int]) -> str:
    values = list(pages)
    if not values:
        return ""
    if len(values) == 1:
        return str(values[0])
    return f"{values[0]}-{values[-1]}"


def split_pdf(
    input_pdf: str,
    groups: list[list[int]],
    output_folder: str | None = None,
) -> list[str]:
    reader = pypdf.PdfReader(input_pdf)
    base_name = os.path.splitext(os.path.basename(input_pdf))[0]
    destination_folder = output_folder or os.path.dirname(input_pdf)
    output_paths: list[str] = []

    if not os.path.isdir(destination_folder):
        os.makedirs(destination_folder, exist_ok=True)

    for index, pages in enumerate(groups, start=1):
        writer = pypdf.PdfWriter()
        for page_number in pages:
            writer.add_page(reader.pages[page_number - 1])

        label = format_page_group(pages)
        output_path = os.path.join(
            destination_folder,
            f"{base_name}_split_{index}_pages_{label}.pdf",
        )
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        output_paths.append(output_path)

    return output_paths


def insert_pdf_at_page(
    original_pdf: str,
    insert_pdf: str,
    after_page_number: int,
    output_path: str,
) -> str:
    return insert_pdfs_at_page(
        original_pdf,
        [insert_pdf],
        after_page_number,
        output_path,
    )


def insert_pdfs_at_page(
    original_pdf: str,
    insert_pdfs: list[str],
    after_page_number: int,
    output_path: str,
) -> str:
    return insert_pdfs_with_settings(
        original_pdf,
        [(path, after_page_number) for path in insert_pdfs],
        output_path,
    )


def insert_pdfs_with_settings(
    original_pdf: str,
    insert_specs: list[tuple[str, int]],
    output_path: str,
) -> str:
    original_reader = pypdf.PdfReader(original_pdf)
    original_page_count = len(original_reader.pages)

    if not insert_specs:
        raise ValueError("Select at least one PDF to insert.")

    inserts_by_position: dict[int, list[pypdf.PdfReader]] = {}
    for path, after_page_number in insert_specs:
        if after_page_number < 0 or after_page_number > original_page_count:
            raise ValueError(
                f"Insert position must be between 0 and {original_page_count}."
            )
        inserts_by_position.setdefault(after_page_number, []).append(
            pypdf.PdfReader(path)
        )

    output_folder = os.path.dirname(output_path)
    if output_folder and not os.path.isdir(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    writer = pypdf.PdfWriter()

    for index, page in enumerate(original_reader.pages, start=1):
        if index == 1:
            _add_insert_pages(writer, inserts_by_position.get(0, []))

        writer.add_page(page)
        _add_insert_pages(writer, inserts_by_position.get(index, []))

    if original_page_count == 0:
        _add_insert_pages(writer, inserts_by_position.get(0, []))

    with open(output_path, "wb") as output_file:
        writer.write(output_file)

    return output_path


def _add_insert_pages(
    writer: pypdf.PdfWriter,
    insert_readers: list[pypdf.PdfReader],
):
    for insert_reader in insert_readers:
        for insert_page in insert_reader.pages:
            writer.add_page(insert_page)


def build_default_merge_output_path(
    original_pdf: str,
    output_folder: str | None = None,
) -> str:
    folder = output_folder or os.path.dirname(original_pdf)
    name = os.path.splitext(os.path.basename(original_pdf))[0]
    return os.path.join(folder, f"{name}_merged.pdf")


@lru_cache(maxsize=128)
def render_pdf_page(
    pdf_path: str,
    page_number: int,
    max_size: tuple[int, int] = (220, 300),
) -> Image.Image:
    with fitz.open(pdf_path) as document:
        if page_number < 1 or page_number > document.page_count:
            raise ValueError(
                f"Page {page_number} is outside the PDF page count ({document.page_count})."
            )

        page = document.load_page(page_number - 1)
        rect = page.rect
        max_width, max_height = max_size
        scale = min(max_width / rect.width, max_height / rect.height)
        scale = max(scale, 0.1)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        image = Image.frombytes(
            "RGB",
            (pixmap.width, pixmap.height),
            pixmap.samples,
        )
        return image.copy()
