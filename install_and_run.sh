#!/bin/bash

# 颜色定义
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
RESET='\033[0m'

# 仓库配置
REPO_URL="https://github.com/figo118/nexus-uniswapv2-bot.git"
REPO_DIR="nexus-uniswapv2-bot"
ENV_PATH="$REPO_DIR/feature/.env"  # 修正的.env路径

# 检查并安装Git
if ! command -v git &>/dev/null; then
    echo -e "${YELLOW}正在安装Git...${RESET}"
    sudo apt update && sudo apt install -y git || {
        echo -e "${RED}Git安装失败！请手动安装后重试。${RESET}"
        exit 1
    }
fi

# 克隆/更新仓库
if [ ! -d "$REPO_DIR" ]; then
    echo -e "${YELLOW}正在下载机器人代码...${RESET}"
    git clone "$REPO_URL" "$REPO_DIR" || {
        echo -e "${RED}代码下载失败！请检查网络或仓库地址。${RESET}"
        exit 1
    }
else
    echo -e "${GREEN}✓ 代码已存在，正在更新...${RESET}"
    cd "$REPO_DIR"
    git pull || echo -e "${YELLOW}警告：代码更新失败，继续使用本地版本${RESET}"
    cd ..
fi

# 检查Python
if ! command -v python3 &>/dev/null; then
    echo -e "${YELLOW}正在安装Python3...${RESET}"
    sudo apt install -y python3 python3-pip || {
        echo -e "${RED}Python安装失败！请手动安装后重试。${RESET}"
        exit 1
    }
fi

# 安装依赖
echo -e "${YELLOW}正在安装依赖库...${RESET}"
cd "$REPO_DIR" && pip3 install -r requirements.txt || {
    echo -e "${YELLOW}尝试安装默认依赖...${RESET}"
    pip3 install colorama python-dotenv web3
}

# 配置私钥（如果首次运行）
if [ ! -f "$ENV_PATH" ]; then
    echo -e "\n${YELLOW}首次运行需要配置:${RESET}"
    read -p "请输入钱包私钥: " private_key
    # 清理私钥输入
    cleaned_key=$(echo "$private_key" | tr -d '[:space:]')
    
    # 确保feature目录存在
    mkdir -p "$REPO_DIR/feature"
    echo "PRIVATE_KEY=$cleaned_key" > "$ENV_PATH"
    echo -e "${GREEN}✓ 配置已保存到 $ENV_PATH${RESET}"
    
    # 验证私钥格式
    if ! python3 -c "
from web3 import Web3
try:
    Web3().eth.account.from_key('$cleaned_key')
except:
    exit(1)
" &>/dev/null; then
        echo -e "${RED}错误：私钥格式无效！请检查：${RESET}"
        echo "1. 必须是64字符十六进制"
        echo "2. 不要包含0x前缀"
        echo "3. 不要换行或空格"
        rm -f "$ENV_PATH"
        exit 1
    fi
else
    echo -e "${GREEN}✓ 使用现有配置文件${RESET}"
fi

# 修复权限
cd "$REPO_DIR" && chmod +x *.py feature/*.py

# 启动机器人
echo -e "\n${GREEN}✅ 启动 Nexus UniswapV2 机器人...${RESET}"
cd "$REPO_DIR" && python3 main.py
