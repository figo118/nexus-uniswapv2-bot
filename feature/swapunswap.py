import os
import random
import time
from web3 import Web3
from dotenv import load_dotenv

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
    raise ConnectionError(f"{Colors.RED}连接RPC URL失败{Colors.RESET}")

uniswap_v2_router_abi = '''
[
    {
        "inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type":"uint256"}
        ],
        "name": "swapExactTokensForETH",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type":"uint256[]"}
        ],
        "stateMutability": "nonpayable",
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
            print(f"  {Colors.YELLOW}⏳ 正在批准 {web3.from_wei(amount_to_approve, 'ether')} 代币给Uniswap路由器...{Colors.RESET}")

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
            print(f"  {Colors.GREEN}✅ {Colors.BOLD}批准交易已发送{Colors.RESET}{Colors.GREEN}: {web3.to_hex(tx_hash)}{Colors.RESET}")
            web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            print(f"{Colors.GREEN}  🎉 批准确认成功!{Colors.RESET}")
            return True

        except Exception as e:
            if 'replacement transaction underpriced' in str(e) or 'nonce too low' in str(e):
                gas_price += web3.to_wei(2, 'gwei')
                print(f"  {Colors.YELLOW}⚠️ 批准交易的Gas价格过低或nonce问题，增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            elif 'out of gas' in str(e):
                gas_price += web3.to_wei(5, 'gwei')
                print(f"  {Colors.RED}🔥 批准交易Gas不足，增加Gas价格至 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            else:
                print(f"  {Colors.RED}❌ 批准过程中发生错误: {e}{Colors.RESET}")
                return False

def swap_eth_for_tokens(account, private_key, amount_in_wei, amount_out_min, deadline, token_address_to_swap):
    path = [web3.to_checksum_address(WETH_ADDRESS),
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
                'gas': 220000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': CHAIN_ID
            })

            signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"  {Colors.GREEN}✅ {Colors.BOLD}NEX兑换交易已发送{Colors.RESET}{Colors.GREEN} https://testnet3.explorer.nexus.xyz/tx/{web3.to_hex(tx_hash)}{Colors.RESET}")
            web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            print(f"{Colors.GREEN}  🎉 NEX兑换为 {SELECTED_TOKEN_NAME} 确认成功!{Colors.RESET}")
            return web3.to_hex(tx_hash)

        except Exception as e:
            if 'replacement transaction underpriced' in str(e) or 'nonce too low' in str(e):
                gas_price += web3.to_wei(2, 'gwei')
                print(f"  {Colors.YELLOW}⚠️ Gas价格过低或nonce问题，增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            elif 'out of gas' in str(e):
                gas_price += web3.to_wei(5, 'gwei')
                print(f"  {Colors.RED}🔥 交易Gas不足，增加Gas价格至 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            else:
                print(f"  {Colors.RED}❌ NEX兑换代币过程中发生错误: {e}{Colors.RESET}")
                raise

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
            print(f"  {Colors.GREEN}✅ {Colors.BOLD}代币反向兑换交易已发送{Colors.RESET}{Colors.GREEN} https://testnet3.explorer.nexus.xyz/tx/{web3.to_hex(tx_hash)}{Colors.RESET}")
            web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            print(f"{Colors.GREEN}  🎉 {SELECTED_TOKEN_NAME} 兑换回NEX确认成功!{Colors.RESET}")
            return web3.to_hex(tx_hash)

        except Exception as e:
            if 'replacement transaction underpriced' in str(e) or 'nonce too low' in str(e):
                gas_price += web3.to_wei(2, 'gwei')
                print(f"  {Colors.YELLOW}⚠️ Gas价格过低或nonce问题，增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            elif 'out of gas' in str(e):
                gas_price += web3.to_wei(5, 'gwei')
                print(f"  {Colors.RED}🔥 交易Gas不足，增加Gas价格至 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            else:
                print(f"  {Colors.RED}❌ 代币兑换NEX过程中发生错误: {e}{Colors.RESET}")
                raise

def has_sufficient_eth_balance(account, amount_in_wei):
    balance = web3.eth.get_balance(account.address)
    return balance >= amount_in_wei

if __name__ == "__main__":
    print(f"{Colors.BOLD}{Colors.MAGENTA}--- 🔄 Nexswap兑换循环 🔄 ---{Colors.RESET}")

    min_eth = 0.0
    max_eth = 0.0
    try:
        min_eth = float(input(f"{Colors.CYAN}输入初始兑换的最小NEX数量(例如: 0.1): {Colors.RESET}"))
        max_eth = float(input(f"{Colors.CYAN}输入初始兑换的最大NEX数量(例如: 0.5): {Colors.RESET}"))
        if min_eth <= 0 or max_eth <= 0 or min_eth > max_eth:
            raise ValueError("无效的NEX范围。请确保输入正值且最小值不大于最大值。")
    except ValueError as e:
        print(f"{Colors.RED}错误: {e}{Colors.RESET}")
        exit()

    print(f"\n{Colors.BOLD}{Colors.BLUE}--- 选择要兑换的目标代币(NEX兑换为代币) ---{Colors.RESET}")
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
                print(f"{Colors.RED}无效选择。请输入有效编号。{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}无效输入。请输入数字。{Colors.RESET}")

    unswap_percentage = 0.0
    while True:
        try:
            percent_input = float(input(f"{Colors.CYAN}\n输入要反向兑换回NEX的{SELECTED_TOKEN_NAME}百分比(例如: 50表示50%): {Colors.RESET}"))
            if 0 <= percent_input <= 100:
                unswap_percentage = percent_input / 100.0
                print(f"{Colors.GREEN}✅ 您选择将 {Colors.BOLD}{percent_input:.2f}%{Colors.RESET}{Colors.GREEN} 的接收代币反向兑换。{Colors.RESET}")
                break
            else:
                print(f"{Colors.RED}无效百分比。请输入0到100之间的值。{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}无效输入。请输入数字。{Colors.RESET}")

    run_in_loop = False
    while True:
        loop_choice = input(f"{Colors.CYAN}是否要连续运行兑换循环? (y/n): {Colors.RESET}").lower().strip()
        if loop_choice in ['yes', 'y', '是']:
            run_in_loop = True
            print(f"{Colors.GREEN}✅ 循环模式已激活。兑换循环将连续运行。{Colors.RESET}")
            break
        elif loop_choice in ['no', 'n', '否']:
            run_in_loop = False
            print(f"{Colors.GREEN}✅ 单次执行模式。兑换循环将为每个账户运行一次。{Colors.RESET}")
            break
        else:
            print(f"{Colors.RED}无效选择。请输入'y'或'n'。{Colors.RESET}")

    amount_out_min = 0
    amount_out_min_eth = 0

    deadline = int(web3.eth.get_block('latest').timestamp) + 300

    accounts = [web3.eth.account.from_key(pk) for pk in PRIVATE_KEYS]
    account_index = 0

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- 开始兑换循环 ---{Colors.RESET}")

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

            # --- NEX兑换代币 ---
            print(f"\n{Colors.BOLD}{Colors.CYAN}--- 开始NEX兑换代币 ---{Colors.RESET}")
            eth_amount = round(random.uniform(min_eth, max_eth), 4)
            amount_in_wei = web3.to_wei(eth_amount, 'ether')

            print(f"{Colors.WHITE}🔄 尝试将 {Colors.BOLD}{eth_amount} NEX{Colors.RESET}{Colors.WHITE} 兑换为 {SELECTED_TOKEN_NAME}...{Colors.RESET}")

            if not has_sufficient_eth_balance(current_account, amount_in_wei):
                current_eth_balance = web3.from_wei(web3.eth.get_balance(current_account.address), 'ether')
                print(f"  {Colors.RED}❌ {Colors.BOLD}账户 {current_account.address} 的NEX余额不足{Colors.RESET}{Colors.RED}。余额: {current_eth_balance} NEX。跳过兑换。{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(1)
                continue

            estimated_token_received_wei = 0
            try:
                swap_path_eth_to_token = [web3.to_checksum_address(WETH_ADDRESS), web3.to_checksum_address(TOKEN_ADDRESS)]
                estimated_amounts = uniswap_router.functions.getAmountsOut(amount_in_wei, swap_path_eth_to_token).call()
                estimated_token_received_wei = estimated_amounts[1]
                print(f"   {Colors.CYAN}预计接收的 {SELECTED_TOKEN_NAME} 数量: {web3.from_wei(estimated_token_received_wei, 'ether')} {SELECTED_TOKEN_NAME}{Colors.RESET}")
            except Exception as e:
                print(f"  {Colors.RED}❌ 获取预计代币数量失败: {e}。跳过兑换。{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(1)
                continue

            try:
                swap_eth_for_tokens(current_account, current_private_key, amount_in_wei, amount_out_min, deadline, TOKEN_ADDRESS)
            except Exception as e:
                print(f"  {Colors.RED}❌ NEX兑换 {SELECTED_TOKEN_NAME} 失败: {e}。跳过反向兑换。{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(5)
                continue

            delay = random.randint(5, 10)
            print(f"{Colors.YELLOW}😴 兑换后等待 {delay} 秒...{Colors.RESET}")
            time.sleep(delay)

            # --- 代币反向兑换NEX ---
            print(f"\n{Colors.BOLD}{Colors.CYAN}--- 开始代币反向兑换NEX ---{Colors.RESET}")
            if unswap_percentage > 0 and estimated_token_received_wei > 0:
                unswap_token_amount_wei = int(estimated_token_received_wei * unswap_percentage)
                unswap_token_amount = web3.from_wei(unswap_token_amount_wei, 'ether')

                print(f"{Colors.WHITE}🔄 尝试将 {Colors.BOLD}{unswap_token_amount} {SELECTED_TOKEN_NAME}{Colors.RESET}{Colors.WHITE} ({unswap_percentage*100:.2f}%) 兑换回NEX...{Colors.RESET}")

                current_token_balance_wei_after_swap = get_token_balance(current_account.address, TOKEN_ADDRESS)
                current_token_balance_after_swap = web3.from_wei(current_token_balance_wei_after_swap, 'ether')

                if current_token_balance_wei_after_swap < unswap_token_amount_wei:
                    print(f"  {Colors.RED}❌ 反向兑换的 {SELECTED_TOKEN_NAME} 余额不足。余额: {current_token_balance_after_swap} {SELECTED_TOKEN_NAME}。跳过反向兑换。{Colors.RESET}")
                else:
                    if not approve_token(current_account, current_private_key, TOKEN_ADDRESS, UNISWAP_V2_ROUTER_ADDRESS, unswap_token_amount_wei):
                        print(f"  {Colors.RED}❌ 批准代币反向兑换失败。跳过反向兑换。{Colors.RESET}")
                    else:
                        try:
                            swap_tokens_for_eth(current_account, current_private_key, unswap_token_amount_wei, amount_out_min_eth, deadline, TOKEN_ADDRESS)
                        except Exception as e:
                            print(f"  {Colors.RED}❌ {SELECTED_TOKEN_NAME} 兑换回NEX失败: {e}。{Colors.RESET}")
            else:
                print(f"  {Colors.CYAN}ℹ️ 未执行反向兑换，因为百分比为0%或预计接收代币为0。{Colors.RESET}")

            delay = random.randint(5, 10)
            print(f"{Colors.YELLOW}😴 反向兑换后等待 {delay} 秒...{Colors.RESET}")
            time.sleep(delay)

            current_operation_retries = 0
            account_index = (account_index + 1) % len(accounts)
            if not run_in_loop and account_index == 0:
                break

        except Exception as e:
            error_message = str(e)
            print(f"\n{Colors.RED}❌ 账户 {current_account.address} 的循环中发生意外错误: {error_message}{Colors.RESET}")

            if "Could not transact with/call contract function, is contract deployed correctly and chain synced?" in error_message and current_operation_retries < max_retries_per_operation:
                current_operation_retries += 1
                print(f"{Colors.YELLOW}⚠️ 正在重试 {current_account.address} 的操作 ({current_operation_retries}/{max_retries_per_operation} 次重试)...{Colors.RESET}")
                time.sleep(5)
                continue
            else:
                current_operation_retries = 0
                print(f"{Colors.YELLOW}  短暂暂停后移至下一个账户...{Colors.RESET}")
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(5)

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- 所有兑换循环已完成。 ---{Colors.RESET}")
