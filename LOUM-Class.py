import numpy as np
import random
import pandas as pd
import json
import re
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

number_of_bids = 10
J = 100000


def normalize_to_range(original_list, target_max):
    # Convert to numpy array if not already
    arr = np.array(original_list)

    # Get original min and max
    original_min = np.min(arr)
    original_max = np.max(arr)

    # Normalize to 0-1 first
    normalized = (arr - original_min) / (original_max - original_min)

    # Scale to target range (0 to target_max)
    scaled = normalized * target_max

    return scaled


def calculate_correlation_time_cross(list1, list2):
    # Ensure lists are numpy arrays
    array1 = np.array(list1)
    array2 = np.array(list2)

    # Calculate Pearson correlation coefficient
    correlation = np.corrcoef(array1, array2)[0, 1]

    # Calculate cross-correlation
    cross_corr = np.correlate(array1 - np.mean(array1),
                              array2 - np.mean(array2),
                              mode='full')

    # Normalize cross-correlation
    cross_corr = cross_corr / (np.std(array1) * np.std(array2) * len(array1))

    # Find max correlation and its lag
    max_corr = np.max(np.abs(cross_corr))
    lag = np.argmax(np.abs(cross_corr)) - (len(array1) - 1)

    # Calculate other correlation metrics
    results = {
        "Pearson": correlation,
        "Spearman": np.corrcoef(np.argsort(array1), np.argsort(array2))[0, 1],
        "Covariance": np.cov(array1, array2)[0, 1],
        "Cross_Correlation": {
            "max_correlation": max_corr,
            "lag": lag,
            "full_correlation": cross_corr.tolist()
        }
    }

    return results

def calculate_correlation(list1, list2):
    # Calculate Pearson correlation coefficient
    correlation = np.corrcoef(list1, list2)[0, 1]

    # Calculate other correlation metrics
    results = {
        "Pearson": correlation,
        "Spearman": np.corrcoef(np.argsort(list1), np.argsort(list2))[0, 1],
        "Covariance": np.cov(list1, list2)[0, 1]
    }

    return results


def plot_lists_with_demand(list1, list2, list3, title1, title2, title3, figure_title):
    plt.figure(figsize=(12, 6))

    # Plot list3 in background first
    x3 = np.arange(len(list3))
    plt.plot(x3, list3, 'g-', linewidth=1, alpha=0.2, label=title3)
    plt.scatter(x3, list3, color='green', alpha=0.2, s=30)

    x1 = np.arange(len(list1))
    plt.plot(x1, list1, 'b-', linewidth=1, alpha=0.7, label=title1)
    plt.scatter(x1, list1, color='blue', alpha=0.5, s=30)

    x2 = np.arange(len(list2))
    plt.plot(x2, list2, 'r-', linewidth=1, alpha=0.7, label=title2)
    plt.scatter(x2, list2, color='red', alpha=0.5, s=30)

    plt.title(figure_title, fontsize=16)
    plt.xlabel('Index')
    plt.ylabel('Value')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()

    # Save the plot
    filename = f"{figure_title.replace(' ', '_')}.png"  # Replace spaces with underscores
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()  # Close the figure to free memory


def plot_lists_with_ma_and_demand(list1, list2, list3, title1, title2, title3, figure_title, window=10):
    plt.figure(figsize=(12, 6))

    # Plot list3 in background first
    x3 = np.arange(len(list3))
    plt.plot(x3, list3, 'g-', linewidth=1, alpha=0.2, label=title3)
    plt.scatter(x3, list3, color='green', alpha=0.2, s=30)

    # Plot list1 and its moving average
    x1 = np.arange(len(list1))
    ma1 = pd.Series(list1).rolling(window=window).mean()
    plt.plot(x1, ma1, 'b-', linewidth=2, label=f'{title1} MA({window})')

    # Plot list2 and its moving average
    x2 = np.arange(len(list2))
    ma2 = pd.Series(list2).rolling(window=window).mean()
    plt.plot(x2, ma2, 'r-', linewidth=2, label=f'{title2} MA({window})')

    plt.title(figure_title, fontsize=16)
    plt.xlabel('Index')
    plt.ylabel('Value')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()

    # Save the plot
    filename = f"{figure_title.replace(' ', '_')}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()


