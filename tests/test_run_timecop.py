import pytest
import os
from collections import namedtuple
from p4_timecop.kernel.run_timecop import (
    get_open_files_dict,
    perform_reverts,
    check_open_files,
    gather_ignored_users,
    apply_filetype_filter,
    main,
)

import datetime

args_tuple = namedtuple('ArgsTuple', ['config', 'timelimit', 'data', 'log'])

class MockP4(object):
    def __init__(
        self,
    ):
        self.run_called = False
        self.run_return_value = None
        self.fetch_group_called = False
        self.fetch_group_return_value = None

    def run(self, *args):
        self.run_called = True
        return self.run_return_value
    
    def fetch_group(self, *args):
        self.fetch_group_called = True
        return self.fetch_group_return_value

class MockArgumentParser(object):
    def __init__(self, args_dict=None):
        self.args_dict = args_dict or {}

    def add_argument(
        self, short_name, long_name, default=None, nargs=None, action=None
    ):
        pass

    def parse_args(self):
        return self.args_dict

    def set_args(self, args_dict=None):
        self.args_dict = args_dict or {}

class mydatetime(datetime.datetime):
    @classmethod
    def now(cls):
        return datetime.datetime.strptime("Tue Feb 20 19:18:25 2024", "%a %b %d %H:%M:%S %Y")


def test_get_open_files_dict(mocker):
    existing_date = datetime.datetime.strptime("Tue Feb 20 19:18:25 2024", "%a %b %d %H:%M:%S %Y")
    mock_get_file_datetime = mocker.patch('p4_timecop.kernel.run_timecop.get_file_datetime', return_value=existing_date)
    server = MockP4()
    server.run_return_value = [
        {
            'depotFile': '//a/newly/openedfile/path.txt', 
            'type': 'binary', 
            'client': "client", 
            'user': 'rmaffesoli'
        },
        {
            'depotFile': '//an/existing/file/path.txt', 
            'type': 'binary', 
            'client': "client", 
            'user': 'rmaffesoli'
        },
    ]

    existing_data = {
        '//an/existing/file/path.txt': [
            {
                'type': 'binary', 
                'client': "client", 
                'user': 'rmaffesoli',
                'timestamp': "Tue Feb 20 19:18:25 2024"
            }
        ]

    }
    
    expected_result = {
        '//an/existing/file/path.txt': [
            {
                'type': 'binary', 
                'client': "client", 
                'user': 'rmaffesoli',
                'timestamp': existing_date
            },
        ],
        '//a/newly/openedfile/path.txt': [
            {
                'type': 'binary', 
                'client': "client", 
                'user': 'rmaffesoli',
                'timestamp': existing_date
            },
        ]
    }

    datetime_calls = [
        mocker.call('//a/newly/openedfile/path.txt', 'client', 'rmaffesoli', existing_data),
        mocker.call('//an/existing/file/path.txt', 'client', 'rmaffesoli', existing_data)
    ]

    result = get_open_files_dict(server, existing_data=existing_data)
    print(result)

    mock_get_file_datetime.assert_has_calls(datetime_calls)
    assert result == expected_result
    assert server.run_called == True


def test_check_open_files():
    time_limit = datetime.datetime.strptime("Tue Feb 20 19:18:25 2024", "%a %b %d %H:%M:%S %Y")

    open_files = {
        '/a/file/path/to/be/unlocked': [
            {
                'user': 'user',
                'timestamp': datetime.datetime.strptime("Sun Feb 18 19:18:25 2024", "%a %b %d %H:%M:%S %Y")
            },
        ],
        '/a/file/path/to/be/ignored': [
            {
                'user': 'user',
                'timestamp': datetime.datetime.strptime("Wed Feb 21 19:18:25 2024", "%a %b %d %H:%M:%S %Y")
            },
        ],
        '/a/file/path/to/be/ignored2': [
            {
                'user': 'ignore',
                'timestamp': datetime.datetime.strptime("Wed Feb 21 19:18:25 2024", "%a %b %d %H:%M:%S %Y")
            },
        ]
    }
        
    expected_results = {
        '/a/file/path/to/be/unlocked':
        [
            {
                'user': 'user',
                'timestamp': datetime.datetime.strptime("Sun Feb 18 19:18:25 2024", "%a %b %d %H:%M:%S %Y")
            },
        ]
    }

    results = check_open_files(open_files, time_limit, ['ignore'])

    assert results == expected_results


