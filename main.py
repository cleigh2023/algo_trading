from alpaca_data import AlpacaTrade

def main():
    ALPACA = AlpacaTrade(isPaper=False)
    ALPACA.verify_all_symbols(check_sameday=False)

if __name__ == '__main__':
    main()