def plot_lists_with_ma(list1, list2, title1, title2, figure_title, window=10):
    plt.figure(figsize=(12, 6))

    x1 = np.arange(len(list1))
    plt.plot(x1, list1, 'b-', linewidth=1, alpha=0.3, label=f'{title1} raw')
    plt.scatter(x1, list1, color='blue', alpha=0.3, s=30)

    # Calculate and plot moving average
    ma1 = pd.Series(list1).rolling(window=window).mean()
    plt.plot(x1, ma1, 'b-', linewidth=2, label=f'{title1} MA({window})')

    x2 = np.arange(len(list2))
    plt.plot(x2, list2, 'r-', linewidth=1, alpha=0.3, label=f'{title2} raw')
    plt.scatter(x2, list2, color='red', alpha=0.3, s=30)

    # Calculate and plot moving average
    ma2 = pd.Series(list2).rolling(window=window).mean()
    plt.plot(x2, ma2, 'r-', linewidth=2, label=f'{title2} MA({window})')

    plt.title(figure_title, fontsize=16)
    plt.xlabel('Index')
    plt.ylabel('Value')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()

    # Save the plot
    filename = f"{figure_title.replace(' ', '_')}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()


def plot_lists(list1, list2, title1, title2, figure_title):
    plt.figure(figsize=(12, 6))

    x1 = np.arange(len(list1))
    plt.plot(x1, list1, 'b-', linewidth=1, alpha=0.7, label=title1)
    plt.scatter(x1, list1, color='blue', alpha=0.5, s=30)

    x2 = np.arange(len(list2))
    plt.plot(x2, list2, 'r-', linewidth=1, alpha=0.7, label=title2)
    plt.scatter(x2, list2, color='red', alpha=0.5, s=30)

    plt.title(figure_title, fontsize=16)
    plt.xlabel('Index')
    plt.ylabel('Value')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()

    # Save the plot
    filename = f"{figure_title.replace(' ', '_')}.png"  # Replace spaces with underscores
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()  # Close the figure to free memory


def get_transaction_list(i):
    with open('block_analysis_with_payment.json', 'r') as file:
        data = json.loads(file.read())

    # Convert blocks to list and get the i-th block
    blocks = list(data.items())
    if i < 0 or i >= len(blocks):
        raise ValueError(f"Index {i} is out of range. Available blocks: 0-{len(blocks) - 1}")

    block_number, block_data = blocks[i]
    transactions = block_data.get("transactions", {})

    # Count transactions starting with "0x"
    count_winners = sum(1 for tx_hash in transactions.keys() if tx_hash.startswith("0x"))

    # Get transaction values
    transaction_values = [float(value['fee']) for value in transactions.values()]
    transaction_payments = [float(value['payment']) for value in transactions.values()]

    priority_fee = float(block_data["total_priority_fee"])
    return transaction_values,transaction_payments, priority_fee, count_winners


def MONOPOLISTIC(ordered_bids):
    i_star = np.argmax([(i + 1) * ordered_bids[i] for i in range(len(ordered_bids))])
    b_i_star = ordered_bids[i_star]
    # revenue = b_i_star * (i_star + 1)
    return b_i_star, i_star


def LOUM(ordered_bids):
    winners = []
    payments = []
    # ordered_bids = sorted(bids, reverse=True)
    for index, bid in enumerate(ordered_bids):
        current_bids = [ordered_bids[i] for i in range(len(ordered_bids)) if i != index]  #b_{-i}
        required_payment, index_of_payment = MONOPOLISTIC(current_bids)
        if bid >= required_payment:
            winners.append(index)
            payments.append(required_payment)
    # winners_after_budget = [i for i in range(index_of_payment)]
    winners_after_budget = [i for i in range(len(ordered_bids)) if ordered_bids[i] > payments[0]]

    revenue_after_budget = payments[0]*len(winners_after_budget)
    return payments[0], winners_after_budget, revenue_after_budget


