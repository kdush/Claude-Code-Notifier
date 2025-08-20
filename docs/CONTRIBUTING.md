# 🤝 贡献指南

感谢您对 Claude Code Notifier 项目的关注！本指南将帮助您了解如何为项目做出贡献。

## 🎯 贡献方式

### 代码贡献
- 🐛 修复 Bug
- ✨ 添加新功能
- 🚀 性能优化
- 📝 改进文档
- 🧪 增加测试覆盖率

### 非代码贡献
- 🐛 报告问题
- 💡 功能建议
- 📖 文档翻译
- 🎨 UI/UX 设计
- 📢 推广项目

## 🚀 快速开始

### 1. 环境准备

```bash
# 系统要求
- Python 3.8+
- Git
- Claude Code (最新版本)

# 克隆项目
git clone https://github.com/your-repo/claude-code-notifier.git
cd claude-code-notifier

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装开发依赖
pip install -r requirements-dev.txt
pip install -e .
```

### 2. 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行代码质量检查
flake8 src/ tests/
black --check src/ tests/
mypy src/

# 运行性能测试
python tests/test_performance_benchmarks.py
```

### 3. 验证安装

```bash
# 测试命令行工具
claude-notifier --version

# 运行集成测试
python tests/run_all_tests.py
```

## 📋 开发规范

### 代码风格

我们使用以下工具确保代码质量：

```bash
# 代码格式化
black src/ tests/

# 导入排序
isort src/ tests/

# 代码质量检查
flake8 src/ tests/

# 类型检查
mypy src/
```

### 提交信息规范

使用 [Conventional Commits](https://conventionalcommits.org/) 格式：

```
<类型>[可选 范围]: <描述>

[可选 正文]

[可选 脚注]
```

**提交类型：**
- `feat`: 新功能
- `fix`: 问题修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例：**
```bash
git commit -m "feat(channels): add WeChat Work support"
git commit -m "fix(dingtalk): resolve signature validation issue"
git commit -m "docs: update configuration guide"
```

### 分支管理

```bash
# 主分支
main          # 稳定发布版本
develop       # 开发分支

# 功能分支
feature/xxx   # 新功能开发
bugfix/xxx    # 问题修复
hotfix/xxx    # 紧急修复
release/xxx   # 发布准备
```

## 🐛 问题报告

### 报告 Bug

使用 [Bug 报告模板](https://github.com/your-repo/claude-code-notifier/issues/new?template=bug_report.md)：

```markdown
**Bug 描述**
简明扼要地描述这个 bug。

**重现步骤**
1. 执行 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

**期望行为**
描述您期望发生的情况。

**实际行为**
描述实际发生的情况。

**环境信息**
- OS: [例如 macOS 12.6]
- Python 版本: [例如 3.9.7]
- Claude Code 版本: [例如 1.2.3]
- 项目版本: [例如 0.8.5]

**附加信息**
- 日志文件
- 配置文件
- 错误截图
```

### 功能建议

使用 [功能请求模板](https://github.com/your-repo/claude-code-notifier/issues/new?template=feature_request.md)：

```markdown
**功能描述**
简明扼要地描述您希望的功能。

**问题背景**
描述这个功能要解决的问题。

**解决方案**
描述您希望的解决方案。

**替代方案**
描述您考虑过的其他解决方案。

**附加信息**
其他相关信息或截图。
```

## 💻 开发工作流

### 1. 创建功能分支

```bash
# 从 develop 分支创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/my-awesome-feature
```

### 2. 开发和测试

```bash
# 编写代码
# 编写测试
# 运行测试确保通过
python -m pytest tests/ -v

# 运行代码质量检查
make lint  # 或手动运行 flake8, black, mypy
```

### 3. 提交代码

```bash
# 添加更改
git add .

# 提交（使用规范的提交信息）
git commit -m "feat(channels): add Slack notification support"

# 推送到远程分支
git push origin feature/my-awesome-feature
```

### 4. 创建 Pull Request

1. 访问 GitHub 仓库
2. 点击 "Compare & pull request"
3. 填写 PR 模板
4. 等待代码审查

### Pull Request 模板

```markdown
## 变更描述
简要描述此 PR 的更改。

## 变更类型
- [ ] 🐛 Bug 修复
- [ ] ✨ 新功能
- [ ] 🔄 代码重构
- [ ] 📝 文档更新
- [ ] 🧪 测试增强
- [ ] 🚀 性能改进

