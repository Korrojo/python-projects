"""Tests for exporter module."""

import csv
from unittest.mock import patch


from db_collection_stats.collector import CollectionStats
from db_collection_stats.exporter import export_to_csv, format_bytes, print_summary


class TestExportToCsv:
    """Tests for export_to_csv function."""

    def test_export_to_csv_creates_file(self, tmp_path):
        """Test that CSV file is created with correct structure."""
        stats_list = [
            CollectionStats(
                collection_name="users",
                document_count=1000,
                collection_size_bytes=500000,
                avg_document_size_bytes=500.5,
                storage_size_bytes=600000,
                num_indexes=3,
                total_index_size_bytes=50000,
            ),
            CollectionStats(
                collection_name="orders",
                document_count=500,
                collection_size_bytes=250000,
                avg_document_size_bytes=500.0,
                storage_size_bytes=300000,
                num_indexes=2,
                total_index_size_bytes=25000,
            ),
        ]

        output_path = export_to_csv(stats_list, tmp_path, "test_db")

        # Verify file was created
        assert output_path.exists()
        assert output_path.parent == tmp_path
        # Filename pattern: YYYYMMDD_HHMMSS_collection_stats_<database>.csv
        assert "_collection_stats_test_db.csv" in output_path.name
        assert output_path.name[0].isdigit()  # Starts with timestamp
        assert output_path.suffix == ".csv"

    def test_export_to_csv_correct_content(self, tmp_path):
        """Test that CSV contains correct data."""
        stats_list = [
            CollectionStats(
                collection_name="products",
                document_count=200,
                collection_size_bytes=100000,
                avg_document_size_bytes=500.123,
                storage_size_bytes=120000,
                num_indexes=4,
                total_index_size_bytes=10000,
            )
        ]

        output_path = export_to_csv(stats_list, tmp_path, "shop_db")

        # Read and verify CSV content
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["collection_name"] == "products"
        assert rows[0]["document_count"] == "200"
        assert rows[0]["collection_size_bytes"] == "100000"
        assert rows[0]["avg_document_size_bytes"] == "500.12"  # Rounded to 2 decimals
        assert rows[0]["storage_size_bytes"] == "120000"
        assert rows[0]["num_indexes"] == "4"
        assert rows[0]["total_index_size_bytes"] == "10000"

    def test_export_to_csv_correct_headers(self, tmp_path):
        """Test that CSV has correct headers."""
        stats_list = [
            CollectionStats(
                collection_name="test",
                document_count=1,
                collection_size_bytes=1,
                avg_document_size_bytes=1.0,
                storage_size_bytes=1,
                num_indexes=1,
                total_index_size_bytes=1,
            )
        ]

        output_path = export_to_csv(stats_list, tmp_path, "test_db")

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)

        expected_headers = [
            "collection_name",
            "document_count",
            "collection_size_bytes",
            "avg_document_size_bytes",
            "storage_size_bytes",
            "num_indexes",
            "total_index_size_bytes",
        ]
        assert headers == expected_headers

    def test_export_to_csv_creates_directory(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        nested_path = tmp_path / "nested" / "output"
        stats_list = [
            CollectionStats(
                collection_name="test",
                document_count=1,
                collection_size_bytes=1,
                avg_document_size_bytes=1.0,
                storage_size_bytes=1,
                num_indexes=1,
                total_index_size_bytes=1,
            )
        ]

        output_path = export_to_csv(stats_list, nested_path, "test_db")

        assert nested_path.exists()
        assert output_path.exists()

    def test_export_to_csv_empty_list(self, tmp_path):
        """Test exporting empty statistics list."""
        stats_list = []

        output_path = export_to_csv(stats_list, tmp_path, "empty_db")

        # File should still be created with headers only
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) == 1  # Only headers
        assert rows[0][0] == "collection_name"

    @patch("db_collection_stats.exporter.datetime")
    def test_export_to_csv_filename_format(self, mock_datetime, tmp_path):
        """Test that filename includes correct timestamp format."""
        mock_datetime.now.return_value.strftime.return_value = "20240115_143022"

        stats_list = [
            CollectionStats(
                collection_name="test",
                document_count=1,
                collection_size_bytes=1,
                avg_document_size_bytes=1.0,
                storage_size_bytes=1,
                num_indexes=1,
                total_index_size_bytes=1,
            )
        ]

        output_path = export_to_csv(stats_list, tmp_path, "mydb")

        assert output_path.name == "20240115_143022_collection_stats_mydb.csv"


