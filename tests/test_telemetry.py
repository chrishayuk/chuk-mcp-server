#!/usr/bin/env python3
"""Tests for the telemetry module (thin OpenTelemetry wrapper)."""

import importlib
from unittest.mock import MagicMock, patch

import pytest

from chuk_mcp_server.telemetry import is_telemetry_available, trace_tool_call


class TestIsTelemetryAvailable:
    """Test is_telemetry_available function."""

    def test_returns_bool(self):
        """is_telemetry_available() returns a boolean reflecting otel installation."""
        result = is_telemetry_available()
        assert isinstance(result, bool)

    def test_matches_otel_import(self):
        """is_telemetry_available() matches whether opentelemetry can be imported."""
        try:
            import opentelemetry  # noqa: F401

            expected = True
        except ImportError:
            expected = False
        assert is_telemetry_available() is expected


class TestTraceToolCall:
    """Test trace_tool_call context manager."""

    def test_works_as_context_manager_without_otel(self):
        """trace_tool_call works as a context manager even without OpenTelemetry."""
        with trace_tool_call("test_tool") as ctx:
            assert ctx["tool_name"] == "test_tool"
            assert "start_time" in ctx

    def test_populates_timing_info(self):
        """trace_tool_call populates duration in ctx dict after exiting."""
        with trace_tool_call("timed_tool") as ctx:
            # Simulate some work
            sum(range(1000))

        assert "duration" in ctx
        assert isinstance(ctx["duration"], float)
        assert ctx["duration"] >= 0

    def test_propagates_exceptions(self):
        """trace_tool_call propagates exceptions raised inside the context."""
        with pytest.raises(ValueError, match="test error"):
            with trace_tool_call("failing_tool") as ctx:
                raise ValueError("test error")

        # Duration should still be set even when an exception occurs
        assert "duration" in ctx
        assert ctx["duration"] >= 0

    def test_ctx_can_store_additional_data(self):
        """The ctx dict returned by trace_tool_call can store arbitrary user data."""
        with trace_tool_call("custom_tool") as ctx:
            ctx["result_size"] = 42
            ctx["custom_key"] = "custom_value"

        assert ctx["result_size"] == 42
        assert ctx["custom_key"] == "custom_value"
        assert ctx["tool_name"] == "custom_tool"
        assert "duration" in ctx


class TestTraceToolCallWithOtel:
    """Test trace_tool_call when OpenTelemetry is available (via mocking)."""

    def _setup_mock_otel(self):
        """Set up mock OpenTelemetry by patching module-level variables."""
        mock_trace = MagicMock()
        mock_status = MagicMock()
        mock_status_code = MagicMock()
        mock_status_code.ERROR = "ERROR"
        mock_trace.Status = mock_status
        mock_trace.StatusCode = mock_status_code

        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)

        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span

        return mock_trace, mock_tracer, mock_span

    def test_otel_available_flag_after_reload(self):
        """When otel is available, _OTEL_AVAILABLE should be True after reload."""
        mock_trace = MagicMock()
        mock_trace.get_tracer.return_value = MagicMock()

        with patch.dict("sys.modules", {"opentelemetry": MagicMock(), "opentelemetry.trace": mock_trace}):
            import chuk_mcp_server.telemetry as tel_mod

            importlib.reload(tel_mod)
            assert tel_mod._OTEL_AVAILABLE is True
            assert tel_mod.is_telemetry_available() is True

        # Reload back to normal
        importlib.reload(tel_mod)

    def test_otel_span_created(self):
        """When otel is available, a span should be created."""
        import chuk_mcp_server.telemetry as tel_mod

        mock_trace, mock_tracer, mock_span = self._setup_mock_otel()

        # Patch module-level variables directly
        original_available = tel_mod._OTEL_AVAILABLE
        original_tracer = tel_mod._tracer
        try:
            tel_mod._OTEL_AVAILABLE = True
            tel_mod._tracer = mock_tracer
            # Also need the trace module for Status/StatusCode
            tel_mod.trace = mock_trace  # type: ignore[attr-defined]

            with tel_mod.trace_tool_call("my_tool") as ctx:
                ctx["extra"] = "data"

            mock_tracer.start_as_current_span.assert_called_once_with(
                "tool.my_tool", attributes={"tool.name": "my_tool"}
            )
            assert "duration" in ctx
        finally:
            tel_mod._OTEL_AVAILABLE = original_available
            tel_mod._tracer = original_tracer
            if hasattr(tel_mod, "trace"):
                delattr(tel_mod, "trace")

    def test_otel_span_sets_duration_attribute(self):
        """When otel is available, duration_ms should be set on span."""
        import chuk_mcp_server.telemetry as tel_mod

        mock_trace, mock_tracer, mock_span = self._setup_mock_otel()

        original_available = tel_mod._OTEL_AVAILABLE
        original_tracer = tel_mod._tracer
        try:
            tel_mod._OTEL_AVAILABLE = True
            tel_mod._tracer = mock_tracer
            tel_mod.trace = mock_trace  # type: ignore[attr-defined]

            with tel_mod.trace_tool_call("timed_tool"):
                pass

            mock_span.set_attribute.assert_called()
            calls = mock_span.set_attribute.call_args_list
            attr_names = [c[0][0] for c in calls]
            assert "tool.duration_ms" in attr_names
        finally:
            tel_mod._OTEL_AVAILABLE = original_available
            tel_mod._tracer = original_tracer
            if hasattr(tel_mod, "trace"):
                delattr(tel_mod, "trace")

    def test_otel_span_error_status_on_exception(self):
        """When otel is available and exception occurs, span status should be ERROR."""
        import chuk_mcp_server.telemetry as tel_mod

        mock_trace, mock_tracer, mock_span = self._setup_mock_otel()

        original_available = tel_mod._OTEL_AVAILABLE
        original_tracer = tel_mod._tracer
        try:
            tel_mod._OTEL_AVAILABLE = True
            tel_mod._tracer = mock_tracer
            tel_mod.trace = mock_trace  # type: ignore[attr-defined]

            with pytest.raises(RuntimeError, match="otel test"):
                with tel_mod.trace_tool_call("error_tool"):
                    raise RuntimeError("otel test")

            mock_span.set_status.assert_called_once()
        finally:
            tel_mod._OTEL_AVAILABLE = original_available
            tel_mod._tracer = original_tracer
            if hasattr(tel_mod, "trace"):
                delattr(tel_mod, "trace")
