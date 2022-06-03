#!/usr/bin/env python3
import json, csv, sys

if len(sys.argv) != 3:
    print("ERROR: Need more arguments")
    print("Usage: ./json2csv.py <input json file> <output csv filename>")
    sys.exit()

json_file_path = sys.argv[1]

with open(json_file_path) as data:
    data = json.load(data)

with open('data2.csv','w') as file:
    csv_writer = csv.writer(file)
    count = 0
    for d in data:
        if count == 0:
            header = d.keys()
            csv_writer.writerow(header)
            count += 1
        
        csv_writer.writerow(d.values())