class TestFormatBytes:
    """Tests for format_bytes function."""

    def test_format_bytes_bytes(self):
        """Test formatting values in bytes range."""
        assert format_bytes(0) == "0.00 B"
        assert format_bytes(512) == "512.00 B"
        assert format_bytes(1023) == "1023.00 B"

    def test_format_bytes_kilobytes(self):
        """Test formatting values in kilobytes range."""
        assert format_bytes(1024) == "1.00 KB"
        assert format_bytes(1536) == "1.50 KB"
        assert format_bytes(10240) == "10.00 KB"

    def test_format_bytes_megabytes(self):
        """Test formatting values in megabytes range."""
        assert format_bytes(1048576) == "1.00 MB"
        assert format_bytes(5242880) == "5.00 MB"
        assert format_bytes(1572864) == "1.50 MB"

    def test_format_bytes_gigabytes(self):
        """Test formatting values in gigabytes range."""
        assert format_bytes(1073741824) == "1.00 GB"
        assert format_bytes(2147483648) == "2.00 GB"
        assert format_bytes(5368709120) == "5.00 GB"

    def test_format_bytes_terabytes(self):
        """Test formatting values in terabytes range."""
        assert format_bytes(1099511627776) == "1.00 TB"
        assert format_bytes(2199023255552) == "2.00 TB"

    def test_format_bytes_petabytes(self):
        """Test formatting values in petabytes range."""
        assert format_bytes(1125899906842624) == "1.00 PB"
        assert format_bytes(5629499534213120) == "5.00 PB"

    def test_format_bytes_precision(self):
        """Test that formatting maintains 2 decimal precision."""
        assert format_bytes(1536) == "1.50 KB"
        assert format_bytes(1587) == "1.55 KB"
        assert format_bytes(1590886) == "1.52 MB"


class TestPrintSummary:
    """Tests for print_summary function."""

    def test_print_summary_empty_list(self, capsys):
        """Test printing summary with empty statistics list."""
        print_summary([], "empty_db")

        captured = capsys.readouterr()
        assert "empty_db" in captured.out
        assert "No collections found" in captured.out

    def test_print_summary_displays_database_name(self, capsys):
        """Test that database name is displayed."""
        stats_list = [
            CollectionStats(
                collection_name="test",
                document_count=100,
                collection_size_bytes=10000,
                avg_document_size_bytes=100.0,
                storage_size_bytes=12000,
                num_indexes=2,
                total_index_size_bytes=1000,
            )
        ]

        print_summary(stats_list, "production_db")

        captured = capsys.readouterr()
        assert "production_db" in captured.out

    def test_print_summary_displays_totals(self, capsys):
        """Test that totals are calculated and displayed correctly."""
        stats_list = [
            CollectionStats(
                collection_name="users",
                document_count=1000,
                collection_size_bytes=500000,
                avg_document_size_bytes=500.0,
                storage_size_bytes=600000,
                num_indexes=3,
                total_index_size_bytes=50000,
            ),
            CollectionStats(
                collection_name="orders",
                document_count=500,
                collection_size_bytes=250000,
                avg_document_size_bytes=500.0,
                storage_size_bytes=300000,
                num_indexes=2,
                total_index_size_bytes=25000,
            ),
        ]

        print_summary(stats_list, "test_db")

        captured = capsys.readouterr()
        assert "Total Collections: 2" in captured.out
        assert "Total Documents: 1,500" in captured.out
        assert "Total Indexes: 5" in captured.out

    def test_print_summary_shows_top_5_collections(self, capsys):
        """Test that top 5 largest collections are displayed."""
        stats_list = [CollectionStats(f"collection_{i}", 100, i * 10000, 100.0, i * 12000, 2, 1000) for i in range(10)]

        print_summary(stats_list, "test_db")

        captured = capsys.readouterr()
        assert "Top 5 Largest Collections" in captured.out
        # Largest should be collection_9
        assert "collection_9" in captured.out

    def test_print_summary_formats_bytes_human_readable(self, capsys):
        """Test that byte values are formatted in human-readable format."""
        stats_list = [
            CollectionStats(
                collection_name="large_collection",
                document_count=1000000,
                collection_size_bytes=5368709120,  # 5 GB
                avg_document_size_bytes=5000.0,
                storage_size_bytes=6442450944,  # 6 GB
                num_indexes=5,
                total_index_size_bytes=1073741824,  # 1 GB
            )
        ]

        print_summary(stats_list, "test_db")

        captured = capsys.readouterr()
        assert "GB" in captured.out  # Should show GB units

    def test_print_summary_displays_collection_details(self, capsys):
        """Test that individual collection details are shown."""
        stats_list = [
            CollectionStats(
                collection_name="important_collection",
                document_count=12345,
                collection_size_bytes=1048576,  # 1 MB
                avg_document_size_bytes=85.0,
                storage_size_bytes=2097152,  # 2 MB
                num_indexes=3,
                total_index_size_bytes=524288,  # 512 KB
            )
        ]

        print_summary(stats_list, "test_db")

        captured = capsys.readouterr()
        assert "important_collection" in captured.out
        assert "12,345" in captured.out  # Formatted with comma
        assert "3" in captured.out  # Number of indexes

    def test_print_summary_sorts_by_size(self, capsys):
        """Test that collections are sorted by size in top 5."""
        stats_list = [
            CollectionStats("small", 100, 1000, 10.0, 1200, 1, 100),
            CollectionStats("large", 100, 10000, 100.0, 12000, 1, 100),
            CollectionStats("medium", 100, 5000, 50.0, 6000, 1, 100),
        ]

        print_summary(stats_list, "test_db")

        captured = capsys.readouterr()
        lines = captured.out.split("\n")

        # Find the section with collection details
        large_line_idx = None
        medium_line_idx = None
        small_line_idx = None

        for i, line in enumerate(lines):
            if "large" in line:
                large_line_idx = i
            elif "medium" in line:
                medium_line_idx = i
            elif "small" in line:
                small_line_idx = i

        # Verify ordering: large should appear before medium before small
        if all(idx is not None for idx in [large_line_idx, medium_line_idx, small_line_idx]):
            assert large_line_idx < medium_line_idx < small_line_idx
