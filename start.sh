#!/bin/bash

# FLUX.1-Kontext API 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 检查Python版本
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_error "Python not found. Please install Python 3.8+"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    log_info "Using Python $PYTHON_VERSION"
}

# 检查GPU可用性
check_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        log_info "NVIDIA GPU detected:"
        nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits
        export DEVICE="cuda"
    else
        log_warn "No NVIDIA GPU detected, using CPU"
        export DEVICE="cpu"
    fi
}

# 创建虚拟环境
create_venv() {
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
    fi
    
    log_info "Activating virtual environment..."
    source venv/bin/activate
    
    log_info "Configuring pip to use China mirrors..."
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
    
    log_info "Upgrading pip..."
    pip install --upgrade pip
}

# 安装依赖
install_dependencies() {
    log_info "Installing dependencies..."
    
    # 配置中国大陆pip源
    log_info "Configuring pip to use China mirrors..."
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
    
    # 根据设备类型安装PyTorch
    if [ "$DEVICE" = "cuda" ]; then
        log_info "Installing PyTorch with CUDA 12.1 support (compatible with CUDA 12.9)..."
        pip install torch torchvision torchaudio \
            --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
            --extra-index-url https://download.pytorch.org/whl/cu121
    else
        log_info "Installing PyTorch CPU version..."
        pip install torch torchvision torchaudio \
            --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
            --extra-index-url https://download.pytorch.org/whl/cpu
    fi
    
    # 安装其他依赖
    pip install -r requirements.txt
}

# 创建必要目录
create_directories() {
    log_info "Creating necessary directories..."
    mkdir -p static/uploads static/outputs logs
}

# 检查环境变量
check_environment() {
    if [ -f ".env" ]; then
        log_info "Loading environment variables from .env file..."
        export $(cat .env | grep -v '^#' | xargs)
    else
        log_warn "No .env file found, using default settings"
        if [ -f ".env.example" ]; then
            log_info "You can copy .env.example to .env and modify it"
        fi
    fi
    
    # 设置默认值
    export HOST=${HOST:-"0.0.0.0"}
    export PORT=${PORT:-8000}
    export DEVICE=${DEVICE:-"auto"}
    
    log_info "Configuration:"
    log_info "  Host: $HOST"
    log_info "  Port: $PORT"
    log_info "  Device: $DEVICE"
}

# 启动API服务
start_api() {
    log_info "Starting FLUX.1-Kontext API..."
    
    # 检查是否在容器中运行
    if [ -f "/.dockerenv" ]; then
        log_info "Running in Docker container"
        exec uvicorn app.main:app --host $HOST --port $PORT --workers 1
    else
        # 本地运行
        if [ -d "venv" ] && [ -z "$VIRTUAL_ENV" ]; then
            log_info "Activating virtual environment..."
            source venv/bin/activate
        fi
        
        uvicorn app.main:app --host $HOST --port $PORT --reload
    fi
}

# 快速启动（跳过所有安装步骤）
quick_start() {
    log_info "Quick start mode - skipping all setup steps..."
    
    # 检查虚拟环境是否存在
    if [ ! -d "venv" ]; then
        log_error "Virtual environment not found. Please run without --run-only first."
        exit 1
    fi
    
    # 激活虚拟环境
    log_info "Activating virtual environment..."
    source venv/bin/activate
    
    # 检查环境变量
    check_environment
    
    # 创建必要目录
    create_directories
    
    # 直接启动服务
    start_api
}

# 主函数
main() {
    # 检查是否为快速启动模式
    if [ "$1" = "--run-only" ] || [ "$1" = "--skip-setup" ]; then
        quick_start
        return
    fi
    
    log_info "Starting FLUX.1-Kontext API setup..."
    
    # 检查是否在容器中
    if [ -f "/.dockerenv" ]; then
        log_info "Running in Docker container, skipping setup"
        check_environment
        create_directories
        start_api
        return
    fi
    
    # 本地环境设置
    check_python
    check_gpu
    check_environment
    create_directories
    
    # 检查是否需要创建虚拟环境
    if [ "$1" = "--no-venv" ]; then
        log_info "Skipping virtual environment creation"
    else
        create_venv
    fi
    
    # 检查是否需要安装依赖
    if [ "$1" = "--no-install" ]; then
        log_info "Skipping dependency installation"
    else
        install_dependencies
    fi
    
    start_api
}

# 帮助信息
show_help() {
    echo "FLUX.1-Kontext API 启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --run-only    快速启动模式，跳过所有安装步骤（推荐用于已安装环境）"
    echo "  --skip-setup  同 --run-only"
    echo "  --no-venv     跳过虚拟环境创建"
    echo "  --no-install  跳过依赖安装"
    echo "  --help        显示此帮助信息"
    echo ""
    echo "环境变量:"
    echo "  HOST          服务器地址 (默认: 0.0.0.0)"
    echo "  PORT          服务器端口 (默认: 8000)"
    echo "  DEVICE        设备类型 (cuda/cpu/auto, 默认: auto)"
    echo ""
    echo "使用场景:"
    echo "  首次运行:     $0                    # 完整安装和启动"
    echo "  日常启动:     $0 --run-only         # 快速启动（推荐）"
    echo "  自定义安装:   $0 --no-venv         # 不创建虚拟环境"
    echo "  指定地址:     HOST=127.0.0.1 $0    # 指定主机地址"
    echo ""
    echo "注意: --run-only 需要先完成完整安装"
}

# 处理命令行参数
case "$1" in
    --help|-h)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac