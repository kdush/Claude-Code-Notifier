# Makefile for Claude Notifier
# PyPI标准化开发和发布流程

.PHONY: help install install-dev test lint format type-check security clean build upload upload-test docs

# 默认目标
help:
	@echo "Claude Notifier 开发工具"
	@echo ""
	@echo "开发环境:"
	@echo "  install          安装核心依赖"
	@echo "  install-dev      安装开发依赖"
	@echo "  install-all      安装所有依赖"
	@echo ""
	@echo "代码质量:"
	@echo "  test             运行测试"
	@echo "  test-cov         运行测试并生成覆盖率报告"
	@echo "  lint             代码风格检查"
	@echo "  format           代码格式化"
	@echo "  type-check       类型检查"
	@echo "  security         安全检查"
	@echo "  quality          运行所有质量检查"
	@echo ""
	@echo "构建发布:"
	@echo "  clean            清理构建文件"
	@echo "  build            构建分发包"
	@echo "  upload-test      上传到测试PyPI"
	@echo "  upload           上传到正式PyPI"
	@echo ""
	@echo "文档:"
	@echo "  docs             生成文档"
	@echo "  docs-serve       本地预览文档"

# 安装依赖
install:
	pip install -e .

install-dev:
	pip install -e .[dev]

install-all:
	pip install -e .[all,dev]

# 测试
test:
	pytest

test-cov:
	pytest --cov=claude_notifier --cov-report=html --cov-report=term-missing

test-all:
	pytest --cov=claude_notifier --cov-report=html --cov-report=term-missing tests/

# 代码质量
lint:
	flake8 src/claude_notifier tests/
	@echo "✅ Lint检查通过"

format:
	black src/claude_notifier tests/
	@echo "✅ 代码格式化完成"

type-check:
	mypy src/claude_notifier
	@echo "✅ 类型检查通过"

security:
	@echo "🔍 安全检查..."
	@command -v bandit >/dev/null 2>&1 || pip install bandit
	bandit -r src/claude_notifier -f json -o security-report.json || true
	@if [ -f security-report.json ]; then \
		echo "⚠️  安全报告已生成: security-report.json"; \
	else \
		echo "✅ 安全检查通过"; \
	fi

quality: format lint type-check test security
	@echo "🎉 所有质量检查完成"

# 构建和发布
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "🧹 清理完成"

build: clean
	python -m build
	@echo "📦 构建完成"
	@echo "分发包:"
	@ls -la dist/

check-build: build
	python -m twine check dist/*
	@echo "✅ 分发包检查通过"

upload-test: check-build
	@echo "📤 上传到测试PyPI..."
	python -m twine upload --repository testpypi dist/*
	@echo "🎉 测试上传完成"
	@echo "测试安装: pip install -i https://test.pypi.org/simple/ claude-notifier"

upload: check-build
	@echo "⚠️  准备上传到正式PyPI"
	@read -p "确认上传? [y/N] " confirm && [ "$$confirm" = "y" ]
	python -m twine upload dist/*
	@echo "🎉 正式发布完成"

# 版本管理
version-patch:
	@echo "🔖 更新patch版本..."
	bump2version patch

version-minor:
	@echo "🔖 更新minor版本..."
	bump2version minor

version-major:
	@echo "🔖 更新major版本..."
	bump2version major

# 文档
docs:
	@command -v mkdocs >/dev/null 2>&1 || pip install mkdocs mkdocs-material
	mkdocs build
	@echo "📚 文档生成完成"

docs-serve:
	@command -v mkdocs >/dev/null 2>&1 || pip install mkdocs mkdocs-material
	mkdocs serve

# 开发工作流
dev-setup: install-dev
	@echo "🛠️  开发环境设置..."
	@command -v pre-commit >/dev/null 2>&1 || pip install pre-commit
	pre-commit install
	@echo "✅ 开发环境就绪"

dev-test: format lint type-check test
	@echo "🧪 开发测试完成"

# CI/CD支持
ci-install:
	pip install -e .[all,dev]
	pip install build twine

ci-test: lint type-check test-cov
	@echo "✅ CI测试完成"

ci-build: clean build check-build
	@echo "✅ CI构建完成"

# 本地完整测试 (模拟CI)
ci-local: clean dev-setup ci-test ci-build
	@echo "🎉 本地CI测试完成"

# 预发布检查
pre-release: ci-local
	@echo "📋 预发布检查清单:"
	@echo "  ✅ 所有测试通过"
	@echo "  ✅ 代码质量检查通过"
	@echo "  ✅ 构建包验证通过"
	@echo ""
	@echo "📝 发布前确认:"
	@echo "  1. 版本号已更新 (src/claude_notifier/__version__.py)"
	@echo "  2. CHANGELOG.md 已更新"
	@echo "  3. README.md 已更新"
	@echo "  4. 所有功能已测试"
	@echo ""
	@echo "🚀 准备就绪，可以发布!"

# Docker支持 (可选)
docker-build:
	docker build -t claude-notifier:latest .

docker-test:
	docker run --rm claude-notifier:latest pytest

# 安装验证
verify-install:
	@echo "🔍 验证安装..."
	python -c "import claude_notifier; print(f'✅ 核心模块: {claude_notifier.__version__}')"
	@python -c "from claude_notifier import has_intelligence, has_monitoring; print(f'🧠 智能功能: {\"✅\" if has_intelligence() else \"❌\"}')" 2>/dev/null || echo "🧠 智能功能: ❌"
	@python -c "from claude_notifier import has_monitoring; print(f'📊 监控功能: {\"✅\" if has_monitoring() else \"❌\"}')" 2>/dev/null || echo "📊 监控功能: ❌"
	claude-notifier --version
	@echo "✅ 安装验证完成"