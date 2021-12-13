import csv
import io
import re
import sqlite3


def create_connection(sqlite_file):
    """ Creates a database connection. """

    try:
        conn = sqlite3.connect(sqlite_file)
        return conn
    except sqlite3.Error as error:
        raise (
            "An error has occurred while connecting to the database: ",
            error.args[0],
        )


def __write_csv_to_stream(stream, headers, data):
    """Writes the data in CSV format to a stream."""

    dict_writer = csv.DictWriter(stream, headers)
    dict_writer.writeheader()
    dict_writer.writerows(data)


def export_to_csv(headers, data, filename=None, mode="w", newline=""):
    """Exports the generated table into a CSV file if a file is mentioned.
    Returns the CSV table as a string if no file is mentioned."""

    if filename:
        with open(filename, mode, newline=newline) as output_file:
            __write_csv_to_stream(output_file, headers, data)
        return None
    stream = io.StringIO()
    __write_csv_to_stream(stream, headers, data)
    return stream.getvalue()


def export_to_db(headers, data, filename):
    """ Exports the generated table into a SQLite database into a file."""

    field_list = ""
    table_name = "screener_results"  # name of the table to be created
    conn = create_connection(filename)
    c = conn.cursor()

    for field in headers:
        field_cleaned = re.sub(r"[^\w\s]", "", field)
        field_cleaned = field_cleaned.replace(" ", "")
        field_cleaned = field_cleaned.replace("50DHigh", "High50D")
        field_cleaned = field_cleaned.replace("50DLow", "Low50D")
        field_cleaned = field_cleaned.replace("52WHigh", "High52W")
        field_cleaned = field_cleaned.replace("52WLow", "Low52W")
        field_list += field_cleaned + " TEXT, "

    c.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({field_list[:-2]});")

    inserts = ""
    for row in data:

        insert_fields = "("
        for field, value in row.items():

            insert_fields += '"' + value + '", '

        inserts += insert_fields[:-2] + "), "

    insert_lines = inserts[:-2]

    try:
        c.execute(f"INSERT INTO {table_name} VALUES {insert_lines};")
    except sqlite3.Error as error:
        print("An error has occurred", error.args[0])

    conn.commit()
    conn.close()
