import asyncio
from web3 import Web3
from datetime import datetime
import time
import json
import os
from decimal import Decimal

PROVIDERS = [
    "https://mainnet.infura.io/v3/5072be99908f41e7aaa136eddae7858a",
    "https://eth-mainnet.g.alchemy.com/v2/r1pvjCEAzk_yb80SsdFLoSUh6u5NJoAB",
]

w3_list = [Web3(Web3.HTTPProvider(url)) for url in PROVIDERS]
w3 = w3_list[0]

mempool = {}
last_block_number = w3.eth.block_number
provider_index = 0
OUTPUT_FILE = 'block_analysis_with_payment.json'
capture_rate_threshold = 70


def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


async def update_mempool():
    global mempool, provider_index
    try:
        w3_instance = w3_list[provider_index]
        pending = w3_instance.eth.get_block('pending', full_transactions=True)

        for tx in pending['transactions']:
            tx_hash = tx['hash'].hex()
            if tx_hash not in mempool:
                mempool[tx_hash] = {
                    'transaction': tx,
                    'first_seen': datetime.now(),
                    'last_seen': datetime.now(),
                    'provider': PROVIDERS[provider_index],
                }
            else:
                mempool[tx_hash]['last_seen'] = datetime.now()

        provider_index = (provider_index + 1) % len(PROVIDERS)

    except Exception as e:
        provider_index = (provider_index + 1) % len(PROVIDERS)
        await asyncio.sleep(0.1)


async def clean_mempool():
    global mempool
    current_time = datetime.now()
    to_remove = [
        tx_hash for tx_hash, tx_data in mempool.items()
        if (current_time - tx_data['last_seen']).total_seconds() > 180
    ]
    for tx_hash in to_remove:
        del mempool[tx_hash]


async def calculate_priority_fees(block, block_txs):
    base_fee_per_gas = block['baseFeePerGas']
    fees = {}

    for tx_hash, tx in block_txs.items():
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        gas_used = receipt['gasUsed']

        max_priority_fee = min(
            tx.get('maxPriorityFeePerGas', 0),
            tx.get('maxFeePerGas', 0) - base_fee_per_gas
        ) if 'maxPriorityFeePerGas' in tx else tx.get('gasPrice', 0) - base_fee_per_gas

        priority_fee = max_priority_fee * gas_used
        fees[tx_hash] = float(w3.from_wei(priority_fee, 'ether'))

    return fees


async def calculate_priority_fee(tx, receipt, base_fee_per_gas):
    gas_used = receipt['gasUsed']
    if 'maxFeePerGas' in tx:
        # Type 2 transaction (EIP-1559)
        priority_fee_per_gas = min(
            tx['maxPriorityFeePerGas'],
            tx['maxFeePerGas'] - base_fee_per_gas
        )
        return priority_fee_per_gas * gas_used
    else:
        # Legacy transaction
        if tx['gasPrice'] > base_fee_per_gas:
            return (tx['gasPrice'] - base_fee_per_gas) * gas_used
        return 0


async def calculate_priority_fee_mempool(tx, base_fee_per_gas):
    gas_limit = tx['gas']
    if 'maxFeePerGas' in tx:
        priority_fee_per_gas = min(
            tx['maxPriorityFeePerGas'],
            tx['maxFeePerGas'] - base_fee_per_gas
        )
        return priority_fee_per_gas * gas_limit
    else:
        if tx['gasPrice'] > base_fee_per_gas:
            return (tx['gasPrice'] - base_fee_per_gas) * gas_limit
        return 0


async def get_tx_priority_fee(tx, receipt):
    gas_used = receipt['gasUsed']
    gas_price = w3.from_wei(tx['gasPrice'], 'ether')
    return gas_price * gas_used


async def calculate_block_reward(block_txs, block, provider_index=0):
    try:
        w3_instance = w3_list[provider_index]
        total_fees = sum(
            tx['gasPrice'] * w3_instance.eth.get_transaction_receipt(tx['hash'])['gasUsed']
            for tx in block_txs.values()
        )
        burnt_fees = block['baseFeePerGas'] * sum(
            w3_instance.eth.get_transaction_receipt(tx['hash'])['gasUsed']
            for tx in block_txs.values()
        )
        return w3.from_wei(total_fees - burnt_fees, 'ether')
    except Exception:
        if provider_index + 1 < len(w3_list):
            await asyncio.sleep(0.1)
            return await calculate_block_reward(block_txs, block, provider_index + 1)
        raise


