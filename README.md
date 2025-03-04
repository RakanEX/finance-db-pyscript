Based on the code changes, here's an updated README:

# finance-db-pyscript

## Quick Start

1. Download the script
2. Install required packages: `pip install -r requirements.txt`
3. Run the script

## How to Use

Basic usage:
```
python3 process_netsuite.py file1.csv [file2.csv ...] [options]
```

Flags:

- `-d` or `--directory`: Sets the current directory as the script directory

- `--mode`: Choose "monthly-income", "dump-income", "monthly-balance", or "dump-balance" (default is "monthly-income")
  Example: `python process_netsuite.py file1.csv file2.csv --mode dump-income`

- `-v` or `--verbose`: Verbose -- will display logging

- `--scenario`: Specify a scenario (default is "Actual")
  Example: `python process_netsuite.py file1.csv file2.csv --scenario Budget`

- `--mapping-file`: Path to Excel file with entity name mappings (default is "entity_mappings.xlsx")
  Example: `python process_netsuite.py file1.csv --mapping-file custom_mappings.xlsx`

Currently only takes in CSV files

## Entity Mapping

The script uses an Excel file to map entity names. By default, it looks for "entity_mappings.xlsx" in the current directory.

The Excel file should have the following structure:
- Four sheets named: "monthly-income", "dump-income", "monthly-balance", "dump-balance"
- Each sheet should have two columns: "Original" and "Mapped"

To create a default mapping file, run the included script:
```
python create_default_mappings.py
```

## Examples:

Process multiple monthly income statement files:
```
python3 process_netsuite.py 'jan.csv' 'feb.csv' 'mar.csv' --mode monthly-income -v
```

Process multiple dump income statement files:
```
python process_netsuite.py 'Holdings.csv' 'Tech.csv' --mode dump-income
```

Process multiple monthly balance sheet files:
```
python3 process_netsuite.py 'balance_jan.csv' 'balance_feb.csv' --mode monthly-balance -v
```

Process multiple dump balance sheet files:
```
python process_netsuite.py 'Balance_Holdings.csv' 'Balance_Tech.csv' --mode dump-balance
```

## Database Connection

The script now connects to a PostgreSQL database. You will be prompted to enter the database password when running the script.

You must be connected to the tailscale to connect successfully

## Notes

- The script now uses a PostgreSQL database instead of SQLite
- The database table structure has been updated to include new fields like Scenario and Timestamp
- Error handling and logging have been improved for better debugging
- Entity name mapping is now handled through an external Excel file