def test_perform_reverts():
    server = MockP4()
    server.run_return_value = 'yup'
    expected_results = ['yup']
    data_dict = {'/a/fake/file/path.txt': [{'client': 'client'}]}
    
    results = perform_reverts(server, data_dict)
    assert results == expected_results
    assert server.run_called == True


def test_gather_ignored_users():
    server = MockP4()
    server.fetch_group_return_value = {'Users': {'group_member'}}
    config = {
        'ignored_usernames': ['single_user'],
        'ignored_groupnames': ['group_name']
    }
    expected_results = {'single_user', 'group_member'}
    results = gather_ignored_users(server, config)
    
    assert results == expected_results
    assert server.fetch_group_called


def test_apply_filetype_filter():
    existing_date = datetime.datetime.strptime("Tue Feb 20 19:18:25 2024", "%a %b %d %H:%M:%S %Y")
    to_be_unlocked = {
        '//an/existing/file/to_be_unlocked_binary.txt': [
            {
                'type': 'binary+l', 
                'client': "client", 
                'user': 'rmaffesoli',
                'timestamp': existing_date
            },
        ],
        '//a/newly/openedfile/to_be_filtered_binary.txt': [
            {
                'type': 'binary', 
                'client': "client", 
                'user': 'rmaffesoli',
                'timestamp': existing_date
            },
        ],
        '//a/newly/openedfile/to_be_filtered_text.txt': [
            {
                'type': 'text', 
                'client': "client", 
                'user': 'rmaffesoli',
                'timestamp': existing_date
            },
        ],
        '//a/newly/openedfile/to_be_unlocked_text.txt': [
            {
                'type': 'text+l', 
                'client': "client", 
                'user': 'rmaffesoli',
                'timestamp': existing_date
            },
        ]
    }
    pattern = "\\+[^l]*l"

    expected_results = {
        '//a/newly/openedfile/to_be_unlocked_text.txt': [
            {
                'client': 'client', 
                'timestamp': datetime.datetime(2024, 2, 20, 19, 18, 25), 
                'type': 'text+l', 
                'user': 'rmaffesoli'
            }
        ], 
        '//an/existing/file/to_be_unlocked_binary.txt': [
            {
                'client': 'client', 
                'timestamp': datetime.datetime(2024, 2, 20, 19, 18, 25), 
                'type': 'binary+l', 
                'user': 'rmaffesoli'
            }
        ]
    }

    results = apply_filetype_filter(to_be_unlocked, pattern)
    assert results == expected_results


