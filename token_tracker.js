const fs = require("fs");
const url = `https://mainnet.helius-rpc.com/?api-key=`; // API key from Helius

// Token configuration
const TOKEN_MINT = "6rQt2W1kPAZGhuSMJmPnRgJndLb1HfK6E4cHiQTxoxzq";
const TOKEN_DECIMALS = 6; // Number of decimals in the token check on Solscan if not sure

// Define holding tiers
const TIERS = [
  { id: 1, name: "Tier 1", min: 10000, max: 99999 },
  { id: 2, name: "Tier 2", min: 100000, max: 499999 },
  { id: 3, name: "Tier 3", min: 500000, max: 999999 },
  { id: 4, name: "Tier 4", min: 1000000, max: 4999999 },
  { id: 5, name: "Tier 5", min: 5000000, max: Number.MAX_SAFE_INTEGER }
];

// Define winner count per tier
const WINNERS_BY_TIER = {
  1: 5,  // Tier 1: 5 winners
  2: 4,  // Tier 2: 4 winners
  3: 3,  // Tier 3: 3 winners
  4: 2,  // Tier 4: 2 winners
  5: 1   // Tier 5: 1 winner
};

// Time interval in milliseconds (10 minutes)
const INTERVAL_MS = 10 * 60 * 1000;

// Create logs directory if it doesn't exist
const logDir = './logs';
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir);
}

/**
 * Get the tier for a given amount
 * @param {number} amount - Token amount
 * @returns {object|null} - Tier object or null if no tier matches
 */
const getTierForAmount = (amount) => {
  for (const tier of TIERS) {
    if (amount >= tier.min && amount <= tier.max) {
      return tier;
    }
  }
  return null; // No tier matches (amount is less than the minimum of any tier)
};

/**
 * Format current date and time
 * @returns {string} Formatted date and time
 */
const getFormattedDateTime = () => {
  const now = new Date();
  return now.toISOString().replace(/T/, ' ').replace(/\..+/, '');
};

/**
 * Append a message to the log file
 * @param {string} message - Message to log
 */
const logToFile = (message) => {
  const logFile = `${logDir}/tracker_${new Date().toISOString().split('T')[0]}.log`;
  fs.appendFileSync(logFile, `${getFormattedDateTime()} - ${message}\n`);
};

/**
 * Find all token holders and categorize them by tier
 * @returns {Array} Array of wallet data objects
 */
