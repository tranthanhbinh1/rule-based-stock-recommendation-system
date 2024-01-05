import warnings
from scipy.stats import trim_mean
from scipy.optimize import minimize
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from utils.timescale_connector import TimescaleConnector


# Preparing financial ratios data
def financial_ratio():
    _df = TimescaleConnector.query_financial_ratios()

    _columns = [
        "quarter",
        "net_profit",
        "profit_growth_(%)",
        "revenue",
        "revenue_growth_(%)",
        "market_capital",
        "eps_(vnd)",
        "p/e",
        "outstanding_share",
        "roe_(%)",
        "symbol",
    ]

    _df = _df[_columns]

    _trimmed_mean_roe = trim_mean(_df["roe_(%)"].dropna(), 0.1)
    _trimmed_mean_market_capital = trim_mean(_df["market_capital"].dropna(), 0.1)
    _trimmed_mean_eps = trim_mean(_df["eps_(vnd)"].dropna(), 0.1)
    _trimmed_mean_pe = trim_mean(_df["p/e"].dropna(), 0.1)
    _trimmed_mean_outstanding_share = trim_mean(_df["outstanding_share"].dropna(), 0.1)

    _df["roe_(%)"].fillna(_trimmed_mean_roe, inplace=True)
    _df["market_capital"].fillna(_trimmed_mean_market_capital, inplace=True)
    _df["eps_(vnd)"].fillna(_trimmed_mean_eps, inplace=True)
    _df["p/e"].fillna(_trimmed_mean_pe, inplace=True)
    _df["outstanding_share"].fillna(_trimmed_mean_outstanding_share, inplace=True)

    _revenue_null_value = _df[_df["revenue"].isnull()]
    _revenue_null_value.head(5)

    _financial_ratios_cleaned = _df.dropna()
    return _financial_ratios_cleaned


# Rule-based for medium and long-term trading
# Industry sector analysis
df_VNINDEX = pd.read_csv(
    "C:/Users/Admin/OneDrive/Desktop/Personal Items/Stock Recommendation System Project/Dữ liệu Lịch sử VN Index.csv"
)
df_VNINDEX.head()


df_VNINDEX["Ngày"] = pd.to_datetime(df_VNINDEX["Ngày"])


df_sorted = df_VNINDEX.sort_values(by="Ngày")
df_sorted


df_sorted.to_csv(
    "C:/Users/Admin/OneDrive/Desktop/Personal Items/Stock Recommendation System Project/Dữ liệu Lịch sử VN Index.csv"
)


