from __future__ import print_function

import json
import re
import os
from datetime import datetime, timedelta
from P4 import P4


def load_server_config(config_path="config.json"):
    return read_json(config_path)


def setup_server_connection(port=None, user=None, password=None, charset="none"):
    if not (port and user):
        print("missing needed variable")
        print("port:", port)
        print("user:", user)
        return

    if not password:
        print("passwd:", password)
        print('Password not provided, attempting to use local ticket')

    p4 = P4()

    p4.charset = charset
    if password:
        p4.password = password
    p4.user = user
    p4.port = port

    p4.connect()
    if password:
        p4.run_login()

    return p4


def set_default(obj):
    """
    Converts any set to a list type object.
    """
    if isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, datetime):
        return obj.strftime("%a %b %d %H:%M:%S %Y")
    return obj


def write_json(data_dict, output_path, sort_keys=False):
    """
    Writes a dictionary into a json file.
    """
    with open(output_path, "w") as outfile:
        json.dump(
            data_dict, outfile, default=set_default, indent=4, sort_keys=sort_keys
        )


def read_json(json_path):
    """
    Reads a json file in to a dictionary.
    """
    with open(json_path) as json_file:
        data_dict = json.load(json_file)
    return data_dict


def write_log(lines=None, file_path=''):
    with open(file_path, "a") as outfile:
        outfile.writelines(lines)


def get_file_datetime(file_path, existing_data):
    if file_path in existing_data:
        return datetime.strptime(existing_data[file_path]['timestamp'], "%a %b %d %H:%M:%S %Y")
    else:
        return datetime.now()


def calc_limit(time_limit):
    now = datetime.now()
    days, hours, minutes, seconds = time_limit.split(':')
    delta = timedelta(days=int(days), hours=int(hours), minutes=int(minutes), seconds=(int(seconds)))
    limit = now - delta
    return limit