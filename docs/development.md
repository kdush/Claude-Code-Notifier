# 🛠️ 开发文档

## 项目架构

### 核心组件

```
src/
├── channels/           # 通知渠道实现
│   ├── base.py        # 基础通道接口
│   ├── dingtalk.py    # 钉钉机器人
│   ├── feishu.py      # 飞书机器人
│   ├── telegram.py    # Telegram Bot
│   ├── email.py       # SMTP 邮件
│   └── ...
├── events/            # 事件检测和处理
│   ├── base.py        # 基础事件接口
│   ├── builtin.py     # 内置事件类型
│   └── custom.py      # 自定义事件
├── templates/         # 消息模板引擎
│   └── template_engine.py  # 统一模板引擎
├── claude_notifier/   # 新架构核心模块
│   ├── core/         # 核心功能
│   ├── intelligence/ # 智能限制组件
│   ├── monitoring/   # 监控系统
│   └── utils/        # 工具函数
└── utils/            # 工具函数（兼容性）
    ├── helpers.py    # 辅助函数
    ├── statistics.py # 统计收集
    └── ...
```

### 设计模式

1. **策略模式** - 通知渠道
2. **观察者模式** - 事件监听
3. **模板方法模式** - 消息格式化
4. **工厂模式** - 组件创建
5. **装饰器模式** - 功能增强

## 开发环境搭建

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/claude-code-notifier.git
cd claude-code-notifier
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
# 开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 可编辑安装
pip install -e .
```

### 4. 配置开发环境

```bash
# 复制配置模板
cp config/enhanced_config.yaml.template config/config.yaml

# 设置环境变量
export CLAUDE_NOTIFIER_DEBUG=1
export CLAUDE_NOTIFIER_LOG_LEVEL=DEBUG
```

## 代码规范

### Python 代码风格

```python
# 使用 Black 格式化
black src/ tests/

# 使用 isort 排序导入
isort src/ tests/

# 使用 flake8 检查代码质量
flake8 src/ tests/

