import time
from web3 import Web3
import asyncio
from datetime import datetime

# Use multiple providers
PROVIDERS = [
    "https://mainnet.infura.io/v3/5072be99908f41e7aaa136eddae7858a",
    "https://eth-mainnet.g.alchemy.com/v2/r1pvjCEAzk_yb80SsdFLoSUh6u5NJoAB",
    # Public node, be mindful of rate limits
]

w3_list = [Web3(Web3.HTTPProvider(url)) for url in PROVIDERS]
w3 = w3_list[0]

mempool = {}
last_block_number = w3_list[0].eth.block_number


async def update_mempool():
    global mempool
    for w3 in w3_list:
        try:
            pending = w3.eth.get_block('pending', full_transactions=True)
            for tx in pending['transactions']:
                tx_hash = tx['hash'].hex()
                if tx_hash not in mempool:
                    mempool[tx_hash] = {
                        'transaction': tx,
                        'first_seen': datetime.now(),
                        'last_seen': datetime.now()
                    }
                else:
                    mempool[tx_hash]['last_seen'] = datetime.now()
        except Exception as e:
            print(f"Error updating mempool from a provider: {e}")


async def clean_mempool():
    global mempool
    current_time = datetime.now()
    to_remove = []
    for tx_hash, tx_data in mempool.items():
        if (current_time - tx_data['last_seen']).total_seconds() > 600:  # Remove after 10 minutes
            to_remove.append(tx_hash)
    for tx_hash in to_remove:
        del mempool[tx_hash]


async def check_new_blocks():
    global last_block_number, mempool
    try:
        current_block = w3.eth.block_number
        if current_block > last_block_number:
            print(f"\nNew block: {current_block}")
            block = w3.eth.get_block(current_block, full_transactions=True)
            block_txs = {tx['hash'].hex() for tx in block['transactions']}
            included_from_mempool = block_txs.intersection(mempool.keys())

            print(f"Transactions in block: {len(block_txs)}")
            print(f"Transactions from our mempool: {len(included_from_mempool)}")
            print(f"Transactions not in our mempool: {len(block_txs - included_from_mempool)}")

            # Remove included transactions from mempool
            for tx_hash in included_from_mempool:
                del mempool[tx_hash]

            last_block_number = current_block
    except Exception as e:
        print(f"Error checking new blocks: {e}")


async def print_stats():
    print(f"\nCurrent mempool size: {len(mempool)}")
    if mempool:
        oldest_tx = min(mempool.values(), key=lambda x: x['first_seen'])
        newest_tx = max(mempool.values(), key=lambda x: x['first_seen'])
        print(
            f"Oldest transaction in mempool: {(datetime.now() - oldest_tx['first_seen']).total_seconds():.2f} seconds")
        print(
            f"Newest transaction in mempool: {(datetime.now() - newest_tx['first_seen']).total_seconds():.2f} seconds")


async def main():
    while True:
        await update_mempool()
        await clean_mempool()
        await check_new_blocks()
        await print_stats()
        await asyncio.sleep(1)  # Reduced from 5 to 1 second


if __name__ == '__main__':
    asyncio.run(main())