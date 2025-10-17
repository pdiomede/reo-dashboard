# Eligibility Dashboard Generator

A Python script that generates a static HTML dashboard displaying indexer information with real-time blockchain data from Arbitrum Sepolia.

## Overview

This dashboard provides a searchable, sortable table of indexers along with contract information including the last transaction and oracle update times fetched directly from the blockchain.

## Context: Rewards Eligibility Oracle (GIP-0079)

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
┌─────────────────┐
│  indexers.txt   │ ──┐
└─────────────────┘   │
                      │
┌─────────────────┐   │
│last_transaction │ ──┤
│    .json        │   ├──► Python Script ──► HTML Dashboard
└─────────────────┘   │   (generate_dashboard.py)
                      │
┌─────────────────┐   │
│ QuickNode RPC   │ ──┘
│  (Blockchain)   │
└─────────────────┘
```

### Main Components

#### 1. **Data Loading**
- **`read_indexers_data()`**: Reads the list of indexer addresses and ENS names from `indexers.txt`
  - Format: `address,ens_name` (one per line)
  - Handles missing ENS names gracefully

#### 2. **Transaction Data Retrieval**
The script tries multiple methods to fetch the last transaction data (in priority order):

1. **`get_last_transaction_from_json()`**: 
   - Reads from local `last_transaction.json` file (fastest, offline-capable)
   
2. **`get_last_transaction_via_quicknode()`**: 
   - Scans recent blocks via QuickNode RPC endpoint
   - Finds the most recent transaction to the contract address
   
3. **`get_last_transaction()`**: 
   - Falls back to Arbiscan API
   - Returns `None` if API is unavailable (no mock data used)

#### 3. **Oracle Update Time**
- **`get_oracle_update_time()`**: 
  - Calls the contract's `getLastOracleUpdateTime()` function via RPC
  - Function selector: `0xbe626dd2`
  - Returns Unix timestamp of the last oracle update

#### 4. **HTML Generation**
- **`generate_html_dashboard()`**: 
  - Creates a complete, self-contained HTML file
  - Embeds all CSS styling
  - Includes JavaScript for search and sort functionality
  - Formats timestamps to human-readable dates

## File Structure

```
.
├── generate_dashboard.py    # Main script
├── indexers.txt             # List of indexer addresses and ENS names
├── last_transaction.json    # Cached transaction data (optional)
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
   ARBISCAN_API_KEY=your_arbiscan_api_key
   QUICK_NODE=your_quicknode_rpc_url
   ```

The script will automatically load these variables. If the `.env` file is not found or variables are not set, it will use default/fallback values.

### Running the Script

```bash
python3 generate_dashboard.py
```

This will:
1. Read indexer data from `indexers.txt`
2. Fetch the latest transaction data
3. Fetch the oracle update time from the contract
4. Generate `index.html`

### Opening the Dashboard

```bash
open index.html
```

Or simply double-click `index.html` to open it in your browser.

## Configuration

### Contract Address
Default: `0x9BED32d2b562043a426376b99d289fE821f5b04E` (Arbitrum Sepolia)

To change the contract address, modify the `generate_html_dashboard()` function parameter.

### QuickNode RPC Endpoint
The script uses a QuickNode endpoint for Arbitrum Sepolia. Update the `QUICK_NODE` environment variable or modify the default in `main()`.

## Data Sources

### Input: `indexers.txt`
Format:
```
0x0058223c6617cca7ce76fc929ec9724cd43d4542,grassets-tech-2.eth
0x01f17c392614c7ea586e7272ed348efee21b90a3,oraclegen-indexer.eth
0x089f78d8cf0a5ae1b7a581b1910a73f8cb3e4774,darksiders-team.eth
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
- **Sortable columns**: Click any header to sort
- **Search functionality**: Real-time filtering by address or ENS name
- **Statistics**: Shows total indexers and filtered count
- **Color-coded**: ENS names highlighted, missing ENS shown in gray

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