# 使用 mypy 进行类型检查
mypy src/
```

### 文档字符串

```python
def send_notification(self, data: Dict[str, Any], template: str) -> bool:
    """发送通知消息
    
    Args:
        data: 通知数据字典
        template: 消息模板名称
        
    Returns:
        bool: 发送成功返回 True，失败返回 False
        
    Raises:
        NotificationError: 通知发送失败时抛出
        
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

### 类型注解

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
        """发送通知的抽象方法"""
        pass
```

## 测试框架

### 测试架构

```
tests/
├── conftest.py                    # pytest 配置
├── test_basic_units.py           # 基础单元测试
├── test_integration_flows.py     # 集成测试
├── test_performance_benchmarks.py # 性能测试
├── test_system_validation.py     # 系统验证测试
├── test_intelligence.py          # 智能组件测试
├── test_monitoring.py            # 监控系统测试
└── run_all_tests.py              # 测试运行器
```

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_basic_units.py -v

# 运行性能测试
python tests/test_performance_benchmarks.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html tests/
```

### 测试示例

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
        # 模拟成功响应
        mock_response = Mock()
        mock_response.json.return_value = {'errcode': 0}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # 执行测试
        result = self.channel.send_notification(
            {'project': 'test'}, 
            'template'
        )
        
        # 验证结果
        self.assertTrue(result)
        mock_post.assert_called_once()
```

## 新增通知渠道

### 1. 创建渠道类

```python
# src/channels/my_channel.py
from typing import Dict, Any
from .base import BaseChannel

class MyChannel(BaseChannel):
    """自定义通知渠道"""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.endpoint = config.get('endpoint')
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        return bool(self.api_key and self.endpoint)
    
    def send_notification(
        self, 
        data: Dict[str, Any], 
        template: str
    ) -> bool:
        """发送通知实现"""
        if not self.enabled or not self.validate_config():
            return False
        
        try:
            # 格式化消息
            message = self._format_message(data, template)
            
            # 发送请求
            response = self._send_request(message)
            
            # 处理响应
            return self._handle_response(response)
            
        except Exception as e:
            self._log_error(f"发送失败: {e}")
            return False
    
    def _format_message(self, data: Dict[str, Any], template: str) -> str:
        """格式化消息内容"""
        # 实现消息格式化逻辑
        pass
    
    def _send_request(self, message: str) -> Any:
        """发送 HTTP 请求"""
        # 实现请求发送逻辑
        pass
    
    def _handle_response(self, response: Any) -> bool:
        """处理响应结果"""
        # 实现响应处理逻辑
        pass
```

### 2. 注册通知渠道

```python
# src/channels/__init__.py
from .my_channel import MyChannel

AVAILABLE_CHANNELS = {
    'dingtalk': DingtalkChannel,
    'feishu': FeishuChannel,
    'my_channel': MyChannel,  # 添加新渠道
}
```

### 3. 添加配置模板

```yaml
# config/enhanced_config.yaml.template
channels:
  my_channel:
    enabled: false
    api_key: "YOUR_API_KEY"
    endpoint: "https://api.mychannel.com/notify"
    # 其他配置参数
```

### 4. 编写测试

```python
# tests/test_my_channel.py
import unittest
from channels.my_channel import MyChannel

class TestMyChannel(unittest.TestCase):
    def test_channel_initialization(self):
        config = {'enabled': True, 'api_key': 'test', 'endpoint': 'test'}
        channel = MyChannel(config)
        self.assertTrue(channel.enabled)
    
    def test_config_validation(self):
        # 测试配置验证逻辑
        pass
    
    def test_send_notification(self):
        # 测试通知发送逻辑
        pass
```

## 新增事件类型

### 1. 创建事件类

```python
# src/events/my_event.py
from typing import Dict, Any
from .base import BaseEvent, EventType, EventPriority

class MyCustomEvent(BaseEvent):
    """自定义事件类型"""
    
    def __init__(self):
        super().__init__()
        self.event_id = "my_custom_event"
        self.name = "我的自定义事件"
        self.event_type = EventType.CUSTOM
        self.priority = EventPriority.NORMAL
    
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """判断是否应该触发事件"""
        # 实现触发条件逻辑
        if context.get('trigger_condition'):
            return True
        return False
    
    def extract_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """从上下文提取通知数据"""
        return {
            'event_name': self.name,
            'timestamp': context.get('timestamp'),
            'custom_data': context.get('custom_data', {}),
            # 其他需要的数据
        }
    
    def get_template_name(self) -> str:
        """获取消息模板名称"""
        return "my_custom_template"
```

### 2. 注册事件类型

```python
# src/events/__init__.py
from .my_event import MyCustomEvent

AVAILABLE_EVENTS = {
    'sensitive_operation': SensitiveOperationEvent,
    'task_completion': TaskCompletionEvent,
    'my_custom_event': MyCustomEvent,  # 添加新事件
}
```

### 3. 添加消息模板

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
          
          **时间:** {{ timestamp }}
          **数据:** {{ custom_data }}
    
    feishu:
      msg_type: "text"
      content:
        text: "{{ event_name }}: {{ custom_data }}"
```

## 智能组件开发

### 操作门控 (Operation Gate)

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
    """操作门控，智能控制敏感操作"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.blocked_patterns = config.get('blocked_patterns', [])
        self.protected_paths = config.get('protected_paths', [])
    
    def should_allow_operation(
        self, 
        request: OperationRequest
    ) -> Tuple[OperationResult, str]:
        """评估操作是否应该被允许"""
        
        # 检查阻止模式
        for pattern in self.blocked_patterns:
            if pattern in request.command:
                return (
                    OperationResult.BLOCKED, 
                    f"操作包含阻止模式: {pattern}"
                )
        
        # 检查保护路径
        for path in self.protected_paths:
            if path in request.command:
                return (
                    OperationResult.REQUIRES_CONFIRMATION,
                    f"操作涉及保护路径: {path}"
                )
        
        return (OperationResult.ALLOWED, "操作被允许")
```

### 通知限流 (Notification Throttle)

```python
# src/claude_notifier/utils/notification_throttle.py
import time
from collections import defaultdict, deque
from typing import Dict, Any

class NotificationThrottle:
    """通知限流，防止通知轰炸"""
    
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
        """检查是否应该发送通知"""
        current_time = time.time()
        
        # 检查冷却期
        if self._is_in_cooldown(channel, current_time):
            return False
        
        # 检查频率限制
        if not self._check_rate_limit(channel, current_time):
            self._set_cooldown(channel, current_time)
            return False
        
        # 记录通知
        self._record_notification(channel, current_time)
        return True
    
    def _check_rate_limit(self, channel: str, current_time: float) -> bool:
        """检查速率限制"""
        # 清理过期记录
        self._cleanup_old_records(channel, current_time)
        
        # 检查每分钟限制
        if len(self.minute_counter[channel]) >= self.max_per_minute:
            return False
        
        # 检查每小时限制
        if len(self.hour_counter[channel]) >= self.max_per_hour:
            return False
        
        return True
```

## 监控系统开发

### 统计收集器

```python
# src/claude_notifier/monitoring/statistics.py
import json
import time
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict, Counter

