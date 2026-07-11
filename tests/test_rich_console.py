import pytest
from unittest.mock import MagicMock, patch, call
from quads_client.rich_console import RichConsole
from quads_client import __version__


@pytest.fixture
def rich_console():
    """Fixture for RichConsole instance"""
    return RichConsole()


def test_init(rich_console):
    """Test RichConsole initialization"""
    assert rich_console.console is not None
    from rich.console import Console

    assert isinstance(rich_console.console, Console)


def test_print_banner(rich_console):
    """Test print_banner displays version correctly"""
    with patch.object(rich_console.console, "print") as mock_print:
        rich_console.print_banner()

        # Verify print was called once
        assert mock_print.call_count == 1

        # Get the Panel object that was passed
        panel_arg = mock_print.call_args[0][0]

        # Verify the Panel contains the version
        assert __version__ in str(panel_arg.renderable)
        assert "QUADS Client" in str(panel_arg.renderable)
        assert "Interactive TUI Shell" in str(panel_arg.renderable)
        assert "https://quads.dev" in str(panel_arg.renderable)


def test_print_table_with_title(rich_console):
    """Test print_table with title"""
    headers = ["Name", "Model", "Type"]
    rows = [["host01", "r640", "baremetal"], ["host02", "r650", "virtual"]]
    title = "Available Hosts"

    with patch.object(rich_console.console, "print") as mock_print:
        rich_console.print_table(headers, rows, title=title)

        # Verify print was called
        assert mock_print.call_count == 1

        # Get the Table object
        table_arg = mock_print.call_args[0][0]
        from rich.table import Table

        assert isinstance(table_arg, Table)
        assert table_arg.title == title


def test_print_table_without_title(rich_console):
    """Test print_table without title"""
    headers = ["Name", "Value"]
    rows = [["key1", "value1"], ["key2", "value2"]]

    with patch.object(rich_console.console, "print") as mock_print:
        rich_console.print_table(headers, rows)

        assert mock_print.call_count == 1
        table_arg = mock_print.call_args[0][0]
        from rich.table import Table

        assert isinstance(table_arg, Table)
        assert table_arg.title is None


def test_print_table_with_non_string_values(rich_console):
    """Test print_table converts non-string values to strings"""
    headers = ["Name", "Count", "Active"]
    rows = [["host01", 5, True], ["host02", 10, False]]

    with patch.object(rich_console.console, "print") as mock_print:
        rich_console.print_table(headers, rows)

        # Should not raise an error with mixed types
        assert mock_print.call_count == 1


def test_print_success(rich_console):
    """Test print_success formatting"""
    message = "Operation completed successfully"

    with patch.object(rich_console.console, "print") as mock_print:
        rich_console.print_success(message)

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert ">>" in call_args
        assert message in call_args
        assert "[bold green]" in call_args


def test_print_error(rich_console):
    """Test print_error formatting"""
    message = "Something went wrong"

    with patch.object(rich_console.console, "print") as mock_print:
        rich_console.print_error(message)

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "ERROR:" in call_args
        assert message in call_args
        assert "[bold red]" in call_args

        # Check style parameter
        assert mock_print.call_args[1]["style"] == "red"


def test_print_warning(rich_console):
    """Test print_warning formatting"""
    message = "This is a warning"

    with patch.object(rich_console.console, "print") as mock_print:
        rich_console.print_warning(message)

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "WARNING:" in call_args
        assert message in call_args
        assert "[bold yellow]" in call_args

        # Check style parameter
        assert mock_print.call_args[1]["style"] == "yellow"


def test_print_info(rich_console):
    """Test print_info"""
    message = "Informational message"

    with patch.object(rich_console.console, "print") as mock_print:
        rich_console.print_info(message)

        mock_print.assert_called_once_with(message)


def test_print_section(rich_console):
    """Test print_section formatting"""
    title = "Configuration"

    with patch.object(rich_console.console, "print") as mock_print:
        rich_console.print_section(title)

        # Should be called twice (title + separator)
        assert mock_print.call_count == 2

        # Check first call (title)
        first_call = mock_print.call_args_list[0][0][0]
        assert title in first_call
        assert "[bold cyan]" in first_call

        # Check second call (separator)
        second_call = mock_print.call_args_list[1]
        assert "=" * 80 in second_call[0][0]
        assert second_call[1]["style"] == "dim"


def test_print_property(rich_console):
    """Test print_property formatting"""
    key = "hostname"
    value = "host01.example.com"

    with patch.object(rich_console.console, "print") as mock_print:
        rich_console.print_property(key, value)

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert key in call_args
        assert value in call_args
        assert "[cyan]" in call_args
        assert ":" in call_args


def test_print_banner_contains_ascii_art(rich_console):
    """Test print_banner contains QUADS ASCII art"""
    with patch.object(rich_console.console, "print") as mock_print:
        rich_console.print_banner()

        panel_arg = mock_print.call_args[0][0]
        panel_content = str(panel_arg.renderable)

        # Check for parts of ASCII art
        assert "QUADS" in panel_content or "___" in panel_content


def test_print_banner_contains_help_text(rich_console):
    """Test print_banner contains help instructions"""
    with patch.object(rich_console.console, "print") as mock_print:
        rich_console.print_banner()

        panel_arg = mock_print.call_args[0][0]
        panel_content = str(panel_arg.renderable)

        # Check for help text
        assert "add_quads_server" in panel_content.lower()
        assert "help" in panel_content.lower()
        assert "connect" in panel_content.lower()


def test_print_banner_contains_config_paths(rich_console):
    """Test print_banner contains configuration paths"""
    with patch.object(rich_console.console, "print") as mock_print:
        rich_console.print_banner()

        panel_arg = mock_print.call_args[0][0]
        panel_content = str(panel_arg.renderable)

        # Check for config paths
        assert "~/.config/quads/quads-client.yml" in panel_content
        assert "~/.config/quads/.quads-client-history.db" in panel_content


def test_print_table_empty_rows(rich_console):
    """Test print_table with empty rows"""
    headers = ["Name", "Model"]
    rows = []

    with patch.object(rich_console.console, "print") as mock_print:
        rich_console.print_table(headers, rows)

        # Should still print the table (with just headers)
        assert mock_print.call_count == 1
