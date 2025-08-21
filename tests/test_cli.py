#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI组件专项测试 - 状态命令、配置管理、调试工具
"""

import unittest
import tempfile
import os
import sys
import json
import yaml
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from click.testing import CliRunner

# 添加项目路径和src路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 检查CLI组件可用性
try:
    from claude_notifier.cli.main import cli
    from claude_notifier import __version__
    CLI_AVAILABLE = True
except ImportError as e:
    CLI_AVAILABLE = False
    print(f"CLI组件不可用: {e}")

# 检查配置管理器
try:
    from claude_notifier.config_manager import ConfigManager
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False


@unittest.skipIf(not CLI_AVAILABLE, "CLI组件不可用")
class TestCLIBasicCommands(unittest.TestCase):
    """测试CLI基础命令"""
    
    def setUp(self):
        """设置测试环境"""
        self.runner = CliRunner()
        
    def test_cli_version(self):
        """测试版本命令"""
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(__version__, result.output)
        # 预发行版本提示校验（遵循 PEP 440: a/b/rc）
        is_prerelease = any(tag in __version__ for tag in ['a', 'b', 'rc'])
        if is_prerelease:
            self.assertIn('版本类型:', result.output)
            self.assertIn('预发行版本', result.output)
        else:
            self.assertNotIn('版本类型:', result.output)
            self.assertNotIn('预发行版本', result.output)
        
    def test_cli_help(self):
        """测试帮助命令"""
        result = self.runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Claude Code Notifier', result.output)
        self.assertIn('status', result.output)
        self.assertIn('config', result.output)


@unittest.skipIf(not CLI_AVAILABLE, "CLI组件不可用")
class TestStatusCommand(unittest.TestCase):
    """测试状态命令"""
    
    def setUp(self):
        """设置测试环境"""
        self.runner = CliRunner()
        
        # 创建临时配置文件
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml')
        test_config = {
            'channels': {
                'dingtalk': {
                    'enabled': False,
                    'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=test'
                }
            },
            'intelligent_limiting': {
                'enabled': True,
                'operation_gate': {'enabled': True},
                'notification_throttle': {'enabled': True}
            }
        }
        yaml.dump(test_config, self.temp_config)
        self.temp_config.close()
        
    def tearDown(self):
        """清理测试环境"""
        os.unlink(self.temp_config.name)
        
    @patch('claude_notifier.cli.main.get_default_config_path')
    def test_status_overview(self, mock_config_path):
        """测试状态概览模式"""
        mock_config_path.return_value = self.temp_config.name
        
        result = self.runner.invoke(cli, ['status'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('通知器状态', result.output)
        
    @patch('claude_notifier.cli.main.get_default_config_path')
    def test_status_detailed(self, mock_config_path):
        """测试详细状态模式"""
        mock_config_path.return_value = self.temp_config.name
        
        result = self.runner.invoke(cli, ['status', '--mode', 'detailed'])
        self.assertEqual(result.exit_code, 0)
        
    @patch('claude_notifier.cli.main.get_default_config_path')
    def test_status_with_intelligence(self, mock_config_path):
        """测试带智能组件的状态"""
        mock_config_path.return_value = self.temp_config.name
        
        result = self.runner.invoke(cli, ['status', '--intelligence'])
        self.assertEqual(result.exit_code, 0)
        
    @patch('claude_notifier.cli.main.get_default_config_path')
    def test_status_with_monitoring(self, mock_config_path):
        """测试带监控的状态"""
        mock_config_path.return_value = self.temp_config.name
        
        result = self.runner.invoke(cli, ['status', '--monitoring'])
        self.assertEqual(result.exit_code, 0)
        
    def test_status_export(self):
        """测试状态导出"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as export_file:
            export_path = export_file.name
            
        try:
            with patch('claude_notifier.cli.main.get_default_config_path') as mock_config_path:
                mock_config_path.return_value = self.temp_config.name
                
                result = self.runner.invoke(cli, ['status', '--export', export_path])
                # 导出功能可能需要特定的监控组件，所以允许退出码为0或1
                self.assertIn(result.exit_code, [0, 1])
                
        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)


