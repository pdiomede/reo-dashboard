#!/usr/bin/env python3
"""
Eligibility Dashboard Generator

This script reads indexer data from indexers.txt and generates a static HTML dashboard
with sortable table and search functionality.
"""

import os
import json
import requests
from datetime import datetime, timezone
from typing import List, Tuple, Optional
from dotenv import load_dotenv

# Version of the dashboard generator
VERSION = "0.0.2"


def get_last_transaction_from_json(json_file: str = 'last_transaction.json') -> Optional[dict]:
    """
    Read the last transaction data from a local JSON file.
    
    Args:
        json_file: Path to the JSON file containing transaction data
        
    Returns:
        Dictionary with transaction data or None if file doesn't exist or is invalid
    """
    try:
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Loaded transaction data from {json_file}")
                return data
        else:
            print(f"{json_file} not found, will try API fallback...")
            return None
    except Exception as e:
        print(f"Error reading {json_file}: {e}")
        return None


def save_transaction_to_json(transaction_data: dict, json_file: str = 'last_transaction.json') -> None:
    """
    Save transaction data to a local JSON file with a timestamp of when the script ran.
    
    Args:
        transaction_data: Dictionary with transaction data
        json_file: Path to the JSON file to save to
    """
    try:
        # Add the script run timestamp
        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        current_readable = datetime.now(timezone.utc).strftime("%b-%d-%Y %H:%M:%S")
        
        # Create the data structure with the script run timestamp
        data_to_save = transaction_data.copy()
        data_to_save['last_script_run'] = current_timestamp
        data_to_save['last_script_run_readable'] = current_readable
        
        # Save to file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2)
        
        print(f"✓ Transaction data saved to {json_file} with timestamp")
    except Exception as e:
        print(f"Error saving to {json_file}: {e}")


def get_last_transaction(contract_address: str, api_key: str) -> Optional[dict]:
    """
    Get the last transaction for a contract from Arbiscan API.
    
    Args:
        contract_address: The contract address to query
        api_key: Arbiscan API key
        
    Returns:
        Dictionary with transaction data or None if error
    """
    try:
        # Try the original Arbiscan API endpoint
        url = "https://api.arbiscan.io/api"
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': contract_address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': 1,  # Get only the latest transaction
            'sort': 'desc',  # Sort by newest first
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == '1' and data['result']:
            return data['result'][0]  # Return the first (latest) transaction
        else:
            # API returned an error or no results
            error_message = data.get('message', 'Unknown error')
            print(f"API Error: {error_message}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Error fetching last transaction: {e}")
        return None


