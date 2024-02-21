#!/usr/bin/env python

"""process_template doc string"""

from __future__ import print_function

from argparse import ArgumentParser
import os
from datetime import datetime

from p4_timecop.kernel.utils import (
    write_json,
    read_json,
    load_server_config,
    setup_server_connection,
    get_file_datetime,
    calc_limit,
    write_log
)

def get_open_files_dict(server, existing_data=None):
    """get_open_files doc string"""

    existing_data = existing_data or {}
    data_dict = {}
    opened_files = server.run('opened', '-a')

    for open_file in opened_files:
        depot_path = open_file['depotFile']
        file_type = open_file['type']
        client = open_file['client']
        user = open_file['user']
        timestamp = get_file_datetime(depot_path, existing_data)

        if depot_path not in data_dict:
            data_dict[depot_path] = {
                'type': file_type,
                'client': client,
                'user': user,
                'timestamp': timestamp
            }

    return data_dict

def record_open_file_data(file_data, output_path):
    write_json(file_data, output_path)

def perform_reverts(server, data_dict):
    results = []
    for file_path in data_dict:    
        result = server.run('revert', '-C', data_dict[file_path]['client'], file_path)
        results.append(result)
    return results

def check_open_files(open_files, time_limit):
    to_do = {}
    for file_path in open_files:
        if open_files[file_path]['timestamp'] <= time_limit:
            to_do[file_path] = open_files[file_path]
    return to_do

def main():
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", default="../config.json")
    parser.add_argument("-t", "--timelimit", default="01:00:00:00")
    parser.add_argument("-d", "--data", default="../data.json")
    parser.add_argument("-l", "--log", default="../log.txt")
    
    parsed_args = parser.parse_args()

    script_dir = os.path.dirname(__file__)
    os.chdir(script_dir)

    print("Connecting to server:")
    p4_connection = setup_server_connection(
        **load_server_config(parsed_args.config)
    )

    existing_data = read_json(parsed_args.data)

    open_files = get_open_files_dict(p4_connection, existing_data)
    
    time_limit = calc_limit(parsed_args.timelimit)

    to_be_unlocked = check_open_files(open_files, time_limit)
    
    results = perform_reverts(p4_connection, to_be_unlocked)
    
    print(results)
    

    log_lines = []
    for file_path in to_be_unlocked:
        line = '{time}: {file_path} has been force reverted from {user}@{client}.\n'.format(
            time=datetime.now().strftime("%a %b %d %H:%M:%S %Y"), 
            file_path=file_path,
            user=to_be_unlocked[file_path]['user'], 
            client=to_be_unlocked[file_path]['client']
        )

        log_lines.append(line)
        if file_path in open_files:
            del open_files[file_path]

    write_log(log_lines, parsed_args.log)

    record_open_file_data(open_files, parsed_args.data)
    line = '{time}: Auto Unlock Completed.\n'.format(
            time=datetime.now().strftime("%a %b %d %H:%M:%S %Y"))
    write_log([line], parsed_args.log)

if __name__ == "__main__":
    main()