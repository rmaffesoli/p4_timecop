import pytest

from p4_timecop.kernel.utils import (
    load_server_config,
    setup_server_connection,
    set_default,
    write_json,
    read_json,
    write_log,
    get_file_datetime,
    calc_limit
)

import datetime

class MockP4(object):
    def __init__(
        self,
    ):
        self.charset = None
        self.password = None
        self.user = None
        self.port = None
        self.connect_called = False
        self.run_login_called = False

    def connect(self):
        self.connect_called = True

    def run_login(self):
        self.run_login_called = True


class mydatetime(datetime.datetime):
    @classmethod
    def now(cls):
        return datetime.datetime.strptime("Tue Feb 20 19:18:25 2024", "%a %b %d %H:%M:%S %Y")
    

def test_load_server_config(mocker):
    m_read_json = mocker.patch("p4_timecop.kernel.utils.read_json")

    load_server_config("a/fake/config/path.json")

    m_read_json.assert_called_once_with("a/fake/config/path.json")


@pytest.mark.parametrize(
    "port,user,password,charset,connect_called,run_login_called",
    [
        ("port", "user", "password", "charset", True, True),
        ("port", "user", None, "charset", True, False),
        (None, "user", "password", "charset", False, False),
        ("port", None, "password", "charset", False, False),
    ],
)
def test_setup_server_connection(
    mocker, port, user, password, charset, connect_called, run_login_called
):
    mocker.patch("p4_timecop.kernel.utils.P4", return_value=MockP4())
    p4_connection = setup_server_connection(port, user, password, charset)

    if not connect_called and not run_login_called:
        assert p4_connection == None
    else:
        assert p4_connection.port == port
        assert p4_connection.user == user
        assert p4_connection.password == password
        assert p4_connection.charset == charset
        assert p4_connection.connect_called == connect_called
        assert p4_connection.run_login_called == run_login_called


def test_set_default():
    expected_date = "Tue Feb 20 19:18:25 2024"
    test_set = {1, 2, 3}
    test_list = [1, 2, 3]
    test_date = datetime.datetime.strptime(expected_date, "%a %b %d %H:%M:%S %Y")
    
    set_result = set_default(test_set)
    list_result = set_default(test_list)
    date_result = set_default(test_date)

    assert isinstance(set_result, list)
    assert isinstance(list_result, list)
    assert isinstance(date_result, str)
    assert set_result == test_list
    assert list_result == test_list
    assert date_result == expected_date


def test_write_json(mocker):
    m_open = mocker.patch(
        "p4_timecop.kernel.utils.open", mocker.mock_open(read_data="{'fake':'data'}")
    )
    m_json_dump = mocker.patch("p4_timecop.kernel.utils.json.dump")

    write_json({"fake": "data"}, "/a/fake/output/path.json")

    m_open.assert_called_once_with("/a/fake/output/path.json", "w")
    m_json_dump.assert_called_once_with(
        {"fake": "data"},
        m_open.return_value,
        default=set_default,
        indent=4,
        sort_keys=False,
    )


def test_read_json(mocker):
    m_open = mocker.patch(
        "p4_timecop.kernel.utils.open", mocker.mock_open(read_data="{'fake':'data'}")
    )
    m_json_load = mocker.patch("p4_timecop.kernel.utils.json.load", return_value= {'fake':'data'})

    read_json("/a/fake/output/path.json")

    m_open.assert_called_once_with("/a/fake/output/path.json")
    m_json_load.assert_called_once_with(m_open.return_value)

def test_write_log(mocker):
    m_open = mocker.patch(
        "p4_timecop.kernel.utils.open", mocker.mock_open(read_data="{'fake':'data'}")
    )

    write_log(lines=['test', 'lines'], file_path='/a/fake/file/path.json')

    open_calls = [
        mocker.call('/a/fake/file/path.json', 'a'),
        mocker.call().__enter__(),
        mocker.call().writelines(['test', 'lines']),
        mocker.call().__exit__(None, None, None)
    ]

    m_open.assert_has_calls(open_calls)

@pytest.mark.parametrize(
    "file_path,expected_result",
    [
        ('//a/fake/depot/file/path1.json', "Tue Feb 20 19:18:25 2024"),
        ('//a/fake/depot/file/path2.json', "Sun Feb 18 19:00:00 2024"),
    ],
)
def test_file_datetime(mocker, file_path, expected_result):
    mocker.patch('p4_timecop.kernel.utils.datetime', mydatetime)
    existing_data = {
        '//a/fake/depot/file/path2.json': {
            "type": "binary+Fl",
            "client": "local_lib",
            "user": "rmaffesoli",
            "timestamp": "Sun Feb 18 19:00:00 2024"
        }
    }
    
    result = get_file_datetime(file_path, existing_data)
    assert isinstance(result, datetime.datetime)
    assert result.strftime("%a %b %d %H:%M:%S %Y") == expected_result


def test_calc_limit(mocker):
    mocker.patch('p4_timecop.kernel.utils.datetime', mydatetime)
    expected_result = 'Mon Feb 19 19:18:25 2024'
    result = calc_limit("1:00:00:00")

    assert result.strftime('%a %b %d %H:%M:%S %Y') == expected_result