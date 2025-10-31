"""OAuth test configuration and fixtures."""

import sys
from unittest.mock import Mock

# Mock chuk_sessions before any OAuth imports
mock_sessions = Mock()
mock_sessions.get_session = Mock(return_value=Mock())
sys.modules["chuk_sessions"] = mock_sessions