class StatisticsManager:
    """统计数据收集和管理"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.stats_file = Path(config.get('stats_file', '~/.claude-notifier/stats.json')).expanduser()
        self.retention_days = config.get('retention_days', 30)
        
        self.load_statistics()
    
    def record_event(self, event_type: str, channel: str, success: bool, metadata: Dict[str, Any] = None):
        """记录事件统计"""
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
        """获取统计摘要"""
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

## 性能优化

### 异步处理

```python
import asyncio
import aiohttp
from typing import List, Dict, Any

class AsyncNotificationSender:
    """异步通知发送器"""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def send_notifications(
        self, 
        notifications: List[Dict[str, Any]]
    ) -> List[bool]:
        """批量异步发送通知"""
        tasks = [
            self._send_single_notification(notification)
            for notification in notifications
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [isinstance(result, bool) and result for result in results]
    
    async def _send_single_notification(self, notification: Dict[str, Any]) -> bool:
        """发送单个通知"""
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

### 缓存机制

```python
from functools import lru_cache
import hashlib
import pickle
from typing import Any

class TemplateCache:
    """模板缓存系统"""
    
    def __init__(self, max_size: int = 128):
        self.cache = {}
        self.max_size = max_size
        self.access_count = {}
    
    def get(self, template_key: str, data: Dict[str, Any]) -> str:
        """获取缓存的模板"""
        cache_key = self._generate_cache_key(template_key, data)
        
        if cache_key in self.cache:
            self.access_count[cache_key] = self.access_count.get(cache_key, 0) + 1
            return self.cache[cache_key]
        
        return None
    
    def put(self, template_key: str, data: Dict[str, Any], rendered: str):
        """存储渲染结果"""
        cache_key = self._generate_cache_key(template_key, data)
        
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[cache_key] = rendered
        self.access_count[cache_key] = 1
    
    def _generate_cache_key(self, template_key: str, data: Dict[str, Any]) -> str:
        """生成缓存键"""
        data_str = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        hash_obj = hashlib.md5(f"{template_key}:{data_str}".encode())
        return hash_obj.hexdigest()
```

## 调试和诊断

### 调试工具

```bash
# 启用调试模式
export CLAUDE_NOTIFIER_DEBUG=1

# 详细日志
export CLAUDE_NOTIFIER_LOG_LEVEL=DEBUG

# 性能分析
python -m cProfile -o profile.stats scripts/test_performance.py

# 内存分析
python -m memory_profiler scripts/test_memory.py
```

### 诊断命令

```bash
# 系统健康检查
claude-notifier health

# 配置验证
claude-notifier config validate

# 渠道连接测试
claude-notifier test --all-channels

# 性能基准测试
claude-notifier benchmark

# 统计报告
claude-notifier stats --days 7
```

## 贡献指南

### 1. Fork 和分支

```bash
# Fork 项目到你的账户
# 克隆 fork 的仓库
git clone https://github.com/your-username/claude-code-notifier.git

# 创建功能分支
git checkout -b feature/my-new-feature
```

### 2. 开发流程

1. 编写代码和测试
2. 运行完整测试套件
3. 更新文档
4. 提交 Pull Request

### 3. Pull Request 标准

- 清晰的标题和描述
- 包含测试用例
- 通过所有 CI 检查
- 更新相关文档
- 遵循代码规范

### 4. 代码审查

所有 Pull Request 需要通过代码审查：
- 功能正确性
- 代码质量
- 测试覆盖率
- 性能影响
- 安全性考虑

## 发布流程

### 版本号管理

使用语义化版本号（Semantic Versioning）：
- `MAJOR.MINOR.PATCH`
- `1.0.0` - 重大更新
- `1.1.0` - 新功能
- `1.1.1` - 问题修复

### 发布步骤

```bash
# 1. 更新版本号
echo "1.2.0" > src/__version__.py

# 2. 更新 CHANGELOG
vim CHANGELOG.md

# 3. 提交版本更新
git add .
git commit -m "chore: bump version to 1.2.0"
git tag v1.2.0

# 4. 推送到远程
git push origin main --tags

# 5. 构建和发布
python setup.py sdist bdist_wheel
twine upload dist/*
```

## 问题反馈

如果您在开发过程中遇到问题：

1. 检查 [常见问题](../README.md#故障排除)
2. 搜索 [GitHub Issues](https://github.com/your-repo/claude-code-notifier/issues)
3. 创建新的 Issue，包含：
   - 详细的问题描述
   - 重现步骤
   - 环境信息
   - 错误日志

## 技术支持

- 📧 技术咨询: dev@your-company.com
- 💬 开发者社区: [Discord/Slack 链接]
- 📖 API 文档: [API 文档链接]
- 🎥 开发视频教程: [视频教程链接]