def analyze_industry_sector():
    _df_industry_sector = pd.read_csv(
        "/home/tb24/projects/rule-based-stock-recommendation-system/data/industry_sector_analysis.csv",
        encoding="ISO-8859-1",
    )
    _df_industry_sector = _df_industry_sector.dropna()
    # rename industry sector to industry_sector
    _df_industry_sector.rename(
        columns={"industry sector": "industry_sector"}, inplace=True
    )

    _corrections = {
        "Hóa Ch?t": "Hóa Chất",
        "Hóa ch?t": "Hóa Chất",
        "B?t ??ng s?n": "Bất Động Sản",
        "S?n xu?t th?c ph?m": "Sản xuất thực phẩm",
        "D?ch v? tài chính": "Dịch vụ tài chính",
        "Xây d?ng và v?t li?u": "Xây dựng và vật liệu",
        "B?o hi?m nhân th?": "Bảo hiểm nhân thọ",
        "N??c và khí ??t": "Nước và khí đốt",
        "Ph?n m?m d?ch v? máy tính": "Phần mềm dịch vụ máy tính",
        "Bán l?": "Bán lẻ",
        "Lâm nghi?p và gi?y": "Lâm nghiệp và giấy",
        "Ph?n m?m và d?ch v? máy tính": "Phần mềm và dịch vụ máy tính",
        "S?n xu?t và phân ph?i ?i?n": "Sản xuất và phân phối điện",
        "?i?n t? và thi?t b? ?i?n": "Điện tử và thiết bị điện",
        "V?n t?i": "Vận tải",
        "Kim lo?i": "Kim loại",
        "D??c ph?m": "Dược phẩm",
        "S?n xu?t d??c ph?m": "Sản xuất dược phẩm",
        "S?n xu?t d?u khí": "Sản xuất dầu khí",
        "Hàng cá nhân": "Hàng cá nhân",
        "Thi?t b?, d?ch v? và phân ph?i d?u khí": "Thiết bị, dịch vụ và phân phối dầu khí",
        "Công nghi?p n?ng": "Công nghiệp nặng",
        "Bia và ?? u?ng": "Bia và đồ uống",
        "Thi?t b? và ph?n c?ng": "Thiết bị và phần cứng",
        "Du l?ch và gi?i trí": "Du lịch và giải trí",
        "Ch? s? th? tr??ng chung": "Chỉ số thị trường chung",
    }

    _df_industry_sector.industry_sector = _df_industry_sector.industry_sector.replace(
        _corrections
    )
    _df_industry_sector = _df_industry_sector.reset_index()
    _df_industry_sector = _df_industry_sector.drop(["index"], axis=1)

    _df_industry_sector.date = pd.to_datetime(_df_industry_sector.date)
    _df_industry_sector.close = pd.to_numeric(
        _df_industry_sector.close, errors="coerce"
    )
    _df_industry_sector.dropna(subset=["close"], inplace=True)

    _df_vn_index = _df_industry_sector[_df_industry_sector.symbol == "VN-Index"]
    _df_vn_index["vn_index_change"] = _df_vn_index["close"].pct_change()
    _df_industry_sector["stock_price_change"] = _df_industry_sector.groupby("symbol").close.pct_change()

    _df_merged = _df_industry_sector.merge(
        _df_vn_index[["date", "vn_index_change"]], on="date", how="left"
    )

    _grouped = _df_merged.groupby("industry_sector").agg(
        {"stock_price_change": "mean", "vn_index_change": "mean"}
    )

    _grouped["RS"] = _grouped["stock_price_change"] / _grouped["vn_index_change"]
    _ranked_sectors = _grouped.sort_values(by="RS", ascending=False)
    _ranked_sectors.reset_index(inplace=True)
    _ranked_sectors["ranking"] = _ranked_sectors.reset_index(drop=False).index + 1
    return _ranked_sectors


# ### Fundamental Analysis Conditions
# Prepare fundamental ratios data
def process_dataframe(_df):
    _df["eps_growth(%)"] = (
        (_df["eps_(vnd)"] - _df.groupby("symbol")["eps_(vnd)"].shift(4))
        / _df.groupby("symbol")["eps_(vnd)"].shift(4)
    ) * 100
    _df = _df.dropna()

    _df["profit_growth_(%)"] *= 100
    _df["revenue_growth_(%)"] *= 100

    _df_fundamental = _df[
        [
            "quarter",
            "net_profit",
            "profit_growth_(%)",
            "revenue",
            "revenue_growth_(%)",
            "eps_(vnd)",
            "eps_growth(%)",
            "roe_(%)",
            "symbol",
        ]
    ]
    return _df_fundamental


# The most recent quarter's EPS growth is greater than 15% compared to the same quarter of the previous year
def check_eps_growth_1stcondition(df_fundamental, latest_quarter, growth_threshold):
    # Filter DataFrame for the latest quarter
    latest_quarter_df = df_fundamental[df_fundamental["quarter"] == latest_quarter]
    # Check if the EPS growth is greater than the specified threshold
    latest_quarter_df["condition_met"] = (
        latest_quarter_df["eps_growth(%)"] > growth_threshold
    )
    return latest_quarter_df[["symbol", "eps_growth(%)", "condition_met"]]


result_1st = check_eps_growth_1stcondition(df_fundamental, "Q3 2023", 15)

result_1st.head()


# EPS growth for the two most recent quarters is greater than 15% compared to the same quarters of the previous year
def check_eps_growth_2ndcondition(df_fundamental, recent_quarters, growth_threshold):
    # Filter DataFrame for the recent quarters
    recent_quarter_df = df_fundamental[df_fundamental["quarter"].isin(recent_quarters)]

    # Group by stock symbol and check if EPS growth is greater than the threshold for all recent quarters
    result = recent_quarter_df.groupby("symbol").apply(
        lambda x: (x["eps_growth(%)"] > growth_threshold).all()
    )

    return result


