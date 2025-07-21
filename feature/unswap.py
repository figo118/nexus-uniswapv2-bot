import os
import random
import time
from web3 import Web3
from dotenv import load_dotenv

class Colors:
    RESET = "\033[0m"          # 重置颜色
    RED = "\033[91m"           # 红色
    GREEN = "\033[92m"         # 绿色
    YELLOW = "\033[93m"        # 黄色
    BLUE = "\033[94m"          # 蓝色
    MAGENTA = "\033[95m"       # 洋红色
    CYAN = "\033[96m"          # 青色
    WHITE = "\033[97m"         # 白色
    BOLD = "\033[1m"           # 加粗
    UNDERLINE = "\033[4m"      # 下划线

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
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForETH",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "nonpayable",
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
            print(f"  {Colors.YELLOW}⏳ 正在为Uniswap路由器授权 {web3.from_wei(amount_to_approve, 'ether')} {SELECTED_TOKEN_NAME}...{Colors.RESET}")

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
            print(f"  {Colors.GREEN}✅ {Colors.BOLD}授权交易已发送{Colors.RESET}{Colors.GREEN} https://testnet3.explorer.nexus.xyz/tx/{web3.to_hex(tx_hash)}{Colors.RESET}")
            web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            print(f"{Colors.GREEN}  🎉 授权确认成功!{Colors.RESET}")
            return True

        except Exception as e:
            if 'replacement transaction underpriced' in str(e) or 'nonce too low' in str(e):
                gas_price += web3.to_wei(2, 'gwei')
                print(f"  {Colors.YELLOW}⚠️ 授权交易Gas价格过低或nonce问题，增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            elif 'out of gas' in str(e):
                gas_price += web3.to_wei(5, 'gwei')
                print(f"  {Colors.RED}🔥 授权交易Gas不足，增加Gas价格至 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            else:
                print(f"  {Colors.RED}❌ 授权过程中发生错误: {e}{Colors.RESET}")
                return False

def swap_tokens_for_eth(account, private_key, amount_in_token_wei, amount_out_min_eth, deadline, token_address_to_swap):
    path = [web3.to_checksum_address(token_address_to_swap), web3.to_checksum_address(WETH_ADDRESS)]

    gas_price = web3.eth.gas_price

    while True:
        try:
            nonce = web3.eth.get_transaction_count(account.address, "pending")

            transaction = uniswap_router.functions.swapExactTokensForETH(
                amount_in_token_wei,
                amount_out_min_eth,
                path,
                account.address,
                deadline
            ).build_transaction({
                'from': account.address,
                'value': 0,
                'gas': 270000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': CHAIN_ID
            })

            signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"  {Colors.GREEN}✅ {Colors.BOLD}交易已发送{Colors.RESET}")
            return web3.to_hex(tx_hash)

        except Exception as e:
            if 'replacement transaction underpriced' in str(e) or 'nonce too low' in str(e):
                gas_price += web3.to_wei(2, 'gwei')
                print(f"  {Colors.YELLOW}⚠️ Gas价格过低或nonce问题，增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            elif 'out of gas' in str(e):
                gas_price += web3.to_wei(5, 'gwei')
                print(f"  {Colors.RED}🔥 交易Gas不足，增加Gas价格至 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            else:
                print(f"  {Colors.RED}❌ 交易过程中发生错误: {e}{Colors.RESET}")
                raise

if __name__ == "__main__":
    print(f"{Colors.BOLD}{Colors.MAGENTA}--- 🔄 Nexswap代币兑换NEX工具 🔄 ---{Colors.RESET}")

    print(f"\n{Colors.BOLD}{Colors.BLUE}--- 选择要兑换为NEX的代币 ---{Colors.RESET}")
    token_names = list(AVAILABLE_TOKENS.keys())
    for i, token_name in enumerate(token_names):
        print(f"{Colors.WHITE}{i+1}. {token_name} ({AVAILABLE_TOKENS[token_name]}){Colors.RESET}")

    while True:
        try:
            choice = int(input(f"{Colors.CYAN}输入要兑换的代币编号: {Colors.RESET}"))
            if 1 <= choice <= len(token_names):
                SELECTED_TOKEN_NAME = token_names[choice - 1]
                TOKEN_ADDRESS = AVAILABLE_TOKENS[SELECTED_TOKEN_NAME]
                print(f"{Colors.GREEN}✅ 您选择了: {Colors.BOLD}{SELECTED_TOKEN_NAME}{Colors.RESET}")
                break
            else:
                print(f"{Colors.RED}无效选择，请输入有效编号。{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}无效输入，请输入数字。{Colors.RESET}")

    min_token_amount = 0.0
    max_token_amount = 0.0
    try:
        min_token_amount = float(input(f"{Colors.CYAN}输入最小兑换{SELECTED_TOKEN_NAME}数量(例如10): {Colors.RESET}"))
        max_token_amount = float(input(f"{Colors.CYAN}输入最大兑换{SELECTED_TOKEN_NAME}数量(例如50): {Colors.RESET}"))
        if min_token_amount <= 0 or max_token_amount <= 0 or min_token_amount > max_token_amount:
            raise ValueError("无效的代币范围。请确保输入正值且最小值不大于最大值。")
    except ValueError as e:
        print(f"{Colors.RED}错误: {e}{Colors.RESET}")
        exit()

    run_in_loop = False
    while True:
        loop_choice = input(f"{Colors.CYAN}是否要连续循环运行兑换？(y/n): {Colors.RESET}").lower().strip()
        if loop_choice in ['yes', 'y']:
            run_in_loop = True
            print(f"{Colors.GREEN}✅ 循环模式已激活。兑换将连续运行。{Colors.RESET}")
            break
        elif loop_choice in ['no', 'n']:
            run_in_loop = False
            print(f"{Colors.GREEN}✅ 单次执行模式。每个账户将只运行一次兑换。{Colors.RESET}")
            break
        else:
            print(f"{Colors.RED}无效选择，请输入'y'或'n'。{Colors.RESET}")

    amount_out_min_eth = 0

    deadline = int(web3.eth.get_block('latest').timestamp) + 300

    accounts = [web3.eth.account.from_key(pk) for pk in PRIVATE_KEYS]
    account_index = 0

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- 开始代币兑换NEX操作 ---{Colors.RESET}")

    if run_in_loop:
        while True:
            try:
                current_account = accounts[account_index]
                current_private_key = PRIVATE_KEYS[account_index]

                token_amount = round(random.uniform(min_token_amount, max_token_amount), 4)
                amount_in_token_wei = web3.to_wei(token_amount, 'ether')

                print(f"\n{Colors.WHITE}🔄 {Colors.BOLD}正在为账户准备兑换:{Colors.RESET}{Colors.WHITE} {current_account.address}{Colors.RESET}")
                print(f"{Colors.WHITE}   正在尝试将 {Colors.BOLD}{token_amount} {SELECTED_TOKEN_NAME}{Colors.RESET}{Colors.WHITE} 兑换为NEX...{Colors.RESET}")

                current_token_balance_wei = get_token_balance(current_account.address, TOKEN_ADDRESS)
                current_token_balance = web3.from_wei(current_token_balance_wei, 'ether')

                if current_token_balance_wei < amount_in_token_wei:
                    print(f"  {Colors.RED}❌ {Colors.BOLD}账户 {current_account.address} 的{SELECTED_TOKEN_NAME}余额不足{Colors.RESET}{Colors.RED}。余额: {current_token_balance} {SELECTED_TOKEN_NAME}。跳过到下一个账户。{Colors.RESET}")
                    account_index = (account_index + 1) % len(accounts)
                    time.sleep(1)
                    continue

                if not approve_token(current_account, current_private_key, TOKEN_ADDRESS, UNISWAP_V2_ROUTER_ADDRESS, amount_in_token_wei):
                    print(f"  {Colors.RED}❌ 无法为账户 {current_account.address} 授权代币。跳过此兑换。{Colors.RESET}")
                    account_index = (account_index + 1) % len(accounts)
                    time.sleep(1)
                    continue

                tx_hash = swap_tokens_for_eth(current_account, current_private_key, amount_in_token_wei, amount_out_min_eth, deadline, TOKEN_ADDRESS)
                print(f"{Colors.GREEN}  🎉 {Colors.BOLD}成功将 {token_amount} {SELECTED_TOKEN_NAME} 兑换为NEX{Colors.RESET}{Colors.GREEN} https://testnet3.explorer.nexus.xyz/tx/{tx_hash}{Colors.RESET}")

                delay = random.randint(5, 15)
                print(f"{Colors.YELLOW}  😴 等待 {delay} 秒后进行下一笔交易...{Colors.RESET}")
                time.sleep(delay)

                account_index = (account_index + 1) % len(accounts)

            except Exception as e:
                print(f"  {Colors.RED}❌ 账户 {accounts[account_index].address} 发生意外错误: {e}{Colors.RESET}")
                print(f"{Colors.YELLOW}  短暂暂停后将转到下一个账户...{Colors.RESET}")
                account_index = (account_index + 1) % len(accounts)
                time.sleep(5)
    else:
        for i in range(len(accounts)):
            try:
                current_account = accounts[account_index]
                current_private_key = PRIVATE_KEYS[account_index]

                token_amount = round(random.uniform(min_token_amount, max_token_amount), 4)
                amount_in_token_wei = web3.to_wei(token_amount, 'ether')

                print(f"\n{Colors.WHITE}🔄 {Colors.BOLD}正在为账户准备兑换:{Colors.RESET}{Colors.WHITE} {current_account.address}{Colors.RESET}")
                print(f"{Colors.WHITE}   正在尝试将 {Colors.BOLD}{token_amount} {SELECTED_TOKEN_NAME}{Colors.RESET}{Colors.WHITE} 兑换为NEX...{Colors.RESET}")

                current_token_balance_wei = get_token_balance(current_account.address, TOKEN_ADDRESS)
                current_token_balance = web3.from_wei(current_token_balance_wei, 'ether')

                if current_token_balance_wei < amount_in_token_wei:
                    print(f"  {Colors.RED}❌ {Colors.BOLD}账户 {current_account.address} 的{SELECTED_TOKEN_NAME}余额不足{Colors.RESET}{Colors.RED}。余额: {current_token_balance} {SELECTED_TOKEN_NAME}。跳过到下一个账户。{Colors.RESET}")
                    account_index = (account_index + 1) % len(accounts)
                    time.sleep(1)
                    continue

                if not approve_token(current_account, current_private_key, TOKEN_ADDRESS, UNISWAP_V2_ROUTER_ADDRESS, amount_in_token_wei):
                    print(f"  {Colors.RED}❌ 无法为账户 {current_account.address} 授权代币。跳过此兑换。{Colors.RESET}")
                    account_index = (account_index + 1) % len(accounts)
                    time.sleep(1)
                    continue

                tx_hash = swap_tokens_for_eth(current_account, current_private_key, amount_in_token_wei, amount_out_min_eth, deadline, TOKEN_ADDRESS)
                print(f"{Colors.GREEN}  🎉 {Colors.BOLD}成功将 {token_amount} {SELECTED_TOKEN_NAME} 兑换为NEX{Colors.RESET}{Colors.GREEN} https://testnet3.explorer.nexus.xyz/tx/{tx_hash}{Colors.RESET}")

                if i < len(accounts) - 1:
                    delay = random.randint(5, 15)
                    print(f"{Colors.YELLOW}  😴 等待 {delay} 秒后进行下一笔交易...{Colors.RESET}")
                    time.sleep(delay)

                account_index = (account_index + 1) % len(accounts)

            except Exception as e:
                print(f"  {Colors.RED}❌ 账户 {accounts[account_index].address} 发生意外错误: {e}{Colors.RESET}")
                print(f"{Colors.YELLOW}  短暂暂停后将转到下一个账户...{Colors.RESET}")
                account_index = (account_index + 1) % len(accounts)
                time.sleep(5)
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- 所有单次执行兑换已完成。 ---{Colors.RESET}")
