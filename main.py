import os
from colorama import Fore, Style, init

init(autoreset=True)

from banner import banner

print(banner)

def main():
    while True:
        print(Fore.CYAN + "\n请选择功能:")
        print(Fore.CYAN + "1. 代币兑换(NEX→代币)")
        print(Fore.CYAN + "2. 代币反向兑换(代币→NEX)")
        print(Fore.CYAN + "3. 双向兑换(NEX↔代币)")
        print(Fore.CYAN + "4. 添加流动性")
        print(Fore.CYAN + "5. 移除流动性")
        print(Fore.CYAN + "6. 全功能模式")
        print(Fore.CYAN + "0. 退出程序\n")

        pilihan = input(Fore.CYAN + "请输入选项(0-6): " + Style.RESET_ALL)
        
        if pilihan == "1":
            os.system('cls' if os.name == 'nt' else 'clear')
            os.system("python feature/swap.py")
        elif pilihan == "2":
            os.system('cls' if os.name == 'nt' else 'clear')
            os.system("python feature/unswap.py")
        elif pilihan == "3":
            os.system('cls' if os.name == 'nt' else 'clear')
            os.system("python feature/swapunswap.py")
        elif pilihan == "4":
            os.system('cls' if os.name == 'nt' else 'clear')
            os.system("python feature/addliquidity.py")
        elif pilihan == "5":
            os.system('cls' if os.name == 'nt' else 'clear')
            os.system("python feature/removeliquidity.py")
        elif pilihan == "6":
            os.system('cls' if os.name == 'nt' else 'clear')
            os.system("python feature/allfeature.py")
        elif pilihan == "0":
            print(Fore.RED + "程序已退出" + Style.RESET_ALL)
            break
        else:
            print(Fore.RED + "[错误] 无效的选项，请输入0-6之间的数字" + Style.RESET_ALL)

if __name__ == "__main__":
    main()
