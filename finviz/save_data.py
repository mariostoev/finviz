import csv


def export_to_csv(headers, data, directory):

    with open(directory + '/screener_results.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, headers)
        dict_writer.writeheader()

        for n in data:
            dict_writer.writerows(n)
