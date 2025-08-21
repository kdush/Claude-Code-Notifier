[中文文档](development.md)

# 🛠️ Development Guide

## Project Architecture

### Core Components

```
src/
├── channels/           # Notification channel implementations
│   ├── base.py         # Base channel interface
│   ├── dingtalk.py     # Dingtalk robot
│   ├── feishu.py       # Feishu robot
│   ├── telegram.py     # Telegram Bot
│   ├── email.py        # SMTP email
│   └── ...
├── events/             # Event detection and handling
│   ├── base.py         # Base event interface
│   ├── builtin.py      # Built-in event types
│   └── custom.py       # Custom events
├── templates/          # Message template engine
│   └── template_engine.py  # Unified template engine
├── claude_notifier/    # New architecture core modules
│   ├── core/           # Core features
│   ├── intelligence/   # Intelligent limiting components
│   ├── monitoring/     # Monitoring system
│   └── utils/          # Utilities
└── utils/              # Utilities (compat)
    ├── helpers.py      # Helper functions
    ├── statistics.py   # Stats collection
    └── ...
```

### Design Patterns

1. Strategy — channels
2. Observer — event listening
3. Template Method — message formatting
4. Factory — component creation
5. Decorator — feature enhancement

## Development Environment Setup

### 1. Clone the project

```bash
git clone https://github.com/your-repo/claude-code-notifier.git
cd claude-code-notifier
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows
```

### 3. Install dependencies

```bash
# Development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Editable install
pip install -e .
```

### 4. Configure development environment

```bash
# Copy config template
cp config/enhanced_config.yaml.template config/config.yaml

# Environment variables
export CLAUDE_NOTIFIER_DEBUG=1
export CLAUDE_NOTIFIER_LOG_LEVEL=DEBUG
```

## Code Conventions

### Python Code Style

```python
# Use Black for formatting
black src/ tests/

# Use isort for import sorting
isort src/ tests/

# Use flake8 for linting
flake8 src/ tests/

# Use mypy for type checking
mypy src/
```

### Docstrings

```python
def send_notification(self, data: Dict[str, Any], template: str) -> bool:
    """Send a notification message
    
    Args:
        data: Notification data dictionary
        template: Message template name
        
    Returns:
        bool: True if sent successfully, False otherwise
        
    Raises:
        NotificationError: Raised when sending fails
        
    Example:
        >>> channel = DingtalkChannel(config)
        >>> success = channel.send_notification(
        ...     {"project": "test", "operation": "build"}, 
        ...     "task_completion"
        ... )
        >>> print(success)
        True
    """
```

### Type Annotations

```python
from typing import Dict, List, Optional, Union, Any
from abc import ABC, abstractmethod

class BaseChannel(ABC):
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.enabled: bool = config.get('enabled', False)
    
    @abstractmethod
    def send_notification(
        self, 
        data: Dict[str, Any], 
        template: str
    ) -> bool:
        """Abstract method to send notification"""
        pass
```

## Testing Framework

### Layout

```
tests/
├── conftest.py                    # pytest config
├── test_basic_units.py            # basic unit tests
├── test_integration_flows.py      # integration tests
├── test_performance_benchmarks.py # performance tests
├── test_system_validation.py      # system validation tests
├── test_intelligence.py           # intelligent components
├── test_monitoring.py             # monitoring system tests
└── run_all_tests.py               # test runner
```

### Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test
python -m pytest tests/test_basic_units.py -v

# Performance tests
python tests/test_performance_benchmarks.py

# Coverage report
pytest --cov=src --cov-report=html tests/
```

### Test Example

```python
import unittest
from unittest.mock import Mock, patch
from channels.dingtalk import DingtalkChannel

class TestDingtalkChannel(unittest.TestCase):
    def setUp(self):
        self.config = {
            'enabled': True,
            'webhook': 'https://test.com/webhook',
            'secret': 'test_secret'
        }
        self.channel = DingtalkChannel(self.config)
    
    @patch('requests.post')
    def test_send_notification_success(self, mock_post):
        # Simulate a successful response
        mock_response = Mock()
        mock_response.json.return_value = {'errcode': 0}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Execute
        result = self.channel.send_notification(
            {'project': 'test'}, 
            'template'
        )
        
        # Verify
        self.assertTrue(result)
        mock_post.assert_called_once()
```

## Adding a New Notification Channel

### 1. Create the channel class

```python
# src/claude_notifier/core/channels/my_channel.py
from typing import Dict, Any
from .base import BaseChannel

