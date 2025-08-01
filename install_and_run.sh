#!/bin/bash

# 颜色定义
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
BLUE='\033[34m'
RESET='\033[0m'

# 配置参数
REPO_URL="https://github.com/figo118/nexus-uniswapv2-bot.git"
REPO_NAME="nexus-uniswapv2-bot"
CONFIG_BACKUP="$HOME/.nexus_bot_backup.env"
VENV_DIR="$HOME/nexus-bot-venv"  # 虚拟环境目录

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$SCRIPT_DIR/$REPO_NAME"
ENV_PATH="$WORK_DIR/feature/.env"

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 安装必要组件
install_dependencies() {
    echo -e "${BLUE}[1/4] 检查系统依赖...${RESET}"
    
    if ! command_exists git; then
        echo -e "${YELLOW}正在安装Git...${RESET}"
        sudo apt update && sudo apt install -y git || {
            echo -e "${RED}Git安装失败! 请手动安装后重试。${RESET}"
            exit 1
        }
    fi

    if ! command_exists python3; then
        echo -e "${YELLOW}正在安装Python3...${RESET}"
        sudo apt install -y python3 python3-pip python3-venv || {
            echo -e "${RED}Python安装失败! 请手动安装后重试。${RESET}"
            exit 1
        }
    fi
}

# 设置虚拟环境
setup_venv() {
    echo -e "${YELLOW}正在设置Python虚拟环境...${RESET}"
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR" || {
            echo -e "${RED}虚拟环境创建失败!${RESET}"
            exit 1
        }
    fi
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
}

# 克隆或更新仓库
setup_repository() {
    echo -e "${BLUE}[2/4] 设置代码仓库...${RESET}"
    
    if [ -d "$WORK_DIR" ]; then
        echo -e "${YELLOW}检测到已有仓库，正在更新...${RESET}"
        cd "$WORK_DIR" || exit
        git pull || {
            echo -e "${YELLOW}更新失败，尝试重新克隆...${RESET}"
            cd "$SCRIPT_DIR" || exit
            rm -rf "$WORK_DIR"
            git clone "$REPO_URL" "$WORK_DIR"
        }
    else
        git clone "$REPO_URL" "$WORK_DIR"
    fi
}

# 安装Python依赖
install_python_deps() {
    echo -e "${BLUE}[3/4] 安装Python依赖...${RESET}"
    cd "$WORK_DIR" || exit
    
    # 确保在虚拟环境中
    if [ -z "$VIRTUAL_ENV" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    pip install --upgrade pip || {
        echo -e "${YELLOW}pip升级失败，继续安装...${RESET}"
    }
    
    pip install -r requirements.txt || {
        echo -e "${YELLOW}尝试安装核心依赖...${RESET}"
        pip install colorama python-dotenv web3
    }
}

# 配置私钥
setup_config() {
    echo -e "${BLUE}[4/4] 钱包配置...${RESET}"
    
    # 从备份恢复配置
    if [ -f "$CONFIG_BACKUP" ]; then
        mkdir -p "$(dirname "$ENV_PATH")"
        cp "$CONFIG_BACKUP" "$ENV_PATH"
        echo -e "${GREEN}✓ 自动恢复上次配置${RESET}"
        return
    fi

    # 全新配置
    while true; do
        read -p "请输入钱包私钥（64字符十六进制）: " private_key
        cleaned_key=$(echo "$private_key" | tr -d '[:space:]')
        
        if python3 -c "
from web3 import Web3
try:
    Web3().eth.account.from_key('$cleaned_key')
    print('VALID')
except:
    exit(1)
" &>/dev/null; then
            mkdir -p "$(dirname "$ENV_PATH")"
            echo "PRIVATE_KEYS=$cleaned_key" > "$ENV_PATH"
            # 备份配置
            cp "$ENV_PATH" "$CONFIG_BACKUP"
            chmod 600 "$ENV_PATH" "$CONFIG_BACKUP"
            echo -e "${GREEN}✓ 配置已保存（已备份）${RESET}"
            break
        else
            echo -e "${RED}无效私钥！请检查：${RESET}"
            echo "1. 必须是64字符十六进制（不含0x前缀）"
            echo "2. 不要包含空格或特殊字符"
            echo "3. 示例正确格式: af5d4b39e27b1..."
        fi
    done
}

# 主流程
main() {
    # 安装依赖
    install_dependencies
    
    # 设置虚拟环境
    setup_venv
    
    # 设置仓库
    setup_repository
    
    # 安装Python依赖
    install_python_deps
    
    # 配置
    setup_config
    
    # 设置权限
    find "$WORK_DIR" -name "*.py" -exec chmod +x {} \;
    
    # 启动
    echo -e "\n${GREEN}✅ 启动 Nexus UniswapV2 机器人...${RESET}"
    echo -e "${YELLOW}注意：请确保在虚拟环境中运行！${RESET}"
    echo -e "激活虚拟环境命令: ${BLUE}source $VENV_DIR/bin/activate${RESET}"
    echo -e "运行命令: ${BLUE}cd $WORK_DIR && python main.py${RESET}"
}

# 确认提示
echo -e "${YELLOW}即将安装/更新 Nexus UniswapV2 机器人${RESET}"
read -p "是否继续？[y/N] " confirm
case "$confirm" in
    [yY][eE][sS]|[yY])
        main
        ;;
    *)
        echo -e "${RED}操作已取消${RESET}"
        exit 0
        ;;
esac
