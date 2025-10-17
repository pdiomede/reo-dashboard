## Rewards Eligibility Oracle (GIP-0079)

This dashboard is built to monitor indexers participating in [The Graph Protocol's Rewards Eligibility Oracle system](https://forum.thegraph.com/t/gip-0079-indexer-rewards-eligibility-oracle/6734).

### What is the Rewards Eligibility Oracle?

The **Rewards Eligibility Oracle** links eligibility for indexing rewards to the provision of quality service to consumers. Only indexers meeting minimum performance standards receive rewards, ensuring incentives align with providing value to the network.

**Key Features:**
- **Off-chain Oracle Nodes**: Assess indexer performance against published criteria
- **On-chain Oracle Contract**: Tracks which indexers are eligible for rewards
- **Service Quality Metrics**: Indexers are evaluated on actual service provision
- **14-Day Eligibility Period**: Qualifying indexers have their eligibility renewed for 14 days
- **Performance-Based**: Ineligible indexers are denied rewards until they improve service quality

This system ensures that rewards are distributed only to indexers who actively serve queries and maintain quality service, rather than simply allocating tokens based on stake alone.

**Learn More:**
- [GIP-0079 Forum Discussion](https://forum.thegraph.com/t/gip-0079-indexer-rewards-eligibility-oracle/6734)
- [Full GIP-0079 Proposal](https://forum.thegraph.com/t/gip-0079-indexer-rewards-eligibility-oracle/6734)

## Features

- 📊 **Sortable Table**: Click column headers to sort by number, address, or ENS name
- 🔍 **Real-time Search**: Filter indexers by address or ENS name
- 🔗 **Blockchain Integration**: Fetches live data from Arbitrum Sepolia via QuickNode RPC
- ⏰ **Oracle Update Time**: Displays the last oracle update timestamp from the contract
- 📱 **Responsive Design**: Mobile-friendly dark theme UI
- 💾 **Offline Fallback**: Can work with cached transaction data from JSON file

## How It Works

### Data Flow

```
┌──────────────────┐
│ Network Subgraph │ ──┐
│  (Active Indexers)│   │
└──────────────────┘   │
                       │
┌──────────────────┐   │
│  ENS Subgraph    │ ──┤
│  (Name Resolution)│   ├──► retrieveActiveIndexers() 
└──────────────────┘   │         │
                       │         ▼
┌──────────────────┐   │    active_indexers.json
│ Contract: Oracle │ ──┤         │
│  (Eligibility)   │   │         ▼
└──────────────────┘   │    checkEligibility()
                       │         │
┌──────────────────┐   │         ▼
│last_transaction  │ ──┤    renderIndexerTable()
│     .json        │   │         │
└──────────────────┘   │         ▼
                       └──► HTML Dashboard (only eligible indexers)
```

### Main Components

#### 1. **Active Indexers Retrieval**
- **`retrieveActiveIndexers()`**: Queries The Graph's network subgraph to get indexers with self stake > 0
  - Queries network subgraph (deployment ID: `DZz4kDTdmzWLWsV373w2bSmoar3umKKH9y82SUKr5qmp`)
  - Resolves ENS names via ENS subgraph (deployment ID: `5XqPmWe6gjyrJtFn9cLy237i4cWw2j9HcUJEXsP5qGtH`)
  - Writes results to `active_indexers.json` with fields: `address`, `ens_name`, `is_eligible`, `status`, `eligible_until`, `eligibility_renewal_time`

#### 2. **Eligibility Check (Two-Pass Approach)**
- **`checkEligibility()`**: Checks eligibility status for all active indexers
  - **Pass 1**: Calls `isEligible(address)` on contract for all indexers, stores result in `is_eligible` field
  - **Pass 2**: Only for eligible indexers, calls `getEligibilityRenewalTime(address)` and updates `eligibility_renewal_time`
  - Updates `active_indexers.json` with eligibility data

#### 3. **Dashboard Rendering**
- **`renderIndexerTable()`**: Reads `active_indexers.json` and filters only eligible indexers (`is_eligible = true`)
  - Returns list of eligible indexers to display on the dashboard
  - Indexers with `is_eligible = false` are excluded from the dashboard view

#### 4. **Transaction Data Retrieval**
The script tries multiple methods to fetch the last transaction data (in priority order):

1. **`get_last_transaction_from_json()`**: 
   - Reads from local `last_transaction.json` file (fastest, offline-capable)
   
2. **`get_last_transaction_via_quicknode()`**: 
   - Scans recent blocks via QuickNode RPC endpoint
   - Finds the most recent transaction to the contract address
   
3. **`get_last_transaction()`**: 
   - Falls back to Arbiscan API
   - Returns `None` if API is unavailable (no mock data used)

#### 5. **Oracle Update Time**
- **`get_oracle_update_time()`**: 
  - Calls the contract's `getLastOracleUpdateTime()` function via RPC
  - Function selector: `0xbe626dd2`
  - Returns Unix timestamp of the last oracle update

#### 6. **Eligibility Period**
- **`get_eligibility_period()`**: 
  - Calls the contract's `getEligibilityPeriod()` function via RPC
  - Function selector: `0xd0a5379e`
  - Returns eligibility period in seconds

#### 7. **HTML Generation**
- **`generate_html_dashboard()`**: 
  - Loads eligible indexers using `renderIndexerTable()`
  - Creates a complete, self-contained HTML file
  - Embeds all CSS styling
  - Includes JavaScript for search and sort functionality
  - **Displays only eligible indexers** in the main table
  - Formats timestamps to human-readable dates

## File Structure

```
.
├── generate_dashboard.py    # Main script
├── indexers.txt             # Legacy file (still read for backwards compatibility)
├── active_indexers.json     # Active indexers with eligibility data (generated)
├── last_transaction.json    # Cached transaction data (generated)
├── grt.png                  # Logo image for the dashboard
├── index.html               # Generated dashboard (output)
├── .env                     # Environment variables (create from .env.example)
├── .env.example             # Template for environment variables
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Usage

### Prerequisites

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install requests python-dotenv pycryptodome
```

### Environment Variables

The script reads configuration from a `.env` file in the project root. 

**Setup:**
1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your actual values:
   ```bash
   CONTRACT_ADDRESS=0x9BED32d2b562043a426376b99d289fE821f5b04E
   ARBISCAN_API_KEY=your_arbiscan_api_key
   QUICK_NODE=your_quicknode_rpc_url
   ```

The script will automatically load these variables. All three variables are required for the script to run.

### Running the Script

```bash
python3 generate_dashboard.py
```

This will:
1. **Retrieve active indexers** from The Graph's network subgraph (with self stake > 0)
2. **Resolve ENS names** via ENS subgraph
3. **Check eligibility** for each indexer by calling the contract's `isEligible()` function
4. **Get renewal times** for eligible indexers via `getEligibilityRenewalTime()`
5. Save all data to `active_indexers.json`
6. **Render dashboard** showing only eligible indexers (`is_eligible = true`)
7. Fetch the latest transaction data
8. Fetch the oracle update time from the contract
9. Generate `index.html`

### Opening the Dashboard

```bash
open index.html
```

Or simply double-click `index.html` to open it in your browser.

## Configuration

All configuration is managed through environment variables in the `.env` file:

### Contract Address
- **Variable**: `CONTRACT_ADDRESS`
- **Default**: `0x9BED32d2b562043a426376b99d289fE821f5b04E` (Arbitrum Sepolia)
- **Purpose**: The Rewards Eligibility Oracle contract address

### Arbiscan API Key
- **Variable**: `ARBISCAN_API_KEY`
- **Purpose**: Fetches transaction data from Arbiscan API
- **Get yours**: [Arbiscan API Keys](https://arbiscan.io/myapikey)

### QuickNode RPC Endpoint
- **Variable**: `QUICK_NODE`
- **Purpose**: Connects to Arbitrum Sepolia for real-time blockchain data
- **Get yours**: [QuickNode](https://quicknode.com)

## Data Sources

### Generated: `active_indexers.json`
This file is automatically generated by the script and contains all active indexers with their eligibility data.

Structure:
```json
{
  "metadata": {
    "retrieved": "2025-10-17 20:00:00 UTC",
    "total_count": 100,
    "ens_resolved": 74
  },
  "indexers": [
    {
      "address": "0x0058223c6617cca7ce76fc929ec9724cd43d4542",
      "ens_name": "grassets-tech-2.eth",
      "is_eligible": true,
      "status": "",
      "eligible_until": "",
      "eligibility_renewal_time": 1760696509
    }
  ]
}
```

**Key Fields:**
- `is_eligible`: Boolean indicating if the indexer is eligible for rewards (from contract's `isEligible()`)
- `eligibility_renewal_time`: Unix timestamp of eligibility renewal (from contract's `getEligibilityRenewalTime()`)
- **Only indexers with `is_eligible = true` are displayed on the dashboard**

### Legacy: `indexers.txt` (Optional)
This file is still read for backwards compatibility but is not used for the main dashboard table.

Format:
```
0x0058223c6617cca7ce76fc929ec9724cd43d4542,grassets-tech-2.eth
0x01f17c392614c7ea586e7272ed348efee21b90a3,oraclegen-indexer.eth
```

### Cache: `last_transaction.json`
Example:
```json
{
  "hash": "0x4401f694b80775533566053f88026220e1eab4c84f771e5b600df76f89a768bc",
  "blockNumber": "205536308",
  "timeStamp": "1760696509",
  "status": "Success",
  "readable_time": "Oct-17-2025 10:21:49"
}
```

## Dashboard Features

### Contract Information Section
Displays before the table:
- **Sepolia Contract on Arbitrum**: Contract address with link to Arbiscan
- **Last Transaction ID**: Transaction hash with link to Arbiscan
- **Block Number**: Block where the transaction occurred
- **Transaction Time**: When the transaction was executed
- **Last Oracle Update Time**: Latest oracle update timestamp from the contract

### Indexers Table
- **Eligibility Filtering**: Only displays indexers where `is_eligible = true`
- **Sortable columns**: Click any header to sort
- **Search functionality**: Real-time filtering by address or ENS name
- **Statistics**: Shows total eligible indexers and filtered count
- **Color-coded**: ENS names highlighted, missing ENS shown in gray
- **Clickable addresses**: Each indexer address links to their profile on The Graph Explorer

## Technical Details

### Timestamp Conversion
All Unix timestamps are converted to UTC format:
```python
datetime.fromtimestamp(timestamp_int, tz=timezone.utc)
    .strftime("%d %b %Y at %H:%M (UTC)")
```

### Contract Function Call
The script calls `getLastOracleUpdateTime()` using RPC:
```python
function_selector = '0xbe626dd2' + '0' * 56  # Padded to 32 bytes
# eth_call to contract
```

### Block Scanning
When fetching transactions, the script scans the last 100 blocks to find the most recent transaction to the contract address.

## Error Handling

The script includes robust error handling with **no mock data**:
- Falls back through multiple data sources (JSON → QuickNode → Arbiscan)
- Prints informative console messages for debugging
- Gracefully handles missing data without using fake/mock values
- Displays clear error messages in the dashboard UI when data is unavailable:
  - **"Unable to fetch transaction data"** - when all transaction fetch methods fail
  - **"Unable to fetch oracle update time"** - when contract call fails
- All errors are displayed in styled red text (`.error-message` class) in the dashboard

## Styling

The dashboard uses a modern dark theme:
- **Background**: `#0C0A1D` (dark purple)
- **Text**: `#F8F6FF` (off-white)
- **Accent**: `#494755` (medium gray)
- **Font**: Poppins (from Google Fonts)

## Browser Compatibility

Works in all modern browsers:
- Chrome/Edge (Chromium)
- Firefox
- Safari
- Mobile browsers

## License

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contact

**X (Twitter):** [@pdiomede](https://x.com/pdiomede)

