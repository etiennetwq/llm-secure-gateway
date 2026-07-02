import argparse
import csv
import sqlite3
from pathlib import Path


DEFAULT_DATABASE_PATH = "secure_gateway.db"
DEFAULT_EXPORT_DIR = "exports"

TABLE_EXPORTS = {
    "chat_logs": "chat_logs.csv",
    "security_alerts": "security_alerts.csv"
}


def table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    """
    Check whether a table exists in the SQLite database.

    Args:
        cursor: SQLite cursor.
        table_name: Name of the table to check.

    Returns:
        True if the table exists, otherwise False.
    """

    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = ?
        """,
        (table_name,)
    )

    return cursor.fetchone() is not None


def export_table_to_csv(
    connection: sqlite3.Connection,
    table_name: str,
    output_path: Path
) -> int:
    """
    Export a SQLite table to a CSV file.

    Args:
        connection: SQLite database connection.
        table_name: Name of the table to export.
        output_path: Output CSV file path.

    Returns:
        Number of exported rows.
    """

    cursor = connection.cursor()

    if not table_exists(cursor, table_name):
        print(f"⚠️  Skipped: table '{table_name}' does not exist.")
        return 0

    # Table names are controlled by TABLE_EXPORTS, not user input.
    cursor.execute(f"SELECT * FROM {table_name} ORDER BY id ASC")

    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        mode="w",
        encoding="utf-8",
        newline=""
    ) as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(column_names)

        for row in rows:
            writer.writerow([row[column] for column in column_names])

    print(f"✅ Exported {len(rows)} rows from '{table_name}' to {output_path}")

    return len(rows)


def export_logs(
    database_path: Path,
    export_dir: Path
) -> dict[str, int]:
    """
    Export audit log tables from SQLite to CSV files.

    Args:
        database_path: Path to the SQLite database.
        export_dir: Directory where CSV files will be written.

    Returns:
        Dictionary mapping table names to exported row counts.
    """

    if not database_path.exists():
        print(f"❌ Database file not found: {database_path}")
        print("Run 'python init_db.py' first, then generate some logs before exporting.")
        return {}

    export_dir.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    export_results: dict[str, int] = {}

    try:
        for table_name, csv_filename in TABLE_EXPORTS.items():
            output_path = export_dir / csv_filename

            exported_count = export_table_to_csv(
                connection=connection,
                table_name=table_name,
                output_path=output_path
            )

            export_results[table_name] = exported_count

    finally:
        connection.close()

    return export_results


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description="Export SQLite audit logs to CSV files."
    )

    parser.add_argument(
        "--db",
        default=DEFAULT_DATABASE_PATH,
        help="Path to the SQLite database file. Default: secure_gateway.db"
    )

    parser.add_argument(
        "--output-dir",
        default=DEFAULT_EXPORT_DIR,
        help="Directory for exported CSV files. Default: exports"
    )

    return parser.parse_args()


def main() -> None:
    """
    Main entry point for the export script.
    """

    args = parse_arguments()

    database_path = Path(args.db)
    export_dir = Path(args.output_dir)

    print("Starting SQLite log export...")
    print(f"Database: {database_path}")
    print(f"Export directory: {export_dir}")

    results = export_logs(
        database_path=database_path,
        export_dir=export_dir
    )

    if not results:
        print("No logs were exported.")
        return

    print("\nExport summary:")

    for table_name, exported_count in results.items():
        print(f"- {table_name}: {exported_count} rows")

    print("\nExport completed.")


if __name__ == "__main__":
    main()
    