const findHolders = async () => {
  console.log('Scanning for token holders...');
  logToFile('Starting token holder scan');
  
  let page = 1;
  let allOwners = new Map(); // Map to store owner-amount pairs
  
  // Track counts for each tier
  const tierCounts = TIERS.reduce((acc, tier) => {
    acc[tier.id] = 0;
    return acc;
  }, {});
  
  let totalWallets = 0;
  let walletsBelowMinTier = 0;

  try {
    while (true) {
      console.log(`Fetching page ${page}...`);
      
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          jsonrpc: "2.0",
          method: "getTokenAccounts",
          id: "helius-test",
          params: {
            page: page,
            limit: 1000,
            displayOptions: {},
            mint: TOKEN_MINT,
          },
        }),
      });

      // Check if any error in the response
      if (!response.ok) {
        console.log(`Error: ${response.status}, ${response.statusText}`);
        logToFile(`API Error: ${response.status}, ${response.statusText}`);
        break;
      }

      const data = await response.json();

      if (!data.result || data.result.token_accounts.length === 0) {
        console.log(`No more results. Total pages: ${page - 1}`);
        break;
      }
      
      console.log(`Processing results from page ${page}`);
      
      // Store both owner address and token amount
      data.result.token_accounts.forEach((account) => {
        // Get the amount from the account
        const rawAmount = account.amount ? Number(account.amount) : 0;
        
        // Convert to human-readable format by dividing by 10^TOKEN_DECIMALS
        const amount = rawAmount / Math.pow(10, TOKEN_DECIMALS);
        
        // If owner already exists in map, add to their total balance
        if (allOwners.has(account.owner)) {
          const currentAmount = allOwners.get(account.owner);
          allOwners.set(account.owner, currentAmount + amount);
        } else {
          allOwners.set(account.owner, amount);
        }
      });
      
      page++;
    }

    // Convert Map to array of objects with wallet, amount, and tier information
    const walletData = Array.from(allOwners.entries()).map(([wallet, amount]) => {
      const tier = getTierForAmount(amount);
      if (tier) {
        tierCounts[tier.id]++;
      } else {
        walletsBelowMinTier++;
      }
      totalWallets++;
      
      return {
        wallet,
        amount: amount.toFixed(5), // Format amount to 5 decimal places for readability
        tier: tier ? tier.id : 0
      };
    });

    // Sort wallets by amount in descending order (highest holders first)
    walletData.sort((a, b) => parseFloat(b.amount) - parseFloat(a.amount));

    // Output wallet data
    fs.writeFileSync(
      "output.json",
      JSON.stringify(walletData, null, 2)
    );
    
    // Create tier summary
    const tierSummary = {
      totalWallets,
      walletsBelowMinTier,
      tiers: TIERS.map(tier => ({
        ...tier,
        walletCount: tierCounts[tier.id],
        percentage: ((tierCounts[tier.id] / totalWallets) * 100).toFixed(2) + '%'
      }))
    };
    
    // Output tier summary
    fs.writeFileSync(
      "tier_summary.json",
      JSON.stringify(tierSummary, null, 2)
    );

    console.log(`Finished scanning token mint: ${TOKEN_MINT}`);
    console.log(`Total holders: ${allOwners.size}`);
    console.log("Tier summary:");
    console.log(`Below all tiers (<${TIERS[0].min}): ${walletsBelowMinTier} wallets (${((walletsBelowMinTier / totalWallets) * 100).toFixed(2)}%)`);
    
    TIERS.forEach(tier => {
      console.log(`${tier.name} (${tier.min}-${tier.max === Number.MAX_SAFE_INTEGER ? 'MAX' : tier.max}): ${tierCounts[tier.id]} wallets (${((tierCounts[tier.id] / totalWallets) * 100).toFixed(2)}%)`);
    });

    logToFile(`Finished token scan. Found ${allOwners.size} holders`);
    
    return walletData;
  } catch (error) {
    console.error('Error scanning token holders:', error);
    logToFile(`Error scanning token holders: ${error.message}`);
    return [];
  }
};

/**
 * Select random winners from each tier
 * @param {Array} holders - Array of wallet data objects
 * @param {Object} winnerCountPerTier - Object with tier IDs as keys and winner counts as values
 * @returns {Object} Object with tier IDs as keys and arrays of winners as values
 */
const selectWinners = (holders, winnerCountPerTier = WINNERS_BY_TIER) => {
  console.log('Selecting winners...');
  logToFile('Selecting winners');
  
  const tierHolders = {
    1: [],
    2: [],
    3: [],
    4: [],
    5: []
  };
  
  // Group holders by tier
  holders.forEach(holder => {
    if (holder.tier > 0) {
      tierHolders[holder.tier].push(holder);
    }
  });
  
  const winners = {};
  
  // Select winners for each tier
  for (const tier in tierHolders) {
    winners[tier] = [];
    
    if (tierHolders[tier].length === 0) {
      console.log(`No holders found in Tier ${tier}`);
      continue;
    }
    
    // Select random winners without replacement
    const selectedIndices = new Set();
    const tierHolderCount = tierHolders[tier].length;
    const winnerCount = winnerCountPerTier[tier] || 1;
    const actualWinnerCount = Math.min(winnerCount, tierHolderCount);
    
    while (selectedIndices.size < actualWinnerCount) {
      const randomIndex = Math.floor(Math.random() * tierHolderCount);
      if (!selectedIndices.has(randomIndex)) {
        selectedIndices.add(randomIndex);
        const winner = tierHolders[tier][randomIndex];
        
        winners[tier].push({
          wallet: winner.wallet,
          amount: winner.amount,
          tier: tier
        });
      }
    }
  }
  
  return winners;
};