## 测试
- [ ] 现有测试通过
- [ ] 添加了新的测试
- [ ] 手动测试通过

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 自测试所有更改
- [ ] 更新了相关文档
- [ ] 没有引入破坏性更改

## 截图（如适用）
如果有 UI 更改，请附上截图。

## 其他信息
任何其他相关信息。
```

## 🧪 测试指南

### 测试结构

```
tests/
├── conftest.py                    # pytest 配置和 fixtures
├── test_basic_units.py           # 基础单元测试
├── test_integration_flows.py     # 集成测试
├── test_performance_benchmarks.py # 性能测试
├── test_system_validation.py     # 系统验证测试
├── test_intelligence.py          # 智能组件测试
├── test_monitoring.py            # 监控系统测试
└── run_all_tests.py              # 测试运行器
```

### 编写测试

```python
import unittest
from unittest.mock import Mock, patch
from your_module import YourClass

class TestYourClass(unittest.TestCase):
    """测试您的类"""
    
    def setUp(self):
        """每个测试前的设置"""
        self.config = {'enabled': True, 'param': 'value'}
        self.instance = YourClass(self.config)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.param, 'value')
    
    @patch('external_module.external_function')
    def test_with_mock(self, mock_function):
        """使用 mock 的测试"""
        mock_function.return_value = True
        
        result = self.instance.method_that_calls_external()
        
        self.assertTrue(result)
        mock_function.assert_called_once()
    
    def tearDown(self):
        """每个测试后的清理"""
        pass
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=html tests/

# 查看覆盖率
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

**目标覆盖率：**
- 总体覆盖率 > 85%
- 核心模块覆盖率 > 90%
- 新增代码覆盖率 = 100%

## 📖 文档贡献

### 文档结构

```
docs/
├── quickstart.md          # 快速开始
├── configuration.md       # 配置指南
├── channels.md           # 渠道配置
├── development.md        # 开发文档
├── CONTRIBUTING.md       # 贡献指南
└── advanced_usage.md     # 高级用法
```

### 文档标准

1. **中英文混排规范**
   - 中英文之间加空格
   - 数字与中文之间加空格
   - 专有名词使用正确大小写

2. **Markdown 规范**
   - 使用标准 Markdown 语法
   - 代码块指定语言
   - 链接使用相对路径

3. **内容要求**
   - 清晰的标题结构
   - 实用的代码示例
   - 完整的配置说明
   - 常见问题解答

## 🎖️ 贡献者认可

### Hall of Fame

感谢以下贡献者：

- [@contributor1](https://github.com/contributor1) - 核心开发者
- [@contributor2](https://github.com/contributor2) - 文档维护
- [@contributor3](https://github.com/contributor3) - 测试专家

### 贡献统计

```bash
# 查看贡献统计
git shortlog -sn

# 查看代码行数统计
cloc src/ tests/
```

### 成为维护者

优秀的贡献者有机会成为项目维护者：

**条件：**
- 持续贡献 3 个月以上
- 高质量的代码和文档
- 积极参与社区讨论
- 帮助其他贡献者

**权限：**
- 代码审查权限
- Issue 和 PR 管理
- 发布版本权限
- 技术决策参与

## 📞 联系方式

### 获取帮助

1. **GitHub Issues** - 报告 Bug 或功能请求
2. **GitHub Discussions** - 技术讨论和问答
3. **邮件** - dev@your-company.com
4. **社区群组** - [加入链接]

### 社区准则

我们承诺为每个人提供友好、安全和受欢迎的环境，无论：
- 经验水平
- 性别认同和表达
- 性取向
- 残疾状况
- 个人外貌
- 身体尺寸
- 种族
- 民族
- 年龄
- 宗教信仰

### 行为规范

**我们鼓励的行为：**
- 使用友好和包容的语言
- 尊重不同的观点和经历
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

**不可接受的行为：**
- 使用性化的语言或图像
- 恶意评论或人身攻击
- 公开或私人骚扰
- 未经同意发布他人私人信息
- 其他不道德或不专业的行为

## 🎉 开始贡献

准备好开始了吗？

1. ⭐ Star 这个项目
2. 🍴 Fork 到你的账户
3. 🔧 设置开发环境
4. 💻 开始编码
5. 📝 提交你的第一个 PR

**第一次贡献建议：**
- 查看 [Good First Issue](https://github.com/your-repo/claude-code-notifier/labels/good%20first%20issue) 标签
- 改进文档
- 添加测试用例
- 修复小的 Bug

感谢您的贡献！每一个贡献都让项目变得更好。 🚀