import os
import json
import time
import random
import requests
from datetime import datetime

# API Configuration
url = "https://mainnet.helius-rpc.com/?api-key="  # API key from Helius

# Token configuration
TOKEN_MINT = "6rQt2W1kPAZGhuSMJmPnRgJndLb1HfK6E4cHiQTxoxzq"
TOKEN_DECIMALS = 6  # Number of decimals in the token, check on Solscan if not sure

# Define holding tiers
TIERS = [
    {"id": 1, "name": "Tier 1", "min": 10000, "max": 99999},
    {"id": 2, "name": "Tier 2", "min": 100000, "max": 499999},
    {"id": 3, "name": "Tier 3", "min": 500000, "max": 999999},
    {"id": 4, "name": "Tier 4", "min": 1000000, "max": 4999999},
    {"id": 5, "name": "Tier 5", "min": 5000000, "max": float('inf')}
]

# Define winner count per tier
WINNERS_BY_TIER = {
    1: 5,  # Tier 1: 5 winners
    2: 4,  # Tier 2: 4 winners
    3: 3,  # Tier 3: 3 winners
    4: 2,  # Tier 4: 2 winners
    5: 1   # Tier 5: 1 winner
}

# Time interval in seconds (10 minutes)
INTERVAL_SECONDS = 10 * 60

# Create logs directory if it doesn't exist
log_dir = './logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)


def get_tier_for_amount(amount):
    """
    Get the tier for a given amount
    
    Args:
        amount (float): Token amount
        
    Returns:
        dict or None: Tier object or None if no tier matches
    """
    for tier in TIERS:
        if tier["min"] <= amount <= tier["max"]:
            return tier
    return None  # No tier matches (amount is less than the minimum of any tier)


