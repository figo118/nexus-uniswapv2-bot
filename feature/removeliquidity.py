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
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "liquidity", "type": "uint256"},
            {"internalType": "uint256", "name": "amountTokenMin", "type": "uint256"},
            {"internalType": "uint256", "name": "amountETHMin", "type": "uint256"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "removeLiquidityETH",
        "outputs": [
            {"internalType": "uint256", "name": "amountToken", "type": "uint256"},
            {"internalType": "uint256", "name": "amountETH", "type": "uint256"}
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
            print(f"  {Colors.YELLOW}⏳ 正在为Nexswap路由批准 {web3.from_wei(amount_to_approve, 'ether')} LP代币...{Colors.RESET}")

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
            print(f"  {Colors.GREEN}✅ {Colors.BOLD}批准交易已发送{Colors.RESET}{Colors.GREEN}: https://testnet3.explorer.nexus.xyz/tx/{web3.to_hex(tx_hash)}{Colors.RESET}")
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
            print(f"  {Colors.GREEN}✅ {Colors.BOLD}移除流动性交易已发送{Colors.RESET}{Colors.GREEN} https://testnet3.explorer.nexus.xyz/tx/{web3.to_hex(tx_hash)}{Colors.RESET}")
            web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            print(f"{Colors.GREEN}  🎉 {SELECTED_TOKEN_NAME}/NEX 流动性移除确认!{Colors.RESET}")
            return web3.to_hex(tx_hash)

        except Exception as e:
            if 'replacement transaction underpriced' in str(e) or 'nonce too low' in str(e):
                gas_price += web3.to_wei(2, 'gwei')
                print(f"  {Colors.YELLOW}⚠️ 移除流动性交易的Gas价格过低或nonce问题，增加到 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            elif 'out of gas' in str(e):
                gas_price += web3.to_wei(5, 'gwei')
                print(f"  {Colors.RED}🔥 移除流动性交易Gas不足，增加Gas价格至 {web3.from_wei(gas_price, 'gwei')} gwei并重试...{Colors.RESET}")
            else:
                print(f"  {Colors.RED}❌ 移除流动性过程中发生错误: {e}{Colors.RESET}")
                raise

if __name__ == "__main__":
    print(f"{Colors.BOLD}{Colors.MAGENTA}--- 💸 Nexswap流动性移除工具 💸 ---{Colors.RESET}")

    print(f"\n{Colors.BOLD}{Colors.BLUE}--- 选择流动性交易对代币 (与NEX配对) ---{Colors.RESET}")
    token_names = list(AVAILABLE_TOKENS.keys())
    for i, token_name in enumerate(token_names):
        print(f"{Colors.WHITE}{i+1}. {token_name} ({AVAILABLE_TOKENS[token_name]}){Colors.RESET}")

    while True:
        try:
            choice = int(input(f"{Colors.CYAN}输入要移除流动性的代币编号: {Colors.RESET}"))
            if 1 <= choice <= len(token_names):
                SELECTED_TOKEN_NAME = token_names[choice - 1]
                TOKEN_ADDRESS = AVAILABLE_TOKENS[SELECTED_TOKEN_NAME]
                print(f"{Colors.GREEN}✅ 已选择: {Colors.BOLD}{SELECTED_TOKEN_NAME}{Colors.RESET}{Colors.GREEN}/NEX{Colors.RESET}")
                break
            else:
                print(f"{Colors.RED}无效选择。请输入有效编号。{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}无效输入。请输入数字。{Colors.RESET}")

    LP_TOKEN_ADDRESS = LP_TOKEN_ADDRESSES.get(SELECTED_TOKEN_NAME)
    if not LP_TOKEN_ADDRESS:
        print(f"{Colors.RED}❌ 未找到 {SELECTED_TOKEN_NAME} 的LP代币地址。请确保已添加。{Colors.RESET}")
        exit()
    print(f"{Colors.CYAN}ℹ️ 关联的LP代币地址: {LP_TOKEN_ADDRESS}{Colors.RESET}")

    remove_amount_lp = 0.0
    remove_percentage = 0.0
    remove_by_percentage = False

    while True:
        mode_choice = input(f"{Colors.CYAN}\n选择移除流动性的方式:\n1. LP代币数量\n2. LP代币百分比\n选择模式 (1或2): {Colors.RESET}").strip()
        if mode_choice == '1':
            try:
                remove_amount_lp = float(input(f"{Colors.CYAN}输入要移除的LP代币数量 (例如: 0.01): {Colors.RESET}"))
                if remove_amount_lp <= 0:
                    raise ValueError("LP代币数量必须为正数。")
                break
            except ValueError as e:
                print(f"{Colors.RED}无效输入: {e}。请输入数字。{Colors.RESET}")
        elif mode_choice == '2':
            try:
                remove_percentage = float(input(f"{Colors.CYAN}输入要移除的LP代币百分比 (例如: 50表示50%): {Colors.RESET}"))
                if not (0 < remove_percentage <= 100):
                    raise ValueError("百分比必须在0(不含)到100(含)之间。")
                remove_by_percentage = True
                break
            except ValueError as e:
                print(f"{Colors.RED}无效输入: {e}。请输入数字。{Colors.RESET}")
        else:
            print(f"{Colors.RED}无效选择。请输入'1'或'2'。{Colors.RESET}")

    run_in_loop = False
    while True:
        loop_choice = input(f"{Colors.CYAN}\n是否要连续循环运行流动性移除? (y/n): {Colors.RESET}").lower().strip()
        if loop_choice in ['yes', 'y']:
            run_in_loop = True
            print(f"{Colors.GREEN}✅ 循环模式已激活。流动性移除将连续运行。{Colors.RESET}")
            break
        elif loop_choice in ['no', 'n']:
            run_in_loop = False
            print(f"{Colors.GREEN}✅ 单次执行模式。流动性移除将为每个账户运行一次。{Colors.RESET}")
            break
        else:
            print(f"{Colors.RED}无效选择。请输入'yes'或'no'。{Colors.RESET}")

    slippage_tolerance_percent = 0.5

    deadline = int(web3.eth.get_block('latest').timestamp) + 300

    accounts = [web3.eth.account.from_key(pk) for pk in PRIVATE_KEYS]
    account_index = 0

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- 开始流动性移除操作 ---{Colors.RESET}")

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

            current_lp_balance_wei = get_token_balance(current_account.address, LP_TOKEN_ADDRESS)
            current_lp_balance = web3.from_wei(current_lp_balance_wei, 'ether')
            print(f"   {Colors.CYAN}您的LP代币 ({SELECTED_TOKEN_NAME}/NEX) 余额: {current_lp_balance:.8f}{Colors.RESET}")

            liquidity_to_remove_wei = 0
            if remove_by_percentage:
                liquidity_to_remove_wei = int(current_lp_balance_wei * (remove_percentage / 100.0))
                if liquidity_to_remove_wei == 0 and current_lp_balance_wei > 0:
                    liquidity_to_remove_wei = 1
                print(f"   {Colors.WHITE}移除 {Colors.BOLD}{remove_percentage:.2f}%{Colors.RESET}{Colors.WHITE} 的LP代币: {web3.from_wei(liquidity_to_remove_wei, 'ether')} LP代币{Colors.RESET}")
            else:
                liquidity_to_remove_wei = web3.to_wei(remove_amount_lp, 'ether')
                print(f"   {Colors.WHITE}移除指定的LP代币数量: {remove_amount_lp} LP代币{Colors.RESET}")

            if current_lp_balance_wei == 0:
                print(f"  {Colors.RED}❌ 账户 {current_account.address} 没有LP代币。跳过流动性移除。{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(1)
                continue

            if liquidity_to_remove_wei == 0:
                print(f"  {Colors.CYAN}ℹ️ 要移除的LP代币数量为零。跳过流动性移除。{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(1)
                continue

            if current_lp_balance_wei < liquidity_to_remove_wei:
                print(f"  {Colors.RED}❌ 账户 {current_account.address} 的LP代币余额不足。您想移除 {web3.from_wei(liquidity_to_remove_wei, 'ether')}，但只有 {current_lp_balance} LP代币。跳过流动性移除。{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(1)
                continue

            if not approve_token(current_account, current_private_key, LP_TOKEN_ADDRESS, UNISWAP_V2_ROUTER_ADDRESS, liquidity_to_remove_wei):
                print(f"  {Colors.RED}❌ 批准LP代币移除流动性失败。跳过移除流动性。{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(1)
                continue

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
                print(f"  {Colors.RED}❌ 警告: 池中的代币顺序不符合预期。可能是代币或WETH地址有问题。{Colors.RESET}")
                reserve_token = reserves[0]
                reserve_eth = reserves[1]

            expected_token_out_wei = int(reserve_token * liquidity_to_remove_wei / total_lp_supply)
            expected_eth_out_wei = int(reserve_eth * liquidity_to_remove_wei / total_lp_supply)

            amount_token_min = int(expected_token_out_wei * (1 - slippage_tolerance_percent / 100))
            amount_eth_min = int(expected_eth_out_wei * (1 - slippage_tolerance_percent / 100))

            print(f"   {Colors.CYAN}滑点容忍度: {slippage_tolerance_percent}%{Colors.RESET}")
            print(f"   {Colors.CYAN}预计收到的 {SELECTED_TOKEN_NAME}: {web3.from_wei(expected_token_out_wei, 'ether')} (最低: {web3.from_wei(amount_token_min, 'ether')}){Colors.RESET}")
            print(f"   {Colors.CYAN}预计收到的 NEX: {web3.from_wei(expected_eth_out_wei, 'ether')} (最低: {web3.from_wei(amount_eth_min, 'ether')}){Colors.RESET}")

            try:
                remove_liquidity_eth(current_account, current_private_key, TOKEN_ADDRESS,
                                     liquidity_to_remove_wei, amount_token_min, amount_eth_min, deadline)
            except Exception as e:
                print(f"  {Colors.RED}❌ 移除流动性失败: {e}.{Colors.RESET}")
                current_operation_retries = 0
                account_index = (account_index + 1) % len(accounts)
                if not run_in_loop and account_index == 0:
                    break
                time.sleep(5)
                continue

            delay = random.randint(5, 15)
            print(f"\n{Colors.YELLOW}😴 等待 {delay} 秒后进入下一轮...{Colors.RESET}")
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

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- 所有流动性移除操作完成。 ---{Colors.RESET}")