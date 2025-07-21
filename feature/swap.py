import os
import random
import time
from web3 import Web3
from dotenv import load_dotenv
from colorama import Fore

class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

load_dotenv()

PRIVATE_KEYS = os.getenv("PRIVATE_KEYS").split(",")
if not PRIVATE_KEYS:
    raise ValueError(f"{Colors.RED}.env文件中未找到私钥{Colors.RESET}")

RPC_URL = "https://testnet3.rpc.nexus.xyz"
CHAIN_ID = 3940

UNISWAP_V2_ROUTER_ADDRESS = "0x32aA9448586b06d2d42Fe4CFabF1c7AcD03bAE31"

AVAILABLE_TOKENS = {
    "NXS": "0x3eC55271351865ab99a9Ce92272C3E908f2E627b",
    "NEXI": "0x184eE44cF8B7Fec2371dc46D9076fFB2c1E0Ce65",
    "AIE": "0xF6f61565947621387ADF3BeD7ba02533aB013CCd"
}

TOKEN_ADDRESS = ""
SELECTED_TOKEN_NAME = ""

web3 = Web3(Web3.HTTPProvider(RPC_URL))
if not web3.is_connected():
    raise ConnectionError(f"{Colors.RED}连接RPC URL失败{Colors.RESET}")

uniswap_v2_router_abi = '[{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"}]'

uniswap_router = web3.eth.contract(address=Web3.to_checksum_address(UNISWAP_V2_ROUTER_ADDRESS), abi=uniswap_v2_router_abi)

