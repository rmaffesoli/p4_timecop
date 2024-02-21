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
    parser.add_argument("-t", "--timelimit")
    parser.add_argument("-d", "--data")
    parser.add_argument("-l", "--log")
    
    parsed_args = parser.parse_args()

    script_dir = os.path.dirname(__file__)
    os.chdir(script_dir)

    config = load_server_config(parsed_args.config)        

    
    
    log_path  = config.get('log', "../log.txt")    
    if parsed_args.log:
        log_path = parsed_args.log

    data_path  = config.get('data', "../data.json")
    if parsed_args.data:
        data_path = parsed_args.data
    
    limit_str  = config.get('file_lock_time_limit', "01:00:00:00")
    if parsed_args.timelimit:
        limit_str = parsed_args.timelimit
    time_limit = calc_limit(limit_str)

    existing_data = read_json(data_path)

    print("Connecting to server:")
    p4_connection = setup_server_connection(**config['server'])

    open_files = get_open_files_dict(p4_connection, existing_data)
    to_be_unlocked = check_open_files(open_files, time_limit)
    
    perform_reverts(p4_connection, to_be_unlocked)

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

    write_log(log_lines, log_path)

    write_json(open_files, data_path)

    line = '{time}: Auto Unlock Completed.\n'.format(
            time=datetime.now().strftime("%a %b %d %H:%M:%S %Y"))
    write_log([line], log_path)
    print("Auto Unlock Completed.")

if __name__ == "__main__":
    main()