Based on the code changes, here's an updated README:

# finance-db-pyscript

## Quick Start

1. Download the script
2. Install required packages: `pip install -r requirements.txt`
3. Run the script

## How to Use

Basic usage:
```
python3 process_netsuite.py your_file.csv [options]
```

Flags:

- `-d` or `--directory`: Sets the current directory as the script directory

- `--mode`: Choose "monthly-income", "dump-income", "monthly-balance", or "dump-balance" (default is "monthly-income")
  Example: `python process_netsuite.py file.csv --mode dump-income`

- `-v` or `--verbose`: Verbose -- will display logging

- `--scenario`: Specify a scenario (default is "Actual")
  Example: `python process_netsuite.py file.csv --scenario Budget`

Currently only takes in CSV files

## Examples:

Process a monthly income statement file:
```
python3 process_netsuite.py 'new month upload file.csv' --mode monthly-income -v
```

Process a dump income statement file (containing multiple months):
```
python process_netsuite.py 'Income Statement Dump from Netsuite (Holdings).csv' --mode dump-income
```

Process a monthly balance sheet file:
```
python3 process_netsuite.py 'monthly balance sheet.csv' --mode monthly-balance -v
```

Process a dump balance sheet file:
```
python process_netsuite.py 'Balance Sheet Dump.csv' --mode dump-balance
```

## Database Connection

The script now connects to a PostgreSQL database. You will be prompted to enter the database password when running the script.

You must be connected to the tailscale to connect successfully

## Notes

- The script now uses a PostgreSQL database instead of SQLite
- The database table structure has been updated to include new fields like Scenario and Timestamp
- Error handling and logging have been improved for better debugging