def test_main(mocker):

    given_args = args_tuple("a/config/path.json", "1:00:00:00", 'a/data/path.json', 'a/log/path/log.txt')
    existing_date = datetime.datetime.strptime("Tue Feb 20 19:18:25 2024", "%a %b %d %H:%M:%S %Y")
    m_ArgumentParser_parse = mocker.patch('p4_timecop.kernel.run_timecop.ArgumentParser', return_value=MockArgumentParser(given_args))
    m_os_chdir = mocker.patch('p4_timecop.kernel.run_timecop.os.chdir')

    m_load_server_config = mocker.patch(
        'p4_timecop.kernel.run_timecop.load_server_config', 
        return_value={
            "servers": {
                "local": {
                    "server":{
                        "port": "ssl:helix:1666",
                        "user": "rmaffesoli",
                        "password": None,
                        "charset": "none"
                    },
                    "file_lock_time_limit": "01:00:00:00",
                    "log_filepath": "../log.txt",
                    "data_filepath": "../data.json",
                    "filetype_filter": "\\+[^l]*l"
                }
            }
        }
    )

    m_calc_limit = mocker.patch(
        'p4_timecop.kernel.run_timecop.calc_limit', 
        return_value=existing_date
    )

    m_read_json = mocker.patch(
        'p4_timecop.kernel.run_timecop.read_json', 
        return_value= {  
            '//an/existing/file/path.txt': [
                {
                    'type': 'binary+l', 
                    'client': "client", 
                    'user': 'rmaffesoli',
                    'timestamp': "Tue Feb 20 19:18:25 2024",
                },
            ],
            '/a/file/path/to/be/unlocked': # return value stored in old data format style to test upgrade functionality
                {
                    'type': 'binary+l', 
                    'client': 'client', 
                    'user': 'rmaffesoli', 
                    'timestamp': "Tue Feb 20 19:18:25 2024"
                }
            
        }
    )

    m_setup_server_connection = mocker.patch('p4_timecop.kernel.run_timecop.setup_server_connection', return_value=MockP4())
    m_get_open_files_dict = mocker.patch(
        'p4_timecop.kernel.run_timecop.get_open_files_dict', 
        return_value={
            '//an/existing/file/path.txt': [
                {
                    'type': 'binary+l', 
                    'client': "client", 
                    'user': 'rmaffesoli',
                    'timestamp': existing_date
                },
            ],
            '//a/newly/openedfile/path.txt': [
                {
                    'type': 'binary+l', 
                    'client': "client", 
                    'user': 'rmaffesoli',
                    'timestamp': existing_date
                },
            ],
            '/a/file/path/to/be/unlocked': [
                {
                    'type': 'binary+l', 
                    'client': 'client', 
                    'user': 'rmaffesoli', 
                    'timestamp': existing_date
                },
            ],
            '/a/file/path/to/be/ignored': [
                {
                    'type': 'binary', 
                    'client': 'client', 
                    'user': 'rmaffesoli', 
                    'timestamp': existing_date
                },
            ]
        }
    )
    m_check_open_files = mocker.patch(
        'p4_timecop.kernel.run_timecop.check_open_files', 
        return_value={
            '/a/file/path/to/be/unlocked': [
                {
                    'type': 'binary+l', 
                    'client': "client", 
                    'user': 'rmaffesoli',
                    'timestamp': existing_date
                }
            ]
        }
    )
    m_perform_reverts = mocker.patch('p4_timecop.kernel.run_timecop.perform_reverts')
    mocker.patch('p4_timecop.kernel.run_timecop.datetime', mydatetime)
    m_write_log = mocker.patch('p4_timecop.kernel.run_timecop.write_log')
    m_write_json = mocker.patch('p4_timecop.kernel.run_timecop.write_json')

    log_calls = [
        mocker.call(['Tue Feb 20 19:18:25 2024: /a/file/path/to/be/unlocked has been force reverted from rmaffesoli@client.\n'], 'a/log/path/log.txt'),
        mocker.call(['Tue Feb 20 19:18:25 2024: Auto Unlock Completed.\n'], 'a/log/path/log.txt')
    ]

    main()


    m_ArgumentParser_parse.assert_called_once()
    m_os_chdir.assert_called_once()
    m_load_server_config.assert_called_once_with('a/config/path.json')
    m_calc_limit.assert_called_once_with('1:00:00:00')
    m_read_json.assert_called_once_with('a/data/path.json')
    m_setup_server_connection.assert_called_once_with(port='ssl:helix:1666', user='rmaffesoli', password=None, charset='none')
    m_get_open_files_dict.assert_called_once_with(
        m_setup_server_connection.return_value, 
        {
            '//an/existing/file/path.txt': [{
                'type': 'binary+l', 
                'client': 'client', 
                'user': 'rmaffesoli', 
                'timestamp': 'Tue Feb 20 19:18:25 2024', 
            }],
            '/a/file/path/to/be/unlocked': [{
                'type': 'binary+l', 
                'client': 'client', 
                'user': 'rmaffesoli', 
                'timestamp': 'Tue Feb 20 19:18:25 2024'
            }]
        },
    )
    
    m_check_open_files.assert_called_once_with(
        m_get_open_files_dict.return_value, 
        existing_date,
        set()
    )

    m_perform_reverts.assert_called_once_with(
        m_setup_server_connection.return_value,
        {
            '/a/file/path/to/be/unlocked': [
                {
                    'type': 'binary+l', 
                    'client': 'client', 
                    'user': 'rmaffesoli', 
                    'timestamp': existing_date
                }
            ]
        }
    )

    m_write_log.assert_has_calls(log_calls)

    m_write_json.assert_called_once_with(
        {
            '//an/existing/file/path.txt': [
                {
                    'type': 'binary+l', 
                    'client': 'client', 
                    'user': 'rmaffesoli', 
                    'timestamp': existing_date
                }, 
            ],
            '//a/newly/openedfile/path.txt': [
                {
                    'type': 'binary+l', 
                    'client': 'client', 
                    'user': 'rmaffesoli', 
                    'timestamp': existing_date
                }
            ],
            '/a/file/path/to/be/ignored': [
                {
                    'type': 'binary', 
                    'client': 'client', 
                    'user': 'rmaffesoli', 
                    'timestamp': existing_date
                },
            ]
        }, 
        'a/data/path.json'
    )