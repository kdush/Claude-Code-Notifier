#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
综合测试运行器 - 运行所有测试套件
测试基础设施的统一入口点
"""

import os
import sys
import unittest
import time
from pathlib import Path

# 添加项目路径和src路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 导入所有测试模块
try:
    from test_comprehensive import run_tests as run_comprehensive_tests
    COMPREHENSIVE_AVAILABLE = True
except ImportError as e:
    COMPREHENSIVE_AVAILABLE = False
    print(f"综合测试模块不可用: {e}")

try:
    from test_events import run_tests as run_events_tests
    EVENTS_AVAILABLE = True
except ImportError as e:
    EVENTS_AVAILABLE = False
    print(f"事件测试模块不可用: {e}")

try:
    from test_monitoring import run_tests as run_monitoring_tests
    MONITORING_AVAILABLE = True
except ImportError as e:
    MONITORING_AVAILABLE = False
    print(f"监控测试模块不可用: {e}")

try:
    from test_cli import run_tests as run_cli_tests
    CLI_AVAILABLE = True
except ImportError as e:
    CLI_AVAILABLE = False
    print(f"CLI测试模块不可用: {e}")

try:
    from test_intelligence import run_tests as run_intelligence_tests
    INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    INTELLIGENCE_AVAILABLE = False
    print(f"智能组件测试模块不可用: {e}")


class TestSuiteResult:
    """测试套件结果"""
    
    def __init__(self, name: str, success: bool, duration: float, error: str = None):
        self.name = name
        self.success = success
        self.duration = duration
        self.error = error


class ComprehensiveTestRunner:
    """综合测试运行器"""
    
    def __init__(self):
        self.results = []
        
    def run_test_suite(self, name: str, test_function, available: bool) -> TestSuiteResult:
        """运行单个测试套件"""
        print(f"\n{'='*60}")
        print(f"运行测试套件: {name}")
        print(f"{'='*60}")
        
        if not available:
            print(f"⚠️  {name} 不可用，跳过测试")
            return TestSuiteResult(name, False, 0.0, "模块不可用")
            
        start_time = time.time()
        
        try:
            success = test_function()
            duration = time.time() - start_time
            
            if success:
                print(f"✅ {name} 测试通过 (耗时: {duration:.2f}秒)")
                return TestSuiteResult(name, True, duration)
            else:
                print(f"❌ {name} 测试失败 (耗时: {duration:.2f}秒)")
                return TestSuiteResult(name, False, duration, "测试失败")
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"💥 {name} 测试出错: {str(e)} (耗时: {duration:.2f}秒)")
            return TestSuiteResult(name, False, duration, str(e))
            
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 开始运行 Claude Code Notifier 完整测试套件")
        print(f"Python版本: {sys.version}")
        print(f"工作目录: {os.getcwd()}")
        print(f"项目路径: {Path(__file__).parent.parent}")
        
        overall_start = time.time()
        
        # 定义测试套件
        test_suites = [
            ("综合功能测试", run_comprehensive_tests, COMPREHENSIVE_AVAILABLE),
            ("事件系统测试", run_events_tests, EVENTS_AVAILABLE),
            ("智能组件测试", run_intelligence_tests, INTELLIGENCE_AVAILABLE),
            ("监控系统测试", run_monitoring_tests, MONITORING_AVAILABLE),
            ("CLI组件测试", run_cli_tests, CLI_AVAILABLE),
        ]
        
        # 运行所有测试套件
        for name, test_func, available in test_suites:
            result = self.run_test_suite(name, test_func, available)
            self.results.append(result)
            
        overall_duration = time.time() - overall_start
        
        # 生成总结报告
        self.generate_summary_report(overall_duration)
        
        # 返回是否所有测试都成功
        return all(result.success for result in self.results if result.error != "模块不可用")
        
    def generate_summary_report(self, total_duration: float):
        """生成总结报告"""
        print(f"\n{'='*60}")
        print("🎯 测试总结报告")
        print(f"{'='*60}")
        
        total_suites = len(self.results)
        successful_suites = sum(1 for r in self.results if r.success)
        failed_suites = sum(1 for r in self.results if not r.success and r.error != "模块不可用")
        skipped_suites = sum(1 for r in self.results if r.error == "模块不可用")
        
        print(f"📊 总体统计:")
        print(f"   - 总测试套件数: {total_suites}")
        print(f"   - 成功: {successful_suites}")
        print(f"   - 失败: {failed_suites}")
        print(f"   - 跳过: {skipped_suites}")
        print(f"   - 总耗时: {total_duration:.2f}秒")
        
        if successful_suites == (total_suites - skipped_suites) and (total_suites - skipped_suites) > 0:
            print(f"\n🎉 所有可用测试套件均通过!")
        elif failed_suites > 0:
            print(f"\n⚠️  {failed_suites} 个测试套件失败")
            
        print(f"\n📋 详细结果:")
        for result in self.results:
            status_icon = "✅" if result.success else ("⚠️" if result.error == "模块不可用" else "❌")
            status_text = "通过" if result.success else ("跳过" if result.error == "模块不可用" else "失败")
            
            print(f"   {status_icon} {result.name:<20} {status_text:<6} ({result.duration:.2f}s)")
            
            if result.error and result.error != "模块不可用":
                print(f"      错误: {result.error}")
                
        # 环境信息
        print(f"\n🔧 环境信息:")
        print(f"   - Python: {sys.version.split()[0]}")
        print(f"   - 工作目录: {os.getcwd()}")
        print(f"   - 可用组件:")
        
        components = [
            ("综合功能", COMPREHENSIVE_AVAILABLE),
            ("事件系统", EVENTS_AVAILABLE),
            ("智能组件", INTELLIGENCE_AVAILABLE),
            ("监控系统", MONITORING_AVAILABLE),
            ("CLI组件", CLI_AVAILABLE)
        ]
        
        for name, available in components:
            status = "✅" if available else "❌"
            print(f"     {status} {name}")
            
        # 建议
        if failed_suites > 0:
            print(f"\n💡 建议:")
            print(f"   1. 检查失败的测试套件详细输出")
            print(f"   2. 确保所有依赖正确安装")
            print(f"   3. 验证配置文件格式正确")
            
        if skipped_suites > 0:
            print(f"\n📦 跳过的组件:")
            print(f"   某些可选组件不可用，这是正常的")
            print(f"   轻量级架构支持可选组件优雅降级")


def create_test_config():
    """创建测试配置文件"""
    config_dir = Path.home() / '.claude-notifier'
    config_file = config_dir / 'config.yaml'
    
    if not config_file.exists():
        print("📝 创建测试配置文件...")
        
        config_dir.mkdir(exist_ok=True)
        
        test_config = """channels:
  dingtalk:
    enabled: false  # 测试时不发送真实通知
    webhook: 'https://oapi.dingtalk.com/robot/send?access_token=test'
    secret: ''

intelligent_limiting:
  enabled: true
  operation_gate:
    enabled: true
  notification_throttle:
    enabled: true
  message_grouper:
    enabled: true
  cooldown_manager:
    enabled: true

notifications:
  default_channels: ['dingtalk']

advanced:
  logging:
    level: 'info'
"""
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(test_config)
            
        print(f"✅ 测试配置文件已创建: {config_file}")
        
    return config_file


def main():
    """主函数"""
    # 创建测试配置
    try:
        config_file = create_test_config()
        print(f"📁 使用配置文件: {config_file}")
    except Exception as e:
        print(f"⚠️  创建测试配置失败: {e}")
        
    # 运行测试
    runner = ComprehensiveTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print(f"\n🎉 所有测试通过!")
        return 0
    else:
        print(f"\n❌ 部分测试失败")
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试运行器出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)