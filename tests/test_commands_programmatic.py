"""Tests for programmatic command variants (GUI/scripting support)"""

import time

import pytest
from unittest.mock import MagicMock, patch, mock_open
import yaml


class TestServerCommandsProgrammatic:
    """Test programmatic server management methods"""

    @pytest.fixture
    def mock_shell(self):
        """Create mock shell"""
        shell = MagicMock()
        shell.config = MagicMock()
        shell.config.config_path = "/tmp/test_config.yml"
        shell.config.get_all_servers.return_value = {}
        shell.poutput = MagicMock()
        shell.perror = MagicMock()
        shell.pwarning = MagicMock()
        return shell

    @pytest.fixture
    def server_commands(self, mock_shell):
        """Create ServerCommands instance"""
        from quads_client.commands.server import ServerCommands

        return ServerCommands(mock_shell)

    def test_add_server_programmatic_success(self, server_commands, mock_shell):
        """Test adding server programmatically succeeds"""
        # Mock config file operations
        mock_config_data = {"servers": {}}

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config_data))):
            with patch("yaml.safe_load", return_value=mock_config_data):
                with patch("yaml.dump"):
                    with patch("requests.get") as mock_get:
                        # Mock successful server connection
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {"version": "2.2.6"}
                        mock_get.return_value = mock_response

                        success, message, version = server_commands.add_server_programmatic(
                            name="test-server",
                            url="https://test.example.com",
                            username="test@example.com",
                            password="testpass",
                            verify=True,
                            test_connection=True,
                        )

                        assert success is True
                        assert "successfully" in message.lower()
                        assert version == "2.2.6"

    def test_add_server_programmatic_connection_failure(self, server_commands):
        """Test adding server with connection failure"""
        with patch("builtins.open", mock_open(read_data=yaml.dump({"servers": {}}))):
            with patch("yaml.safe_load", return_value={"servers": {}}):
                with patch("requests.get") as mock_get:
                    # Mock connection failure
                    mock_get.side_effect = Exception("Connection timeout")

                    success, message, version = server_commands.add_server_programmatic(
                        name="test-server",
                        url="https://test.example.com",
                        username="",
                        password="",
                        verify=True,
                        test_connection=True,
                    )

                    assert success is False
                    assert "Could not connect" in message
                    assert version is None

    def test_add_server_programmatic_skip_connection_test(self, server_commands):
        """Test adding server without connection test"""
        mock_config_data = {"servers": {}}

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config_data))):
            with patch("yaml.safe_load", return_value=mock_config_data):
                with patch("yaml.dump"):
                    success, message, version = server_commands.add_server_programmatic(
                        name="test-server",
                        url="https://test.example.com",
                        username="",
                        password="",
                        verify=True,
                        test_connection=False,
                    )

                    assert success is True
                    assert version is None  # No connection test = no version

    def test_add_server_programmatic_duplicate(self, server_commands):
        """Test adding duplicate server"""
        mock_config_data = {
            "servers": {"test-server": {"url": "https://existing.example.com", "username": "", "password": ""}}
        }

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config_data))):
            with patch("yaml.safe_load", return_value=mock_config_data):
                success, message, version = server_commands.add_server_programmatic(
                    name="test-server",
                    url="https://test.example.com",
                    username="",
                    password="",
                    verify=True,
                    test_connection=False,
                )

                assert success is False
                assert "already exists" in message.lower()

    def test_rm_server_programmatic_success(self, server_commands, mock_shell):
        """Test removing server programmatically succeeds"""
        mock_config_data = {
            "servers": {"test-server": {"url": "https://test.example.com", "username": "", "password": ""}},
            "default_server": "other-server",
        }
        mock_shell.connection = None

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config_data))):
            with patch("yaml.safe_load", return_value=mock_config_data):
                with patch("yaml.dump"):
                    success, message = server_commands.rm_server_programmatic("test-server")

                    assert success is True
                    assert "removed successfully" in message.lower()

    def test_rm_server_programmatic_not_found(self, server_commands, mock_shell):
        """Test removing non-existent server"""
        mock_config_data = {"servers": {}}
        mock_shell.connection = None

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config_data))):
            with patch("yaml.safe_load", return_value=mock_config_data):
                success, message = server_commands.rm_server_programmatic("nonexistent")

                assert success is False
                assert "not found" in message.lower()

    def test_rm_server_programmatic_currently_connected(self, server_commands, mock_shell):
        """Test removing currently connected server is prevented"""
        mock_shell.connection = MagicMock()
        mock_shell.connection.current_server = "test-server"

        success, message = server_commands.rm_server_programmatic("test-server")

        assert success is False
        assert "currently connected" in message.lower()

    def test_rm_server_programmatic_clears_default(self, server_commands, mock_shell):
        """Test removing default server clears default_server"""
        mock_config_data = {
            "servers": {"test-server": {"url": "https://test.example.com", "username": "", "password": ""}},
            "default_server": "test-server",
        }
        mock_shell.connection = None

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config_data))):
            with patch("yaml.safe_load", return_value=mock_config_data):
                with patch("yaml.dump"):
                    success, message = server_commands.rm_server_programmatic("test-server")

                    assert success is True
                    assert mock_config_data["default_server"] is None
                    assert "test-server" not in mock_config_data["servers"]

    def test_rm_server_programmatic_no_config(self, server_commands, mock_shell):
        """Test removing server when config not loaded"""
        mock_shell.config = None

        success, message = server_commands.rm_server_programmatic("test-server")

        assert success is False
        assert "configuration not loaded" in message.lower()


