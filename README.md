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

- 📊 **Smart Sorting**: Automatically sorts by eligibility status (eligible → grace → ineligible), then by ENS name
- 🏷️ **Three Status Types**: 
  - **Eligible**: Indexers with current eligibility (green badge)
  - **Grace Period**: Indexers in 14-day grace period with expiration date (yellow badge)
  - **Ineligible**: Indexers who lost eligibility (red badge)
- 🔍 **Real-time Search**: Filter indexers by address or ENS name
- 🔗 **Blockchain Integration**: Fetches live data from Arbitrum Sepolia via QuickNode RPC
- ⏰ **Oracle Tracking**: Displays last oracle update time and 14-day eligibility period from contract
- ⏳ **Grace Period Monitoring**: Shows when grace period expires for indexers in transition
- 📱 **Responsive Design**: Mobile-friendly dark theme UI with collapsible sections
- 💾 **Offline Fallback**: Can work with cached transaction data from JSON file

## How It Works

### Data Flow

```
┌───────────────────┐
│ Network Subgraph  │ ──┐
│  (Active Indexers)│   │
└───────────────────┘   │
                        │
┌───────────────────┐   │
│  ENS Subgraph     │ ──┤
│  (Name Resolution)│   ├──► retrieveActiveIndexers() 
└───────────────────┘   │         │
     (or cached)        │         ▼
                        │    active_indexers.json
┌───────────────────┐   │         +
│ ens_resolution    │ ──┤    ens_resolution.json (cached ENS)
│     .json         │   │         │
└───────────────────┘   │         ▼
                        │    checkEligibility()
┌───────────────────┐   │         │
│ Contract: Oracle  │ ──┤         ▼
│  (Eligibility)    │   │    renderIndexerTable() (merges ENS data)
└───────────────────┘   │         │
                        │         ▼
┌───────────────────┐   │    HTML Dashboard (only eligible indexers)
│last_transaction   │ ──┘
│     .json         │
└───────────────────┘
```

### Main Components

#### 1. **Active Indexers Retrieval**
- **`retrieveActiveIndexers()`**: Queries The Graph's network subgraph to get indexers with self stake > 0
  - Queries network subgraph (deployment ID: `DZz4kDTdmzWLWsV373w2bSmoar3umKKH9y82SUKr5qmp`)
  - Fetches contract metadata:
    - Calls `getLastOracleUpdateTime()` (function selector: `0xbe626dd2`)
    - Calls `getEligibilityPeriod()` (function selector: `0xd0a5379e`)
    - Stores both values in metadata section of JSON
  - ENS resolution strategy (controlled by `USE_CACHED_ENS` environment variable):
    - **If `USE_CACHED_ENS=Y`**: Loads ENS names from `ens_resolution.json` cache file
    - **If `USE_CACHED_ENS=N`**: Queries ENS subgraph (deployment ID: `5XqPmWe6gjyrJtFn9cLy237i4cWw2j9HcUJEXsP5qGtH`) and updates cache
  - Writes results to `active_indexers.json` with fields: `address`, `is_eligible`, `status`, `eligible_until`, `eligible_until_readable`, `eligibility_renewal_time` (ENS stored separately)
  - ENS data saved to `ens_resolution.json` for caching

#### 2. **Eligibility Check (Three-Pass Approach)**
- **`checkEligibility()`**: Checks eligibility status for all active indexers
  - **Pass 1**: Calls `isEligible(address)` on contract for all indexers, stores result in `is_eligible` field
  - **Pass 2**: Only for eligible indexers, calls `getEligibilityRenewalTime(address)` (function selector: `0xd353402d`) and updates `eligibility_renewal_time`
  - **Pass 3**: Determines final status based on eligibility renewal time and grace period:
    - **"eligible"**: `eligibility_renewal_time == last_oracle_update_time`
    - **"grace"**: `eligibility_renewal_time != last_oracle_update_time` AND `current_time < eligibility_renewal_time + eligibility_period`
      - Sets `eligible_until` (Unix timestamp) and `eligible_until_readable` (human-readable format)
    - **"ineligible"**: Grace period has expired or no eligibility renewal time
  - Updates `active_indexers.json` with complete eligibility data including status

