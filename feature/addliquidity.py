import os
import random
import time
from web3 import Web3
from dotenv import load_dotenv

class Colors:
    RESET = "\033[0m"  # 重置颜色
    RED = "\033[91m"  # 红色
    GREEN = "\033[92m"  # 绿色
    YELLOW = "\033[93m"  # 黄色
    BLUE = "\033[94m"  # 蓝色
    MAGENTA = "\033[95m"  # 洋红色
    CYAN = "\033[96m"  # 青色
    WHITE = "\033[97m"  # 白色
    BOLD = "\033[1m"  # 粗体
    UNDERLINE = "\033[4m"  # 下划线

load_dotenv()

PRIVATE_KEYS = os.getenv("PRIVATE_KEYS").split(",")
if not PRIVATE_KEYS:
    raise ValueError(f"{Colors.RED}未在.env文件中找到私钥{Colors.RESET}")

RPC_URL = "https://testnet3.rpc.nexus.xyz"
CHAIN_ID = 3940

UNISWAP_V2_ROUTER_ADDRESS = "0x32aA9448586b06d2d42Fe4CFabF1c7AcD03bAE31"
WETH_ADDRESS = "0xfAdf8E61BE6e95790d627057251AA41258a207d0"

AVAILABLE_TOKENS = {
    "NXS": "0x3eC55271351865ab99a9Ce92272C3E908f2E627b",
    "NEXI": "0x184eE44cF8B7Fec2371dc46D9076fFB2c1E0Ce65",
    "AIE": "0xF6f61565947621387ADF3BeD7ba02533aB013CCd"
}

TOKEN_ADDRESS = ""
SELECTED_TOKEN_NAME = ""

web3 = Web3(Web3.HTTPProvider(RPC_URL))
if not web3.is_connected():
    raise ConnectionError(f"{Colors.RED}无法连接到RPC URL{Colors.RESET}")

uniswap_v2_router_abi = '''
[
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "amountTokenDesired", "type": "uint256"},
            {"internalType": "uint256", "name": "amountTokenMin", "type": "uint256"},
            {"internalType": "uint256", "name": "amountETHMin", "type": "uint256"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "addLiquidityETH",
        "outputs": [
            {"internalType": "uint256", "name": "amountToken", "type": "uint256"},
            {"internalType": "uint256", "name": "amountETH", "type": "uint256"},
            {"internalType": "uint256", "name": "liquidity", "type": "uint256"}
        ],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]
'''

erc20_abi = '''
[
    {
        "constant": true,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]
'''

uniswap_router = web3.eth.contract(address=Web3.to_checksum_address(UNISWAP_V2_ROUTER_ADDRESS), abi=uniswap_v2_router_abi)

def get_token_contract(token_address):
    return web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc20_abi)

def get_token_balance(account_address, token_address):
    token_contract = get_token_contract(token_address)
    return token_contract.functions.balanceOf(account_address).call()

