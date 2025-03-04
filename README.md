# Token Tracker

A Node.js application that tracks token holders on the Solana blockchain, categorizes them by tier based on their holdings, and randomly selects winners from each tier.

## Features

- Scans for all holders of a specified token on Solana
- Categorizes holders into predefined tiers based on token amounts
- Selects random winners from each tier according to configurable rules
- Generates detailed logs and holder statistics
- Outputs data in JSON format for further analysis

## Prerequisites

- Node.js (v14 or higher)
- npm (Node Package Manager)

## Installation

1. Clone this repository or download the source code
2. Install the required dependencies:

```bash
npm install
```

## Configuration

The token tracker is configured with the following parameters in the `token_tracker.js` file:

- `TOKEN_MINT`: The Solana mint address of the token to track
- `TOKEN_DECIMALS`: The number of decimal places for the token
- `TIERS`: Holding tiers for categorizing wallets
- `WINNERS_BY_TIER`: Number of winners to select from each tier
- `INTERVAL_MS`: Time interval between tracking runs (in milliseconds)

## Usage

To run the token tracker:

```bash
node token_tracker.js
```

The script will:
1. Scan for all token holders
2. Categorize holders into tiers
3. Select random winners from each tier
4. Generate output files with results
5. Log activities to the console and log files

## Output Files

The token tracker generates the following output files:

- `output.json`: Contains data for all token holders with their wallet addresses, token amounts, and tier information
- `tier_summary.json`: Summary of wallets in each tier with statistics
- `winners_summary.json`: Information about the randomly selected winners
- Log files in the `./logs` directory (created automatically)

## Scheduled Runs

The token tracker is designed to run continuously at intervals defined by the `INTERVAL_MS` setting. By default, it runs every 10 minutes.