class TestUserCommandsProgrammatic:
    """Test programmatic user command methods"""

    @pytest.fixture
    def mock_shell(self):
        """Create mock shell with connection"""
        shell = MagicMock()
        shell.config = MagicMock()
        shell.config.config_path = "/tmp/test_config.yml"
        shell.config.get_server_url.return_value = "https://test.example.com"
        shell.config.get_server_verify.return_value = True

        # Mock connection
        mock_connection = MagicMock()
        mock_connection.is_connected = True
        mock_connection.is_authenticated = False
        mock_connection.current_server = "test-server"
        mock_connection.api = MagicMock()
        mock_connection._decode_role_from_token = MagicMock(return_value="user")

        shell.connection = mock_connection
        shell.session_manager = MagicMock()
        shell.session_manager.active_connection = mock_connection

        shell.poutput = MagicMock()
        shell.perror = MagicMock()
        shell.pwarning = MagicMock()
        shell._update_visible_commands = MagicMock()

        return shell

    @pytest.fixture
    def user_commands(self, mock_shell):
        """Create UserCommands instance"""
        from quads_client.commands.user import UserCommands

        return UserCommands(mock_shell)

    def test_login_programmatic_success(self, user_commands, mock_shell):
        """Test programmatic login succeeds"""
        with patch("quads_lib.QuadsApi") as mock_api_class:
            # Mock QuadsApi instance
            mock_api = MagicMock()
            mock_api.login.return_value = {"auth_token": "test_token_123", "status": "success"}
            mock_api.token = "test_token_123"
            mock_api_class.return_value = mock_api

            success, message, role = user_commands.login_programmatic(email="test@example.com", password="testpass")

            assert success is True
            assert "successfully" in message.lower()
            # Verify connection was updated
            assert mock_shell.connection._api == mock_api
            assert mock_shell.connection._token == "test_token_123"
            assert mock_shell.connection._username == "test@example.com"
            assert mock_shell.connection._registration_mode is False

    def test_login_programmatic_failure(self, user_commands, mock_shell):
        """Test programmatic login fails"""
        with patch("quads_lib.QuadsApi") as mock_api_class:
            # Mock failed login
            mock_api = MagicMock()
            mock_api.login.side_effect = Exception("Invalid credentials")
            mock_api_class.return_value = mock_api

            success, message, role = user_commands.login_programmatic(email="test@example.com", password="wrongpass")

            assert success is False
            assert "Failed to login" in message
            assert role is None

    def test_login_programmatic_not_connected(self, user_commands, mock_shell):
        """Test programmatic login when not connected"""
        mock_shell.connection = None

        success, message, role = user_commands.login_programmatic(email="test@example.com", password="testpass")

        assert success is False
        assert "Not connected" in message
        assert role is None

    def test_login_programmatic_updates_role(self, user_commands, mock_shell):
        """Test programmatic login updates user role"""
        with patch("quads_lib.QuadsApi") as mock_api_class:
            mock_api = MagicMock()
            mock_api.login.return_value = {"auth_token": "test_token_123", "status": "success"}
            mock_api.token = "test_token_123"
            mock_api_class.return_value = mock_api

            # Mock role detection
            mock_shell.connection._decode_role_from_token.return_value = "admin"

            success, message, role = user_commands.login_programmatic(email="admin@example.com", password="adminpass")

            assert success is True
            assert role == "admin"
            assert mock_shell.connection._user_role == "admin"
            mock_shell._update_visible_commands.assert_called_once()


