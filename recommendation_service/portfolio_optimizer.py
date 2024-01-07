import pandas as pd
import numpy as np
import logging
from functools import lru_cache
from scipy.optimize import minimize
from utils.timescale_connector import TimescaleConnector
from config.logging_config import setup_logging
from recommendation_service.stock_recommender import StockRecommender

setup_logging()


class PortfolioOptimizer:
    def __init__(self, portfolio_size: int, risk_free_rate: float, upper_bound: float):
        self.stock_recommender = StockRecommender(
            latest_year="2023",
            latest_quarter="Q3 2023",
            recent_2_quarters=["Q3 2023", "Q2 2023"],
            recent_3_quarters=["Q1 2023", "Q2 2023", "Q3 2023"],
            growth_threshold_eps=15,
            growth_threshold_revenue=20,
            growth_threshold_roe=15,
        )
        self.portfolio_size = portfolio_size
        self.risk_free_rate = risk_free_rate
        self.upper_bound = upper_bound
        self.top_stocks: list = []

    @lru_cache(maxsize=2)  # 3 and 5 best stocks
    def get_top_stocks(self):
        recommended_stock = self.stock_recommender.get_recommendation()
        self.top_stocks = recommended_stock.head(self.portfolio_size).index.tolist()

    def query_stock_prices(self):
        for symbol in self.top_stocks:
            df = TimescaleConnector.query_ohlcv_daily(symbol)
            df = df.close
            df.columns = [symbol]
            if symbol == self.top_stocks[0]:
                self.top_stocks_df = df
            else:
                self.top_stocks_df = pd.concat([self.top_stocks_df, df], axis=1)

    def calculate_log_returns(self):
        self.top_stocks_df = self.top_stocks_df.astype(float)
        self.log_returns = np.log(
            self.top_stocks_df / self.top_stocks_df.shift(1)
        ).dropna()

    def calculate_covariance_matrix(self):
        self.cov_matrix_annual = self.log_returns.cov() * 252

    def standard_deviation(self, weights):
        variance = weights.T @ self.cov_matrix_annual @ weights
        return np.sqrt(variance)

    def expected_return(self, weights):
        return np.sum(self.log_returns.mean() * weights) * 252

    def sharpe_ratio(self, weights, risk_free_rate):
        return (
            self.expected_return(weights) - risk_free_rate
        ) / self.standard_deviation(weights)

    def optimize_portfolio(self):
        constraints = {"type": "eq", "fun": lambda weights: np.sum(weights) - 1}
        bounds = [(0, self.upper_bound) for _ in range(len(self.top_stocks))]
        initial_weights = np.array([1 / len(self.top_stocks)] * len(self.top_stocks))
        optimized_results = minimize(
            self.sharpe_ratio,
            initial_weights,
            args=(self.risk_free_rate,),
            method="SLSQP",
            constraints=constraints,
            bounds=bounds,
        )
        self.optimal_weights = optimized_results.x

    def optimal_portfolio(self):
        optimal_portfolio_return = self.expected_return(self.optimal_weights)
        optimal_portfolio_volatility = self.standard_deviation(self.optimal_weights)
        optimal_sharpe_ratio = self.sharpe_ratio(
            self.optimal_weights, risk_free_rate=0.02
        )

        logging.info("Optimal Weights:")
        for ticker, weight in zip(self.top_stocks, self.optimal_weights):
            logging.info(f"{ticker}: {weight:.4f}")

        logging.info(f"Expected Annual Return: {optimal_portfolio_return:.4f}")
        logging.info(f"Expected Volatility: {optimal_portfolio_volatility:.4f}")
        logging.info(f"Sharpe Ratio: {optimal_sharpe_ratio:.4f}")


if __name__ == "__main__":
    optimizer = PortfolioOptimizer(
        portfolio_size=3, risk_free_rate=0.02, upper_bound=0.5
    )
    optimizer.get_top_stocks()
    optimizer.query_stock_prices()
    optimizer.calculate_log_returns()
    optimizer.calculate_covariance_matrix()
    optimizer.optimize_portfolio()
    optimizer.optimal_portfolio()
