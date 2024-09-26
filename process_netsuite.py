import pandas as pd
import sqlite3
from datetime import datetime
from calendar import monthrange
import argparse
import os
import sys
import logging


def setup_logging(verbose):
    if verbose:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
    else:
        logging.basicConfig(
            level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
        )
    return logging.getLogger(__name__)


def fill_type_column(df, logger):
    logger.info("Starting to fill type column")
    current_type = None
    type_column = []

    for _, row in df.iterrows():
        if pd.isna(row.iloc[1:]).all() and not pd.isna(row.iloc[0]):
            current_type = row.iloc[0]
            type_column.append(pd.NA)
        else:
            type_column.append(current_type)

    logger.info("Finished filling type column")
    return type_column


def date_format(date_str, logger):
    try:
        date_obj = datetime.strptime(date_str, "%b-%y")
        _, last_day = monthrange(date_obj.year, date_obj.month)
        last_date = date_obj.replace(day=last_day)
        return last_date.strftime("%Y-%m-%d")
    except ValueError:
        logger.error(
            f"Invalid date format in the file. Expected 'Mon-YY', got '{date_str}'"
        )
        sys.exit(1)


def process_file_monthly(file_path, logger):
    logger.info(f"Processing monthly file: {file_path}")
    try:
        # Gets date
        df = pd.read_csv(file_path, nrows=3)
        date = date_format(df.iloc[2, 0], logger)
        logger.info(f"Extracted date: {date}")

        df = pd.read_csv(file_path, skiprows=6)
        logger.info("CSV file loaded successfully")

        # fixes netsuite introduced white space
        df.columns = df.columns.str.strip()

        df = df.drop(0)
        df.drop("Total", axis=1, inplace=True)

        df["Type"] = fill_type_column(df, logger)
        df = df.dropna(subset=df.columns[1:], how="all")
        df = df.reset_index(drop=True)

        df = df.melt(
            id_vars=["Financial Row", "Type"], var_name=["Branch"], value_name="Value"
        )

        df["Value"] = df["Value"].str.strip()
        df = df[df["Value"] != "$0.00"]

        df["GL_Number"] = df["Financial Row"].apply(
            lambda x: int(x[0:5]) if x[0:5].isnumeric() else 0
        )
        df = df[df["GL_Number"] != 0]

        df["Description"] = df["Financial Row"].apply(lambda x: str(x[8:]).strip())

        df.drop("Financial Row", axis=1, inplace=True)
        df["Date"] = date

        df = df[["GL_Number", "Description", "Branch", "Type", "Date", "Value"]]
        logger.info("File processing completed successfully")
        return df
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        sys.exit(1)


def process_file_dump(filename, logger):
    logger.info(f"Processing dump file: {filename}")
    df = pd.read_csv(filename, header=None)
    branch = df.loc[0, 0]
    logger.info(f"Extracted branch: {branch}")

    df = pd.read_csv(filename, skiprows=6)
    logger.info("CSV file loaded successfully")

    df.columns = df.columns.str.strip()
    df.drop(0, inplace=True)
    df.drop("Total", axis=1, inplace=True)

    df["Type"] = fill_type_column(df, logger)
    df = df.dropna(subset=df.columns[1:], how="all")
    df = df.reset_index(drop=True)

    df = df.melt(
        id_vars=["Financial Row", "Type"], var_name=["Date"], value_name="Value"
    )
    df["Date"] = df["Date"].apply(lambda x: date_format(x, logger))

    df["Value"] = df["Value"].str.strip()
    df = df[df["Value"] != "$0.00"]

    df["GL_Number"] = df["Financial Row"].apply(
        lambda x: int(x[0:5]) if x[0:5].isnumeric() else 0
    )
    df = df[df["GL_Number"] != 0]

    df["Description"] = df["Financial Row"].apply(lambda x: str(x[8:]).strip())

    df.drop("Financial Row", axis=1, inplace=True)

    df["Branch"] = branch
    df = df[["GL_Number", "Branch", "Description", "Type", "Date", "Value"]]
    df = df.reset_index(drop=True)
    logger.info("File processing completed successfully")
    return df


def insert_into_db(df, db_path, logger):
    logger.info(f"Inserting data into database: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS GL_Table (
            GL_Number INTEGER,
            Description TEXT,
            Branch TEXT,
            Type TEXT,
            Date TEXT,
            Value TEXT,
            UNIQUE(GL_Number, Date, Branch, Value)
        )
        """)
        logger.info("Table created or already exists")

        data_to_insert = df.to_dict("records")

        cursor.executemany(
            """
        INSERT OR IGNORE INTO GL_Table 
        (GL_Number, Description, Branch, Type, Date, Value)
        VALUES (:GL_Number, :Description, :Branch, :Type, :Date, :Value)
        """,
            data_to_insert,
        )

        inserted_rows = cursor.rowcount
        conn.commit()
        logger.info(f"{inserted_rows} new records inserted into {db_path}")

    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
    except Exception as e:
        logger.error(f"Error inserting data into database: {e}")
    finally:
        if conn:
            conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Process GL file and insert into SQLite database."
    )
    parser.add_argument("filename", help="Name of the CSV file to process")
    parser.add_argument(
        "-d",
        "--directory",
        help="set the current directory as the script directory",
        action="store_true",
    )
    parser.add_argument(
        "--mode",
        choices=["monthly", "dump"],
        default="monthly",
        help="Processing mode: 'monthly' or 'dump'",
    )
    parser.add_argument(
        "--db", help="Path to the SQLite database file", default="finance_db_ex.sqlite"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()
    logger = setup_logging(args.verbose)
    logger.info(f"Arguments parsed: {args}")

    if args.directory:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        logger.info(f"Changed working directory to: {os.getcwd()}")

    file_path = os.path.join(os.getcwd(), args.filename)

    if not os.path.exists(file_path):
        logger.error(f"File '{file_path}' not found.")
        sys.exit(1)

    if args.mode == "monthly":
        logger.info("Processing in monthly mode")
        df = process_file_monthly(file_path, logger)
    else:  # args.mode == 'dump'
        logger.info("Processing in dump mode")
        df = process_file_dump(file_path, logger)

    insert_into_db(df, args.db, logger)
    logger.info("Script execution completed successfully")


if __name__ == "__main__":
    main()
