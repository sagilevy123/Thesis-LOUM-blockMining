from web3 import Web3
import time
import asyncio

# Connect to an Ethereum node (replace with your node URL)
w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/5072be99908f41e7aaa136eddae7858a'))

async def get_pending_transactions():
    # Get pending transactions
    pending = w3.eth.get_block('pending', full_transactions=True)
    return {tx['hash'].hex(): tx for tx in pending['transactions']}

async def get_block_transactions(block_number):
    # Get transactions in a specific block
    block = w3.eth.get_block(block_number, full_transactions=True)
    return {tx['hash'].hex(): tx for tx in block['transactions']}

async def main():
    # Get initial pending transactions
    print("Fetching pending transactions...")
    pending_txs = await get_pending_transactions()
    print(f"Number of pending transactions: {len(pending_txs)}")

    # Wait for the next block
    print("Waiting for the next block...")
    initial_block = w3.eth.block_number
    while w3.eth.block_number == initial_block:
        await asyncio.sleep(1)

    new_block_number = w3.eth.block_number
    print(f"New block mined: {new_block_number}")

    # Get transactions in the new block
    block_txs = await get_block_transactions(new_block_number)

    # Find which pending transactions made it into the block
    included_txs = set(pending_txs.keys()) & set(block_txs.keys())

    print(f"Number of transactions in the new block: {len(block_txs)}")
    print(f"Number of previously pending transactions included: {len(included_txs)}")

    # Print details of included transactions
    print("\nDetails of included transactions:")
    for tx_hash in included_txs:
        tx = pending_txs[tx_hash]
        print(f"Hash: {tx_hash}")
        print(f"From: {tx['from']}")
        print(f"To: {tx['to']}")
        print(f"Value: {Web3.from_wei(tx['value'], 'ether')} ETH")
        print("---")

if __name__ == "__main__":
    asyncio.run(main())