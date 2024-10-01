import pandas as pd
from datetime import datetime
from calendar import monthrange
import argparse
import os
import sys
import logging
import psycopg2
from psycopg2 import sql
import getpass
import re

thost = "10.205.240.3"
tdatabase = "postgres"
tuser = "postgres"
tport = 5432


def extract_bracketed_word(text: str):
    pattern = r"\((.*?)\)"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return str(text.strip().split(" ")[-1])


def balance_date_strip(date_string: str):
    date_object = datetime.strptime(date_string.strip(), "As of %b %Y")
    _, last_day = monthrange(date_object.year, date_object.month)
    last_date = date_object.replace(day=last_day)
    return last_date.strftime("%Y-%m-%d")


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
        date_obj = datetime.strptime(date_str, "%b %Y")
        _, last_day = monthrange(date_obj.year, date_obj.month)
        last_date = date_obj.replace(day=last_day)
        return last_date.strftime("%Y-%m-%d")
    except ValueError:
        logger.error(
            f"Invalid date format in the file. Expected 'Mon YYYY', got '{date_str}'"
        )
        sys.exit(1)


def process_income_monthly(file_path, logger, scenario):
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
        df.rename(columns={"Total": "Consol"}, inplace=True)

        df.rename(columns={"ElectronX": "Holdings"}, inplace=True)

        df["Type"] = fill_type_column(df, logger)
        df = df.dropna(subset=df.columns[1:], how="all")
        df = df.reset_index(drop=True)

        df = df.melt(
            id_vars=["Financial Row", "Type"], var_name=["Entity"], value_name="Value"
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
        df["Scenario"] = scenario
        df["Timestamp"] = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")

        df = df[
            [
                "GL_Number",
                "Description",
                "Entity",
                "Type",
                "Date",
                "Value",
                "Scenario",
                "Timestamp",
            ]
        ]
        logger.info("File processing completed successfully")
        return df
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        sys.exit(1)


def process_income_dump(filename, logger, scenario):
    logger.info(f"Processing dump file: {filename}")
    df = pd.read_csv(filename,header=None,nrows=2)
    Entity = df.iloc[1, 0].split(" ")[-1]
    if Entity == "Co":
        Entity = "Tech"
    logger.info(f"Extracted Entity: {Entity}")

    df = pd.read_csv(filename, skiprows=6)
    logger.info("CSV file loaded successfully")

    df.columns = df.columns.str.strip()
    df.drop(0, inplace=True)
    # df.drop("Total", axis=1, inplace=True)
    df.drop("Total", axis=1, inplace=True)
    # df.rename(columns={"Total": "Consol"}, inplace=True)

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

    df["Entity"] = Entity

    df.loc[df["Entity"] == "ElectronX", "Entity"] = "Holdings"
    df["Scenario"] = scenario
    df["Timestamp"] = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
    df = df.reset_index(drop=True)
    df = df[
        [
            "GL_Number",
            "Description",
            "Entity",
            "Type",
            "Date",
            "Value",
            "Scenario",
            "Timestamp",
        ]
    ]
    logger.info("File processing completed successfully")
    return df


def process_balance_monthly(filename, logger, scenario):
    df = pd.read_csv(filename, nrows=4, header=None)
    # entity = extract_bracketed_word(df.iloc[1, 0])

    date_object = datetime.strptime(
        " ".join(str(df.iloc[3, 0]).split(" ")[-2:]), "%b %Y"
    )
    _, last_day = monthrange(date_object.year, date_object.month)
    last_date = date_object.replace(day=last_day)
    date = last_date.strftime("%Y-%m-%d")
    date

    df = pd.read_csv(filename, skiprows=6)
    df.columns = df.columns.str.strip()

    df.rename(
        columns={"xElimination": "Elim", "ElectronX": "Holdings", "Total": "Consol"},
        inplace=True,
    )
    df["Type"] = fill_type_column(df, logger)
    df["Type"] = fill_type_column(df, logger)
    df = df.dropna(subset=df.columns[1:], how="all")
    df = df.reset_index(drop=True)

    df = df.melt(
        id_vars=["Financial Row", "Type"], var_name=["Entity"], value_name="Value"
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
    df["Scenario"] = scenario
    df["Timestamp"] = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")

    df = df[
        [
            "GL_Number",
            "Description",
            "Entity",
            "Type",
            "Date",
            "Value",
            "Scenario",
            "Timestamp",
        ]
    ]
    logger.info("File processing completed successfully")
    return df


def insert_into_db(df, db_config, logger):
    logger.info("Inserting data into database: finance-db-netsuite")
    conn = None

    tpassword = os.environ.get('FINANCE_DB_PASS')
    if tpassword is None:
        tpassword = getpass.getpass("Enter Database Password: ")
    
    try:
        conn = psycopg2.connect(
            host=thost,
            database=tdatabase,
            user=tuser,
            password=tpassword,
            port=tport,
        )

        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Accounting_table (
            GL_Number INTEGER,
            Description TEXT,
            Entity TEXT,
            Type TEXT,
            Date TEXT,
            Value TEXT,
            Scenario TEXT,
            Timestamp TEXT,
            UNIQUE(GL_Number, Date, Entity, Value)
        )
        """)
        logger.info("Table created or already exists")

        data_to_insert = df.to_dict("records")

        insert_query = sql.SQL("""
        INSERT INTO Accounting_table 
        (GL_Number, Description, Entity, Type, Date, Value, Scenario, Timestamp)
        VALUES (%(GL_Number)s, %(Description)s, %(Entity)s, %(Type)s, %(Date)s, %(Value)s, %(Scenario)s, %(Timestamp)s)
        ON CONFLICT (GL_Number, Date, Entity, Value) 
        DO UPDATE SET 
            Description = EXCLUDED.Description,
            Type = EXCLUDED.Type,
            Scenario = EXCLUDED.Scenario,
            Timestamp = EXCLUDED.Timestamp
        """)

        cursor.executemany(insert_query, data_to_insert)

        inserted_rows = cursor.rowcount
        conn.commit()
        logger.info(f"{inserted_rows} new records inserted into finance-db-netsuite")

    except psycopg2.Error as e:
        logger.error(f"PostgreSQL error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inserting data into database: {e}")
        raise
    finally:
        if conn:
            conn.close()


def process_balance_dump(filename, logger, scenario):
    with open(filename, "r") as f:
        max_columns = max(len(line.split(",")) for line in f)

    # Generate column names
    columns = [f"col_{i}" for i in range(max_columns)]

    # Read the CSV with the maximum number of columns
    df = pd.read_csv(
        filename,
        header=None,  # No header
        names=columns,  # Use our generated column names
        na_values=[""],  # Empty fields are NaN
        keep_default_na=True,
        on_bad_lines="skip",
    )  # Skip lines that can't be parsed

    entity = extract_bracketed_word(df.iloc[1, 0])

    df = pd.read_csv(filename, skiprows=7)
    df.columns = df.columns.str.strip()
    df.drop(0, inplace=True)
    df["Type"] = fill_type_column(df, logger)
    df = df.dropna(subset=df.columns[1:], how="all")
    df = df.reset_index(drop=True)
    df = df.rename(columns={df.columns[0]: "Financial Row"})

    df = df.melt(
        id_vars=["Financial Row", "Type"], var_name=["Date"], value_name="Value"
    )

    df["Entity"] = entity
    df["Date"] = df["Date"].apply(balance_date_strip)
    df["Value"] = df["Value"].str.strip()
    df = df[df["Value"] != "$0.00"]

    df["GL_Number"] = df["Financial Row"].apply(
        lambda x: int(x[0:5]) if x[0:5].isnumeric() else 0
    )

    df = df[df["GL_Number"] != 0]

    df["Description"] = df["Financial Row"].apply(lambda x: str(x[8:]).strip())

    df.drop("Financial Row", axis=1, inplace=True)

    df["Entity"] = entity

    df.loc[df["Entity"] == "ElectronX", "Entity"] = "Holdings"
    df["Scenario"] = scenario
    df["Timestamp"] = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
    df = df.reset_index(drop=True)
    df = df[
        [
            "GL_Number",
            "Description",
            "Entity",
            "Type",
            "Date",
            "Value",
            "Scenario",
            "Timestamp",
        ]
    ]
    logger.info("File processing completed successfully")

    return df


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
        choices=["monthly-income", "dump-income", "dump-balance", "monthly-balance"],
        default="monthly-income",
        help="Processing mode: 'monthly-income', 'dump-income', 'dump-balance or 'monthly-balance",
    )
    parser.add_argument(
        "--db", help="Path to the SQLite database file", default="finance_db_ex.sqlite"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument("--scenario", help="Specify a scenario", default="Actual")

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

    if args.mode == "monthly-income":
        logger.info("Processing in monthly mode")
        df = process_income_monthly(file_path, logger, args.scenario)
    elif args.mode == "dump-income":
        logger.info("Processing in dump mode")
        df = process_income_dump(file_path, logger, args.scenario)
    elif args.mode == "dump-balance":
        df = process_balance_dump(file_path, logger, args.scenario)
    elif args.mode == "monthly-balance":
        df = process_balance_monthly(file_path, logger, args.scenario)

    insert_into_db(df, args.db, logger)
    logger.info("Script execution completed successfully")


if __name__ == "__main__":
    main()
