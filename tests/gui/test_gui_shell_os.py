"""Tests for get_available_os logic in gui_shell"""

from unittest.mock import MagicMock


class TestGetAvailableOs:
    """Test get_available_os extracted logic"""

    def _make_shell(self, mock_api):
        shell = MagicMock()
        shell.is_authenticated.return_value = True
        shell.connection.api = mock_api
        return shell

    def _get_available_os(self, shell):
        """Extracted logic from GuiShell.get_available_os()"""
        if not shell.is_authenticated():
            return []

        try:
            os_list = shell.connection.api.get_os_list()
            if not os_list:
                return []
            return [os_item.get("Title", "") for os_item in os_list if os_item.get("Title")]
        except Exception:
            return []

    def test_returns_os_titles(self):
        api = MagicMock()
        api.get_os_list.return_value = [
            {"Id": 1, "Title": "RHEL 9.4", "Release Name": "Plow", "Family": "rhel"},
            {"Id": 2, "Title": "RHEL 8.10", "Release Name": "Ootpa", "Family": "rhel"},
            {"Id": 3, "Title": "CentOS 9", "Release Name": "Stream", "Family": "centos"},
        ]
        shell = self._make_shell(api)

        result = self._get_available_os(shell)

        assert result == ["RHEL 9.4", "RHEL 8.10", "CentOS 9"]

    def test_empty_os_list(self):
        api = MagicMock()
        api.get_os_list.return_value = []
        shell = self._make_shell(api)

        result = self._get_available_os(shell)

        assert result == []

    def test_none_os_list(self):
        api = MagicMock()
        api.get_os_list.return_value = None
        shell = self._make_shell(api)

        result = self._get_available_os(shell)

        assert result == []

    def test_api_error(self):
        api = MagicMock()
        api.get_os_list.side_effect = Exception("Connection error")
        shell = self._make_shell(api)

        result = self._get_available_os(shell)

        assert result == []

    def test_not_authenticated(self):
        api = MagicMock()
        shell = self._make_shell(api)
        shell.is_authenticated.return_value = False

        result = self._get_available_os(shell)

        assert result == []
        api.get_os_list.assert_not_called()

    def test_skips_entries_without_title(self):
        api = MagicMock()
        api.get_os_list.return_value = [
            {"Id": 1, "Title": "RHEL 9.4", "Release Name": "Plow", "Family": "rhel"},
            {"Id": 2, "Release Name": "Unknown", "Family": "other"},
            {"Id": 3, "Title": "", "Release Name": "Empty", "Family": "other"},
        ]
        shell = self._make_shell(api)

        result = self._get_available_os(shell)

        assert result == ["RHEL 9.4"]
