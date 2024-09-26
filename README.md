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

- `--mode`: Choose "monthly" or "dump" (default is "monthly")
  Example: `python gl_processor.py file.csv --mode dump`

- `--db`: Specify the SQLite database file (default is "finance_db_ex.sqlite")
  Example: `python gl_processor.py file.csv --db my_database.sqlite`

- `-v` or `--verbose`: Verbose -- will display logging



Currently only takes in CSV files



Examples:


Process a monthly file:
```
python3 process_netsuite.py 'new month upload file.csv' --mode monthly -v
```


Process a dump file (containing multiple months):
```
python gl_processor.py 'Income Statement Dump from Netsuite (Holdings).csv' --mode dump
```

