import os
import pandas as pd
from utils.files_transformer import files_concater


balancesheet_columns_to_process = [
    "Quarter",
    "Ticker",
    "TOTAL ASSETS",
    "CURRENT ASSETS",
    "Cash and cash equivalents",
    "Short-term investments",
    "Accounts receivable",
    "Inventories",
    "Other current assets",
    "LONG-TERM ASSETS",
    "Long-term trade receivables",
    "Fixed assets",
    "Investment properties",
    "Long-term incomplete assets",
    "Long-term investments",
    "Other long-term assets",
    "LIABILITIES",
    "Current liabilities",
    "Long-term liabilities",
    "OWNER'S EQUITY",
    "Capital and reserves",
    "Budget sources and other funds",
    "Bonus and welfare funds (Before 2010)",
    "Minority Interest",
    "TOTAL RESOURCES",
]
incomestatement_columns_to_process = []
cashflow_columns_to_process = []

categories = {
    "BalanceSheet": balancesheet_columns_to_process,
    "IncomeStatement": incomestatement_columns_to_process,
    "CashFlow": cashflow_columns_to_process,
}
directory = "financial_statements/grouped_records/0570"

for category in categories:
    prefix = category

    data = files_concater(directory=directory, prefix=prefix)

    data_processed = data[balancesheet_columns_to_process]
    data_processed.head()
    
    # Get the column names
    cols = pd.Series(data_processed.columns)

    # Find any duplicate column names
    for dup in cols[cols.duplicated()].unique(): 
        cols[cols[cols == dup].index.values.tolist()] = [dup + '_' + str(i) if i != 0 else dup for i in range(sum(cols == dup))]

    # Rename the columns with the new names
    data_processed.columns = cols