def swap_eth_for_tokens(account, private_key, amount_in_wei, amount_out_min, deadline, token_address_to_swap):
    path = [web3.to_checksum_address("0xfAdf8E61BE6e95790d627057251AA41258a207d0"),
            web3.to_checksum_address(token_address_to_swap)]

    gas_price = web3.eth.gas_price

    while True:
        try:
            nonce = web3.eth.get_transaction_count(account.address, "pending")

            transaction = uniswap_router.functions.swapExactETHForTokens(
                amount_out_min,
                path,
                account.address,
                deadline
            ).build_transaction({
                'from': account.address,
                'value': amount_in_wei,
                'gas': 200000,
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
                print(f"  {Colors.YELLOW}⚠️ Gas价格过低或nonce问题，增加到 {web3.from_wei(gas_price, 'gwei')} gwei 并重试...{Colors.RESET}")
            elif 'out of gas' in str(e):
                gas_price += web3.to_wei(5, 'gwei')
                print(f"  {Colors.RED}🔥 交易Gas不足，增加到 {web3.from_wei(gas_price, 'gwei')} gwei 并重试...{Colors.RESET}")
            else:
                print(f"  {Colors.RED}❌ 交易过程中发生错误: {e}{Colors.RESET}")
                raise

if __name__ == "__main__":
    print(f"{Colors.BOLD}{Colors.MAGENTA}--- 🚀 Nexswap NEX兑换代币机器人 🚀 ---{Colors.RESET}")

    min_eth = 0.0
    max_eth = 0.0
    try:
        min_eth = float(input(f"{Colors.CYAN}输入最小NEX兑换数量(例如: 0.1): {Colors.RESET}"))
        max_eth = float(input(f"{Colors.CYAN}输入最大NEX兑换数量(例如: 0.5): {Colors.RESET}"))
        if min_eth <= 0 or max_eth <= 0 or min_eth > max_eth:
            raise ValueError("无效的NEX范围。请确保输入正值且最小值≤最大值。")
    except ValueError as e:
        print(f"{Colors.RED}错误: {e}{Colors.RESET}")
        exit()

    print(f"\n{Colors.BOLD}{Colors.BLUE}--- 选择要兑换的代币 ---{Colors.RESET}")
    token_names = list(AVAILABLE_TOKENS.keys())
    for i, token_name in enumerate(token_names):
        print(f"{Colors.WHITE}{i+1}. {token_name} ({AVAILABLE_TOKENS[token_name]}){Colors.RESET}")

    while True:
        try:
            choice = int(input(f"{Colors.CYAN}输入要兑换的代币编号: {Colors.RESET}"))
            if 1 <= choice <= len(token_names):
                SELECTED_TOKEN_NAME = token_names[choice - 1]
                TOKEN_ADDRESS = AVAILABLE_TOKENS[SELECTED_TOKEN_NAME]
                print(f"{Colors.GREEN}✅ 已选择: {Colors.BOLD}{SELECTED_TOKEN_NAME}{Colors.RESET}")
                break
            else:
                print(f"{Colors.RED}无效的选择。请输入有效的编号。{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}无效的输入。请输入数字。{Colors.RESET}")

    run_in_loop = False
    while True:
        loop_choice = input(f"{Colors.CYAN}是否要循环运行兑换?(y/n): {Colors.RESET}").lower().strip()
        if loop_choice in ['yes', 'y', '是']:
            run_in_loop = True
            print(f"{Colors.GREEN}✅ 循环模式已激活。兑换将连续运行。{Colors.RESET}")
            break
        elif loop_choice in ['no', 'n', '否']:
            run_in_loop = False
            print(f"{Colors.GREEN}✅ 单次执行模式。每个账户将运行一次兑换。{Colors.RESET}")
            break
        else:
            print(f"{Colors.RED}无效的选择。请输入'y'或'n'。{Colors.RESET}")

    amount_out_min = 0

    deadline = int(web3.eth.get_block('latest').timestamp) + 300

    accounts = [web3.eth.account.from_key(pk) for pk in PRIVATE_KEYS]
    account_index = 0

    def has_sufficient_balance(account, amount_in_wei):
        balance = web3.eth.get_balance(account.address)
        return balance >= amount_in_wei

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- 开始兑换操作 ---{Colors.RESET}")

    if run_in_loop:
        while True:
            try:
                current_account = accounts[account_index]
                current_private_key = PRIVATE_KEYS[account_index]

                eth_amount = round(random.uniform(min_eth, max_eth), 4)
                amount_in_wei = web3.to_wei(eth_amount, 'ether')

                print(f"\n{Colors.WHITE}🔄 {Colors.BOLD}准备为账户执行兑换:{Colors.RESET}{Colors.WHITE} {current_account.address}{Colors.RESET}")
                print(f"{Colors.WHITE}   尝试将 {Colors.BOLD}{eth_amount} NEX{Colors.RESET}{Colors.WHITE} 兑换为 {SELECTED_TOKEN_NAME}...{Colors.RESET}")

                if not has_sufficient_balance(current_account, amount_in_wei):
                    current_balance = web3.from_wei(web3.eth.get_balance(current_account.address), 'ether')
                    print(f"  {Colors.RED}❌ {Colors.BOLD}账户 {current_account.address} 余额不足{Colors.RESET}{Colors.RED}。余额: {current_balance} NEX。跳过此账户。{Colors.RESET}")
                    account_index = (account_index + 1) % len(accounts)
                    time.sleep(1)
                    continue

                tx_hash = swap_eth_for_tokens(current_account, current_private_key, amount_in_wei, amount_out_min, deadline, TOKEN_ADDRESS)
                print(f"{Colors.GREEN}  🎉 {Colors.BOLD}成功兑换 {eth_amount} NEX{Colors.RESET}{Colors.GREEN} https://testnet3.explorer.nexus.xyz/tx/{tx_hash}{Colors.RESET}")

                delay = random.randint(5, 15)
                print(f"{Colors.YELLOW}  😴 等待 {delay} 秒后进行下一笔交易...{Colors.RESET}")
                time.sleep(delay)

                account_index = (account_index + 1) % len(accounts)

            except Exception as e:
                print(f"  {Colors.RED}❌ 账户 {accounts[account_index].address} 兑换过程中发生意外错误: {e}{Colors.RESET}")
                print(f"{Colors.YELLOW}  短暂暂停后转到下一个账户...{Colors.RESET}")
                account_index = (account_index + 1) % len(accounts)
                time.sleep(5)
    else:
        for i in range(len(accounts)):
            try:
                current_account = accounts[account_index]
                current_private_key = PRIVATE_KEYS[account_index]

                eth_amount = round(random.uniform(min_eth, max_eth), 4)
                amount_in_wei = web3.to_wei(eth_amount, 'ether')

                print(f"\n{Colors.WHITE}🔄 {Colors.BOLD}准备为账户执行兑换:{Colors.RESET}{Colors.WHITE} {current_account.address}{Colors.RESET}")
                print(f"{Colors.WHITE}   尝试将 {Colors.BOLD}{eth_amount} NEX{Colors.RESET}{Colors.WHITE} 兑换为 {SELECTED_TOKEN_NAME}...{Colors.RESET}")

                if not has_sufficient_balance(current_account, amount_in_wei):
                    current_balance = web3.from_wei(web3.eth.get_balance(current_account.address), 'ether')
                    print(f"  {Colors.RED}❌ {Colors.BOLD}账户 {current_account.address} 余额不足{Colors.RESET}{Colors.RED}。余额: {current_balance} NEX。跳过此账户。{Colors.RESET}")
                    account_index = (account_index + 1) % len(accounts)
                    time.sleep(1)
                    continue

                tx_hash = swap_eth_for_tokens(current_account, current_private_key, amount_in_wei, amount_out_min, deadline, TOKEN_ADDRESS)
                print(f"{Colors.GREEN}  🎉 {Colors.BOLD}成功兑换 {eth_amount} NEX{Colors.RESET}{Colors.GREEN} https://testnet3.explorer.nexus.xyz/tx/{tx_hash}{Colors.RESET}")

                if i < len(accounts) - 1:
                    delay = random.randint(5, 15)
                    print(f"{Colors.YELLOW}  😴 等待 {delay} 秒后进行下一笔交易...{Colors.RESET}")
                    time.sleep(delay)

                account_index = (account_index + 1) % len(accounts)

            except Exception as e:
                print(f"  {Colors.RED}❌ 账户 {accounts[account_index].address} 兑换过程中发生意外错误: {e}{Colors.RESET}")
                print(f"{Colors.YELLOW}  短暂暂停后转到下一个账户...{Colors.RESET}")
                account_index = (account_index + 1) % len(accounts)
                time.sleep(5)
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- 所有单次兑换已完成 ---{Colors.RESET}")