recent_2nd = ["Q3 2023", "Q2 2023"]
result_2nd = check_eps_growth_2ndcondition(df_fundamental, recent_quarters, 15)

result_2nd.head()


# Earnings Per Share (EPS) in each quarter of the last 12 months is at or near its peak
def assess_eps_near_peak_3rdcondition(df_fundamental, year):
    # Filter DataFrame for the specified year
    year_df = df_fundamental[df_fundamental["quarter"].str.contains(year)]

    # Function to check if EPS is at or near peak for each stock
    def is_eps_at_peak(stock_df):
        # Track the maximum EPS value encountered
        max_eps = 0
        for eps in stock_df["eps_(vnd)"]:
            # Define "near peak" criteria (e.g., within 5% of the max)
            near_peak = max_eps * 0.95
            if eps < near_peak:
                return False
            max_eps = max(max_eps, eps)
        return True

    # Group by stock symbol and apply the check
    result = year_df.groupby("symbol").apply(is_eps_at_peak)

    return result


result_3rd = assess_eps_near_peak_3rdcondition(df, "2023")

result_3rd.head()


# Most recent quarter's revenue is greater than 20% compared to the same quarter of the previous year
def check_revenue_growth_4thcondition(df_fundamental, latest_quarter, growth_threshold):
    # Filter DataFrame for the latest quarter
    latest_quarter_df = df_fundamental[df_fundamental["quarter"] == latest_quarter]

    # Check if the revenue growth is greater than the specified threshold
    latest_quarter_df["condition_met"] = (
        latest_quarter_df["revenue_growth_(%)"] > growth_threshold
    )

    # Return the DataFrame with an additional column indicating if the condition is met
    return latest_quarter_df[["symbol", "revenue_growth_(%)", "condition_met"]]


result_4th = check_revenue_growth_4thcondition(df_fundamental, "Q3 2023", 20)

result_4th.head()


# Accelerating revenue growth over the last three quarters
def check_accelerating_revenue_growth_5thcondition(df_fundamental, quarters):
    # Filter DataFrame for the specified quarters
    filtered_df = df_fundamental[df_fundamental["quarter"].isin(quarters)]

    # Function to check if revenue growth is accelerating for each stock
    def is_growth_accelerating(stock_df):
        # Ensure the DataFrame is sorted by quarter
        stock_df = stock_df.sort_values(by="quarter")
        growth_rates = stock_df["revenue_growth_(%)"].tolist()

        # Check if each subsequent growth rate is greater than the previous
        return all(x < y for x, y in zip(growth_rates, growth_rates[1:]))

    # Group by stock symbol and apply the check
    result = filtered_df.groupby("symbol").apply(is_growth_accelerating)

    return result


relevant_quarters = ["Q1 2023", "Q2 2023", "Q3 2023"]
result_5th = check_accelerating_revenue_growth_5thcondition(
    df_fundamental, relevant_quarters
)

result_5th.head()


# Accelerating profit growth over the last three quarters
def check_accelerating_profit_growth_6thcondition(df_fundamental, quarters):
    # Filter DataFrame for the specified quarters
    filtered_df = df_fundamental[df_fundamental["quarter"].isin(quarters)]

    # Function to check if revenue growth is accelerating for each stock
    def is_growth_accelerating(stock_df):
        # Ensure the DataFrame is sorted by quarter
        stock_df = stock_df.sort_values(by="quarter")
        growth_rates = stock_df["profit_growth_(%)"].tolist()

        # Check if each subsequent growth rate is greater than the previous
        return all(x < y for x, y in zip(growth_rates, growth_rates[1:]))

    # Group by stock symbol and apply the check
    result = filtered_df.groupby("symbol").apply(is_growth_accelerating)

    return result


relevant_quarters = ["Q1 2023", "Q2 2023", "Q3 2023"]
result_6th = check_accelerating_profit_growth_6thcondition(
    df_fundamental, relevant_quarters
)

result_6th.head()


