#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pytest配置文件和测试夹具
为pytest风格的测试提供通用配置和夹具
"""

import pytest
import os
import sys
import tempfile
import yaml
from pathlib import Path

# 添加项目路径和src路径到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))


@pytest.fixture(scope="session")
def project_root():
    """项目根目录路径"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_config_dir():
    """临时测试配置目录"""
    temp_dir = tempfile.mkdtemp(prefix="claude_notifier_test_")
    yield temp_dir
    
    # 清理
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def test_config_file(test_config_dir):
    """测试配置文件"""
    config_file = os.path.join(test_config_dir, "config.yaml")
    
    test_config = {
        'channels': {
            'dingtalk': {
                'enabled': False,
                'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=test',
                'secret': 'test_secret'
            },
            'email': {
                'enabled': False,
                'smtp_host': 'smtp.gmail.com',
                'smtp_port': 587,
                'sender': 'test@example.com',
                'password': 'test_password',
                'receivers': ['receiver@example.com']
            }
        },
        'events': {
            'builtin': {
                'sensitive_operation': {'enabled': True},
                'task_completion': {'enabled': True},
                'error_occurred': {'enabled': True}
            },
            'custom': {}
        },
        'intelligent_limiting': {
            'enabled': True,
            'operation_gate': {
                'enabled': True,
                'strategies': {
                    'critical_operations': {
                        'type': 'hard_block',
                        'patterns': ['sudo rm -rf', 'DROP TABLE']
                    }
                }
            },
            'notification_throttle': {
                'enabled': True,
                'limits': {
                    'per_minute': 10,
                    'per_hour': 100
                }
            },
            'message_grouper': {
                'enabled': True,
                'strategies': {
                    'similarity_threshold': 0.8
                }
            },
            'cooldown_manager': {
                'enabled': True,
                'cooldown_rules': [
                    {
                        'name': 'global_cooldown',
                        'scope': 'global',
                        'type': 'static',
                        'duration': 60
                    }
                ]
            }
        },
        'monitoring': {
            'enabled': True,
            'statistics': {
                'enabled': True,
                'file_path': os.path.join(test_config_dir, 'stats.json')
            },
            'health_check': {
                'enabled': True,
                'check_interval': 60
            },
            'performance': {
                'enabled': True,
                'metrics': ['cpu', 'memory']
            }
        },
        'notifications': {
            'default_channels': ['dingtalk'],
            'templates': {
                'default': 'basic_template'
            }
        },
        'advanced': {
            'logging': {
                'level': 'INFO',
                'file': os.path.join(test_config_dir, 'test.log')
            }
        }
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(test_config, f, default_flow_style=False)
        
    return config_file


@pytest.fixture(scope="function")
def temp_stats_file():
    """临时统计文件"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    temp_file.close()
    
    yield temp_file.name
    
    # 清理
    try:
        os.unlink(temp_file.name)
    except FileNotFoundError:
        pass


@pytest.fixture(scope="function") 
def mock_notification_channels():
    """模拟通知渠道"""
    from unittest.mock import Mock
    
    channels = {
        'dingtalk': Mock(),
        'email': Mock(),
        'telegram': Mock()
    }
    
    # 配置mock行为
    for channel_name, channel_mock in channels.items():
        channel_mock.validate_config.return_value = True
        channel_mock.send_notification.return_value = True
        channel_mock.get_max_content_length.return_value = 10000
        
    return channels


@pytest.fixture(scope="function")
def sample_notification_data():
    """示例通知数据"""
    return {
        'project': 'test-project',
        'operation': 'test operation',
        'timestamp': '2025-08-20 12:00:00',
        'user': 'test-user',
        'command': 'test command',
        'status': 'success'
    }


@pytest.fixture(scope="function")
def sample_event_context():
    """示例事件上下文"""
    return {
        'tool_input': 'test command',
        'event_type': 'test_event',
        'project': 'test-project',
        'timestamp': '2025-08-20 12:00:00',
        'user': 'test-user'
    }


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """自动设置测试环境"""
    # 设置测试环境变量
    os.environ['CLAUDE_NOTIFIER_TEST'] = '1'
    os.environ['CLAUDE_NOTIFIER_LOG_LEVEL'] = 'DEBUG'
    
    yield
    
    # 清理环境变量
    os.environ.pop('CLAUDE_NOTIFIER_TEST', None)
    os.environ.pop('CLAUDE_NOTIFIER_LOG_LEVEL', None)


@pytest.fixture(scope="function")
def capture_logs():
    """捕获日志输出"""
    import logging
    from io import StringIO
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    # 获取根日志记录器
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    yield log_capture
    
    # 清理
    logger.removeHandler(handler)
    

def _is_component_available(component: str) -> bool:
    """检查组件是否可用"""
    try:
        if component == 'intelligence':
            from claude_notifier.utils.operation_gate import OperationGate
            return True
        elif component == 'monitoring':
            from claude_notifier.monitoring.statistics import StatisticsManager
            return True
        elif component == 'cli':
            from claude_notifier.cli.main import cli
            return True
        else:
            return False
    except ImportError:
        return False


class TestMarkers:
    """测试标记类"""
    
    # 组件可用性标记
    INTELLIGENCE = pytest.mark.skipif(
        not _is_component_available('intelligence'),
        reason="智能组件不可用"
    )
    
    MONITORING = pytest.mark.skipif(
        not _is_component_available('monitoring'),
        reason="监控组件不可用"
    )
    
    CLI = pytest.mark.skipif(
        not _is_component_available('cli'),
        reason="CLI组件不可用"
    )
    
    # 测试类型标记
    UNIT = pytest.mark.unit
    INTEGRATION = pytest.mark.integration
    E2E = pytest.mark.e2e
    
    # 性能标记
    SLOW = pytest.mark.slow
    FAST = pytest.mark.fast
    
    # 依赖标记
    REQUIRES_CONFIG = pytest.mark.requires_config
    REQUIRES_NETWORK = pytest.mark.requires_network


# 导出常用的标记
intelligence = TestMarkers.INTELLIGENCE
monitoring = TestMarkers.MONITORING
cli = TestMarkers.CLI
unit = TestMarkers.UNIT
integration = TestMarkers.INTEGRATION
e2e = TestMarkers.E2E
slow = TestMarkers.SLOW
fast = TestMarkers.FAST


# pytest配置函数
def pytest_configure(config):
    """pytest配置"""
    # 注册自定义标记
    config.addinivalue_line("markers", "intelligence: 智能组件测试")
    config.addinivalue_line("markers", "monitoring: 监控组件测试")
    config.addinivalue_line("markers", "cli: CLI组件测试")
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "e2e: 端到端测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "fast: 快速测试")
    config.addinivalue_line("markers", "requires_config: 需要配置文件")
    config.addinivalue_line("markers", "requires_network: 需要网络连接")


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 为没有标记的测试自动添加fast标记
    for item in items:
        if not any(mark.name in ['slow', 'fast'] for mark in item.iter_markers()):
            item.add_marker(pytest.mark.fast)


def pytest_runtest_setup(item):
    """测试运行前设置"""
    # 检查环境依赖
    for mark in item.iter_markers():
        if mark.name == "requires_network":
            # 可以添加网络检查逻辑
            pass
        elif mark.name == "requires_config":
            # 可以添加配置文件检查逻辑
            pass


# pytest报告钩子（仅在安装了 pytest-html 时启用）
try:
    import pytest_html  # noqa: F401

    def pytest_html_report_title(report):
        """自定义HTML报告标题"""
        report.title = "Claude Code Notifier 测试报告"

    def pytest_html_results_summary(prefix, summary, postfix):
        """自定义HTML报告摘要"""
        prefix.extend([
            "<h2>Claude Code Notifier 测试套件</h2>",
            "<p>轻量级架构，可选组件优雅降级</p>"
        ])
except Exception:
    # 未安装 pytest-html 时跳过这些hook，避免未知钩子报错
    pass
    
    
# 命令行选项
def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--component",
        action="store",
        default=None,
        help="指定测试组件: intelligence, monitoring, cli, all"
    )
    
    parser.addoption(
        "--skip-slow",
        action="store_true",
        default=False,
        help="跳过慢速测试"
    )


def pytest_runtest_call(item):
    """测试运行时调用（兼容pytest新版hookspec，参数命名为 item）"""
    # 可以添加测试运行时的逻辑
    pass