async def get_transaction_receipt(tx_hash, provider_index=0):
    try:
        return w3_list[provider_index].eth.get_transaction_receipt(tx_hash)
    except Exception:
        if provider_index + 1 < len(w3_list):
            await asyncio.sleep(0.1)
            return await get_transaction_receipt(tx_hash, provider_index + 1)
        raise


async def get_transaction_receipt_with_retry(tx_hash, provider_index=0):
    try:
        receipt = w3_list[provider_index].eth.get_transaction_receipt(tx_hash)
        return receipt
    except Exception:
        if provider_index + 1 < len(w3_list):
            await asyncio.sleep(0.1)  # Add delay before retrying
            return await get_transaction_receipt_with_retry(tx_hash, provider_index + 1)
        raise


async def update_block_data(block_number, block_txs, block):
    try:
        data = {}
        if os.path.exists(OUTPUT_FILE):
            try:
                with open(OUTPUT_FILE, 'r') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                print("Warning: JSON file corrupted, creating new file")

        fees = {}

        # Process block transactions - with '0x' prefix
        for tx_hash, tx in block_txs.items():
            try:
                receipt = await get_transaction_receipt(tx_hash)

                # Maximum fee willing to pay (in Wei first)
                max_fee_wei = tx['gasPrice'] * tx['gas']
                # Convert to Ether
                max_fee_ether = w3.from_wei(max_fee_wei, 'ether')

                # Actual payment (in Wei first)
                actual_payment_wei = tx['gasPrice'] * receipt['gasUsed']
                # Convert to Ether
                actual_payment_ether = w3.from_wei(actual_payment_wei, 'ether')

                fees[f"0x{tx_hash}"] = {
                    "fee": f"{max_fee_ether:.18f}".rstrip('0').rstrip('.'),
                    "payment": f"{actual_payment_ether:.18f}".rstrip('0').rstrip('.')
                }

                await asyncio.sleep(0.05)  # Rate limiting
            except Exception as e:
                print(f"Error processing block tx {tx_hash[:10]}: {e}")
                continue

        # Process mempool transactions - without '0x' prefix
        for tx_hash, tx_data in mempool.items():
            if tx_hash not in block_txs:
                try:
                    tx = tx_data['transaction']
                    max_fee_wei = tx['gasPrice'] * tx['gas']
                    # Convert to Ether
                    fee = w3.from_wei(max_fee_wei, 'ether')

                    fees[tx_hash] = {"fee": f"{fee:.18f}".rstrip('0').rstrip('.'), "payment": -1}
                except Exception as e:
                    print(f"Error processing mempool tx {tx_hash[:10]}: {e}")
                    continue

        total_priority_fee = await calculate_block_reward(block_txs, block)

        temp_file = f"{OUTPUT_FILE}.temp"
        data[str(block_number)] = {
            'transactions': fees,
            'total_priority_fee': f"{total_priority_fee:.18f}".rstrip('0').rstrip('.')
        }

        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_file, OUTPUT_FILE)

    except Exception as e:
        print(f"Error updating block data file: {e}")
        if 'temp_file' in locals() and os.path.exists(temp_file):
            os.remove(temp_file)


async def check_new_blocks():
    global last_block_number, mempool
    try:
        current_block = None
        for w3_instance in w3_list:
            try:
                current_block = w3_instance.eth.block_number
                block = w3_instance.eth.get_block(current_block, full_transactions=True)
                break
            except Exception:
                await asyncio.sleep(0.1)
                continue

        if current_block is None:
            print("All providers failed")
            return

        if current_block > last_block_number:
            print(f"\nNew block: {current_block}")
            block = w3.eth.get_block(current_block, full_transactions=True)
            block_txs = {tx['hash'].hex(): tx for tx in block['transactions']}
            included_from_mempool = set(block_txs.keys()) & mempool.keys()

            capture_rate = len(included_from_mempool) / len(block_txs) * 100
            print(f"Mempool size: {len(mempool)}")
            print(f"Block transactions: {len(block_txs)}")
            print(f"From mempool: {len(included_from_mempool)}")
            print(f"Missing: {len(block_txs) - len(included_from_mempool)}")
            print(f"Capture rate: {capture_rate:.2f}%")

            if capture_rate >= capture_rate_threshold:
                await update_block_data(current_block, block_txs, block)

            for tx_hash in included_from_mempool:
                del mempool[tx_hash]

            last_block_number = current_block
            await asyncio.sleep(0.1)  # Rate limiting

    except Exception as e:
        print(f"Block check error: {e}")
        await asyncio.sleep(0.1)


async def main():
    while True:
        tasks = [
            update_mempool(),
            clean_mempool(),
            check_new_blocks(),
            # print_stats()
        ]
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.05)


if __name__ == '__main__':
    asyncio.run(main())