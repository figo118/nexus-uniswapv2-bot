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
VENV_DIR="$HOME/nexus-bot-venv"

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

    if ! command_exists systemctl; then
        echo -e "${YELLOW}正在安装systemd...${RESET}"
        apt install -y systemd || {
            echo -e "${RED}systemd安装失败!${RESET}"
            exit 1
        }
    fi
}

# 设置虚拟环境（强制模式）
setup_venv() {
    echo -e "${BLUE}[2/4] 设置虚拟环境...${RESET}"
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR" || {
        echo -e "${RED}虚拟环境创建失败!${RESET}"
        exit 1
    }
    source "$VENV_DIR/bin/activate"
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
            echo "3. 示例: ba4d39b425e17d1c2f78f2a1c0bdaf36c4cf277894801eeec5469169d8124654"
        fi
    done
}

# 配置系统服务
setup_systemd_service() {
    echo -e "${BLUE}[+] 配置系统服务...${RESET}"
    
    SERVICE_FILE="/etc/systemd/system/nexus-bot.service"
    echo "[Unit]
Description=Nexus UniswapV2 Bot
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$WORK_DIR
ExecStart=$VENV_DIR/bin/python $WORK_DIR/main.py
Environment=PATH=$VENV_DIR/bin:\$PATH
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target" | sudo tee $SERVICE_FILE >/dev/null

    sudo systemctl daemon-reload
    sudo systemctl enable nexus-bot
    sudo systemctl start nexus-bot

    echo -e "${GREEN}✓ 系统服务已配置并启动${RESET}"
    echo -e "管理命令:"
    echo -e " 启动: ${BLUE}sudo systemctl start nexus-bot${RESET}"
    echo -e " 停止: ${BLUE}sudo systemctl stop nexus-bot${RESET}"
    echo -e " 状态: ${BLUE}sudo systemctl status nexus-bot${RESET}"
    echo -e " 日志: ${BLUE}journalctl -u nexus-bot -f${RESET}"
}

# 主流程
main() {
    install_dependencies
    setup_venv
    setup_repository
    install_python_deps
    setup_config
    setup_systemd_service
    
    echo -e "\n${GREEN}✅ 安装完成！机器人已作为系统服务自动运行${RESET}"
}

# 执行
echo -e "${YELLOW}即将安装 Nexus UniswapV2 机器人（系统服务模式）${RESET}"
read -p "是否继续? [y/N] " confirm
case "$confirm" in
    [yY]*) main ;;
    *) echo -e "${RED}操作已取消${RESET}"; exit 0 ;;
esac
