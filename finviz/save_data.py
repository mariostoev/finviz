import csv
import os
import sqlite3
import re

def create_connection():
    sqlite_file = "../screener.sqlite"
    try:
        conn = sqlite3.connect(sqlite_file)
        return conn
    except:
        print("Error connecting to DB")
        return None

def export_to_csv(headers, data, directory):

    with open(directory + '/screener_results.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, headers)
        dict_writer.writeheader()

        for n in data:
            dict_writer.writerows(n)

def export_to_db(headers, data):
    field_list = ""
    table_name = "screener_results"  # name of the table to be created
    conn = create_connection()
    c = conn.cursor()

    for field in headers:
        field_cleaned = re.sub(r'[^\w\s]','',field)
        field_cleaned = field_cleaned.replace(" ", "")
        field_list +=  field_cleaned + " TEXT, "
    # Creating a new SQLite if it does not exist

    c.execute("CREATE TABLE IF NOT EXISTS {tn} ({fl})"\
    .format(tn=table_name, fl=field_list[:-2]))

    for data in data:
        insert_lines = ""
        for level in data:
            insert_line = "("
            for field, value in level.items():
                insert_line += "\"" +  value + "\", "
            insert_lines += insert_line[:-2]+")" + ","
        insert_lines += insert_lines [:-1]

    try:
        c.execute("INSERT INTO {tn} VALUES {iv}".\
        format(tn=table_name, iv=insert_lines))
    except:
        print("ERROR: INSERT FAILED")

    conn.commit()
    conn.close()

def select_from_db():
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM screener_results")

    rows = c.fetchall()

    for row in rows:
        print(row)