class MyChannel(BaseChannel):
    """Custom notification channel"""
    
    # Required class attributes
    DISPLAY_NAME = "My Channel"
    DESCRIPTION = "Custom notification channel example"
    REQUIRED_CONFIG = ["api_key", "endpoint"]
    
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.endpoint = config.get('endpoint')
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        return bool(self.api_key and self.endpoint)
    
    def send_notification(
        self, 
        template_data: Dict[str, Any], 
        event_type: str = 'generic'
    ) -> bool:
        """Send notification implementation"""
        if not self.config.get('enabled', False) or not self.validate_config():
            return False
        
        try:
            # Format message
            message = self._format_message(template_data, event_type)
            
            # Send request
            response = self._send_request(message)
            
            # Handle response
            return self._handle_response(response)
            
        except Exception as e:
            self.logger.error(f"Send failed: {e}")
            return False
    
    def _format_message(self, template_data: Dict[str, Any], event_type: str) -> str:
        """Format message content"""
        # Implement your formatting logic
        pass
    
    def _send_request(self, message: str) -> Any:
        """Send HTTP request"""
        # Implement HTTP call
        pass
    
    def _handle_response(self, response: Any) -> bool:
        """Handle response"""
        # Implement response handling
        pass
```

### 2. Register the channel

Add try-catch import in `src/claude_notifier/core/channels/__init__.py`:

```python
# Import custom channel
try:
    from .my_channel import MyChannel
    _available_channels['my_channel'] = MyChannel
except ImportError as e:
    logger.debug(f"Custom channel import failed: {e}")
```

Or use dynamic registration API:

```python
from src.claude_notifier.core.channels import register_channel
from .my_channel import MyChannel

# Register channel dynamically
success = register_channel('my_channel', MyChannel)
if success:
    print("Channel registered successfully")
```

### 3. Add config template

```yaml
# config/enhanced_config.yaml.template
channels:
  my_channel:
    enabled: false
    api_key: "YOUR_API_KEY"
    endpoint: "https://api.mychannel.com/notify"
    # other params
```

### 4. Write tests

```python
# tests/test_my_channel.py
import unittest
from src.claude_notifier.core.channels.my_channel import MyChannel

class TestMyChannel(unittest.TestCase):
    def test_channel_initialization(self):
        config = {'enabled': True, 'api_key': 'test', 'endpoint': 'test'}
        channel = MyChannel(config)
        self.assertTrue(channel.enabled)
    
    def test_config_validation(self):
        # Test config validation logic
        pass
    
    def test_send_notification(self):
        # Test send logic
        pass
```

## Adding a New Event Type

### 1. Create the event class

```python
# src/events/my_event.py
from typing import Dict, Any
from .base import BaseEvent, EventType, EventPriority

class MyCustomEvent(BaseEvent):
    """Custom event type"""
    
    def __init__(self):
        super().__init__()
        self.event_id = "my_custom_event"
        self.name = "My Custom Event"
        self.event_type = EventType.CUSTOM
        self.priority = EventPriority.NORMAL
    
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """Determine whether to trigger"""
        # Implement your trigger logic
        if context.get('trigger_condition'):
            return True
        return False
    
    def extract_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract notification data from context"""
        return {
            'event_name': self.name,
            'timestamp': context.get('timestamp'),
            'custom_data': context.get('custom_data', {}),
        }
    
    def get_template_name(self) -> str:
        """Get message template name"""
        return "my_custom_template"
```

### 2. Register the event

```python
# src/events/__init__.py
from .my_event import MyCustomEvent

AVAILABLE_EVENTS = {
    'sensitive_operation': SensitiveOperationEvent,
    'task_completion': TaskCompletionEvent,
    'my_custom_event': MyCustomEvent,  # add new event
}
```

### 3. Add a message template

```yaml
# templates/custom_templates.yaml
templates:
  my_custom_template:
    dingtalk:
      msgtype: "markdown"
      markdown:
        title: "{{ event_name }}"
        text: |
          ### {{ event_name }}
          
          **Time:** {{ timestamp }}
          **Data:** {{ custom_data }}
    
    feishu:
      msg_type: "text"
      content:
        text: "{{ event_name }}: {{ custom_data }}"
```

## Intelligent Components

### Operation Gate

```python
# src/claude_notifier/utils/operation_gate.py
from enum import Enum
from typing import Dict, Any, Tuple

class OperationResult(Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    REQUIRES_CONFIRMATION = "requires_confirmation"

class OperationRequest:
    def __init__(self, command: str, context: Dict[str, Any], priority: str = "normal"):
        self.command = command
        self.context = context
        self.priority = priority
        self.timestamp = time.time()

class OperationGate:
    """Operation gate to control sensitive operations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.blocked_patterns = config.get('blocked_patterns', [])
        self.protected_paths = config.get('protected_paths', [])
    
    def should_allow_operation(
        self, 
        request: OperationRequest
    ) -> Tuple[OperationResult, str]:
        """Evaluate whether an operation should be allowed"""
        
        # Block patterns
        for pattern in self.blocked_patterns:
            if pattern in request.command:
                return (
                    OperationResult.BLOCKED, 
                    f"Operation contains blocked pattern: {pattern}"
                )
        
        # Protected paths
        for path in self.protected_paths:
            if path in request.command:
                return (
                    OperationResult.REQUIRES_CONFIRMATION,
                    f"Operation touches protected path: {path}"
                )
        
        return (OperationResult.ALLOWED, "Operation allowed")
