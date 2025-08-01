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
VENV_DIR="$HOME/nexus-bot-venv"  # 修复：使用绝对路径

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
        apt update && apt install -y git || {
            echo -e "${RED}Git安装失败!${RESET}"
            exit 1
        }
    fi

    if ! command_exists python3; then
        echo -e "${YELLOW}正在安装Python3...${RESET}"
        apt install -y python3 python3-pip python3-venv || {
            echo -e "${RED}Python安装失败!${RESET}"
            exit 1
        }
    fi
}

# 设置虚拟环境（强制模式）
setup_venv() {
    echo -e "${BLUE}[2/4] 设置虚拟环境...${RESET}"
    # 彻底清除旧环境
    rm -rf "$VENV_DIR"
    # 创建新环境
    python3 -m venv "$VENV_DIR" || {
        echo -e "${RED}虚拟环境创建失败!${RESET}"
        exit 1
    }
    # 直接使用绝对路径激活
    source "$VENV_DIR/bin/activate" || {
        echo -e "${RED}虚拟环境激活失败!${RESET}"
        exit 1
    }
    # 安装核心依赖
    "$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
    "$VENV_DIR/bin/pip" install web3 eth-account python-dotenv colorama || {
        echo -e "${RED}依赖安装失败!${RESET}"
        exit 1
    }
}

# 克隆或更新仓库
setup_repository() {
    echo -e "${BLUE}[3/4] 设置代码仓库...${RESET}"
    
    if [ -d "$WORK_DIR" ]; then
        echo -e "${YELLOW}检测到已有仓库，正在更新...${RESET}"
        cd "$WORK_DIR" && git pull || {
            echo -e "${YELLOW}更新失败，尝试重新克隆...${RESET}"
            cd "$SCRIPT_DIR" && rm -rf "$WORK_DIR"
            git clone "$REPO_URL" "$WORK_DIR"
        }
    else
        git clone "$REPO_URL" "$WORK_DIR"
    fi
}

# 钱包配置（终极验证）
setup_config() {
    echo -e "${BLUE}[4/4] 钱包配置...${RESET}"
    
    # 从备份恢复
    if [ -f "$CONFIG_BACKUP" ]; then
        mkdir -p "$(dirname "$ENV_PATH")"
        cp "$CONFIG_BACKUP" "$ENV_PATH"
        echo -e "${GREEN}✓ 自动恢复上次配置${RESET}"
        return
    fi

    # 全新配置
    while true; do
        read -p "请输入钱包私钥: " private_key
        cleaned_key=$(echo "$private_key" | tr -d '[:space:]' | sed 's/^0x//')
        
        # 使用虚拟环境Python直接验证
        if "$VENV_DIR/bin/python" -c "
from eth_account import Account
try:
    Account().from_key('$cleaned_key').address
    print('VALID')
except:
    exit(1)
" >/dev/null 2>&1; then
            mkdir -p "$(dirname "$ENV_PATH")"
            echo "PRIVATE_KEYS=$cleaned_key" > "$ENV_PATH"
            cp "$ENV_PATH" "$CONFIG_BACKUP"
            chmod 600 "$ENV_PATH" "$CONFIG_BACKUP"
            echo -e "${GREEN}✓ 配置已保存${RESET}"
            break
        else
            echo -e "${RED}无效私钥! 请检查:${RESET}"
            echo "1. 必须是64字符十六进制"
            echo "2. 不要包含空格"
        fi
    done
}

# 主流程
main() {
    install_dependencies
    setup_venv
    setup_repository
    setup_config
    
    echo -e "\n${GREEN}✅ 安装完成! 运行命令:${RESET}"
    echo -e "1. 激活环境: ${BLUE}source $VENV_DIR/bin/activate${RESET}"
    echo -e "2. 启动机器人: ${BLUE}cd $WORK_DIR && python main.py${RESET}"
}

# 执行
echo -e "${YELLOW}即将安装 Nexus UniswapV2 机器人${RESET}"
read -p "是否继续? [y/N] " confirm
case "$confirm" in
    [yY]*) main ;;
    *) echo -e "${RED}操作已取消${RESET}"; exit 0 ;;
esac
