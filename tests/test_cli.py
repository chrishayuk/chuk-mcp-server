#!/usr/bin/env python3
"""
Tests for CLI module.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from chuk_mcp_server.cli import create_example_server, main, scaffold_project, setup_logging


class TestSetupLogging:
    """Test logging setup functionality."""

    @patch("chuk_mcp_server.cli.logging.basicConfig")
    def test_setup_logging_debug(self, mock_basicConfig):
        """Test logging setup with debug mode."""
        setup_logging(debug=True, stderr=True)

        mock_basicConfig.assert_called_once()
        kwargs = mock_basicConfig.call_args[1]
        assert kwargs["level"] == 10  # logging.DEBUG
        assert kwargs["stream"] == sys.stderr

    @patch("chuk_mcp_server.cli.logging.basicConfig")
    def test_setup_logging_info(self, mock_basicConfig):
        """Test logging setup with info mode."""
        setup_logging(debug=False, stderr=False)

        mock_basicConfig.assert_called_once()
        kwargs = mock_basicConfig.call_args[1]
        assert kwargs["level"] == 20  # logging.INFO
        assert kwargs["stream"] == sys.stdout


class TestCreateExampleServer:
    """Test example server creation."""

    def test_create_example_server_with_defaults(self):
        """Test creating server with default tools and resources."""
        server = create_example_server()

        assert server.server_info.name == "chuk-mcp-server"
        assert server.server_info.version == "0.2.3"

        # Check that example tools were added
        tools = server.get_tools()
        tool_names = [tool.name for tool in tools]
        assert "echo" in tool_names
        assert "add" in tool_names
        assert "get_env" in tool_names

        # Check that example resource was added
        resources = server.get_resources()
        resource_uris = [resource.uri for resource in resources]
        assert "server://info" in resource_uris

    @patch.dict("os.environ", {"MCP_SERVER_NAME": "custom-server", "MCP_SERVER_VERSION": "1.0.0"})
    def test_create_example_server_with_env_vars(self):
        """Test creating server with environment variables."""
        server = create_example_server()

        assert server.server_info.name == "custom-server"
        assert server.server_info.version == "1.0.0"

    @patch("chuk_mcp_server.cli.ChukMCPServer")
    def test_create_example_server_with_existing_tools(self, mock_server_class):
        """Test that example tools are not added if tools already exist."""
        mock_server = MagicMock()
        mock_tool = MagicMock()
        mock_tool.name = "existing_tool"
        mock_server.get_tools.return_value = [mock_tool]
        mock_server.get_resources.return_value = []
        mock_server_class.return_value = mock_server

        server = create_example_server()

        # Verify tool decorator was not called (tools already exist)
        assert server == mock_server
        # Check that get_tools was called to check existing tools
        mock_server.get_tools.assert_called()

    def test_example_tools_functionality(self):
        """Test that the example tools work correctly."""
        server = create_example_server()

        # Get the registered tools
        tools = {tool.name: tool for tool in server.get_tools()}

        # Test echo tool via direct call
        assert "echo" in tools

        # Test that tools were registered
        assert len(tools) == 3
        assert "add" in tools
        assert "get_env" in tools


class TestMainFunction:
    """Test main CLI entry point."""

    @patch("chuk_mcp_server.cli.create_example_server")
    @patch("chuk_mcp_server.cli.setup_logging")
    @patch("sys.argv", ["chuk-mcp-server", "stdio"])
    def test_main_stdio_mode(self, mock_setup_logging, mock_create_server):
        """Test main function in stdio mode."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("chuk_mcp_server.cli.logging.info"):
            main()

        # Verify logging setup for stdio (stderr=True)
        mock_setup_logging.assert_called_once_with(debug=False, stderr=True)

        # Verify server creation and run
        mock_create_server.assert_called_once()
        mock_server.run.assert_called_once_with(stdio=True, debug=False, log_level="warning")

    @patch("chuk_mcp_server.cli.create_example_server")
    @patch("chuk_mcp_server.cli.setup_logging")
    @patch("sys.argv", ["chuk-mcp-server", "stdio", "--debug"])
    def test_main_stdio_mode_debug(self, mock_setup_logging, mock_create_server):
        """Test main function in stdio mode with debug."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("chuk_mcp_server.cli.logging.info"):
            main()

        # Verify debug logging
        mock_setup_logging.assert_called_once_with(debug=True, stderr=True)
        mock_server.run.assert_called_once_with(stdio=True, debug=True, log_level="warning")

    @patch("chuk_mcp_server.cli.create_example_server")
    @patch("chuk_mcp_server.cli.setup_logging")
    @patch("sys.argv", ["chuk-mcp-server", "http"])
    def test_main_http_mode(self, mock_setup_logging, mock_create_server):
        """Test main function in HTTP mode."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("chuk_mcp_server.cli.logging.info"):
            main()

        # Verify logging setup for HTTP (stderr=False)
        mock_setup_logging.assert_called_once_with(debug=False, stderr=False)

        # Verify server run with HTTP mode
        mock_server.run.assert_called_once_with(
            host=None, port=None, debug=False, stdio=False, log_level="warning", reload=False, inspect=False
        )

    @patch("chuk_mcp_server.cli.create_example_server")
    @patch("chuk_mcp_server.cli.setup_logging")
    @patch("sys.argv", ["chuk-mcp-server", "http", "--host", "0.0.0.0", "--port", "9000", "--debug"])
    def test_main_http_mode_with_options(self, mock_setup_logging, mock_create_server):
        """Test main function in HTTP mode with custom options."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("chuk_mcp_server.cli.logging.info"):
            main()

        # Verify debug logging
        mock_setup_logging.assert_called_once_with(debug=True, stderr=False)

        # Verify server run with custom options
        mock_server.run.assert_called_once_with(
            host="0.0.0.0", port=9000, debug=True, stdio=False, log_level="warning", reload=False, inspect=False
        )

    @patch("chuk_mcp_server.cli.create_example_server")
    @patch("chuk_mcp_server.cli.setup_logging")
    @patch("sys.argv", ["chuk-mcp-server", "auto"])
    def test_main_auto_mode(self, mock_setup_logging, mock_create_server):
        """Test main function in auto mode."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("chuk_mcp_server.cli.logging.info"):
            main()

        # Verify logging setup for auto (stderr=False)
        mock_setup_logging.assert_called_once_with(debug=False, stderr=False)

        # Verify server run with auto detection
        mock_server.run.assert_called_once_with(host=None, port=None, debug=False, log_level="warning")

    @patch("chuk_mcp_server.cli.create_example_server")
    @patch("chuk_mcp_server.cli.setup_logging")
    @patch("sys.argv", ["chuk-mcp-server", "auto", "--host", "localhost", "--port", "8080"])
    def test_main_auto_mode_with_options(self, mock_setup_logging, mock_create_server):
        """Test main function in auto mode with options."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("chuk_mcp_server.cli.logging.info"):
            main()

        # Verify server run with provided options
        mock_server.run.assert_called_once_with(host="localhost", port=8080, debug=False, log_level="warning")

    @patch("sys.argv", ["chuk-mcp-server", "--help"])
    def test_main_help(self):
        """Test main function with help flag."""
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.stdout"):
                main()

        # Help should exit with code 0
        assert exc_info.value.code == 0

    @patch("sys.argv", ["chuk-mcp-server"])
    def test_main_no_subcommand(self):
        """Test main function without subcommand."""
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.stderr"):
                main()

        # Should exit with error code
        assert exc_info.value.code == 2

    def test_example_resource_functionality(self):
        """Test that the example resource works correctly."""
        server = create_example_server()

        # Check that resource was registered
        resources = server.get_resources()
        assert len(resources) == 1
        assert resources[0].uri == "server://info"


# ============================================================================
# Tests for example tool function bodies
# ============================================================================


class TestExampleToolBodies:
    """Test the actual function bodies of example tools registered by create_example_server."""

    def test_echo_tool_returns_echo_message(self):
        """Cover line 40: return f'Echo: {message}'."""
        server = create_example_server()
        tools = {t.name: t for t in server.get_tools()}
        result = tools["echo"].handler("hello world")
        assert result == "Echo: hello world"

    def test_add_tool_returns_sum(self):
        """Cover line 45: return a + b."""
        server = create_example_server()
        tools = {t.name: t for t in server.get_tools()}
        result = tools["add"].handler(3.0, 4.0)
        assert result == 7.0

    def test_add_tool_with_negative_numbers(self):
        """Test add with negative numbers."""
        server = create_example_server()
        tools = {t.name: t for t in server.get_tools()}
        result = tools["add"].handler(-1.5, 2.5)
        assert result == 1.0

    def test_get_env_tool_returns_env_value(self):
        """Cover line 50: return os.environ.get(key)."""
        server = create_example_server()
        tools = {t.name: t for t in server.get_tools()}
        with patch.dict(os.environ, {"TEST_CLI_VAR": "test_value"}):
            result = tools["get_env"].handler("TEST_CLI_VAR")
        assert result == "test_value"

    def test_get_env_tool_returns_none_for_missing_key(self):
        """Test get_env returns None for nonexistent key."""
        server = create_example_server()
        tools = {t.name: t for t in server.get_tools()}
        result = tools["get_env"].handler("NONEXISTENT_CLI_TEST_KEY_12345")
        assert result is None


# ============================================================================
# Tests for example resource function body
# ============================================================================


class TestExampleResourceBody:
    """Test the resource handler body registered by create_example_server."""

    @patch("chuk_mcp_server.cli.ChukMCPServer")
    def test_skip_resource_registration_when_resources_exist(self, mock_server_class):
        """Cover branch 53->65: resources already exist so example resource is NOT added."""
        mock_server = MagicMock()
        mock_server.get_tools.return_value = [MagicMock()]  # tools exist
        mock_resource = MagicMock()
        mock_resource.uri = "existing://resource"
        mock_server.get_resources.return_value = [mock_resource]  # resources exist
        mock_server_class.return_value = mock_server

        server = create_example_server()

        # resource decorator should NOT have been called since resources already exist
        assert server == mock_server
        mock_server.get_resources.assert_called()

    def test_server_info_resource_returns_dict(self):
        """Cover line 58: the resource handler return dict."""
        server = create_example_server()
        resources = {r.uri: r for r in server.get_resources()}
        result = resources["server://info"].handler()
        assert isinstance(result, dict)
        assert result["name"] == server.server_info.name
        assert result["version"] == server.server_info.version
        assert "transport" in result
        assert "pid" in result
        assert result["pid"] == os.getpid()

    def test_server_info_resource_transport_stdio(self):
        """Test transport field when MCP_STDIO is set."""
        server = create_example_server()
        resources = {r.uri: r for r in server.get_resources()}
        with patch.dict(os.environ, {"MCP_STDIO": "1"}):
            result = resources["server://info"].handler()
        assert result["transport"] == "stdio"

    def test_server_info_resource_transport_http(self):
        """Test transport field when MCP_STDIO is not set."""
        server = create_example_server()
        resources = {r.uri: r for r in server.get_resources()}
        env = os.environ.copy()
        env.pop("MCP_STDIO", None)
        with patch.dict(os.environ, env, clear=True):
            result = resources["server://info"].handler()
        assert result["transport"] == "http"


# ============================================================================
# Tests for scaffold_project
# ============================================================================


class TestScaffoldProject:
    """Test scaffold_project function for creating new MCP server projects."""

    def test_scaffold_creates_project_directory(self, tmp_path):
        """Test that scaffold_project creates the project directory and files."""
        project_dir = tmp_path / "my-test-server"
        scaffold_project("my-test-server", directory=str(project_dir))

        assert project_dir.exists()
        assert project_dir.is_dir()

    def test_scaffold_creates_server_py(self, tmp_path):
        """Test that scaffold_project creates server.py."""
        project_dir = tmp_path / "test-server"
        scaffold_project("test-server", directory=str(project_dir))

        server_file = project_dir / "server.py"
        assert server_file.exists()
        content = server_file.read_text()
        assert "test-server" in content
        assert "from chuk_mcp_server import" in content
        assert "@tool" in content
        assert "@resource" in content
        assert "@prompt" in content

    def test_scaffold_creates_pyproject_toml(self, tmp_path):
        """Test that scaffold_project creates pyproject.toml."""
        project_dir = tmp_path / "test-server"
        scaffold_project("test-server", directory=str(project_dir))

        pyproject_file = project_dir / "pyproject.toml"
        assert pyproject_file.exists()
        content = pyproject_file.read_text()
        assert 'name = "test-server"' in content
        assert "chuk-mcp-server" in content

    def test_scaffold_creates_readme(self, tmp_path):
        """Test that scaffold_project creates README.md."""
        project_dir = tmp_path / "test-server"
        scaffold_project("test-server", directory=str(project_dir))

        readme_file = project_dir / "README.md"
        assert readme_file.exists()
        content = readme_file.read_text()
        assert "test-server" in content
        assert "Quick Start" in content

    def test_scaffold_creates_gitignore(self, tmp_path):
        """Test that scaffold_project creates .gitignore."""
        project_dir = tmp_path / "test-server"
        scaffold_project("test-server", directory=str(project_dir))

        gitignore_file = project_dir / ".gitignore"
        assert gitignore_file.exists()
        content = gitignore_file.read_text()
        assert "__pycache__/" in content
        assert "venv/" in content

    def test_scaffold_creates_dockerfile(self, tmp_path):
        """Test that scaffold_project creates Dockerfile."""
        project_dir = tmp_path / "test-server"
        scaffold_project("test-server", directory=str(project_dir))

        dockerfile = project_dir / "Dockerfile"
        assert dockerfile.exists()
        content = dockerfile.read_text()
        assert "FROM python:" in content
        assert "EXPOSE 8000" in content

    def test_scaffold_creates_docker_compose(self, tmp_path):
        """Test that scaffold_project creates docker-compose.yml."""
        project_dir = tmp_path / "test-server"
        scaffold_project("test-server", directory=str(project_dir))

        compose_file = project_dir / "docker-compose.yml"
        assert compose_file.exists()
        content = compose_file.read_text()
        assert "test-server" in content
        assert "8000:8000" in content

    def test_scaffold_all_files_present(self, tmp_path):
        """Test that all expected files are created."""
        project_dir = tmp_path / "full-server"
        scaffold_project("full-server", directory=str(project_dir))

        expected_files = [
            "server.py",
            "pyproject.toml",
            "README.md",
            ".gitignore",
            "Dockerfile",
            "docker-compose.yml",
        ]
        for filename in expected_files:
            assert (project_dir / filename).exists(), f"Missing file: {filename}"

    def test_scaffold_without_directory_uses_cwd(self, tmp_path, monkeypatch):
        """Test scaffold_project without directory argument uses cwd/project_name."""
        monkeypatch.chdir(tmp_path)
        scaffold_project("auto-dir-server")

        project_dir = tmp_path / "auto-dir-server"
        assert project_dir.exists()
        assert (project_dir / "server.py").exists()

    def test_scaffold_existing_directory_exits(self, tmp_path):
        """Test that scaffold_project exits if directory already exists."""
        project_dir = tmp_path / "existing-server"
        project_dir.mkdir()

        with pytest.raises(SystemExit) as exc_info:
            scaffold_project("existing-server", directory=str(project_dir))
        assert exc_info.value.code == 1

    def test_scaffold_prints_success_messages(self, tmp_path, capsys):
        """Test that scaffold_project prints informative messages."""
        project_dir = tmp_path / "verbose-server"
        scaffold_project("verbose-server", directory=str(project_dir))

        captured = capsys.readouterr()
        assert "Created project directory" in captured.out
        assert "Created server.py" in captured.out
        assert "Created pyproject.toml" in captured.out
        assert "Created README.md" in captured.out
        assert "Created .gitignore" in captured.out
        assert "Created Dockerfile" in captured.out
        assert "Created docker-compose.yml" in captured.out
        assert "verbose-server" in captured.out
        assert "Next steps" in captured.out

    def test_scaffold_nested_directory(self, tmp_path):
        """Test scaffold_project with a nested directory path."""
        nested_dir = tmp_path / "deep" / "nested" / "project"
        scaffold_project("nested-server", directory=str(nested_dir))

        assert nested_dir.exists()
        assert (nested_dir / "server.py").exists()


# ============================================================================
# Tests for init mode in main()
# ============================================================================


class TestMainInitMode:
    """Test the init subcommand in main()."""

    @patch("sys.argv", ["chuk-mcp-server", "init", "my-new-project", "--dir"])
    def test_main_init_mode_calls_scaffold(self, tmp_path):
        """Cover lines 756-757: init mode calls scaffold_project and returns."""
        argv = ["chuk-mcp-server", "init", "my-init-project", "--dir", str(tmp_path / "my-init-project")]
        with patch("sys.argv", argv):
            main()

        project_dir = tmp_path / "my-init-project"
        assert project_dir.exists()
        assert (project_dir / "server.py").exists()

    def test_main_init_mode_without_dir(self, tmp_path, monkeypatch):
        """Test init mode without --dir uses current directory."""
        monkeypatch.chdir(tmp_path)
        with patch("sys.argv", ["chuk-mcp-server", "init", "from-main-server"]):
            main()

        project_dir = tmp_path / "from-main-server"
        assert project_dir.exists()
        assert (project_dir / "server.py").exists()

    def test_main_init_mode_does_not_create_server(self, tmp_path):
        """Test that init mode does not create or run an example server."""
        argv = ["chuk-mcp-server", "init", "no-server-project", "--dir", str(tmp_path / "no-server-project")]
        with patch("sys.argv", argv):
            with patch("chuk_mcp_server.cli.create_example_server") as mock_create:
                main()
                mock_create.assert_not_called()


# ============================================================================
# Tests for HTTP mode with --reload and --inspect flags
# ============================================================================


class TestMainHTTPFlags:
    """Test HTTP mode CLI flags for reload and inspect."""

    @patch("chuk_mcp_server.cli.create_example_server")
    @patch("chuk_mcp_server.cli.setup_logging")
    @patch("sys.argv", ["chuk-mcp-server", "http", "--reload"])
    def test_main_http_reload_flag(self, mock_setup_logging, mock_create_server):
        """Test HTTP mode with --reload flag."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("chuk_mcp_server.cli.logging.info"):
            main()

        mock_server.run.assert_called_once_with(
            host=None,
            port=None,
            debug=False,
            stdio=False,
            log_level="warning",
            reload=True,
            inspect=False,
        )

    @patch("chuk_mcp_server.cli.create_example_server")
    @patch("chuk_mcp_server.cli.setup_logging")
    @patch("sys.argv", ["chuk-mcp-server", "http", "--inspect"])
    def test_main_http_inspect_flag(self, mock_setup_logging, mock_create_server):
        """Test HTTP mode with --inspect flag."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("chuk_mcp_server.cli.logging.info"):
            main()

        mock_server.run.assert_called_once_with(
            host=None,
            port=None,
            debug=False,
            stdio=False,
            log_level="warning",
            reload=False,
            inspect=True,
        )

    @patch("chuk_mcp_server.cli.create_example_server")
    @patch("chuk_mcp_server.cli.setup_logging")
    @patch("sys.argv", ["chuk-mcp-server", "http", "--reload", "--inspect", "--debug"])
    def test_main_http_all_flags(self, mock_setup_logging, mock_create_server):
        """Test HTTP mode with all flags combined."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("chuk_mcp_server.cli.logging.info"):
            main()

        mock_server.run.assert_called_once_with(
            host=None,
            port=None,
            debug=True,
            stdio=False,
            log_level="warning",
            reload=True,
            inspect=True,
        )


