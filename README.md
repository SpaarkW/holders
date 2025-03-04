# Token Tracker

A blockchain application that tracks token holders on the Solana blockchain, categorizes them by tier based on their holdings, and randomly selects winners from each tier. Available in both JavaScript and Python versions.

## Features

- Scans for all holders of a specified token on Solana
- Categorizes holders into predefined tiers based on token amounts
- Selects random winners from each tier according to configurable rules
- Generates detailed logs and holder statistics
- Outputs data in JSON format for further analysis

## Prerequisites

### For JavaScript version
- Node.js (v14 or higher)
- npm (Node Package Manager)

### For Python version
- Python 3.7 or higher
- pip (Python Package Manager)

## Installation

1. Clone this repository or download the source code
2. Install the required dependencies:

### Quick Setup (Recommended)

We provide a setup script that automates the installation process:

```bash
# Make the script executable
chmod +x setup.sh

# Setup JavaScript version
./setup.sh js

# Setup Python version
./setup.sh python

# Setup both versions
./setup.sh both
```

### Manual Setup

#### For JavaScript version
```bash
npm install
```

#### For Python version

##### Setting up a virtual environment (recommended)
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

##### Direct installation (alternative)
```bash
pip install requests
```

## Configuration

The token tracker is configured with similar parameters in both versions:

- `TOKEN_MINT`: The Solana mint address of the token to track
- `TOKEN_DECIMALS`: The number of decimal places for the token
- `TIERS`: Holding tiers for categorizing wallets
- `WINNERS_BY_TIER`: Number of winners to select from each tier
- `INTERVAL_MS`/`INTERVAL_SECONDS`: Time interval between tracking runs

**Important**: You need to add your Helius API key to the `url` variable in the code.

## Usage

### Using the setup script:
```bash
# Run JavaScript version
./setup.sh run-js

# Run Python version
./setup.sh run-python
```

### Manual execution:

#### To run the JavaScript version:
```bash
node token_tracker.js
```

#### To run the Python version:
```bash
# If using virtual environment, make sure it's activated:
source venv/bin/activate  # On Linux/macOS
# venv\Scripts\activate   # On Windows

python token_tracker.py
```

The script will:
1. Scan for all token holders
2. Categorize holders into tiers
3. Select random winners from each tier
4. Generate output files with results
5. Log activities to the console and log files

## Output Files

Both versions generate the following output files:

- `output.json`: Contains data for all token holders with their wallet addresses, token amounts, and tier information
- `tier_summary.json`: Summary of wallets in each tier with statistics
- `winners.json`: Raw data of the selected winners
- `winners_summary.json`: Summary information about the randomly selected winners
- Log files in the `./logs` directory (created automatically)

## Scheduled Runs

The token tracker is designed to run continuously at intervals. By default, it runs every 10 minutes.