class TestUserCommandsRegister:
    """Test programmatic user registration methods"""

    @pytest.fixture
    def mock_shell(self):
        """Create mock shell with connection"""
        shell = MagicMock()
        shell.config = MagicMock()
        shell.config.config_path = "/tmp/test_config.yml"
        shell.config.get_server_url.return_value = "https://test.example.com"
        shell.config.get_server_verify.return_value = True

        mock_connection = MagicMock()
        mock_connection.is_connected = True
        mock_connection.is_authenticated = False
        mock_connection.current_server = "test-server"
        mock_connection.api = MagicMock()
        mock_connection._decode_role_from_token = MagicMock(return_value="user")

        shell.connection = mock_connection
        shell.session_manager = MagicMock()
        shell.session_manager.active_connection = mock_connection
        shell.poutput = MagicMock()
        shell.perror = MagicMock()
        shell.pwarning = MagicMock()
        shell._update_visible_commands = MagicMock()

        return shell

    @pytest.fixture
    def user_commands(self, mock_shell):
        """Create UserCommands instance"""
        from quads_client.commands.user import UserCommands

        return UserCommands(mock_shell)

    def test_register_programmatic_success(self, user_commands, mock_shell):
        """Test registration followed by auto-login"""
        mock_shell.connection.api.register.return_value = {"message": "User created"}

        with patch("quads_lib.QuadsApi") as mock_api_class:
            mock_api = MagicMock()
            mock_api.login.return_value = {"auth_token": "new_token", "status": "success"}
            mock_api.token = "new_token"
            mock_api_class.return_value = mock_api

            success, message, role = user_commands.register_programmatic("new@example.com", "password123")

            assert success is True
            assert "successfully" in message.lower()
            mock_shell.connection.api.register.assert_called_once()

    def test_register_programmatic_already_exists(self, user_commands, mock_shell):
        """Test registration when user already exists"""
        mock_shell.connection.api.register.return_value = {"message": "User already exists"}

        success, message, role = user_commands.register_programmatic("existing@example.com", "password123")

        assert success is False
        assert "already registered" in message.lower()
        assert role is None

    def test_register_programmatic_not_connected(self, user_commands, mock_shell):
        """Test registration when not connected"""
        mock_shell.connection = None

        success, message, role = user_commands.register_programmatic("new@example.com", "password123")

        assert success is False
        assert "not connected" in message.lower()
        assert role is None


class TestGuiShellMetadataCache:
    """Test metadata caching in GuiShell"""

    @pytest.fixture
    def gui_shell(self):
        """Create a GuiShell with mocked dependencies"""
        from quads_client.gui.controllers.gui_shell import GuiShell

        mock_app = MagicMock()
        mock_app.theme_manager = MagicMock()

        with patch("quads_client.gui.controllers.gui_shell.QuadsClientConfig"):
            with patch("quads_client.gui.controllers.gui_shell.SessionManager"):
                shell = GuiShell(mock_app)

        mock_connection = MagicMock()
        mock_connection.is_connected = True
        mock_connection.is_authenticated = True
        mock_connection.api = MagicMock()
        shell.session_manager = MagicMock()
        shell.session_manager.active_connection = mock_connection
        return shell

    def test_get_available_models_caches_result(self, gui_shell):
        """Second call returns cached result without re-fetching"""
        gui_shell.connection.api.get_hosts.return_value = [
            {"model": "1029P", "name": "host1"},
            {"model": "6049P", "name": "host2"},
        ]

        result1 = gui_shell.get_available_models()
        result2 = gui_shell.get_available_models()

        assert result1 == ["1029P", "6049P"]
        assert result2 == result1
        assert gui_shell.connection.api.get_hosts.call_count == 1

    def test_get_available_models_cache_expires(self, gui_shell):
        """Cache expires after TTL and re-fetches"""
        gui_shell.connection.api.get_hosts.return_value = [{"model": "1029P", "name": "host1"}]

        gui_shell.get_available_models()
        gui_shell._models_cache_time = time.monotonic() - gui_shell._metadata_cache_ttl - 1
        gui_shell._hosts_cache_time = time.monotonic() - gui_shell._metadata_cache_ttl - 1
        gui_shell.get_available_models()

        assert gui_shell.connection.api.get_hosts.call_count == 2

    def test_invalidate_metadata_cache_clears(self, gui_shell):
        """invalidate_metadata_cache clears all caches"""
        gui_shell.connection.api.get_hosts.return_value = [{"model": "1029P", "name": "host1"}]

        gui_shell.get_available_models()
        gui_shell.get_available_nic_vendors()
        gui_shell.invalidate_metadata_cache()

        assert gui_shell._models_cache is None
        assert gui_shell._nic_vendors_cache is None
        assert gui_shell._hosts_cache is None

        gui_shell.get_available_models()
        assert gui_shell.connection.api.get_hosts.call_count == 2
