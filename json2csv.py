#!/usr/bin/env python3
import json
import csv
import sys
import os
from pathlib import Path

# Function to check if the file is a JSON file
def is_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            json.load(file)
        return True
    except (ValueError, json.JSONDecodeError):
        return False

# Function to convert JSON data to CSV and save it to the output file
def json2csv(json_file_path, csv_file_path):
    # Load JSON data from the input file
    with open(json_file_path) as data:
        data = json.load(data)

    # Write JSON data to the output CSV file
    with open(csv_file_path, 'w') as file:
        csv_writer = csv.writer(file)
        count = 0
        for d in data:
            if count == 0:
                # Write header (keys of the JSON object) to the CSV file
                header = d.keys()
                csv_writer.writerow(header)
                count += 1

            # Write values of the JSON object to the CSV file
            csv_writer.writerow(d.values())

# Check if the correct number of arguments is provided
if len(sys.argv) != 3:
    print("ERROR: Need 2 arguments")
    print("Usage: ./json2csv.py <input json file> <output csv filename>")
    sys.exit()

# Normalize and validate the input JSON file path
json_file_path = sys.argv[1]
normalized_json_path = os.path.normpath(json_file_path)
base_json_path = Path(normalized_json_path).resolve(strict=True)

# Check if the input JSON file is valid and exists
if not (base_json_path.is_file() and not base_json_path.is_symlink() and is_json_file(normalized_json_path)):
    print("ERROR: The input file is not a valid JSON file or the file does not exist.")
    sys.exit()

# Normalize the output CSV file path
csv_file_path = sys.argv[2]
normalized_csv_path = os.path.normpath(csv_file_path)
base_csv_path = Path(normalized_csv_path).resolve(strict=False)

# Check if the output CSV file path is not a symlink
if base_csv_path.is_symlink():
    print("ERROR: The output file path is a symlink.")
    sys.exit()

# Call the json2csv function to convert JSON data to CSV
json2csv(normalized_json_path, normalized_csv_path)