def get_last_transaction_via_quicknode(contract_address: str, quicknode_url: str) -> Optional[dict]:
    """
    Get the last transaction touching the contract using a QuickNode RPC endpoint.
    Strategy: Scan recent blocks and find transactions where 'to' == contract address.
    Skips eth_getLogs entirely as it causes 413 errors on contracts with many events.
    Returns a dict with 'hash', 'blockNumber' (as decimal string), and 'timeStamp' (as decimal string) or None.
    """
    def rpc_call(method: str, params: list) -> Optional[dict]:
        try:
            response = requests.post(
                quicknode_url,
                json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("error"):
                print(f"QuickNode RPC error for {method}: {data['error']}")
                return None
            return data.get("result")
        except Exception as e:
            print(f"QuickNode RPC exception for {method}: {e}")
            return None

    def hex_to_dec_str(hex_str: Optional[str]) -> str:
        try:
            return str(int(hex_str, 16)) if hex_str else "0"
        except Exception:
            return "0"

    try:
        print("Fetching latest block number...")
        latest_hex = rpc_call("eth_blockNumber", [])
        if not latest_hex:
            return None
        latest_int = int(latest_hex, 16)
        print(f"Latest block: {latest_int}")

        # Scan recent blocks for transactions to the contract
        # Start with a reasonable window
        scan_window = 100
        print(f"Scanning last {scan_window} blocks for transactions to {contract_address}...")
        
        for block_num in range(latest_int, max(-1, latest_int - scan_window), -1):
            # Get block with transaction hashes only (not full tx objects)
            block = rpc_call("eth_getBlockByNumber", [hex(block_num), False])
            if not isinstance(block, dict):
                continue
            
            timestamp_hex = block.get("timestamp")
            tx_hashes = block.get("transactions") or []
            
            # Check each transaction in reverse order (most recent first)
            for tx_hash in reversed(tx_hashes):
                tx = rpc_call("eth_getTransactionByHash", [tx_hash])
                if not isinstance(tx, dict):
                    continue
                
                to_addr = (tx.get("to") or "").lower()
                if to_addr and to_addr == contract_address.lower():
                    print(f"Found transaction in block {block_num}: {tx_hash}")
                    return {
                        "hash": tx.get("hash", ""),
                        "blockNumber": hex_to_dec_str(block.get("number")),
                        "timeStamp": hex_to_dec_str(timestamp_hex),
                    }
        
        print(f"No transactions found in last {scan_window} blocks")
        return None
    except Exception as e:
        print(f"Error in get_last_transaction_via_quicknode: {e}")
        return None


def get_oracle_update_time(contract_address: str, quicknode_url: str) -> Optional[int]:
    """
    Get the last oracle update time from the contract by calling getLastOracleUpdateTime().
    
    Args:
        contract_address: The contract address
        quicknode_url: QuickNode RPC endpoint URL
        
    Returns:
        Unix timestamp of last oracle update or None if error
    """
    try:
        # Function selector for getLastOracleUpdateTime()
        # keccak256("getLastOracleUpdateTime()") = 0xbe626dd2...
        function_selector = '0xbe626dd2' + '0' * 56  # Padded to 32 bytes
        
        payload = {
            'jsonrpc': '2.0',
            'method': 'eth_call',
            'params': [{
                'to': contract_address,
                'data': function_selector
            }, 'latest'],
            'id': 1
        }
        
        response = requests.post(quicknode_url, json=payload, timeout=10)
        result = response.json()
        
        if 'result' in result and result['result'] != '0x':
            timestamp = int(result['result'], 16)
            print(f"Oracle update time retrieved: {timestamp}")
            return timestamp
        else:
            error_msg = result.get('error', {}).get('message', 'Unknown error')
            print(f"Error getting oracle update time: {error_msg}")
            return None
    except Exception as e:
        print(f"Exception getting oracle update time: {e}")
        return None


def get_eligibility_period(contract_address: str, quicknode_url: str) -> Optional[int]:
    """
    Get the eligibility period from the contract by calling getEligibilityPeriod().
    
    Args:
        contract_address: The contract address
        quicknode_url: QuickNode RPC endpoint URL
        
    Returns:
        Eligibility period in seconds or None if error
    """
    try:
        # Function selector for getEligibilityPeriod()
        # keccak256("getEligibilityPeriod()") = 0xd0a5379e...
        function_selector = '0xd0a5379e' + '0' * 56  # Padded to 32 bytes
        
        payload = {
            'jsonrpc': '2.0',
            'method': 'eth_call',
            'params': [{
                'to': contract_address,
                'data': function_selector
            }, 'latest'],
            'id': 1
        }
        
        response = requests.post(quicknode_url, json=payload, timeout=10)
        result = response.json()
        
        if 'result' in result and result['result'] != '0x':
            period = int(result['result'], 16)
            print(f"Eligibility period retrieved: {period} seconds")
            return period
        else:
            error_msg = result.get('error', {}).get('message', 'Unknown error')
            print(f"Error getting eligibility period: {error_msg}")
            return None
    except Exception as e:
        print(f"Exception getting eligibility period: {e}")
        return None


def read_indexers_data(filename: str = 'indexers.txt') -> List[Tuple[str, str]]:
    """
    Read indexer data from the text file.
    
    Args:
        filename: Path to the indexers.txt file
        
    Returns:
        List of tuples containing (address, ens_name)
    """
    indexers = []
    
    if not os.path.exists(filename):
        print(f"Error: {filename} not found!")
        return []
    
    with open(filename, 'r', encoding='utf-8') as file:
        for line_num, line in enumerate(file, 1):
            line = line.strip()
            if not line:
                continue
                
            # Split by comma, handle empty ENS names
            parts = line.split(',', 1)
            if len(parts) == 2:
                address, ens_name = parts
                indexers.append((address.strip(), ens_name.strip()))
            else:
                # Handle case where there's no comma (just address)
                indexers.append((line.strip(), ''))
    
    return indexers


def generate_html_dashboard(indexers: List[Tuple[str, str]], contract_address: str, api_key: Optional[str] = None, quicknode_url: Optional[str] = None) -> str:
    """
    Generate the HTML dashboard content.
    
    Args:
        indexers: List of (address, ens_name) tuples
        contract_address: The Sepolia contract address
        api_key: Arbiscan API key
        
    Returns:
        Complete HTML content as string
    """
    current_time = datetime.now(timezone.utc).strftime("%d %b %Y at %H:%M (UTC)")
    
    # Fetch last transaction data
    print("Fetching last transaction data...")
    last_transaction: Optional[dict] = None
    
    # First, try to load from local JSON file
    last_transaction = get_last_transaction_from_json()
    
    # If no local data, try QuickNode if available
    if not last_transaction and quicknode_url:
        last_transaction = get_last_transaction_via_quicknode(contract_address, quicknode_url)
    
    # Final fallback to Arbiscan API
    if not last_transaction:
        last_transaction = get_last_transaction(contract_address, api_key)
    
    # Save transaction data with script run timestamp
    if last_transaction:
        save_transaction_to_json(last_transaction)
    
    # Fetch oracle update time from contract
    print("Fetching oracle update time from contract...")
    oracle_update_time: Optional[int] = None
    if quicknode_url:
        oracle_update_time = get_oracle_update_time(contract_address, quicknode_url)
    
    # Fetch eligibility period from contract
    print("Fetching eligibility period from contract...")
    eligibility_period: Optional[int] = None
    if quicknode_url:
        eligibility_period = get_eligibility_period(contract_address, quicknode_url)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Eligibility Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Poppins', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0C0A1D;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #0C0A1D;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            overflow: hidden;
            border: 1px solid #9CA3AF;
        }}
        
        .header {{
            background: #0C0A1D;
            color: #F8F6FF;
            padding: 30px;
            text-align: center;
            border-bottom: 1px solid #9CA3AF;
        }}
        
        .title-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            margin-bottom: 10px;
        }}
        
        .header-icon {{
            width: 50px;
            height: 50px;
            object-fit: contain;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin: 0;
            font-weight: 300;
        }}
        
        .header .subtitle {{
            font-size: 0.95em;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .search-container {{
            padding: 25px 30px;
            background: #0C0A1D;
            border-bottom: 1px solid #9CA3AF;
        }}
        
        .search-box {{
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #9CA3AF;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: all 0.3s ease;
            background: #0C0A1D;
            color: #F8F6FF;
        }}
        
        .search-box:focus {{
            border-color: #F8F6FF;
            box-shadow: 0 0 0 3px rgba(248, 246, 255, 0.1);
        }}
        
        .search-box::placeholder {{
            color: #9CA3AF;
        }}
        
        .legend {{
            padding: 20px 30px;
            background: #0C0A1D;
            border-bottom: 1px solid #9CA3AF;
        }}
        
        .legend-title {{
            color: #F8F6FF;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        
        .legend-items {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
        }}
        
        .legend-badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 500;
            font-size: 11px;
        }}
        
        .legend-badge.good {{
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
            border: 1px solid #22c55e;
        }}
        
        .legend-badge.grace {{
            background: rgba(251, 191, 36, 0.2);
            color: #fbbf24;
            border: 1px solid #fbbf24;
        }}
        
        .legend-badge.ineligible {{
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            border: 1px solid #ef4444;
        }}
        
        .legend-description {{
            color: #9CA3AF;
        }}
        
        .table-container {{
            padding: 0 30px 30px;
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: #0C0A1D;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            border: 1px solid #9CA3AF;
        }}
        
        th {{
            background: #0C0A1D;
            color: #9CA3AF;
            padding: 20px 15px;
            text-align: left;
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            cursor: pointer;
            user-select: none;
            position: relative;
            border-bottom: 1px solid #9CA3AF;
        }}
        
        th:hover {{
            background: #1a1825;
        }}
        
        th.sortable::after {{
            content: ' ↕';
            opacity: 0.5;
            font-size: 12px;
        }}
        
        th.sort-asc::after {{
            content: ' ↑';
            opacity: 1;
        }}
        
        th.sort-desc::after {{
            content: ' ↓';
            opacity: 1;
        }}
        
        td {{
            padding: 18px 15px;
            border-bottom: 1px solid #9CA3AF;
            font-size: 14px;
            color: #F8F6FF;
        }}
        
        tr:hover {{
            background-color: #1a1825;
        }}
        
        tr:nth-child(even) {{
            background-color: #0C0A1D;
        }}
        
        tr:nth-child(even):hover {{
            background-color: #1a1825;
        }}
        
        .address {{
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #F8F6FF;
            word-break: break-all;
        }}
        
        .address-link {{
            text-decoration: none;
            transition: opacity 0.3s ease;
        }}
        
        .address-link:hover .address {{
            color: #9CA3AF;
        }}
        
        .ens-name {{
            color: #F8F6FF;
            font-weight: 500;
        }}
        
        .empty-ens {{
            color: #9CA3AF;
            font-style: italic;
        }}
        
        .stats {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 30px;
            background: #0C0A1D;
            border-top: 1px solid #9CA3AF;
            font-size: 14px;
            color: #F8F6FF;
        }}
        
        .total-count {{
            font-weight: 600;
            color: #F8F6FF;
        }}
        
        .filtered-count {{
            color: #F8F6FF;
        }}
        
        .contract-info {{
            padding: 25px 30px;
            background: #0C0A1D;
            border-top: 1px solid #9CA3AF;
        }}
        
        .contract-info h3 {{
            color: #F8F6FF;
            font-size: 1.3em;
            margin-bottom: 15px;
            font-weight: 500;
        }}
        
        .info-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #9CA3AF;
        }}
        
        .info-item:last-child {{
            border-bottom: none;
        }}
        
        .info-label {{
            color: #9CA3AF;
            font-weight: 500;
            font-size: 14px;
        }}
        
        .info-value {{
            color: #F8F6FF;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            word-break: break-all;
            text-align: right;
            max-width: 60%;
        }}
        
        .transaction-hash {{
            color: #F8F6FF;
            text-decoration: none;
            font-family: 'Courier New', monospace;
        }}
        
        .transaction-hash:hover {{
            color: #9CA3AF;
            text-decoration: underline;
        }}
        
        .error-message {{
            color: #9CA3AF;
            font-style: italic;
        }}
        
        .footer {{
            padding: 20px 30px;
            background: #0C0A1D;
            border-top: 1px solid #9CA3AF;
            text-align: center;
            color: #9CA3AF;
            font-size: 12px;
            margin-top: 0;
        }}
        
        .footer-content {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
        }}
        
        .version {{
            font-weight: 600;
            color: #9CA3AF;
        }}
        
        .footer-separator {{
            color: #9CA3AF;
        }}
        
        .footer-credits {{
            margin-top: 10px;
            font-size: 12px;
            color: #9CA3AF;
        }}
        
        .footer-credits a {{
            color: #9CA3AF;
            text-decoration: none;
            transition: color 0.3s ease;
        }}
        
        .footer-credits a:hover {{
            color: #F8F6FF;
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                margin: 10px;
                border-radius: 10px;
            }}
            
            .header {{
                padding: 20px;
            }}
            
            .title-container {{
                flex-direction: column;
                gap: 10px;
            }}
            
            .header-icon {{
                width: 40px;
                height: 40px;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .search-container, .table-container {{
                padding: 20px;
            }}
            
            .stats {{
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title-container">
                <img src="grt.png" alt="GRT" class="header-icon">
                <h1>Eligibility Dashboard</h1>
            </div>
            <div class="subtitle">Last Update: {current_time}</div>
        </div>
        
        <div class="search-container">
            <input type="text" 
                   class="search-box" 
                   id="searchInput" 
                   placeholder="Search by indexer address or ENS name..."
                   autocomplete="off">
        </div>
        
        <div class="contract-info">
            <h3>Contract Information (FOR DEBUG ONLY)</h3>
            <div class="info-item">
                <span class="info-label">Sepolia Contract on Arbitrum:</span>
                <span class="info-value"><a href="https://sepolia.arbiscan.io/address/{contract_address}" target="_blank" class="transaction-hash">{contract_address}</a></span>
            </div>"""
    
    # Add last transaction data
    if last_transaction:
        tx_hash = last_transaction.get('hash', 'N/A')
        block_number = last_transaction.get('blockNumber', 'N/A')
        timestamp = last_transaction.get('timeStamp', 'N/A')
        
        # Convert timestamp to readable format
        if timestamp != 'N/A':
            try:
                timestamp_int = int(timestamp)
                readable_time = datetime.fromtimestamp(timestamp_int, tz=timezone.utc).strftime("%d %b %Y at %H:%M (UTC)")
            except:
                readable_time = timestamp
        else:
            readable_time = 'N/A'
        
        html_content += f"""
            <div class="info-item">
                <span class="info-label">Last Transaction ID:</span>
                <span class="info-value"><a href="https://sepolia.arbiscan.io/tx/{tx_hash}" target="_blank" class="transaction-hash">{tx_hash}</a></span>
            </div>
            <div class="info-item">
                <span class="info-label">Block Number:</span>
                <span class="info-value">{block_number}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Transaction Time:</span>
                <span class="info-value">{readable_time}</span>
            </div>"""
    else:
        html_content += """
            <div class="info-item">
                <span class="info-label">Last Transaction ID:</span>
                <span class="info-value"><span class="error-message">Unable to fetch transaction data</span></span>
            </div>"""
    
    # Add oracle update time
    if oracle_update_time:
        try:
            oracle_readable_time = datetime.fromtimestamp(oracle_update_time, tz=timezone.utc).strftime("%d %b %Y at %H:%M:%S (UTC)")
            html_content += f"""
            <div class="info-item">
                <span class="info-label">Last Oracle Update Time:</span>
                <span class="info-value">{oracle_readable_time}</span>
            </div>"""
        except Exception as e:
            print(f"Error formatting oracle update time: {e}")
            html_content += """
            <div class="info-item">
                <span class="info-label">Last Oracle Update Time:</span>
                <span class="info-value"><span class="error-message">Error formatting oracle update time</span></span>
            </div>"""
    else:
        html_content += """
            <div class="info-item">
                <span class="info-label">Last Oracle Update Time:</span>
                <span class="info-value"><span class="error-message">Unable to fetch oracle update time</span></span>
            </div>"""
    
    # Add eligibility period
    if eligibility_period:
        # Convert seconds to days
        days = eligibility_period / 86400
        html_content += f"""
            <div class="info-item">
                <span class="info-label">Eligibility Period:</span>
                <span class="info-value">{eligibility_period} seconds ({days:.1f} days)</span>
            </div>"""
    else:
        html_content += """
            <div class="info-item">
                <span class="info-label">Eligibility Period:</span>
                <span class="info-value"><span class="error-message">Unable to fetch eligibility period</span></span>
            </div>"""
    
    html_content += """
        </div>
        
        <div class="legend">
            <div class="legend-title">Status Legend</div>
            <div class="legend-items">
                <div class="legend-item">
                    <span class="legend-badge good">Good</span>
                    <span class="legend-description">Indexer is eligible</span>
                </div>
                <div class="legend-item">
                    <span class="legend-badge grace">Grace</span>
                    <span class="legend-description">Grace period active</span>
                </div>
                <div class="legend-item">
                    <span class="legend-badge ineligible">Ineligible</span>
                    <span class="legend-description">Not eligible</span>
                </div>
            </div>
        </div>
        
        <div class="table-container">
            <table id="indexersTable">
                <thead>
                    <tr>
                        <th class="sortable" data-column="0">#</th>
                        <th class="sortable" data-column="1">Indexer Address</th>
                        <th class="sortable" data-column="2">ENS Name</th>
                        <th class="sortable" data-column="3">Status</th>
                        <th class="sortable" data-column="4">Eligible Until</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
"""

    # Add table rows
    for i, (address, ens_name) in enumerate(indexers, 1):
        ens_display = ens_name if ens_name else "No ENS"
        ens_class = "ens-name" if ens_name else "empty-ens"
        explorer_url = f"https://thegraph.com/explorer/profile/{address}?view=Indexing&chain=arbitrum-one"
        
        html_content += f"""                    <tr>
                        <td>{i}</td>
                        <td><a href="{explorer_url}" target="_blank" class="address-link"><span class="address">{address}</span></a></td>
                        <td><span class="{ens_class}">{ens_display}</span></td>
                        <td></td>
                        <td></td>
                    </tr>
"""

    html_content += """                </tbody>
            </table>
        </div>
        
        <div class="stats">
            <div class="total-count">Total Indexers: <span id="totalCount">""" + str(len(indexers)) + """</span></div>
            <div class="filtered-count">Showing: <span id="filteredCount">""" + str(len(indexers)) + """</span></div>
        </div>
    </div>

    <script>
        // Table data
        const originalData = [
"""

    # Add JavaScript data
    for i, (address, ens_name) in enumerate(indexers, 1):
        html_content += f"""            [{i}, "{address}", "{ens_name}", "", ""],
"""

    html_content += """        ];
        
        let currentData = [...originalData];
        let sortColumn = -1;
        let sortDirection = 'asc';
        
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const tableBody = document.getElementById('tableBody');
        const totalCount = document.getElementById('totalCount');
        const filteredCount = document.getElementById('filteredCount');
        
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            currentData = originalData.filter(row => 
                row[1].toLowerCase().includes(searchTerm) || 
                row[2].toLowerCase().includes(searchTerm)
            );
            renderTable();
            updateStats();
        });
        
        // Sorting functionality
        function sortTable(column) {
            if (sortColumn === column) {
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                sortColumn = column;
                sortDirection = 'asc';
            }
            
            currentData.sort((a, b) => {
                let aVal = a[column];
                let bVal = b[column];
                
                // Handle numeric sorting for first column
                if (column === 0) {
                    aVal = parseInt(aVal);
                    bVal = parseInt(bVal);
                } else {
                    aVal = aVal.toLowerCase();
                    bVal = bVal.toLowerCase();
                }
                
                if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
                if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
                return 0;
            });
            
            renderTable();
            updateSortHeaders();
        }
        
        function renderTable() {
            tableBody.innerHTML = '';
            currentData.forEach((row, index) => {
                const [num, address, ensName, status, eligibleUntil] = row;
                const ensDisplay = ensName || 'No ENS';
                const ensClass = ensName ? 'ens-name' : 'empty-ens';
                const explorerUrl = `https://thegraph.com/explorer/profile/${address}?view=Indexing&chain=arbitrum-one`;
                
                const rowHTML = `
                    <tr>
                        <td>${num}</td>
                        <td><a href="${explorerUrl}" target="_blank" class="address-link"><span class="address">${address}</span></a></td>
                        <td><span class="${ensClass}">${ensDisplay}</span></td>
                        <td>${status}</td>
                        <td>${eligibleUntil}</td>
                    </tr>
                `;
                tableBody.innerHTML += rowHTML;
            });
        }
        
        function updateSortHeaders() {
            const headers = document.querySelectorAll('th.sortable');
            headers.forEach((header, index) => {
                header.className = 'sortable';
                if (index === sortColumn) {
                    header.classList.add(sortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
                }
            });
        }
        
        function updateStats() {
            totalCount.textContent = originalData.length;
            filteredCount.textContent = currentData.length;
        }
        
        // Add click handlers to sortable headers
        document.querySelectorAll('th.sortable').forEach((header, index) => {
            header.addEventListener('click', () => sortTable(index));
        });
        
        // Initialize
        renderTable();
        updateStats();
    </script>
"""
    
    # Add footer with version and timestamp
    html_content += f"""    
    <div class="footer">
        <div class="footer-content">
            <span class="version">v{VERSION}</span>
            <span class="footer-separator">•</span>
            <span>Last Update: {current_time}</span>
        </div>
        <div class="footer-credits">
            Created with ❤️ by <a href="https://x.com/pdiomede" target="_blank">pdiomede</a> • View repo on GitHub <a href="https://github.com/pdiomede/reo-dashboard" target="_blank">here</a>
        </div>
    </div>
</body>
</html>"""

    return html_content


def main():
    """Main function to generate the dashboard."""
    print("Generating Eligibility Dashboard...")
    
    # Check if .env file exists
    env_file_path = '.env'
    if os.path.exists(env_file_path):
        print(f"✓ Loading environment variables from {env_file_path}")
        load_dotenv()
    else:
        print(f"⚠ Warning: {env_file_path} file not found!")
        print("  Using default/fallback configuration values.")
        print("  To use custom values:")
        print("    1. Copy .env.example to .env")
        print("    2. Edit .env with your API keys")
        print()
    
    # Read indexer data
    indexers = read_indexers_data('indexers.txt')
    
    if not indexers:
        print("No data found or error reading file.")
        return
    
    print(f"Found {len(indexers)} indexers")
    
    # Load environment variables (no hardcoded fallbacks)
    contract_address = os.getenv("CONTRACT_ADDRESS")
    api_key = os.getenv("ARBISCAN_API_KEY")
    quicknode_url = os.getenv("QUICK_NODE")
    
    # Validate required environment variables
    missing_vars = []
    if not contract_address:
        missing_vars.append("CONTRACT_ADDRESS")
    if not api_key:
        missing_vars.append("ARBISCAN_API_KEY")
    if not quicknode_url:
        missing_vars.append("QUICK_NODE")
    
    if missing_vars:
        print("❌ Error: Required environment variables are missing:")
        for var in missing_vars:
            print(f"  - {var}")
        print()
        print("Please set these variables in your .env file.")
        print("See .env.example for the required format.")
        return
    
    print("✓ Configuration loaded successfully")
    print()
    html_content = generate_html_dashboard(indexers, contract_address=contract_address, api_key=api_key, quicknode_url=quicknode_url)
    
    # Write to index.html
    with open('index.html', 'w', encoding='utf-8') as file:
        file.write(html_content)
    
    print("Dashboard generated successfully!")
    print("Open 'index.html' in your browser to view the dashboard.")


if __name__ == "__main__":
    main()