def check_roe_7thcondition(df_fundamental, current_quarter, roe_threshold):
    # Filter DataFrame for the current quarter
    current_quarter_df = df_fundamental[df_fundamental["quarter"] == current_quarter]

    # Check if the ROE is at least the specified threshold
    current_quarter_df["condition_met"] = current_quarter_df["roe_(%)"] >= roe_threshold

    # Return the DataFrame with an additional column indicating if the condition is met
    return current_quarter_df[["symbol", "roe_(%)", "condition_met"]]


result_7th = check_roe_7thcondition(df_fundamental, "Q3 2023", 15)

result_7th.head()


# ### Technical Analysis Conditions


df_technical = pd.read_csv(
    "C:/Users/Admin/OneDrive/Desktop/Personal Items/Stock Recommendation System Project/stock_price.csv"
)
df_technical.head()


df_technical["date"] = pd.to_datetime(df_technical["date"])


df_technical.dtypes


# Calculate EMA34-89 for each stock
df_technical["EMA34"] = df_technical.groupby("symbol")["close"].transform(
    lambda x: x.ewm(span=34, adjust=False).mean()
)
df_technical["EMA89"] = df_technical.groupby("symbol")["close"].transform(
    lambda x: x.ewm(span=89, adjust=False).mean()
)
df_technical.head()


# Calculate MA5-20-50-150-200 for each stock
df_technical["MA5"] = df_technical.groupby("symbol")["close"].transform(
    lambda x: x.rolling(window=5).mean()
)
df_technical["MA20"] = df_technical.groupby("symbol")["close"].transform(
    lambda x: x.rolling(window=20).mean()
)
df_technical["MA50"] = df_technical.groupby("symbol")["close"].transform(
    lambda x: x.rolling(window=50).mean()
)
df_technical["MA150"] = df_technical.groupby("symbol")["close"].transform(
    lambda x: x.rolling(window=150).mean()
)
df_technical["MA200"] = df_technical.groupby("symbol")["close"].transform(
    lambda x: x.rolling(window=200).mean()
)
df_technical.head()


df_technical = df_technical.dropna()
df_technical.head()


df_technical.shape


df_technical = df_technical.reset_index()


df_technical = df_technical.drop(["index"], axis=1)


df_technical


def check_emacross_8thcondition(df_technical):
    df_technical["EMA_Condition_Met"] = df_technical["EMA34"] > df_technical["EMA89"]
    condition_met_by_stock = df_technical.groupby("symbol")["EMA_Condition_Met"].any()

    return condition_met_by_stock


result_8th = check_emacross_8thcondition(df_technical)
result_8th.head()


def check_ma_9thcondition(df_technical):
    df_technical["MA_Condition_Met"] = (
        df_technical["MA50"] > df_technical["MA150"]
    ) & (df_technical["MA150"] > df_technical["MA200"])
    condition_met_by_stock = df_technical.groupby("symbol")["MA_Condition_Met"].any()
    return condition_met_by_stock


result_9th = check_ma_9thcondition(df_technical)
result_9th.head()


df_technical.to_csv(
    "C:/Users/Admin/OneDrive/Desktop/Personal Items/Stock Recommendation System Project/stock_price_cleaned.csv"
)


# ### Conditions Evaluation


def evaluate_and_rank_stocks(df_fundamental, df_technical):
    latest_quarter = "Q3 2023"
    recent_two_quarters = ["Q3 2023", "Q2 2023"]
    recent_three_quarters = ["Q3 2023", "Q2 2023", "Q1 2023"]
    year = "2023"

    condition_1 = check_eps_growth_1stcondition(df_fundamental, latest_quarter, 15)[
        "condition_met"
    ]
    condition_2 = check_eps_growth_2ndcondition(df_fundamental, recent_two_quarters, 15)
    condition_3 = assess_eps_near_peak_3rdcondition(df_fundamental, year)
    condition_4 = check_revenue_growth_4thcondition(df_fundamental, latest_quarter, 20)[
        "condition_met"
    ]
    condition_5 = check_accelerating_revenue_growth_5thcondition(
        df_fundamental, recent_three_quarters
    )
    condition_6 = check_accelerating_profit_growth_6thcondition(
        df_fundamental, recent_three_quarters
    )
    condition_7 = check_roe_7thcondition(df_fundamental, latest_quarter, 15)[
        "condition_met"
    ]
    condition_8 = check_emacross_8thcondition(df_technical)
    condition_9 = check_ma_9thcondition(df_technical)

    combined = pd.DataFrame(
        {
            "Condition 1": condition_1,
            "Condition 2": condition_2,
            "Condition 3": condition_3,
            "Condition 4": condition_4,
            "Condition 5": condition_5,
            "Condition 6": condition_6,
            "Condition 7": condition_7,
            "Condition 8": condition_8,
            "Condition 9": condition_9,
        }
    )

    combined["Total Conditions Met"] = combined.sum(axis=1)

    ranked_stocks = combined.sort_values(by="Total Conditions Met", ascending=False)

    return ranked_stocks


