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
    MAGENTA = "\033[95m"  # 紫色
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

LP_TOKEN_ADDRESSES = {
    "NXS": "0x053d715880A9A269199186B8BF26909cc6725763",
    "NEXI": "0xFA1BB4324F96Ba4264B95Af1ae706E77ED5B90A8",
    "AIE": "0xa47b8266D2e5a23275a4679254eF46d883576Bf4"
}

TOKEN_ADDRESS = ""
SELECTED_TOKEN_NAME = ""
LP_TOKEN_ADDRESS = ""

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
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "amountTokenDesired", "type": "uint256"},
            {"internalType": "uint256", "name": "amountTokenMin", "type": "uint256"},
            {"internalType": "uint256", "name": "amountETHMin", "type": "uint256"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type":"uint256"}
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
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "liquidity", "type": "uint256"},
            {"internalType": "uint256", "name": "amountTokenMin", "type": "uint256"},
            {"internalType": "uint256", "name": "amountETHMin", "type": "uint256"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type":"uint256"}
        ],
        "name": "removeLiquidityETH",
        "outputs": [
            {"internalType": "uint256", "name": "amountToken", "type": "uint256"},
            {"internalType": "uint256", "name": "amountETH", "type": "uint256"}
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
    },
    {
        "constant": true,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "type": "function"
    }
]
'''

uniswap_v2_pair_abi = '''
[
    {
        "constant": true,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "_reserve0", "type": "uint256"},
            {"internalType": "uint112", "name": "_reserve1", "type": "uint256"},
            {"internalType": "uint32", "name": "blockTimestampLast", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]
'''

uniswap_router = web3.eth.contract(address=Web3.to_checksum_address(UNISWAP_V2_ROUTER_ADDRESS), abi=uniswap_v2_router_abi)

def get_erc20_contract(address):
    return web3.eth.contract(address=web3.to_checksum_address(address), abi=erc20_abi)

def get_pair_contract(pair_address):
    return web3.eth.contract(address=web3.to_checksum_address(pair_address), abi=uniswap_v2_pair_abi)

def get_token_balance(account_address, token_address):
    token_contract = get_erc20_contract(token_address)
    return token_contract.functions.balanceOf(account_address).call()

def approve_token(account, private_key, token_address, router_address, amount_to_approve):
    token_contract = get_erc20_contract(token_address)
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
            print(f"  {Colors.GREEN}✅ {Colors.BOLD}批准交易已发送:{Colors.RESET}{Colors.GREEN} https://testnet3.explorer.nexus.xyz/tx/{web3.to_hex(tx_hash)}{Colors.RESET}")
            web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            print(f"{Colors.GREEN}  🎉 批准确认成功!{Colors.RESET}")
            return True

        except Exception as e:
            if 'replacement transaction underpriced' in str(e) or 'nonce too low' in str(e):
                gas_price += web3.to_wei(2, 'gwei')
                print(f"  {Colors.YELLOW}⚠️ 批准交易gas价格过低或nonce问题，增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            elif 'out of gas' in str(e):
                gas_price += web3.to_wei(5, 'gwei')
                print(f"  {Colors.RED}🔥 批准交易gas不足，增加gas价格到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
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
            print(f"  {Colors.GREEN}✅ {Colors.BOLD}NEX兑换交易已发送:{Colors.RESET}{Colors.GREEN} https://testnet3.explorer.nexus.xyz/tx/{web3.to_hex(tx_hash)}{Colors.RESET}")
            web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            print(f"{Colors.GREEN}  🎉 NEX兑换为 {SELECTED_TOKEN_NAME} 确认成功!{Colors.RESET}")
            return web3.to_hex(tx_hash)

        except Exception as e:
            if 'replacement transaction underpriced' in str(e) or 'nonce too low' in str(e):
                gas_price += web3.to_wei(2, 'gwei')
                print(f"  {Colors.YELLOW}⚠️ gas价格过低或nonce问题，增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            elif 'out of gas' in str(e):
                gas_price += web3.to_wei(5, 'gwei')
                print(f"  {Colors.RED}🔥 交易gas不足，增加gas价格到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
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
            print(f"  {Colors.GREEN}✅ {Colors.BOLD}代币反向兑换交易已发送:{Colors.RESET}{Colors.GREEN} https://testnet3.explorer.nexus.xyz/tx/{web3.to_hex(tx_hash)}{Colors.RESET}")
            web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            print(f"{Colors.GREEN}  🎉 {SELECTED_TOKEN_NAME} 兑换为NEX确认成功!{Colors.RESET}")
            return web3.to_hex(tx_hash)

        except Exception as e:
            if 'replacement transaction underpriced' in str(e) or 'nonce too low' in str(e):
                gas_price += web3.to_wei(2, 'gwei')
                print(f"  {Colors.YELLOW}⚠️ gas价格过低或nonce问题，增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            elif 'out of gas' in str(e):
                gas_price += web3.to_wei(5, 'gwei')
                print(f"  {Colors.RED}🔥 交易gas不足，增加gas价格到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            else:
                print(f"  {Colors.RED}❌ 代币兑换NEX过程中发生错误: {e}{Colors.RESET}")
                raise

def add_liquidity_eth(account, private_key, token_address, amount_token_desired, amount_eth_desired, amount_token_min, amount_eth_min, deadline):
    gas_price = web3.eth.gas_price

    while True:
        try:
            nonce = web3.eth.get_transaction_count(account.address, "pending")
            print(f"  {Colors.YELLOW}⏳ 正在为 {SELECTED_TOKEN_NAME} 和NEX添加流动性...{Colors.RESET}")

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
            print(f"  {Colors.GREEN}✅ {Colors.BOLD}添加流动性交易已发送:{Colors.RESET}{Colors.GREEN} https://testnet3.explorer.nexus.xyz/tx/{web3.to_hex(tx_hash)}{Colors.RESET}")
            web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            print(f"{Colors.GREEN}  🎉 为 {SELECTED_TOKEN_NAME}/NEX 添加流动性确认成功!{Colors.RESET}")
            return web3.to_hex(tx_hash)

        except Exception as e:
            if 'replacement transaction underpriced' in str(e) or 'nonce too low' in str(e):
                gas_price += web3.to_wei(2, 'gwei')
                print(f"  {Colors.YELLOW}⚠️ 添加流动性gas价格过低或nonce问题，增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            elif 'out of gas' in str(e):
                gas_price += web3.to_wei(5, 'gwei')
                print(f"  {Colors.RED}🔥 添加流动性交易gas不足，增加gas价格到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            else:
                print(f"  {Colors.RED}❌ 添加流动性过程中发生错误: {e}{Colors.RESET}")
                raise

def remove_liquidity_eth(account, private_key, token_address, liquidity_amount, amount_token_min, amount_eth_min, deadline):
    gas_price = web3.eth.gas_price

    while True:
        try:
            nonce = web3.eth.get_transaction_count(account.address, "pending")
            print(f"  {Colors.YELLOW}⏳ 正在移除 {SELECTED_TOKEN_NAME}/NEX 的流动性...{Colors.RESET}")

            transaction = uniswap_router.functions.removeLiquidityETH(
                web3.to_checksum_address(token_address),
                liquidity_amount,
                amount_token_min,
                amount_eth_min,
                account.address,
                deadline
            ).build_transaction({
                'from': account.address,
                'value': 0,
                'gas': 320000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': CHAIN_ID
            })

            signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"  {Colors.GREEN}✅ {Colors.BOLD}移除流动性交易已发送:{Colors.RESET}{Colors.GREEN} https://testnet3.explorer.nexus.xyz/tx/{web3.to_hex(tx_hash)}{Colors.RESET}")
            web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            print(f"{Colors.GREEN}  🎉 {SELECTED_TOKEN_NAME}/NEX 流动性移除确认成功!{Colors.RESET}")
            return web3.to_hex(tx_hash)

        except Exception as e:
            if 'replacement transaction underpriced' in str(e) or 'nonce too low' in str(e):
                gas_price += web3.to_wei(2, 'gwei')
                print(f"  {Colors.YELLOW}⚠️ 移除流动性gas价格过低或nonce问题，增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            elif 'out of gas' in str(e):
                gas_price += web3.to_wei(5, 'gwei')
                print(f"  {Colors.RED}🔥 移除流动性交易gas不足，增加gas价格到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            else:
                print(f"  {Colors.RED}❌ 移除流动性过程中发生错误: {e}{Colors.RESET}")
                raise

def has_sufficient_eth_balance(account, amount_in_wei):
    balance = web3.eth.get_balance(account.address)
    return balance >= amount_in_wei

if __name__ == "__main__":
    print(f"{Colors.BOLD}{Colors.MAGENTA}--- 🌟 Nexswap多功能机器人 🌟 ---{Colors.RESET}")

    print(f"\n{Colors.BOLD}{Colors.BLUE}--- 用户输入参数 ---{Colors.RESET}")

    min_eth_swap = 0.0
    max_eth_swap = 0.0
    try:
        min_eth_swap = float(input(f"{Colors.CYAN}输入初始兑换的最小NEX数量(例如0.1): {Colors.RESET}"))
        max_eth_swap = float(input(f"{Colors.CYAN}输入初始兑换的最大NEX数量(例如0.5): {Colors.RESET}"))
        if min_eth_swap <= 0 or max_eth_swap <= 0 or min_eth_swap > max_eth_swap:
            raise ValueError("无效的NEX范围。请确保输入正值且最小值<=最大值。")
    except ValueError as e:
        print(f"{Colors.RED}NEX兑换输入错误: {e}{Colors.RESET}")
        exit()

    print(f"\n{Colors.BOLD}{Colors.BLUE}--- 选择所有操作的目标代币 ---{Colors.RESET}")
    token_names = list(AVAILABLE_TOKENS.keys())
    for i, token_name in enumerate(token_names):
        print(f"{Colors.WHITE}{i+1}. {token_name} ({AVAILABLE_TOKENS[token_name]}){Colors.RESET}")

    while True:
        try:
            choice = int(input(f"{Colors.CYAN}输入要使用的代币编号: {Colors.RESET}"))
            if 1 <= choice <= len(token_names):
                SELECTED_TOKEN_NAME = token_names[choice - 1]
                TOKEN_ADDRESS = AVAILABLE_TOKENS[SELECTED_TOKEN_NAME]
                LP_TOKEN_ADDRESS = LP_TOKEN_ADDRESSES.get(SELECTED_TOKEN_NAME)
                if not LP_TOKEN_ADDRESS:
                    print(f"{Colors.RED}❌ 未在提供的列表中找到 {SELECTED_TOKEN_NAME} 的LP代币地址。{Colors.RESET}")
                    exit()
                print(f"{Colors.GREEN}✅ 您选择了: {Colors.BOLD}{SELECTED_TOKEN_NAME}{Colors.RESET}")
                print(f"{Colors.CYAN}ℹ️ 关联的LP代币地址: {LP_TOKEN_ADDRESS}{Colors.RESET}")
                break
            else:
                print(f"{Colors.RED}无效选择。请输入有效编号。{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}无效输入。请输入数字。{Colors.RESET}")

    unswap_percentage = 0.0
    while True:
        try:
            percent_input = float(input(f"{Colors.CYAN}\n输入要反向兑换回NEX的 {SELECTED_TOKEN_NAME} 百分比(例如50表示50%): {Colors.RESET}"))
            if 0 <= percent_input <= 100:
                unswap_percentage = percent_input / 100.0
                print(f"{Colors.GREEN}✅ 您选择反向兑换 {Colors.BOLD}{percent_input:.2f}%{Colors.RESET}{Colors.GREEN} 收到的代币。{Colors.RESET}")
                break
            else:
                print(f"{Colors.RED}无效百分比。请输入0到100之间的值。{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}无效输入。请输入数字。{Colors.RESET}")

    desired_eth_add_liquidity = 0.0
    try:
        desired_eth_add_liquidity = float(input(f"{Colors.CYAN}\n输入要添加为流动性的NEX数量(例如0.05): {Colors.RESET}"))
        if desired_eth_add_liquidity <= 0:
            raise ValueError("NEX数量必须为正数。")
    except ValueError as e:
        print(f"{Colors.RED}添加流动性NEX输入错误: {e}。请输入数字。{Colors.RESET}")
        exit()

    remove_percentage_lp = 0.0
    while True:
        try:
            percent_input_lp = float(input(f"{Colors.CYAN}\n输入要移除的LP代币({SELECTED_TOKEN_NAME}/NEX)百分比(例如50表示50%): {Colors.RESET}"))
            if not (0 < percent_input_lp <= 100):
                raise ValueError("百分比必须在0(不含)到100(含)之间。")
            remove_percentage_lp = percent_input_lp / 100.0
            print(f"{Colors.GREEN}✅ 您选择移除 {Colors.BOLD}{percent_input_lp:.2f}%{Colors.RESET}{Colors.GREEN} 的LP代币。{Colors.RESET}")
            break
        except ValueError as e:
            print(f"{Colors.RED}移除流动性百分比输入错误: {e}。请输入数字。{Colors.RESET}")

    run_in_loop = False
    while True:
        loop_choice = input(f"{Colors.CYAN}\n您希望整个周期(兑换、反向兑换、添加、移除)连续循环运行吗? (yes/no): {Colors.RESET}").lower().strip()
        if loop_choice in ['yes', 'y']:
            run_in_loop = True
            print(f"{Colors.GREEN}✅ 循环模式已激活。周期将连续运行。{Colors.RESET}")
            break
        elif loop_choice in ['no', 'n']:
            run_in_loop = False
            print(f"{Colors.GREEN}✅ 单次执行模式。周期将为每个账户运行一次。{Colors.RESET}")
            break
        else:
            print(f"{Colors.RED}无效选择。请输入'yes'或'no'。{Colors.RESET}")

    deadline = int(web3.eth.get_block('latest').timestamp) + 300

    accounts = [web3.eth.account.from_key(pk) for pk in PRIVATE_KEYS]
    account_index = 0

    slippage_tolerance_percent = 0.5

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- 开始自动化周期(兑换 -> 反向兑换 -> 添加流动性 -> 移除流动性) ---{Colors.RESET}")

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

            # --- 兑换NEX为代币 ---
            print(f"\n{Colors.BOLD}{Colors.CYAN}--- 开始NEX兑换代币操作 ---{Colors.RESET}")
            eth_amount_for_swap = round(random.uniform(min_eth_swap, max_eth_swap), 4)
            amount_in_wei_swap = web3.to_wei(eth_amount_for_swap, 'ether')

            print(f"{Colors.WHITE}🔄 尝试兑换 {Colors.BOLD}{eth_amount_for_swap} NEX{Colors.RESET}{Colors.WHITE} 为 {SELECTED_TOKEN_NAME}...{Colors.RESET}")

            if not has_sufficient_eth_balance(current_account, amount_in_wei_swap):
                current_eth_balance = web3.from_wei(web3.eth.get_balance(current_account.address), 'ether')
                print(f"  {Colors.RED}❌ {Colors.BOLD}兑换NEX余额不足{Colors.RESET}{Colors.RED}。余额: {current_eth_balance} NEX。跳过此账户的整个周期。{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(2)
                continue

            estimated_token_received_wei_swap = 0
            try:
                path_eth_to_token = [web3.to_checksum_address(WETH_ADDRESS), web3.to_checksum_address(TOKEN_ADDRESS)]
                estimated_amounts = uniswap_router.functions.getAmountsOut(amount_in_wei_swap, path_eth_to_token).call()
                estimated_token_received_wei_swap = estimated_amounts[1]
                print(f"   {Colors.CYAN}预计收到的 {SELECTED_TOKEN_NAME}: {web3.from_wei(estimated_token_received_wei_swap, 'ether')} {SELECTED_TOKEN_NAME}{Colors.RESET}")
            except Exception as e:
                print(f"  {Colors.RED}❌ 获取兑换预估代币数量失败: {e}。跳过此账户的整个周期。{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(2)
                continue

            try:
                swap_eth_for_tokens(current_account, current_private_key, amount_in_wei_swap, 0, deadline, TOKEN_ADDRESS)
            except Exception as e:
                print(f"  {Colors.RED}❌ NEX兑换 {SELECTED_TOKEN_NAME} 失败: {e}。跳过此账户的剩余周期。{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(5)
                continue

            delay = random.randint(5, 10)
            print(f"{Colors.YELLOW}😴 兑换后等待 {delay} 秒...{Colors.RESET}")
            time.sleep(delay)

            # --- 反向兑换代币为NEX ---
            print(f"\n{Colors.BOLD}{Colors.CYAN}--- 开始代币反向兑换NEX操作 ---{Colors.RESET}")
            if unswap_percentage > 0 and estimated_token_received_wei_swap > 0:
                unswap_token_amount_wei = int(estimated_token_received_wei_swap * unswap_percentage)
                unswap_token_amount = web3.from_wei(unswap_token_amount_wei, 'ether')

                print(f"{Colors.WHITE}🔄 尝试反向兑换 {Colors.BOLD}{unswap_token_amount} {SELECTED_TOKEN_NAME}{Colors.RESET}{Colors.WHITE} ({unswap_percentage*100:.2f}%) 回NEX...{Colors.RESET}")

                current_token_balance_wei_after_swap = get_token_balance(current_account.address, TOKEN_ADDRESS)
                current_token_balance_after_swap = web3.from_wei(current_token_balance_wei_after_swap, 'ether')

                if current_token_balance_wei_after_swap < unswap_token_amount_wei:
                    print(f"  {Colors.RED}❌ 反向兑换 {SELECTED_TOKEN_NAME} 余额不足。余额: {current_token_balance_after_swap} {SELECTED_TOKEN_NAME}。跳过反向兑换。{Colors.RESET}")
                else:
                    if not approve_token(current_account, current_private_key, TOKEN_ADDRESS, UNISWAP_V2_ROUTER_ADDRESS, unswap_token_amount_wei):
                        print(f"  {Colors.RED}❌ 批准代币反向兑换失败。跳过反向兑换。{Colors.RESET}")
                    else:
                        try:
                            swap_tokens_for_eth(current_account, current_private_key, unswap_token_amount_wei, 0, deadline, TOKEN_ADDRESS)
                        except Exception as e:
                            print(f"  {Colors.RED}❌ {SELECTED_TOKEN_NAME} 反向兑换NEX失败: {e}。{Colors.RESET}")
            else:
                print(f"  {Colors.CYAN}ℹ️ 未执行反向兑换，因为百分比为0%或预估收到代币为0。{Colors.RESET}")

            delay = random.randint(5, 10)
            print(f"{Colors.YELLOW}😴 反向兑换后等待 {delay} 秒...{Colors.RESET}")
            time.sleep(delay)

            # --- ADD LIQUIDITY ---
            print(f"\n{Colors.BOLD}{Colors.CYAN}--- Initiating ADD LIQUIDITY ---{Colors.RESET}")
            amount_token_add_liquidity_wei = 0
            try:
                path_eth_to_token = [web3.to_checksum_address(WETH_ADDRESS), web3.to_checksum_address(TOKEN_ADDRESS)]
                amounts_out = uniswap_router.functions.getAmountsOut(web3.to_wei(desired_eth_add_liquidity, 'ether'), path_eth_to_token).call()
                amount_token_add_liquidity = web3.from_wei(amounts_out[1], 'ether')
                amount_token_add_liquidity_wei = amounts_out[1]
                print(f"   {Colors.CYAN}Approximately {Colors.BOLD}{amount_token_add_liquidity:.4f} {SELECTED_TOKEN_NAME}{Colors.RESET}{Colors.CYAN} needed for {desired_eth_add_liquidity} NEX at current ratio.{Colors.RESET}")
            except Exception as e:
                print(f"  {Colors.RED}❌ Failed to calculate required {SELECTED_TOKEN_NAME} for add liquidity: {e}. Skipping add liquidity.{Colors.RESET}")
                delay = random.randint(5, 10)
                print(f"{Colors.YELLOW}😴 Waiting {delay} seconds after ADD LIQUIDITY failure...{Colors.RESET}")
                time.sleep(delay)
                pass
            else:
                if not has_sufficient_eth_balance(current_account, web3.to_wei(desired_eth_add_liquidity, 'ether')):
                    current_eth_balance = web3.from_wei(web3.eth.get_balance(current_account.address), 'ether')
                    print(f"  {Colors.RED}❌ {Colors.BOLD}Insufficient NEX balance for add liquidity{Colors.RESET}{Colors.RED}. Balance: {current_eth_balance} NEX. Skipping add liquidity.{Colors.RESET}")
                elif get_token_balance(current_account.address, TOKEN_ADDRESS) < amount_token_add_liquidity_wei:
                    current_token_balance = web3.from_wei(get_token_balance(current_account.address, TOKEN_ADDRESS), 'ether')
                    print(f"  {Colors.RED}❌ {Colors.BOLD}Insufficient {SELECTED_TOKEN_NAME} balance for add liquidity{Colors.RESET}{Colors.RED}. Balance: {current_token_balance} {SELECTED_TOKEN_NAME}. Skipping add liquidity.{Colors.RESET}")
                else:
                    if not approve_token(current_account, current_private_key, TOKEN_ADDRESS, UNISWAP_V2_ROUTER_ADDRESS, amount_token_add_liquidity_wei):
                        print(f"  {Colors.RED}❌ Failed to approve token for add liquidity. Skipping add liquidity.{Colors.RESET}")
                    else:
                        amount_token_min_add = int(amount_token_add_liquidity_wei * (1 - slippage_tolerance_percent / 100))
                        amount_eth_min_add = int(web3.to_wei(desired_eth_add_liquidity, 'ether') * (1 - slippage_tolerance_percent / 100))

                        print(f"   {Colors.CYAN}Slippage Tolerance: {slippage_tolerance_percent}%{Colors.RESET}")
                        print(f"   {Colors.CYAN}Minimum {SELECTED_TOKEN_NAME} (Add): {web3.from_wei(amount_token_min_add, 'ether')}{Colors.RESET}")
                        print(f"   {Colors.CYAN}Minimum NEX (Add): {web3.from_wei(amount_eth_min_add, 'ether')}{Colors.RESET}")

                        try:
                            add_liquidity_eth(current_account, current_private_key, TOKEN_ADDRESS,
                                              amount_token_add_liquidity_wei, web3.to_wei(desired_eth_add_liquidity, 'ether'),
                                              amount_token_min_add, amount_eth_min_add, deadline)
                        except Exception as e:
                            print(f"  {Colors.RED}❌ Add liquidity failed: {e}.{Colors.RESET}")

            delay = random.randint(5, 10)
            print(f"{Colors.YELLOW}😴 Waiting {delay} seconds after ADD LIQUIDITY...{Colors.RESET}")
            time.sleep(delay)

            # --- REMOVE LIQUIDITY ---
            print(f"\n{Colors.BOLD}{Colors.CYAN}--- Initiating REMOVE LIQUIDITY ---{Colors.RESET}")
            current_lp_balance_wei = get_token_balance(current_account.address, LP_TOKEN_ADDRESS)
            current_lp_balance = web3.from_wei(current_lp_balance_wei, 'ether')
            print(f"   {Colors.CYAN}Your LP Token ({SELECTED_TOKEN_NAME}/NEX) Balance: {current_lp_balance:.8f}{Colors.RESET}")

            liquidity_to_remove_wei = 0
            if current_lp_balance_wei > 0:
                liquidity_to_remove_wei = int(current_lp_balance_wei * remove_percentage_lp)
                if liquidity_to_remove_wei == 0 and current_lp_balance_wei > 0:
                    liquidity_to_remove_wei = 1
                print(f"   {Colors.WHITE}Removing {Colors.BOLD}{remove_percentage_lp*100:.2f}%{Colors.RESET}{Colors.WHITE} of your LP Tokens: {web3.from_wei(liquidity_to_remove_wei, 'ether')} LP Tokens{Colors.RESET}")
            else:
                print(f"  {Colors.CYAN}ℹ️ Account {current_account.address} has no LP Tokens. Skipping liquidity removal.{Colors.RESET}")


            if current_lp_balance_wei == 0 or liquidity_to_remove_wei == 0:
                print(f"  {Colors.CYAN}ℹ️ No LP Tokens to remove or amount is zero. Skipping remove liquidity.{Colors.RESET}")
            elif current_lp_balance_wei < liquidity_to_remove_wei:
                print(f"  {Colors.RED}❌ Insufficient LP Token balance for account {current_account.address}. You want to remove {web3.from_wei(liquidity_to_remove_wei, 'ether')}, but only have {current_lp_balance} LP Tokens. Skipping liquidity removal.{Colors.RESET}")
            else:
                if not approve_token(current_account, current_private_key, LP_TOKEN_ADDRESS, UNISWAP_V2_ROUTER_ADDRESS, liquidity_to_remove_wei):
                    print(f"  {Colors.RED}❌ Failed to approve LP Token for remove liquidity. Skipping remove liquidity.{Colors.RESET}")
                else:
                    pair_contract = get_pair_contract(LP_TOKEN_ADDRESS)
                    reserves = pair_contract.functions.getReserves().call()
                    total_lp_supply = get_erc20_contract(LP_TOKEN_ADDRESS).functions.totalSupply().call()

                    token0_address = pair_contract.functions.token0().call()
                    token1_address = pair_contract.functions.token1().call()

                    reserve_token_address = web3.to_checksum_address(TOKEN_ADDRESS)
                    weth_token_address = web3.to_checksum_address(WETH_ADDRESS)

                    reserve_token = 0
                    reserve_eth = 0

                    if token0_address == reserve_token_address and token1_address == weth_token_address:
                        reserve_token = reserves[0]
                        reserve_eth = reserves[1]
                    elif token0_address == weth_token_address and token1_address == reserve_token_address:
                        reserve_token = reserves[1]
                        reserve_eth = reserves[0]
                    else:
                        print(f"  {Colors.RED}❌ Warning: Token order in pool is not as expected. There might be an issue with token or WETH addresses.{Colors.RESET}")
                        reserve_token = reserves[0]
                        reserve_eth = reserves[1]


                    expected_token_out_wei = int(reserve_token * liquidity_to_remove_wei / total_lp_supply)
                    expected_eth_out_wei = int(reserve_eth * liquidity_to_remove_wei / total_lp_supply)

                    amount_token_min_remove = int(expected_token_out_wei * (1 - slippage_tolerance_percent / 100))
                    amount_eth_min_remove = int(expected_eth_out_wei * (1 - slippage_tolerance_percent / 100))

                    print(f"   {Colors.CYAN}Slippage Tolerance: {slippage_tolerance_percent}%{Colors.RESET}")
                    print(f"   {Colors.CYAN}Estimated {SELECTED_TOKEN_NAME} to receive: {web3.from_wei(expected_token_out_wei, 'ether')} (Min: {web3.from_wei(amount_token_min_remove, 'ether')}){Colors.RESET}")
                    print(f"   {Colors.CYAN}Estimated NEX to receive: {web3.from_wei(expected_eth_out_wei, 'ether')} (Min: {web3.from_wei(amount_eth_min_remove, 'ether')}){Colors.RESET}")

                    try:
                        remove_liquidity_eth(current_account, current_private_key, TOKEN_ADDRESS,
                                             liquidity_to_remove_wei, amount_token_min_remove, amount_eth_min_remove, deadline)
                    except Exception as e:
                        print(f"  {Colors.RED}❌ Remove liquidity failed: {e}.{Colors.RESET}")

            delay = random.randint(5, 10)
            print(f"{Colors.YELLOW}😴 Waiting {delay} seconds after REMOVE LIQUIDITY...{Colors.RESET}")
            time.sleep(delay)

            current_operation_retries = 0
            account_index = (account_index + 1) % len(accounts)
            if not run_in_loop and account_index == 0:
                break

        except Exception as e:
            error_message = str(e)
            print(f"\n{Colors.RED}❌ An unexpected error occurred in the cycle for account {current_account.address}: {error_message}{Colors.RESET}")

            if "Could not transact with/call contract function, is contract deployed correctly and chain synced?" in error_message and current_operation_retries < max_retries_per_operation:
                current_operation_retries += 1
                print(f"{Colors.YELLOW}⚠️ Retrying operation for {current_account.address} ({current_operation_retries}/{max_retries_per_operation} retries)...{Colors.RESET}")
                time.sleep(5)
                continue
            else:
                current_operation_retries = 0
                print(f"{Colors.YELLOW}  Moving to the next account after a brief pause...{Colors.RESET}")
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(5)

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- All cycles completed. ---{Colors.RESET}")