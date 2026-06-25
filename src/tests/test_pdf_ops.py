import os
import tempfile
import unittest

import pypdf

from pdf_toolkit.pdf_ops import (
    build_default_merge_output_path,
    get_pdf_page_count,
    insert_pdf_at_page,
    insert_pdfs_at_page,
    insert_pdfs_with_settings,
    parse_split_group_specs,
    parse_split_groups,
    split_pdf,
)


def make_pdf(path: str, page_widths: list[int]):
    writer = pypdf.PdfWriter()
    for width in page_widths:
        writer.add_blank_page(width=width, height=200)
    with open(path, "wb") as output_file:
        writer.write(output_file)


def page_widths(path: str) -> list[int]:
    reader = pypdf.PdfReader(path)
    return [int(page.mediabox.width) for page in reader.pages]


class ParseSplitGroupsTests(unittest.TestCase):
    def test_parses_default_n_syntax(self):
        self.assertEqual(parse_split_groups("1-N", 4), [[1, 2, 3, 4]])

    def test_parses_single_pages_and_ranges(self):
        self.assertEqual(parse_split_groups("1", 10), [[1]])
        self.assertEqual(parse_split_groups("1;3;5", 10), [[1], [3], [5]])
        self.assertEqual(
            parse_split_groups("1-3;5;8-10", 10),
            [[1, 2, 3], [5], [8, 9, 10]],
        )

    def test_rejects_invalid_specs(self):
        invalid_specs = ["", "0", "3-1", "abc", "11"]
        for spec in invalid_specs:
            with self.subTest(spec=spec):
                with self.assertRaises(ValueError):
                    parse_split_groups(spec, 10)

    def test_rejects_duplicate_pages(self):
        with self.assertRaises(ValueError):
            parse_split_groups("1-3;3", 10)

    def test_parses_split_group_specs_from_individual_rows(self):
        self.assertEqual(
            parse_split_group_specs(["1-3", "5", "8-N"], 10),
            [[1, 2, 3], [5], [8, 9, 10]],
        )

    def test_split_group_specs_reject_semicolons(self):
        with self.assertRaises(ValueError):
            parse_split_group_specs(["1-3;5"], 10)

    def test_split_group_specs_allows_overlapping_pages(self):
        self.assertEqual(
            parse_split_group_specs(["1-3", "2-4"], 10),
            [[1, 2, 3], [2, 3, 4]],
        )

    def test_split_group_specs_allows_duplicate_ranges(self):
        self.assertEqual(
            parse_split_group_specs(["1-3", "1-3"], 10),
            [[1, 2, 3], [1, 2, 3]],
        )

    def test_split_group_specs_reject_empty_rows(self):
        with self.assertRaises(ValueError):
            parse_split_group_specs(["1-3", ""], 10)