def approve_token(account, private_key, token_address, router_address, amount_to_approve):
    token_contract = get_token_contract(token_address)
    gas_price = web3.eth.gas_price

    while True:
        try:
            nonce = web3.eth.get_transaction_count(account.address, "pending")
            print(f"  {Colors.YELLOW}⏳ 正在授权 {web3.from_wei(amount_to_approve, 'ether')} {SELECTED_TOKEN_NAME} 给Nexswap路由器...{Colors.RESET}")

            transaction = token_contract.functions.approve(
                router_address,
                amount_to_approve
            ).build_transaction({
                'from': account.address,
                'gas': 120000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': CHAIN_ID
            })

            signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"  {Colors.GREEN}✅ {Colors.BOLD}授权交易已发送{Colors.RESET}")
            web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            print(f"{Colors.GREEN}  🎉 授权确认成功！{Colors.RESET}")
            return True

        except Exception as e:
            if 'replacement transaction underpriced' in str(e) or 'nonce too low' in str(e):
                gas_price += web3.to_wei(2, 'gwei')
                print(f"  {Colors.YELLOW}⚠️ 授权交易的Gas价格过低或Nonce问题，将Gas价格增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            elif 'out of gas' in str(e):
                gas_price += web3.to_wei(5, 'gwei')
                print(f"  {Colors.RED}🔥 授权交易Gas不足，将Gas价格增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            else:
                print(f"  {Colors.RED}❌ 授权过程中发生错误: {e}{Colors.RESET}")
                return False

def add_liquidity_eth(account, private_key, token_address, amount_token_desired, amount_eth_desired, amount_token_min, amount_eth_min, deadline):
    gas_price = web3.eth.gas_price

    while True:
        try:
            nonce = web3.eth.get_transaction_count(account.address, "pending")
            print(f"  {Colors.YELLOW}⏳ 正在为 {SELECTED_TOKEN_NAME} 和 NEX 添加流动性...{Colors.RESET}")

            transaction = uniswap_router.functions.addLiquidityETH(
                web3.to_checksum_address(token_address),
                amount_token_desired,
                amount_token_min,
                amount_eth_min,
                account.address,
                deadline
            ).build_transaction({
                'from': account.address,
                'value': amount_eth_desired,
                'gas': 320000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': CHAIN_ID
            })

            signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"  {Colors.GREEN}✅ {Colors.BOLD}添加流动性交易已发送{Colors.RESET}{Colors.GREEN} https://testnet3.explorer.nexus.xyz/tx/{web3.to_hex(tx_hash)}{Colors.RESET}")
            web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            print(f"{Colors.GREEN}  🎉 {SELECTED_TOKEN_NAME}/NEX 流动性添加确认！{Colors.RESET}")
            return web3.to_hex(tx_hash)

        except Exception as e:
            if 'replacement transaction underpriced' in str(e) or 'nonce too low' in str(e):
                gas_price += web3.to_wei(2, 'gwei')
                print(f"  {Colors.YELLOW}⚠️ 添加流动性的Gas价格过低或Nonce问题，将Gas价格增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            elif 'out of gas' in str(e):
                gas_price += web3.to_wei(5, 'gwei')
                print(f"  {Colors.RED}🔥 添加流动性交易Gas不足，将Gas价格增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            else:
                print(f"  {Colors.RED}❌ 添加流动性过程中发生错误: {e}{Colors.RESET}")
                raise

def has_sufficient_eth_balance(account, amount_in_wei):
    balance = web3.eth.get_balance(account.address)
    return balance >= amount_in_wei

if __name__ == "__main__":
    print(f"{Colors.BOLD}{Colors.MAGENTA}--- 💧 Nexswap 流动性添加工具 💧 ---{Colors.RESET}")

    print(f"\n{Colors.BOLD}{Colors.BLUE}--- 选择要添加流动性的代币（与NEX配对） ---{Colors.RESET}")
    token_names = list(AVAILABLE_TOKENS.keys())
    for i, token_name in enumerate(token_names):
        print(f"{Colors.WHITE}{i+1}. {token_name} ({AVAILABLE_TOKENS[token_name]}){Colors.RESET}")

    while True:
        try:
            choice = int(input(f"{Colors.CYAN}输入要添加流动性的代币编号: {Colors.RESET}"))
            if 1 <= choice <= len(token_names):
                SELECTED_TOKEN_NAME = token_names[choice - 1]
                TOKEN_ADDRESS = AVAILABLE_TOKENS[SELECTED_TOKEN_NAME]
                print(f"{Colors.GREEN}✅ 您选择了: {Colors.BOLD}{SELECTED_TOKEN_NAME}{Colors.RESET}")
                break
            else:
                print(f"{Colors.RED}无效选择。请输入有效编号。{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}无效输入。请输入数字。{Colors.RESET}")

    desired_token_amount = 0.0
    desired_eth_amount = 0.0

    try:
        desired_eth_amount = float(input(f"{Colors.CYAN}输入要添加的NEX数量（例如：0.1）: {Colors.RESET}"))
        if desired_eth_amount <= 0:
            raise ValueError("NEX数量必须为正数。")
    except ValueError as e:
        print(f"{Colors.RED}无效输入: {e}。请输入数字。{Colors.RESET}")
        exit()

    try:
        path_eth_to_token = [web3.to_checksum_address(WETH_ADDRESS), web3.to_checksum_address(TOKEN_ADDRESS)]
        amounts_out = uniswap_router.functions.getAmountsOut(web3.to_wei(desired_eth_amount, 'ether'), path_eth_to_token).call()
        desired_token_amount = web3.from_wei(amounts_out[1], 'ether')
        print(f"   {Colors.CYAN}当前比例下，大约需要 {Colors.BOLD}{desired_token_amount:.4f} {SELECTED_TOKEN_NAME}{Colors.RESET}{Colors.CYAN} 来配对 {desired_eth_amount} NEX。{Colors.RESET}")
    except Exception as e:
        print(f"  {Colors.RED}❌ 计算所需 {SELECTED_TOKEN_NAME} 失败: {e}。请确保池中有流动性。{Colors.RESET}")
        exit()

    run_in_loop = False
    while True:
        loop_choice = input(f"{Colors.CYAN}是否要连续循环运行流动性添加？（y/n）: {Colors.RESET}").lower().strip()
        if loop_choice in ['yes', 'y']:
            run_in_loop = True
            print(f"{Colors.GREEN}✅ 循环模式已激活。流动性添加将连续运行。{Colors.RESET}")
            break
        elif loop_choice in ['no', 'n']:
            run_in_loop = False
            print(f"{Colors.GREEN}✅ 单次执行模式。流动性添加将为每个账户运行一次。{Colors.RESET}")
            break
        else:
            print(f"{Colors.RED}无效选择。请输入'y'或'n'。{Colors.RESET}")

    slippage_tolerance_percent = 0.5

    deadline = int(web3.eth.get_block('latest').timestamp) + 300

    accounts = [web3.eth.account.from_key(pk) for pk in PRIVATE_KEYS]
    account_index = 0

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- 开始流动性添加操作 ---{Colors.RESET}")

    max_retries_per_operation = 3
    current_operation_retries = 0

    loop_condition = True if run_in_loop else False
    while loop_condition or (not run_in_loop and account_index < len(accounts)):
        try:
            current_account = accounts[account_index]
            current_private_key = PRIVATE_KEYS[account_index]

            print(f"\n{Colors.BOLD}{Colors.BLUE}====================================================={Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BLUE}--- 当前账户: {current_account.address} ---{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BLUE}====================================================={Colors.RESET}")

            amount_token_desired_wei = web3.to_wei(desired_token_amount, 'ether')
            amount_eth_desired_wei = web3.to_wei(desired_eth_amount, 'ether')

            print(f"{Colors.WHITE}🔄 {Colors.BOLD}正在为账户准备流动性添加:{Colors.RESET}{Colors.WHITE} {current_account.address}{Colors.RESET}")
            print(f"{Colors.WHITE}   尝试添加 {Colors.BOLD}{desired_token_amount} {SELECTED_TOKEN_NAME}{Colors.RESET}{Colors.WHITE} 和 {Colors.BOLD}{desired_eth_amount} NEX{Colors.RESET}...")

            if not has_sufficient_eth_balance(current_account, amount_eth_desired_wei):
                current_eth_balance = web3.from_wei(web3.eth.get_balance(current_account.address), 'ether')
                print(f"  {Colors.RED}❌ {Colors.BOLD}账户 {current_account.address} 的NEX余额不足{Colors.RESET}{Colors.RED}。余额: {current_eth_balance} NEX。跳过添加流动性。{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(1)
                continue

            current_token_balance_wei = get_token_balance(current_account.address, TOKEN_ADDRESS)
            current_token_balance = web3.from_wei(current_token_balance_wei, 'ether')
            if current_token_balance_wei < amount_token_desired_wei:
                print(f"  {Colors.RED}❌ {Colors.BOLD}账户 {current_account.address} 的 {SELECTED_TOKEN_NAME} 余额不足{Colors.RESET}{Colors.RED}。余额: {current_token_balance} {SELECTED_TOKEN_NAME}。跳过添加流动性。{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(1)
                continue

            if not approve_token(current_account, current_private_key, TOKEN_ADDRESS, UNISWAP_V2_ROUTER_ADDRESS, amount_token_desired_wei):
                print(f"  {Colors.RED}❌ 代币授权失败。跳过添加流动性。{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(1)
                continue

            amount_token_min = int(amount_token_desired_wei * (1 - slippage_tolerance_percent / 100))
            amount_eth_min = int(amount_eth_desired_wei * (1 - slippage_tolerance_percent / 100))

            print(f"   {Colors.CYAN}滑点容忍度: {slippage_tolerance_percent}%{Colors.RESET}")
            print(f"   {Colors.CYAN}最小 {SELECTED_TOKEN_NAME} (添加): {web3.from_wei(amount_token_min, 'ether')}{Colors.RESET}")
            print(f"   {Colors.CYAN}最小 NEX (添加): {web3.from_wei(amount_eth_min, 'ether')}{Colors.RESET}")

            try:
                add_liquidity_eth(current_account, current_private_key, TOKEN_ADDRESS,
                                  amount_token_desired_wei, amount_eth_desired_wei,
                                  amount_token_min, amount_eth_min, deadline)
            except Exception as e:
                print(f"  {Colors.RED}❌ 添加流动性失败: {e}.{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(5)
                continue

            delay = random.randint(5, 15)
            print(f"\n{Colors.YELLOW}😴 等待 {delay} 秒后进行下一轮操作...{Colors.RESET}")
            time.sleep(delay)

            current_operation_retries = 0
            account_index = (account_index + 1) % len(accounts)
            if not run_in_loop and account_index == 0:
                break

        except Exception as e:
            error_message = str(e)
            print(f"\n{Colors.RED}❌ 账户 {current_account.address} 的操作循环中发生意外错误: {error_message}{Colors.RESET}")

            if "Could not transact with/call contract function, is contract deployed correctly and chain synced?" in error_message and current_operation_retries < max_retries_per_operation:
                current_operation_retries += 1
                print(f"{Colors.YELLOW}⚠️ 正在为 {current_account.address} 重试操作 ({current_operation_retries}/{max_retries_per_operation} 次重试)...{Colors.RESET}")
                time.sleep(5)
                continue
            else:
                current_operation_retries = 0
                print(f"{Colors.YELLOW}  短暂暂停后移动到下一个账户...{Colors.RESET}")
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(5)

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- 所有流动性添加操作完成。 ---{Colors.RESET}")