```

### Notification Throttle

```python
# src/claude_notifier/utils/notification_throttle.py
import time
from collections import defaultdict, deque
from typing import Dict, Any

class NotificationThrottle:
    """Notification throttling to prevent spam"""
    
    def __init__(self, config: Dict[str, Any]):
        self.max_per_minute = config.get('max_per_minute', 10)
        self.max_per_hour = config.get('max_per_hour', 60)
        self.cooldown_period = config.get('cooldown_period', 300)
        
        self.minute_counter = defaultdict(deque)
        self.hour_counter = defaultdict(deque)
        self.cooldown_tracker = {}
    
    def should_allow_notification(
        self, 
        channel: str, 
        message_hash: str = None
    ) -> bool:
        """Check whether a notification should be sent"""
        current_time = time.time()
        
        # Cooldown
        if self._is_in_cooldown(channel, current_time):
            return False
        
        # Rate limit
        if not self._check_rate_limit(channel, current_time):
            self._set_cooldown(channel, current_time)
            return False
        
        # Record
        self._record_notification(channel, current_time)
        return True
    
    def _check_rate_limit(self, channel: str, current_time: float) -> bool:
        """Check rate limits"""
        # Cleanup
        self._cleanup_old_records(channel, current_time)
        
        # Per-minute
        if len(self.minute_counter[channel]) >= self.max_per_minute:
            return False
        
        # Per-hour
        if len(self.hour_counter[channel]) >= self.max_per_hour:
            return False
        
        return True
```

## Monitoring System

### Statistics Collector

```python
# src/claude_notifier/monitoring/statistics.py
import json
import time
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict, Counter

class StatisticsManager:
    """Collect and manage statistics"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.stats_file = Path(config.get('stats_file', '~/.claude-notifier/stats.json')).expanduser()
        self.retention_days = config.get('retention_days', 30)
        
        self.load_statistics()
    
    def record_event(self, event_type: str, channel: str, success: bool, metadata: Dict[str, Any] = None):
        """Record an event"""
        timestamp = time.time()
        record = {
            'timestamp': timestamp,
            'event_type': event_type,
            'channel': channel,
            'success': success,
            'metadata': metadata or {}
        }
        
        self.stats['events'].append(record)
        self._cleanup_old_records()
        self.save_statistics()
    
    def get_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary statistics"""
        cutoff_time = time.time() - (days * 24 * 3600)
        recent_events = [
            event for event in self.stats['events']
            if event['timestamp'] > cutoff_time
        ]
        
        return {
            'total_events': len(recent_events),
            'success_rate': self._calculate_success_rate(recent_events),
            'events_by_type': Counter(event['event_type'] for event in recent_events),
            'events_by_channel': Counter(event['channel'] for event in recent_events),
            'daily_breakdown': self._get_daily_breakdown(recent_events, days)
        }
```

## Performance Optimization

### Async Processing

```python
import asyncio
import aiohttp
from typing import List, Dict, Any