class PdfOperationTests(unittest.TestCase):
    def test_split_pdf_creates_expected_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_pdf = os.path.join(temp_dir, "source.pdf")
            make_pdf(input_pdf, [100, 101, 102, 103])

            output_paths = split_pdf(input_pdf, [[1], [2, 3]], temp_dir)

            self.assertEqual(len(output_paths), 2)
            self.assertEqual(get_pdf_page_count(output_paths[0]), 1)
            self.assertEqual(get_pdf_page_count(output_paths[1]), 2)
            self.assertTrue(output_paths[0].endswith("source_split_1_pages_1.pdf"))
            self.assertTrue(output_paths[1].endswith("source_split_2_pages_2-3.pdf"))

    def test_split_pdf_uses_unique_names_for_duplicate_ranges(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_pdf = os.path.join(temp_dir, "source.pdf")
            make_pdf(input_pdf, [100, 101, 102])

            output_paths = split_pdf(input_pdf, [[1, 2], [1, 2]], temp_dir)

            self.assertEqual(len(output_paths), 2)
            self.assertNotEqual(output_paths[0], output_paths[1])
            self.assertTrue(output_paths[0].endswith("source_split_1_pages_1-2.pdf"))
            self.assertTrue(output_paths[1].endswith("source_split_2_pages_1-2.pdf"))

    def test_merge_inserts_before_first_page(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_pdf = os.path.join(temp_dir, "original.pdf")
            insert_pdf = os.path.join(temp_dir, "insert.pdf")
            output_pdf = os.path.join(temp_dir, "merged.pdf")
            make_pdf(original_pdf, [100, 101, 102])
            make_pdf(insert_pdf, [200, 201])

            insert_pdf_at_page(original_pdf, insert_pdf, 0, output_pdf)

            self.assertEqual(page_widths(output_pdf), [200, 201, 100, 101, 102])

    def test_merge_inserts_after_middle_page(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_pdf = os.path.join(temp_dir, "original.pdf")
            insert_pdf = os.path.join(temp_dir, "insert.pdf")
            output_pdf = os.path.join(temp_dir, "merged.pdf")
            make_pdf(original_pdf, [100, 101, 102])
            make_pdf(insert_pdf, [200, 201])

            insert_pdf_at_page(original_pdf, insert_pdf, 2, output_pdf)

            self.assertEqual(page_widths(output_pdf), [100, 101, 200, 201, 102])

    def test_merge_inserts_after_last_page(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_pdf = os.path.join(temp_dir, "original.pdf")
            insert_pdf = os.path.join(temp_dir, "insert.pdf")
            output_pdf = os.path.join(temp_dir, "merged.pdf")
            make_pdf(original_pdf, [100, 101])
            make_pdf(insert_pdf, [200])

            insert_pdf_at_page(original_pdf, insert_pdf, 2, output_pdf)

            self.assertEqual(page_widths(output_pdf), [100, 101, 200])

    def test_merge_inserts_multiple_pdfs_in_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_pdf = os.path.join(temp_dir, "original.pdf")
            first_insert_pdf = os.path.join(temp_dir, "first_insert.pdf")
            second_insert_pdf = os.path.join(temp_dir, "second_insert.pdf")
            output_pdf = os.path.join(temp_dir, "merged.pdf")
            make_pdf(original_pdf, [100, 101, 102])
            make_pdf(first_insert_pdf, [200, 201])
            make_pdf(second_insert_pdf, [300])

            insert_pdfs_at_page(
                original_pdf,
                [first_insert_pdf, second_insert_pdf],
                1,
                output_pdf,
            )

            self.assertEqual(page_widths(output_pdf), [100, 200, 201, 300, 101, 102])

    def test_merge_inserts_multiple_pdfs_with_independent_positions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_pdf = os.path.join(temp_dir, "original.pdf")
            first_insert_pdf = os.path.join(temp_dir, "first_insert.pdf")
            second_insert_pdf = os.path.join(temp_dir, "second_insert.pdf")
            output_pdf = os.path.join(temp_dir, "merged.pdf")
            make_pdf(original_pdf, [100, 101, 102])
            make_pdf(first_insert_pdf, [200])
            make_pdf(second_insert_pdf, [300])

            insert_pdfs_with_settings(
                original_pdf,
                [
                    (first_insert_pdf, 1),
                    (second_insert_pdf, 3),
                ],
                output_pdf,
            )

            self.assertEqual(page_widths(output_pdf), [100, 200, 101, 102, 300])

    def test_merge_keeps_row_order_for_same_position(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_pdf = os.path.join(temp_dir, "original.pdf")
            first_insert_pdf = os.path.join(temp_dir, "first_insert.pdf")
            second_insert_pdf = os.path.join(temp_dir, "second_insert.pdf")
            output_pdf = os.path.join(temp_dir, "merged.pdf")
            make_pdf(original_pdf, [100, 101])
            make_pdf(first_insert_pdf, [200])
            make_pdf(second_insert_pdf, [300])

            insert_pdfs_with_settings(
                original_pdf,
                [
                    (first_insert_pdf, 0),
                    (second_insert_pdf, 0),
                ],
                output_pdf,
            )

            self.assertEqual(page_widths(output_pdf), [200, 300, 100, 101])

    def test_default_merge_output_path(self):
        output_path = build_default_merge_output_path(
            os.path.join("C:\\docs", "source.pdf"),
            os.path.join("C:\\out"),
        )

        self.assertTrue(
            output_path.endswith(os.path.join("C:\\out", "source_merged.pdf"))
        )


if __name__ == "__main__":
    unittest.main()