#### 3. **Status Change Tracking**
- **`updateStatusChangeDates()`**: Detects and tracks status changes between runs
  - **Before generating new data**: Backs up current `active_indexers.json` to `active_indexers_previous_run.json`
  - **After eligibility check**: Compares current run with previous run
  - **Comparison logic** (by indexer address):
    - **Status changed** (e.g., "eligible" → "grace"): Sets `last_status_change_date` to current date (format: `21/Oct/2025`)
    - **Status unchanged**: Keeps the previous `last_status_change_date` value (could be empty or a date)
    - **New indexer**: Leaves `last_status_change_date` empty (no previous status to compare)
  - **Date only appears when status actually changes** - stays empty until first change occurs
  - Updates `active_indexers.json` with status change dates

#### 4. **Dashboard Rendering**
- **`renderIndexerTable()`**: Reads `active_indexers.json` and returns all indexers
  - Loads ENS names from `ens_resolution.json` cache
  - Merges ENS data with indexer eligibility data
  - Returns list of all indexers with ENS names to display on the dashboard
  - **Both eligible and ineligible indexers are displayed** with appropriate status badges

#### 5. **Transaction Data Retrieval**
The script tries multiple methods to fetch the last transaction data (in priority order):

1. **`get_last_transaction_from_json()`**: 
   - Reads from local `last_transaction.json` file (fastest, offline-capable)
   
2. **`get_last_transaction_via_quicknode()`**: 
   - Scans recent blocks via QuickNode RPC endpoint
   - Finds the most recent transaction to the contract address
   
3. **`get_last_transaction()`**: 
   - Falls back to Arbiscan API
   - Returns `None` if API is unavailable (no mock data used)

#### 6. **Oracle Update Time**
- **`get_oracle_update_time()`**: 
  - Calls the contract's `getLastOracleUpdateTime()` function via RPC
  - Function selector: `0xbe626dd2`
  - Returns Unix timestamp of the last oracle update

#### 7. **Eligibility Period**
- **`get_eligibility_period()`**: 
  - Calls the contract's `getEligibilityPeriod()` function via RPC
  - Function selector: `0xd0a5379e`
  - Returns eligibility period in seconds

#### 8. **HTML Generation**
- **`generate_html_dashboard()`**: 
  - Loads all indexers using `renderIndexerTable()`
  - Creates a complete, self-contained HTML file
  - Embeds all CSS styling
  - Includes JavaScript for search and sort functionality
  - **Displays all indexers** with status badges (eligible/ineligible) in the main table
  - Formats timestamps to human-readable dates

## File Structure

```
.
├── generate_dashboard.py              # Main script
├── indexers.txt                       # Legacy file (still read for backwards compatibility)
├── active_indexers.json               # Active indexers with eligibility data (generated)
├── active_indexers_previous_run.json  # Backup of previous run for status change tracking (generated)
├── ens_resolution.json                # ENS name cache (generated)
├── last_transaction.json              # Cached transaction data (generated)
├── grt.png                            # Logo image for the dashboard
├── index.html                         # Generated dashboard (output)
├── .env                               # Environment variables (create from env.example)
├── env.example                        # Template for environment variables
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
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
   cp env.example .env
   ```

2. Edit `.env` and add your actual values:
   ```bash
   CONTRACT_ADDRESS=0x9BED32d2b562043a426376b99d289fE821f5b04E
   ARBISCAN_API_KEY=your_arbiscan_api_key
   QUICK_NODE=your_quicknode_rpc_url
   GRAPH_API_KEY=your_graph_api_key
   USE_CACHED_ENS=N
   ```

The script will automatically load these variables. The first four variables are required for the script to run.

### Running the Script

```bash
python3 generate_dashboard.py
```

This will:
1. **Backup previous run**: Copy `active_indexers.json` to `active_indexers_previous_run.json` (if it exists)
2. **Retrieve active indexers** from The Graph's network subgraph (with self stake > 0)
3. **Fetch contract metadata**:
   - Call `getLastOracleUpdateTime()` to get the latest oracle update timestamp
   - Call `getEligibilityPeriod()` to get the grace period duration (14 days)
4. **Resolve ENS names**:
   - If `USE_CACHED_ENS=Y`: Load ENS names from `ens_resolution.json` cache
   - If `USE_CACHED_ENS=N`: Query ENS subgraph and update `ens_resolution.json` cache