class AsyncNotificationSender:
    """Async notification sender"""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def send_notifications(
        self, 
        notifications: List[Dict[str, Any]]
    ) -> List[bool]:
        """Send notifications in batch asynchronously"""
        tasks = [
            self._send_single_notification(notification)
            for notification in notifications
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [isinstance(result, bool) and result for result in results]
    
    async def _send_single_notification(self, notification: Dict[str, Any]) -> bool:
        """Send a single notification"""
        async with self.semaphore:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        notification['url'],
                        json=notification['data'],
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        return response.status == 200
            except Exception:
                return False
```

### Caching

```python
from functools import lru_cache
import hashlib
import pickle
from typing import Any

class TemplateCache:
    """Template cache system"""
    
    def __init__(self, max_size: int = 128):
        self.cache = {}
        self.max_size = max_size
        self.access_count = {}
    
    def get(self, template_key: str, data: Dict[str, Any]) -> str:
        """Get a cached template"""
        cache_key = self._generate_cache_key(template_key, data)
        
        if cache_key in self.cache:
            self.access_count[cache_key] = self.access_count.get(cache_key, 0) + 1
            return self.cache[cache_key]
        
        return None
    
    def put(self, template_key: str, data: Dict[str, Any], rendered: str):
        """Store a rendered result"""
        cache_key = self._generate_cache_key(template_key, data)
        
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[cache_key] = rendered
        self.access_count[cache_key] = 1
    
    def _generate_cache_key(self, template_key: str, data: Dict[str, Any]) -> str:
        """Generate a cache key"""
        data_str = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        hash_obj = hashlib.md5(f"{template_key}:{data_str}".encode())
        return hash_obj.hexdigest()
```

## Debugging and Diagnostics

### Tools

```bash
# Enable debug mode
export CLAUDE_NOTIFIER_DEBUG=1

# Verbose logs
export CLAUDE_NOTIFIER_LOG_LEVEL=DEBUG

# Performance profiling
python -m cProfile -o profile.stats scripts/test_performance.py

# Memory profiling
python -m memory_profiler scripts/test_memory.py
```

### Diagnostic Commands

```bash
# System health check
claude-notifier health

# Config validation
claude-notifier config validate

# Channel connectivity tests
claude-notifier test --all-channels

# Benchmark
claude-notifier benchmark

# Statistics report
claude-notifier stats --days 7
```

## Contribution Summary

### 1. Fork and branch

```bash
# Fork to your account
# Clone your fork
git clone https://github.com/your-username/claude-code-notifier.git

# Create a feature branch
git checkout -b feature/my-new-feature
```

### 2. Development flow

1. Write code and tests
2. Run the full test suite
3. Update documentation
4. Open a Pull Request

### 3. Pull Request standards

- Clear title and description
- Includes tests
- Passes all CI checks
- Updates relevant docs
- Follows code conventions

### 4. Code review

All PRs are reviewed for:
- Functional correctness
- Code quality
- Test coverage
- Performance impact
- Security considerations

## 📦 Versioning and Pre-release Process

### 🔢 Single Source of Truth
- Version source file: `src/claude_notifier/__version__.py`
- Build config:
  - `pyproject.toml` uses a dynamic version pointing to the same file
  - `setup.py` also reads the version from the same file

### 🧭 PEP 440 Overview
- Format: `X.Y.Z[<pre>][.postN][.devN]`
- Pre-release suffixes:
  - `aN` (Alpha), `bN` (Beta), `rcN` (Release Candidate)
  - Examples: `0.0.3a1`, `0.0.3b1`, `0.0.3rc1`
- Stable release: remove the suffix, e.g., `0.0.3`
- Ordering (low → high): `0.0.3a1 < 0.0.3a2 < 0.0.3b1 < 0.0.3rc1 < 0.0.3`

### 🚧 Pre-release Policy (no TestPyPI by default)
- Publish pre-releases via Git tags: `vX.Y.Z[a|b|rc]N`, e.g., `v0.0.3b1`
- Create a corresponding repo Release with change notes (see `CHANGELOG.md`)
- CLI `--version` displays the “Version Type: Alpha/Beta/RC” and a pre-release notice
- If distribution is needed, you may manually publish pre-releases to PyPI (optional)

### ✅ Stable Release (default)
- Tag `vX.Y.Z` triggers GitHub Actions:
  - Build `sdist` and `wheel`
  - Publish to PyPI (requires PyPI credentials in repo Secrets)
- Update `CHANGELOG.md` and documentation accordingly

### 📝 Checklist
- Pre-release:
  1. Set a pre-release version in `src/claude_notifier/__version__.py` (e.g., `0.0.3b1`)
  2. Tag `v0.0.3b1` and create a Release
  3. Verify CLI `--version` shows the pre-release notice
- Stable release:
  1. Set version to `X.Y.Z` (remove pre-release suffix)
  2. Tag `vX.Y.Z` to trigger GitHub Actions and publish to PyPI
  3. Update `CHANGELOG.md` and docs

### ❓ FAQ
- How to install a pre-release?
  - `pip install --pre claude-code-notifier` (pip excludes pre-releases by default)
- Why does the version output show “Beta/RC”?
  - You're on a pre-release build; CLI clearly indicates this to avoid misuse

## Issue Feedback

If you encounter problems during development:

1. Check the Troubleshooting section in `README.md`
2. Search GitHub Issues: https://github.com/your-repo/claude-code-notifier/issues
3. Open a new issue with:
   - Detailed description
   - Reproduction steps
   - Environment info
   - Error logs

## Technical Support

- 📧 Email: dev@your-company.com
- 💬 Developer community: [Discord/Slack link]
- 📖 API docs: [API docs link]
- 🎥 Video tutorials: [Tutorials link]
