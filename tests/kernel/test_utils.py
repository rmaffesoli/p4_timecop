import pytest

from p4_timecop.kernel.utils import (
    load_server_config,
    setup_server_connection,
    set_default,
    write_json,
    read_json,
    gather_parameters,
    substitute_parameters,
    convert_to_string,
    gather_existing_template_names,
)


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


def test_load_server_config(mocker):
    m_read_json = mocker.patch("p4_templates.kernel.utils.read_json")

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
    mocker.patch("p4_templates.kernel.utils.P4", return_value=MockP4())
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
    test_set = {1, 2, 3}
    test_list = [1, 2, 3]

    set_result = set_default(test_set)
    list_result = set_default(test_list)

    assert isinstance(set_result, list)
    assert isinstance(list_result, list)
    assert set_result == test_list
    assert list_result == test_list


def test_write_json(mocker):
    m_open = mocker.patch(
        "p4_templates.kernel.utils.open", mocker.mock_open(read_data="{'fake':'data'}")
    )
    m_json_dump = mocker.patch("p4_templates.kernel.utils.json.dump")

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
        "p4_templates.kernel.utils.open", mocker.mock_open(read_data="{'fake':'data'}")
    )
    m_json_load = mocker.patch("p4_templates.kernel.utils.json.load", return_value= {'fake':'data'})

    read_json("/a/fake/output/path.json")

    m_open.assert_called_once_with("/a/fake/output/path.json")
    m_json_load.assert_called_once_with(m_open.return_value)