ranked_stocks = evaluate_and_rank_stocks(df_fundamental, df_technical)


ranked_stocks["Ranking"] = (
    ranked_stocks["Total Conditions Met"]
    .rank(ascending=False, method="first")
    .astype(int)
)
ranked_stocks.head(10)


ranked_stocks.to_excel(
    "C:/Users/Admin/OneDrive/Desktop/Personal Items/Stock Recommendation System Project/stock_ranking.xlsx",
    index=False,
)


# region Trading bot
# # Trading bot
import pandas as pd
import matplotlib.pyplot as plt

df_tb = pd.read_csv(
    "C:/Users/Admin/OneDrive/Desktop/Personal Items/Stock Recommendation System Project/SSI_price_for_trading_bot.csv"
)
df_tb.head()


df_tb["date"] = pd.to_datetime(df_tb["date"])


df_tb = df_tb.dropna()


df_tb.shape


df_tb.info()


df_tb.to_excel(
    "C:/Users/Admin/OneDrive/Desktop/Personal Items/Stock Recommendation System Project/SSI_price_cleaned.xlsx"
)


df_tb.set_index("date", inplace=True)


df_tb.head()


def trading_strategy(df):
    buy_signals = []
    sell_signals = []

    for i in range(1, len(df)):
        if (
            df["MA5"].iloc[i] > df["MA20"].iloc[i]
            and df["MA5"].iloc[i - 1] < df["MA20"].iloc[i - 1]
        ):
            buy_signals.append(df.index[i])
        elif (
            df["MA5"].iloc[i] < df["MA20"].iloc[i]
            and df["MA5"].iloc[i - 1] > df["MA20"].iloc[i - 1]
        ):
            sell_signals.append(df.index[i])

    return buy_signals, sell_signals


buy_signals, sell_signals = trading_strategy(df_tb)


print("Buy Signals:")
for signal in buy_signals:
    print(signal)

print("\nSell Signals:")
for signal in sell_signals:
    print(signal)

# endregion

# region Modern Porfolio Theory


portfolio_annual_return
# endregion


# #### Calculate annual return of VN-INDEX


import pandas as pd

df_VN_Index_price = pd.read_csv(
    "C:/Users/Admin/OneDrive/Desktop/Personal Items/Stock Recommendation System Project/VN_Index_price_2017_2023.csv"
)


df_VN_Index_price["date"] = pd.to_datetime(df_VN_Index_price["date"])


df_VN_Index_price = df_VN_Index_price.sort_values(by="date")


df_VN_Index_price = df_VN_Index_price.drop(["Unnamed: 0"], axis=1)


df_VN_Index_price["close"] = (
    df_VN_Index_price["close"].str.replace(",", "").astype(float)
)


df_VN_Index_price["year"] = df_VN_Index_price["date"].dt.year

# Calculate the first and last close price for each year
annual_first_close = df_VN_Index_price.groupby("year")["close"].first()
annual_last_close = df_VN_Index_price.groupby("year")["close"].last()

# Calculate the annual return of each year
annual_returns = (annual_last_close / annual_first_close - 1) * 100

# Calculate the average annual return of each year
average_annual_return = annual_returns.mean()

print("VN-Index annual return of each year in period 2017-2023:")
print(annual_returns)
print("\nVN-Index average annual return of each year in period 2017-2023:")
print(average_annual_return)