def get_formatted_datetime():
    """
    Format current date and time
    
    Returns:
        str: Formatted date and time
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def log_to_file(message):
    """
    Append a message to the log file
    
    Args:
        message (str): Message to log
    """
    log_file = f"{log_dir}/tracker_{datetime.now().strftime('%Y-%m-%d')}.log"
    with open(log_file, 'a') as f:
        f.write(f"{get_formatted_datetime()} - {message}\n")


async def find_holders():
    """
    Find all token holders and categorize them by tier
    
    Returns:
        list: Array of wallet data objects
    """
    print('Scanning for token holders...')
    log_to_file('Starting token holder scan')
    
    page = 1
    all_owners = {}  # Dictionary to store owner-amount pairs
    
    # Track counts for each tier
    tier_counts = {tier["id"]: 0 for tier in TIERS}
    
    total_wallets = 0
    wallets_below_min_tier = 0

    try:
        while True:
            print(f"Fetching page {page}...")
            
            payload = {
                "jsonrpc": "2.0",
                "method": "getTokenAccounts",
                "id": "helius-test",
                "params": {
                    "page": page,
                    "limit": 1000,
                    "displayOptions": {},
                    "mint": TOKEN_MINT,
                }
            }
            
            response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload)

            # Check if any error in the response
            if not response.ok:
                print(f"Error: {response.status_code}, {response.reason}")
                log_to_file(f"API Error: {response.status_code}, {response.reason}")
                break

            data = response.json()

            if not data.get("result") or not data["result"].get("token_accounts") or len(data["result"]["token_accounts"]) == 0:
                print(f"No more results. Total pages: {page - 1}")
                break
            
            print(f"Processing results from page {page}")
            
            # Store both owner address and token amount
            for account in data["result"]["token_accounts"]:
                # Get the amount from the account
                raw_amount = float(account.get("amount", 0))
                
                # Convert to human-readable format by dividing by 10^TOKEN_DECIMALS
                amount = raw_amount / (10 ** TOKEN_DECIMALS)
                
                # If owner already exists in dict, add to their total balance
                if account["owner"] in all_owners:
                    all_owners[account["owner"]] += amount
                else:
                    all_owners[account["owner"]] = amount
            
            page += 1

        # Convert dict to list of objects with wallet, amount, and tier information
        wallet_data = []
        for wallet, amount in all_owners.items():
            tier = get_tier_for_amount(amount)
            if tier:
                tier_counts[tier["id"]] += 1
            else:
                wallets_below_min_tier += 1
            total_wallets += 1
            
            wallet_data.append({
                "wallet": wallet,
                "amount": f"{amount:.5f}",  # Format amount to 5 decimal places for readability
                "tier": tier["id"] if tier else 0
            })

        # Sort wallets by amount in descending order (highest holders first)
        wallet_data.sort(key=lambda x: float(x["amount"]), reverse=True)

        # Output wallet data
        with open("output.json", "w") as f:
            json.dump(wallet_data, f, indent=2)
        
        # Create tier summary
        tier_summary = {
            "totalWallets": total_wallets,
            "walletsBelowMinTier": wallets_below_min_tier,
            "tiers": [{
                **tier,
                "walletCount": tier_counts[tier["id"]],
                "percentage": f"{(tier_counts[tier['id']] / total_wallets * 100):.2f}%"
            } for tier in TIERS]
        }
        
        # Output tier summary
        with open("tier_summary.json", "w") as f:
            json.dump(tier_summary, f, indent=2)

        print(f"Finished scanning token mint: {TOKEN_MINT}")
        print(f"Total holders: {len(all_owners)}")
        print("Tier summary:")
        print(f"Below all tiers (<{TIERS[0]['min']}): {wallets_below_min_tier} wallets ({wallets_below_min_tier / total_wallets * 100:.2f}%)")
        
        for tier in TIERS:
            print(f"{tier['name']} ({tier['min']}-{'MAX' if tier['max'] == float('inf') else tier['max']}): {tier_counts[tier['id']]} wallets ({tier_counts[tier['id']] / total_wallets * 100:.2f}%)")

        log_to_file(f"Finished token scan. Found {len(all_owners)} holders")
        
        return wallet_data
    except Exception as error:
        print(f"Error scanning token holders: {error}")
        log_to_file(f"Error scanning token holders: {error}")
        return []


def select_winners(holders, winner_count_per_tier=None):
    """
    Select random winners from each tier
    
    Args:
        holders (list): List of wallet data objects
        winner_count_per_tier (dict, optional): Dict with tier IDs as keys and winner counts as values
            
    Returns:
        dict: Dictionary with tier IDs as keys and lists of winners as values
    """
    if winner_count_per_tier is None:
        winner_count_per_tier = WINNERS_BY_TIER
        
    print('Selecting winners...')
    log_to_file('Selecting winners')
    
    winners = {}
    
    # Group holders by tier
    holders_by_tier = {}
    for holder in holders:
        tier = holder.get("tier", 0)
        if tier == 0:  # Skip wallets that don't belong to any tier
            continue
            
        if tier not in holders_by_tier:
            holders_by_tier[tier] = []
        
        holders_by_tier[tier].append(holder)
    
    # For each tier, select random winners
    for tier_id, tier_holders in holders_by_tier.items():
        if tier_id not in winner_count_per_tier:
            continue
            
        count = winner_count_per_tier[tier_id]
        
        # If we have fewer holders than the winner count, select all holders
        if len(tier_holders) <= count:
            winners[tier_id] = tier_holders
            print(f"Tier {tier_id}: Only {len(tier_holders)} holders, selected all as winners")
            log_to_file(f"Tier {tier_id}: Only {len(tier_holders)} holders, selected all as winners")
            
            # Log each winner's address
            for winner in tier_holders:
                log_to_file(f"Tier {tier_id} Winner: {winner['wallet']} with {winner['amount']} tokens")
        else:
            # Randomly select winners
            tier_winners = random.sample(tier_holders, count)
            winners[tier_id] = tier_winners
            print(f"Tier {tier_id}: Selected {count} winners out of {len(tier_holders)} holders")
            log_to_file(f"Tier {tier_id}: Selected {count} winners out of {len(tier_holders)} holders")
            
            # Log each winner's address
            for winner in tier_winners:
                log_to_file(f"Tier {tier_id} Winner: {winner['wallet']} with {winner['amount']} tokens")
    
    # Save winners to file
    with open("winners.json", "w") as f:
        # Convert to a serializable format
        serializable_winners = {
            tier_id: [winner for winner in tier_winners]
            for tier_id, tier_winners in winners.items()
        }
        json.dump(serializable_winners, f, indent=2)
    
    return winners


def generate_summary(winners):
    """
    Generate a summary of winners
    
    Args:
        winners (dict): Dictionary with tier IDs as keys and lists of winners as values
            
    Returns:
        dict: Summary object
    """
    print('Generating summary...')
    
    # Create summary object
    summary = {
        "timestamp": get_formatted_datetime(),
        "totalWinners": sum(len(tier_winners) for tier_winners in winners.values()),
        "tiers": []
    }
    
    # Add tier information to summary
    for tier in TIERS:
        tier_id = tier["id"]
        tier_winners = winners.get(tier_id, [])
        
        tier_summary = {
            "id": tier_id,
            "name": tier["name"],
            "winnerCount": len(tier_winners),
            "totalTokens": sum(float(winner["amount"]) for winner in tier_winners)
        }
        
        summary["tiers"].append(tier_summary)
    
    # Save summary to file
    # with open("winners_summary.json", "w") as f:
    #     json.dump(summary, f, indent=2)
    
    return summary


async def run_token_tracker():
    """Run the complete token tracking sequence"""
    start_time = time.time()
    print(f"\n----- Token Tracker Run: {get_formatted_datetime()} -----")
    log_to_file("Starting token tracker run")
    
    try:
        # Find all token holders
        holders = await find_holders()
        
        if not holders:
            print("No holders found, stopping tracking sequence")
            log_to_file("No holders found, stopping tracking sequence")
            return
        
        # Select winners
        winners = select_winners(holders)
        
        # Generate summary
        summary = generate_summary(winners)
        
        # Print summary
        print("\nWinner Selection Summary:")
        print(f"Total Winners: {summary['totalWinners']}")
        print("Tier Breakdown:")
        
        for tier_summary in summary["tiers"]:
            print(f"{tier_summary['name']}: {tier_summary['winnerCount']} winners, {tier_summary['totalTokens']:.2f} tokens total")
        
        # Print winners with their addresses and tiers (similar to JS version)
        print("\nSelected Winners:")
        for tier_id, tier_winners in winners.items():
            print(f"\n--- Tier {tier_id} Winners ---")
            for winner in tier_winners:
                print(f"Address: {winner['wallet']}, Amount: {winner['amount']}")
                log_to_file(f"Winner: Tier {tier_id}, Address: {winner['wallet']}, Amount: {winner['amount']}")
        
        # Calculate runtime
        run_time = time.time() - start_time
        print(f"\nToken tracking complete in {run_time:.2f} seconds")
        log_to_file(f"Token tracking complete in {run_time:.2f} seconds")
        
        # Record the run timestamp (similar to JS version)
        timestamp_file = './last_run.json'
        with open(timestamp_file, 'w') as f:
            json.dump({
                "lastRunAt": datetime.now().isoformat(),
                "completedAt": datetime.now().isoformat(),
                "durationSeconds": run_time,
                "nextRunAt": (datetime.now().timestamp() + INTERVAL_SECONDS)
            }, f, indent=2)
        
    except Exception as error:
        print(f"Error in token tracking sequence: {error}")
        log_to_file(f"Error in token tracking sequence: {error}")


async def main():
    """Main function that runs the token tracker continuously"""
    print(f"Token Tracker starting up at {get_formatted_datetime()}")
    log_to_file("Token Tracker starting up")
    
    while True:
        try:
            await run_token_tracker()
        except Exception as error:
            print(f"Unhandled error in token tracker: {error}")
            log_to_file(f"Unhandled error in token tracker: {error}")
        
        print(f"Waiting {INTERVAL_SECONDS} seconds for next run...")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    import asyncio
    
    try:
        # Add hook to handle keyboard interrupts gracefully
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nToken Tracker shutting down...")
        log_to_file("Token Tracker shutting down by user request")
    except Exception as e:
        print(f"Unhandled error in main process: {e}")
        log_to_file(f"Unhandled error in main process: {e}")
