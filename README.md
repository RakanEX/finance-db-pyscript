# finance-db-pyscript
 
## Quick Start

1. Download the script
2. Install required packages: `pip install -r requirements.txt`
3. Run the script

## How to Use

Basic usage:
```
python gl_processor.py your_file.csv [options]
```

Flags:

- `-d` or `--directory`: Sets the current directory as the script directory

- `--mode`: Choose "monthly" or "dump" (default is "monthly")
  Example: `python gl_processor.py file.csv --mode dump`

- `--db`: Specify the SQLite database file (default is "finance_db_ex.sqlite")
  Example: `python gl_processor.py file.csv --db my_database.sqlite`

Examples:

Process a monthly file:
```
python gl_processor.py january_report.csv
```

Process a dump file:
```
python gl_processor.py big_dump_file.csv --mode dump
```

Use a custom database name:
```
python gl_processor.py february_report.csv --db feb_data.sqlite
```
