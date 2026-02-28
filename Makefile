.PHONY: help install install-dev test lint format clean run docker-build docker-run

# 默认目标
help:
	@echo "OpenClaw - 可用命令:"
	@echo ""
	@echo "  make install      - 安装生产依赖"
	@echo "  make install-dev  - 安装开发依赖"
	@echo "  make test         - 运行测试"
	@echo "  make test-cov     - 运行测试并生成覆盖率报告"
	@echo "  make lint         - 运行代码检查"
	@echo "  make format       - 格式化代码"
	@echo "  make clean        - 清理临时文件"
	@echo "  make run          - 启动 CLI"
	@echo "  make docker-build - 构建 Docker 镜像"
	@echo "  make docker-run   - 运行 Docker 容器"

# 安装
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# 测试
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# 代码质量
lint:
	flake8 src/ tests/ --max-line-length=120
	black src/ tests/ --check
	isort src/ tests/ --check-only

format:
	black src/ tests/
	isort src/ tests/

# 清理
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ .mypy_cache/

# 运行
run:
	python -m src.cli

# Docker
docker-build:
	docker build -t openclaw:latest .

docker-run:
	docker run -it --rm -v $(PWD)/config:/app/config openclaw:latest
