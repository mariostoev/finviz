import csv
import sqlite3
import re


def create_connection():
    """ Creates a database connection. """

    sqlite_file = "../screener.sqlite"

    try:
        conn = sqlite3.connect(sqlite_file)
        return conn
    except sqlite3.Error as error:
        raise ("An error has occurred while connecting to the database: ", error.args[0])


def export_to_csv(headers, data):
    """ Exports the generated table into a CSV file, located in the user's current directory. """

    with open('screener_results.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, headers)
        dict_writer.writeheader()
        dict_writer.writerows(data)


def export_to_db(headers, data):
    """ Exports the generated table into a SQLite database, located in the user's current directory. """

    field_list = ""
    table_name = "screener_results"  # name of the table to be created
    conn = create_connection()
    c = conn.cursor()

    for field in headers:

        field_cleaned = re.sub(r'[^\w\s]', '', field)
        field_cleaned = field_cleaned.replace(" ", "")
        field_list += field_cleaned + " TEXT, "

    c.execute("CREATE TABLE IF NOT EXISTS {tn} ({fl})"
              .format(tn=table_name, fl=field_list[:-2]))

    inserts = ""
    for row in data:

        insert_fields = "("
        for field, value in row.items():

            insert_fields += "\"" + value + "\", "

        inserts += insert_fields[:-2] + "), "

    insert_lines = inserts[:-2]

    try:
        c.execute("INSERT INTO {tn} VALUES {iv}".
                  format(tn=table_name, iv=insert_lines))
    except sqlite3.Error as error:
        print("An error has occurred", error.args[0])

    conn.commit()
    conn.close()