def main():
    revenues = []
    original_revenues = []
    LOUM_fraction_of_winners = []
    original_fraction_of_winners = []
    original_avg_payments, LOUM_avg_payments = [], []
    LOUM_avg_payments = []
    original_utilities, LOUM_utilities = [], []
    original_sum_utilities, LOUM_sum_utilities = [],[]
    bids_length = []
    avg_block_size = []
    try:
        counter = 0
        while True:
            bids, original_payments, original_revenue, count_winners_orginal = get_transaction_list(counter)
            avg_block_size.append(count_winners_orginal)
            bids_length.append(len(bids))
            original_utilities.append([bids[i]-original_payments[i] if original_payments[i] != -1 else 0 for i in range(len(bids))])
            original_sum_utilities.append(sum(original_utilities[-1]))
            ordered_bids = sorted(bids, reverse=True)
            payment, winners_after_budget, revenue_after_budget = LOUM(ordered_bids)
            LOUM_utilities.append([ordered_bids[i]-payment if i<len(winners_after_budget) else 0 for i in range(len(ordered_bids))])
            LOUM_sum_utilities.append(sum(LOUM_utilities[-1]))
            if len(winners_after_budget) > 0.1*len(bids):
                original_avg_payments.append(original_sum_utilities[-1] / len(original_utilities[-1]))
                LOUM_avg_payments.append(payment)
            revenues.append(revenue_after_budget)
            original_revenues.append(original_revenue)
            LOUM_fraction_of_winners.append(len(winners_after_budget)/len(bids)*100)
            original_fraction_of_winners.append(count_winners_orginal/len(bids)*100)
            """To be Continued"""
            # original_avg_payments.append()
            """--------------"""
            # print(f"original_revenue: {original_revenue}")
            # print(f"revenue: {revenue_after_budget}")
            # print(f"winners: {winners_after_budget}")
            # print(f"payment for each winner: {payment}")
            print(counter)
            counter += 1
        raise Exception("End of file")
    except ValueError as e:
        print(e)
        print(f"avg bids length: {sum(bids_length)/len(bids_length)}")
        print(f"Avg block size: {sum(avg_block_size)/len(avg_block_size)}")
        print(f"Avg revenue: {sum(original_revenues) / len(original_revenues)}")
        # plot_lists(LOUM_avg_payments, original_avg_payments, "LOUM average payment",
        #            "EIP average payment", "Avg. payment Comparison (removed outliers)")
        # plot_lists_with_ma(LOUM_avg_payments, original_avg_payments, "LOUM average payment",
        #            "EIP average payment", "Avg. payment Comparison (removed outliers)-MA")
        #
        # plot_lists(LOUM_sum_utilities, original_sum_utilities, "LOUM Utility", "EIP Utility", "Utilities Comparison")
        # plot_lists_with_ma(LOUM_sum_utilities, original_sum_utilities, "LOUM Utility", "EIP Utility", "Utilities Comparison-MA")

        plot_lists_with_ma(revenues, original_revenues, "LOUM Revenues", "EIP Revenues",
                               "Revenue comparaion with demand")
        plot_lists(revenues, original_revenues, "LOUM Revenues", "EIP Revenues", "Revenue comparaion")
        plot_lists_with_ma(revenues, original_revenues, "LOUM Revenues", "EIP Revenues", "Revenue comparaion-MA")

        # plot_lists(LOUM_fraction_of_winners, original_fraction_of_winners, "LOUM winners fraction",
        #            "EIP winners fraction", "Winners Fraction Comparison")
        # plot_lists_with_ma(LOUM_fraction_of_winners, original_fraction_of_winners, "LOUM winners fraction",
        #            "EIP winners fraction", "Winners Fraction Comparison-MA")


        correlations = calculate_correlation(LOUM_sum_utilities, original_sum_utilities)
        print("Correlation Results:")
        for metric, value in correlations.items():
            print(f"{metric}: {value:.4f}")

        results = calculate_correlation_time_cross(LOUM_sum_utilities, original_sum_utilities)
        print(f"Maximum cross-correlation: {results['Cross_Correlation']['max_correlation']}")
        print(f"At lag: {results['Cross_Correlation']['lag']}")


if __name__ == "__main__":
    main()
