#!/usr/bin/env python3
"""
Eligibility Dashboard Generator

This script reads indexer data from indexers.txt and generates a static HTML dashboard
with sortable table and search functionality.
"""

import os
from datetime import datetime, timezone
from typing import List, Tuple


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


def generate_html_dashboard(indexers: List[Tuple[str, str]]) -> str:
    """
    Generate the HTML dashboard content.
    
    Args:
        indexers: List of (address, ens_name) tuples
        
    Returns:
        Complete HTML content as string
    """
    current_time = datetime.now(timezone.utc).strftime("%d %b %Y at %H:%M (UTC)")
    
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
            border: 1px solid #494755;
        }}
        
        .header {{
            background: #0C0A1D;
            color: #F8F6FF;
            padding: 30px;
            text-align: center;
            border-bottom: 1px solid #494755;
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
            font-size: 1.1em;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .search-container {{
            padding: 25px 30px;
            background: #0C0A1D;
            border-bottom: 1px solid #494755;
        }}
        
        .search-box {{
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #494755;
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
            color: #494755;
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
            border: 1px solid #494755;
        }}
        
        th {{
            background: #0C0A1D;
            color: #494755;
            padding: 20px 15px;
            text-align: left;
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            cursor: pointer;
            user-select: none;
            position: relative;
            border-bottom: 1px solid #494755;
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
            border-bottom: 1px solid #494755;
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
        
        .ens-name {{
            color: #F8F6FF;
            font-weight: 500;
        }}
        
        .empty-ens {{
            color: #494755;
            font-style: italic;
        }}
        
        .stats {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 30px;
            background: #0C0A1D;
            border-top: 1px solid #494755;
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
            <div class="subtitle">Last Updated: {current_time}</div>
        </div>
        
        <div class="search-container">
            <input type="text" 
                   class="search-box" 
                   id="searchInput" 
                   placeholder="Search by indexer address or ENS name..."
                   autocomplete="off">
        </div>
        
        <div class="table-container">
            <table id="indexersTable">
                <thead>
                    <tr>
                        <th class="sortable" data-column="0">#</th>
                        <th class="sortable" data-column="1">Indexer Address</th>
                        <th class="sortable" data-column="2">ENS Name</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
"""

    # Add table rows
    for i, (address, ens_name) in enumerate(indexers, 1):
        ens_display = ens_name if ens_name else "No ENS"
        ens_class = "ens-name" if ens_name else "empty-ens"
        
        html_content += f"""                    <tr>
                        <td>{i}</td>
                        <td><span class="address">{address}</span></td>
                        <td><span class="{ens_class}">{ens_display}</span></td>
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
        html_content += f"""            [{i}, "{address}", "{ens_name}"],
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
                const [num, address, ensName] = row;
                const ensDisplay = ensName || 'No ENS';
                const ensClass = ensName ? 'ens-name' : 'empty-ens';
                
                const rowHTML = `
                    <tr>
                        <td>${num}</td>
                        <td><span class="address">${address}</span></td>
                        <td><span class="${ensClass}">${ensDisplay}</span></td>
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
</body>
</html>"""

    return html_content


def main():
    """Main function to generate the dashboard."""
    print("Generating Eligibility Dashboard...")
    
    # Read indexer data
    indexers = read_indexers_data('indexers.txt')
    
    if not indexers:
        print("No data found or error reading file.")
        return
    
    print(f"Found {len(indexers)} indexers")
    
    # Generate HTML dashboard
    html_content = generate_html_dashboard(indexers)
    
    # Write to index.html
    with open('index.html', 'w', encoding='utf-8') as file:
        file.write(html_content)
    
    print("Dashboard generated successfully!")
    print("Open 'index.html' in your browser to view the dashboard.")


if __name__ == "__main__":
    main()