5. **Check eligibility** (Three-Pass Approach):
   - **Pass 1**: Call contract's `isEligible()` function for all indexers
   - **Pass 2**: Call `getEligibilityRenewalTime()` for eligible indexers
   - **Pass 3**: Determine status based on renewal time comparison and grace period:
     - Set status to "eligible", "grace", or "ineligible"
     - Calculate `eligible_until` for grace period indexers
6. **Track status changes**: Compare with previous run to detect status changes
   - If status changed: Set `last_status_change_date` to current date
   - If status unchanged: Keep previous date (or empty if no previous change)
   - If new indexer: Leave date empty
7. Save complete indexer data to `active_indexers.json` (without ENS names)
8. **Render dashboard** showing all indexers with status badges (eligible/grace/ineligible) merged with ENS names from cache
9. Fetch the latest transaction data
10. Generate `index.html` with sorted table and interactive features

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

### The Graph API Key
- **Variable**: `GRAPH_API_KEY`
- **Purpose**: Queries The Graph's network and ENS subgraphs
- **Get yours**: [The Graph Studio](https://thegraph.com/studio/)

### ENS Cache Configuration
- **Variable**: `USE_CACHED_ENS`
- **Values**: `Y` or `N`
- **Purpose**: Controls whether to use cached ENS data or fetch from subgraph
  - **`Y`**: Use cached ENS names from `ens_resolution.json` (faster, saves API calls)
  - **`N`**: Query ENS subgraph and update cache (required for first run or to refresh ENS data)
- **Default**: `N`
- **Note**: On first run or when cache doesn't exist, ENS data will be fetched regardless of this setting

## Data Sources

### Generated: `active_indexers.json`
This file is automatically generated by the script and contains all active indexers with their eligibility data (without ENS names).

Structure:
```json
{
  "metadata": {
    "retrieved": "2025-10-21 08:00:00 UTC",
    "total_count": 99,
    "last_oracle_update_time": 1760956267,
    "eligibility_period": 1209600
  },
  "indexers": [
    {
      "address": "0x0058223c6617cca7ce76fc929ec9724cd43d4542",
      "is_eligible": true,
      "status": "eligible",
      "eligible_until": "",
      "eligible_until_readable": "",
      "eligibility_renewal_time": 1760956267,
      "last_status_change_date": ""
    },
    {
      "address": "0x51637a35f7f054c98ed51904de939b9561d37885",
      "is_eligible": true,
      "status": "grace",
      "eligible_until": 1762111555,
      "eligible_until_readable": "2025-11-02 19:25:55 UTC",
      "eligibility_renewal_time": 1760901955,
      "last_status_change_date": "21/Oct/2025"
    }
  ]
}
```

**Metadata Fields:**
- `retrieved`: Timestamp when the data was fetched
- `total_count`: Total number of active indexers
- `last_oracle_update_time`: Unix timestamp from contract's `getLastOracleUpdateTime()`
- `eligibility_period`: Duration in seconds (14 days = 1209600 seconds) from contract's `getEligibilityPeriod()`

**Indexer Fields:**
- `is_eligible`: Boolean indicating if the indexer returned `true` from contract's `isEligible()`
- `eligibility_renewal_time`: Unix timestamp of eligibility renewal (from contract's `getEligibilityRenewalTime()`)
- `status`: Current eligibility status - one of three values:
  - **"eligible"**: Renewal time matches oracle update time
  - **"grace"**: Within grace period (renewal time + eligibility period > current time)
  - **"ineligible"**: Grace period expired or never eligible
- `eligible_until`: Unix timestamp when grace period expires (only set for "grace" status)
- `eligible_until_readable`: Human-readable expiration date (only set for "grace" status)
- `last_status_change_date`: Date when the status last changed (format: `21/Oct/2025`)
  - **Empty string** (`""`) if status has never changed or for new indexers
  - **Date string** (e.g., `"21/Oct/2025"`) if status changed compared to previous run
  - Tracks status transitions between any states (eligible ↔ grace ↔ ineligible)
- **All indexers are displayed on the dashboard with status badges**

### Generated: `ens_resolution.json`
This file is automatically generated by the script and contains cached ENS name resolutions.

Structure:
```json
{
  "metadata": {
    "retrieved": "2025-10-17 20:00:00 UTC",
    "total_count": 100,
    "ens_resolved": 74
  },
  "ens_resolutions": {
    "0x0058223c6617cca7ce76fc929ec9724cd43d4542": "grassets-tech-2.eth",
    "0x01f17c392614c7ea586e7272ed348efee21b90a3": "oraclegen-indexer.eth",
    "0x0874e792462406dc12ee96b75e52a3bdbba3a123": "posthuman-validator.eth"
  }
}
```

**Key Fields:**
- `ens_resolutions`: Dictionary mapping lowercase addresses to ENS names
- `total_count`: Total number of addresses in the cache
- `ens_resolved`: Number of addresses with resolved ENS names
- **This cache is used during dashboard rendering to merge ENS names with indexer data**

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

### Backup: `active_indexers_previous_run.json`
This file is automatically created as a backup of the previous run's `active_indexers.json`.

**Purpose:**
- Enables status change tracking between script runs
- Contains the exact same structure as `active_indexers.json`
- Automatically created/overwritten before each new run
- Only the most recent previous run is kept (no historical archive)

**Usage in Status Change Detection:**
Each time the script runs, it:
1. Backs up current `active_indexers.json` → `active_indexers_previous_run.json`
2. Generates new `active_indexers.json` with fresh data
3. Compares the new file with the backup to detect status changes
4. Updates `last_status_change_date` in the new file based on comparison

**Example Scenario:**
- **Run 1**: Indexer X has status "eligible" → `last_status_change_date` = `""`
- **Run 2**: Indexer X still has status "eligible" → `last_status_change_date` = `""` (no change)
- **Run 3**: Indexer X changes to status "grace" → `last_status_change_date` = `"21/Oct/2025"` (change detected!)
- **Run 4**: Indexer X still has status "grace" → `last_status_change_date` = `"21/Oct/2025"` (keeps previous date)

## Dashboard Features

### Contract Information Section
**Collapsible debug section** (click header to expand/collapse):
- **Sepolia Contract on Arbitrum**: Contract address with link to Arbiscan
- **Last Oracle Update Time**: Latest oracle update timestamp from the contract
- **Last Transaction ID**: Transaction hash with link to Arbiscan
- **Block Number**: Block where the transaction occurred
- **Eligibility Period**: 14-day grace period duration (1209600 seconds)

### Search and Filter Bar
**Combined search and filter section** (search left-aligned, filters right-aligned):
- **Search Box**: Real-time filtering by indexer address or ENS name
- **Status Filter Buttons**: Click to filter by status (eligible, grace, ineligible)
  - **Active State**: Selected filters invert colors (solid background, dark text)
  - **Toggle Behavior**: Click again to remove filter
  - **Reset Button**: Clears both search and status filter
- **Combined Filtering**: Search and status filters work together

### Indexers Table
- **All Indexers Displayed**: Shows all active indexers (eligible, grace period, and ineligible)
- **Status Badges**: 
  - **eligible** (green): Indexer's renewal time matches oracle update time
  - **grace** (yellow): Indexer is in grace period - eligible until expiration date shown
  - **ineligible** (red): Indexer's grace period has expired or never eligible
- **Eligible Until Column**: Shows grace period expiration date in format: `2-Nov-2025 at 19:25:55 UTC`
- **Smart Sorting**: Automatically sorted by eligibility status first (eligible → grace → ineligible), then alphabetically by ENS name
- **Sortable columns**: Click any header to sort by that column (while maintaining eligibility priority)
- **Statistics**: Shows total indexers and filtered count
- **Color-coded**: ENS names highlighted, missing ENS shown in gray
- **Clickable addresses**: Each indexer address links to their profile on The Graph Explorer

## Technical Details

### Status Determination Logic
The script uses a three-tier status system:

```python
if eligibility_renewal_time == last_oracle_update_time:
    status = "eligible"
elif eligibility_renewal_time != last_oracle_update_time:
    grace_period_end = eligibility_renewal_time + eligibility_period
    if current_time < grace_period_end:
        status = "grace"
        eligible_until = grace_period_end
    else:
        status = "ineligible"
else:
    status = "ineligible"
```

### Timestamp Conversion
All Unix timestamps are converted to UTC format:
```python
datetime.fromtimestamp(timestamp_int, tz=timezone.utc)
    .strftime("%Y-%m-%d %H:%M:%S UTC")
```

### Contract Function Calls
The script calls multiple contract functions using RPC:
```python
# getLastOracleUpdateTime()
function_selector = '0xbe626dd2'

# getEligibilityPeriod()
function_selector = '0xd0a5379e'

# getEligibilityRenewalTime(address)
function_selector = '0xd353402d'
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