# ============================================================================
# Tests for log-level variations
# ============================================================================


class TestMainLogLevel:
    """Test different log-level options across modes."""

    @patch("chuk_mcp_server.cli.create_example_server")
    @patch("chuk_mcp_server.cli.setup_logging")
    @patch("sys.argv", ["chuk-mcp-server", "stdio", "--log-level", "error"])
    def test_stdio_log_level_error(self, mock_setup_logging, mock_create_server):
        """Test stdio mode with log-level=error."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("chuk_mcp_server.cli.logging.info"):
            main()

        mock_server.run.assert_called_once_with(stdio=True, debug=False, log_level="error")

    @patch("chuk_mcp_server.cli.create_example_server")
    @patch("chuk_mcp_server.cli.setup_logging")
    @patch("sys.argv", ["chuk-mcp-server", "http", "--log-level", "debug"])
    def test_http_log_level_debug(self, mock_setup_logging, mock_create_server):
        """Test HTTP mode with log-level=debug."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("chuk_mcp_server.cli.logging.info"):
            main()

        mock_server.run.assert_called_once_with(
            host=None,
            port=None,
            debug=False,
            stdio=False,
            log_level="debug",
            reload=False,
            inspect=False,
        )

    @patch("chuk_mcp_server.cli.create_example_server")
    @patch("chuk_mcp_server.cli.setup_logging")
    @patch("sys.argv", ["chuk-mcp-server", "auto", "--log-level", "critical", "--debug"])
    def test_auto_log_level_critical_with_debug(self, mock_setup_logging, mock_create_server):
        """Test auto mode with log-level=critical and debug."""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        with patch("chuk_mcp_server.cli.logging.info"):
            main()

        mock_server.run.assert_called_once_with(
            host=None,
            port=None,
            debug=True,
            log_level="critical",
        )