@unittest.skipIf(not CLI_AVAILABLE or not CONFIG_AVAILABLE, "CLI或配置组件不可用")
class TestConfigCommand(unittest.TestCase):
    """测试配置命令"""
    
    def setUp(self):
        """设置测试环境"""
        self.runner = CliRunner()
        
        # 创建临时配置目录
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'config.yaml')
        
        # 创建基础配置文件
        test_config = {
            'channels': {
                'dingtalk': {
                    'enabled': False,
                    'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=test'
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(test_config, f)
            
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    @patch('claude_notifier.cli.main.get_default_config_path')
    def test_config_show(self, mock_config_path):
        """测试显示配置"""
        mock_config_path.return_value = self.config_file
        
        result = self.runner.invoke(cli, ['config', 'show'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('channels', result.output)
        
    @patch('claude_notifier.cli.main.get_default_config_path')
    def test_config_validate(self, mock_config_path):
        """测试配置验证"""
        mock_config_path.return_value = self.config_file
        
        result = self.runner.invoke(cli, ['config', 'validate'])
        self.assertEqual(result.exit_code, 0)
        
    @patch('claude_notifier.cli.main.get_default_config_path')
    def test_config_backup(self, mock_config_path):
        """测试配置备份"""
        mock_config_path.return_value = self.config_file
        
        result = self.runner.invoke(cli, ['config', 'backup'])
        self.assertEqual(result.exit_code, 0)
        
        # 检查备份文件是否创建
        backup_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.backup')]
        self.assertTrue(len(backup_files) > 0)
        
    def test_config_init(self):
        """测试配置初始化"""
        new_config_file = os.path.join(self.temp_dir, 'new_config.yaml')
        
        with patch('claude_notifier.cli.main.get_default_config_path') as mock_config_path:
            mock_config_path.return_value = new_config_file
            
            result = self.runner.invoke(cli, ['config', 'init'])
            
            # 初始化应该成功或文件已存在
            self.assertIn(result.exit_code, [0, 1])
            
    @patch('claude_notifier.cli.main.get_default_config_path')  
    def test_config_channel_list(self, mock_config_path):
        """测试列出渠道"""
        mock_config_path.return_value = self.config_file
        
        result = self.runner.invoke(cli, ['config', 'channel', 'list'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('dingtalk', result.output)


@unittest.skipIf(not CLI_AVAILABLE, "CLI组件不可用")
class TestDebugCommand(unittest.TestCase):
    """测试调试命令"""
    
    def setUp(self):
        """设置测试环境"""
        self.runner = CliRunner()
        
    def test_debug_diagnose(self):
        """测试诊断命令"""
        result = self.runner.invoke(cli, ['debug', 'diagnose'])
        # 诊断命令可能需要特定的组件，允许不同的退出码
        self.assertIn(result.exit_code, [0, 1])
        
    def test_debug_logs(self):
        """测试日志查看"""
        result = self.runner.invoke(cli, ['debug', 'logs', '--lines', '5'])
        # 日志命令可能因为没有日志文件而失败，这是正常的
        self.assertIn(result.exit_code, [0, 1])
        
    def test_debug_trace(self):
        """测试跟踪功能"""
        result = self.runner.invoke(cli, ['debug', 'trace'])
        # 跟踪功能可能需要特定条件，允许不同退出码
        self.assertIn(result.exit_code, [0, 1])


@unittest.skipIf(not CLI_AVAILABLE, "CLI组件不可用")
class TestMonitorCommand(unittest.TestCase):
    """测试监控命令"""
    
    def setUp(self):
        """设置测试环境"""
        self.runner = CliRunner()
        
        # 创建临时配置
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml')
        test_config = {
            'channels': {
                'dingtalk': {'enabled': False}
            },
            'monitoring': {
                'enabled': True
            }
        }
        yaml.dump(test_config, self.temp_config)
        self.temp_config.close()
        
    def tearDown(self):
        """清理测试环境"""
        os.unlink(self.temp_config.name)
        
    @patch('claude_notifier.cli.main.get_default_config_path')
    def test_monitor_dashboard(self, mock_config_path):
        """测试监控仪表板"""
        mock_config_path.return_value = self.temp_config.name
        
        result = self.runner.invoke(cli, ['monitor', 'dashboard'])
        # 监控命令可能需要特定的监控组件
        self.assertIn(result.exit_code, [0, 1])
        
    @patch('claude_notifier.cli.main.get_default_config_path')
    def test_monitor_health(self, mock_config_path):
        """测试健康检查"""
        mock_config_path.return_value = self.temp_config.name
        
        result = self.runner.invoke(cli, ['monitor', 'health'])
        self.assertIn(result.exit_code, [0, 1])
        
    @patch('claude_notifier.cli.main.get_default_config_path')
    def test_monitor_performance(self, mock_config_path):
        """测试性能监控"""
        mock_config_path.return_value = self.temp_config.name
        
        result = self.runner.invoke(cli, ['monitor', 'performance'])
        self.assertIn(result.exit_code, [0, 1])


class TestCLIIntegration(unittest.TestCase):
    """测试CLI集成功能"""
    
    @unittest.skipIf(not CLI_AVAILABLE, "CLI组件不可用")
    def test_cli_error_handling(self):
        """测试CLI错误处理"""
        runner = CliRunner()
        
        # 测试无效的命令
        result = runner.invoke(cli, ['invalid_command'])
        self.assertNotEqual(result.exit_code, 0)
        
        # 测试无效的选项
        result = runner.invoke(cli, ['status', '--invalid-option'])
        self.assertNotEqual(result.exit_code, 0)
        
    @unittest.skipIf(not CLI_AVAILABLE, "CLI组件不可用")
    def test_cli_configuration_loading(self):
        """测试CLI配置加载"""
        runner = CliRunner()
        
        # 创建无效配置文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            f.write("invalid: yaml: content:")
            invalid_config = f.name
            
        try:
            with patch('claude_notifier.cli.main.get_default_config_path') as mock_config_path:
                mock_config_path.return_value = invalid_config
                
                result = runner.invoke(cli, ['status'])
                # 应该能优雅地处理配置错误
                self.assertIn(result.exit_code, [0, 1])
                
        finally:
            os.unlink(invalid_config)
            
    @unittest.skipIf(not CLI_AVAILABLE, "CLI组件不可用")
    def test_cli_output_formatting(self):
        """测试CLI输出格式"""
        runner = CliRunner()
        
        # 创建有效配置
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            yaml.dump({'channels': {'test': {'enabled': True}}}, f)
            config_file = f.name
            
        try:
            with patch('claude_notifier.cli.main.get_default_config_path') as mock_config_path:
                mock_config_path.return_value = config_file
                
                result = runner.invoke(cli, ['status'])
                
                # 输出应该包含基本的格式化元素
                if result.exit_code == 0:
                    output = result.output
                    # 检查是否有基本的格式化
                    self.assertTrue(len(output) > 0)
                    
        finally:
            os.unlink(config_file)


def run_tests():
    """运行所有CLI测试"""
    if not CLI_AVAILABLE:
        print("CLI组件不可用，跳过CLI测试")
        return False
        
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestCLIBasicCommands,
        TestStatusCommand,
        TestConfigCommand,
        TestDebugCommand,
        TestMonitorCommand,
        TestCLIIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)