/**
 * Generate a summary of winners
 * @param {Object} winners - Object with tier IDs as keys and arrays of winners as values
 * @returns {Object} Summary object
 */
const generateSummary = (winners) => {
  let totalWinners = 0;
  let summary = {};
  
  for (const tier in winners) {
    totalWinners += winners[tier].length;
    
    summary[tier] = {
      winnerCount: winners[tier].length
    };
  }
  
  return {
    totalWallets: totalWinners,
    tierSummary: summary
  };
};

/**
 * Run the complete token tracking sequence
 */
const runTokenTracker = async () => {
  const startTime = new Date();
  console.log(`\n--- Starting token tracker at ${getFormattedDateTime()} ---`);
  logToFile('--- Starting token tracker sequence ---');
  
  try {
    // Step 1: Find all token holders
    const holders = await findHolders();
    
    if (holders.length === 0) {
      console.log('No holders found. Aborting winner selection.');
      logToFile('No holders found. Aborting winner selection.');
      return;
    }
    
    // Step 2: Select winners from each tier
    const allWinners = selectWinners(holders, WINNERS_BY_TIER);
    
    // Step 3: Generate and save summary
    const summary = generateSummary(allWinners);
    
    // Save results to file
    fs.writeFileSync(
      './winners.json', 
      JSON.stringify(allWinners, null, 2), 
      'utf8'
    );
    
    console.log('\nWinners selected successfully!');
    console.log(`Total winners: ${summary.totalWallets}`);
    
    // Print winners with their addresses and tiers
    for (const tier in allWinners) {
      console.log(`\n--- Tier ${tier} Winners ---`);
      allWinners[tier].forEach(winner => {
        console.log(`Address: ${winner.wallet}, Tier: ${winner.tier}`);
      });
    }
    
    console.log('\nDetails saved to winners.json');
    
    // Record the run timestamp
    const endTime = new Date();
    const durationMs = endTime - startTime;
    const timestampFile = './last_run.json';
    fs.writeFileSync(timestampFile, JSON.stringify({ 
      lastRunAt: startTime.toISOString(),
      completedAt: endTime.toISOString(),
      durationMs: durationMs,
      nextRunAt: new Date(Date.now() + INTERVAL_MS).toISOString()
    }, null, 2));
    
    logToFile(`Completed token tracker sequence. Duration: ${durationMs}ms`);
    console.log(`\n--- Completed token tracker at ${getFormattedDateTime()} ---`);
    console.log(`Duration: ${(durationMs / 1000).toFixed(2)} seconds`);
    console.log(`Next run scheduled at: ${new Date(Date.now() + INTERVAL_MS).toLocaleString()}`);
    
  } catch (error) {
    console.error('Error in token tracker sequence:', error);
    logToFile(`Error in token tracker sequence: ${error.message}`);
  }
};

/**
 * Main function that runs the token tracker continuously
 */
const main = async () => {
  // Run immediately on startup
  await runTokenTracker();
  
  // Schedule to run at the interval
  console.log(`\nToken tracker will run every ${INTERVAL_MS / 60000} minutes.`);
  setInterval(runTokenTracker, INTERVAL_MS);
};

// Start the token tracker
main().catch(err => {
  console.error('Unhandled error in main process:', err);
  logToFile(`Unhandled error in main process: ${err.message}`);
});

// Keep the process alive
process.stdin.resume();

// Handle signals gracefully
process.on('SIGINT', () => {
  console.log('\nShutting down token tracker...');
  logToFile('Token tracker was shutdown by user (SIGINT)');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\nShutting down token tracker...');
  logToFile('Token tracker was shutdown (SIGTERM)');
  process.exit(0);
});
