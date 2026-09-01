import math
from typing import List, Dict, Any, Tuple, Optional

class QuantRiskEngine:
    """Institutional Quantitative Risk & Portfolio Analytics Engine."""

    @staticmethod
    def calculate_returns_series(nav_series: List[float]) -> List[float]:
        """Calculates discrete period-over-period percentage returns from a NAV series."""
        if len(nav_series) < 2:
            return []
        returns = []
        for i in range(1, len(nav_series)):
            prev = nav_series[i - 1]
            curr = nav_series[i]
            if prev > 0:
                ret = (curr - prev) / prev
                returns.append(ret)
            else:
                returns.append(0.0)
        return returns

    @classmethod
    def calculate_sharpe_ratio(cls, returns: List[float], risk_free_rate: float = 0.0) -> float:
        """Calculates Annualized/Normalized Sharpe Ratio. Zero-division protected."""
        if len(returns) < 2:
            return 0.0
        
        n = len(returns)
        mean_ret = sum(returns) / n
        excess_mean = mean_ret - risk_free_rate

        variance = sum((r - mean_ret) ** 2 for r in returns) / (n - 1)
        stdev = math.sqrt(variance) if variance > 0 else 0.0

        if stdev <= 1e-6:
            return round(excess_mean * 10.0, 2) if excess_mean > 0 else 0.0

        sharpe = excess_mean / stdev
        return round(float(sharpe), 2)

    @classmethod
    def calculate_sortino_ratio(cls, returns: List[float], target_return: float = 0.0) -> float:
        """Calculates Sortino Ratio penalizing only downside volatility."""
        if len(returns) < 2:
            return 0.0

        n = len(returns)
        mean_ret = sum(returns) / n
        excess_mean = mean_ret - target_return

        downside_diffs = [min(0.0, r - target_return) ** 2 for r in returns]
        downside_variance = sum(downside_diffs) / n
        downside_stdev = math.sqrt(downside_variance) if downside_variance > 0 else 0.0

        if downside_stdev <= 1e-6:
            return round(excess_mean * 10.0, 2) if excess_mean > 0 else 0.0

        sortino = excess_mean / downside_stdev
        return round(float(sortino), 2)

    @staticmethod
    def calculate_max_drawdown(nav_series: List[float]) -> float:
        """Calculates Maximum Drawdown (MDD) as maximum peak-to-trough drop percentage."""
        if not nav_series:
            return 0.0

        peak = nav_series[0]
        max_dd = 0.0

        for val in nav_series:
            if val > peak:
                peak = val
            if peak > 0:
                dd = (peak - val) / peak
                if dd > max_dd:
                    max_dd = dd

        return round(max_dd * 100.0, 2)

    @staticmethod
    def calculate_beta_and_alpha(
        player_returns: List[float],
        benchmark_returns: List[float],
        risk_free_rate: float = 0.0
    ) -> Tuple[float, float]:
        """Calculates Portfolio Beta and Jensen's Alpha against a benchmark return series."""
        n = min(len(player_returns), len(benchmark_returns))
        if n < 3:
            return 1.0, 0.0

        rp = player_returns[-n:]
        rb = benchmark_returns[-n:]

        mean_p = sum(rp) / n
        mean_b = sum(rb) / n

        var_b = sum((b - mean_b) ** 2 for b in rb) / (n - 1)
        if var_b <= 1e-6:
            return 1.0, round((mean_p - mean_b) * 100.0, 2)

        cov_pb = sum((rp[i] - mean_p) * (rb[i] - mean_b) for i in range(n)) / (n - 1)
        beta = cov_pb / var_b

        # Jensen's Alpha = (Rp - Rf) - Beta * (Rb - Rf)
        alpha = (mean_p - risk_free_rate) - beta * (mean_b - risk_free_rate)
        return round(float(beta), 2), round(float(alpha * 100.0), 2)

    @staticmethod
    def calculate_trade_analytics(wagers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates trading performance statistics (Win Rate, Profit Factor, Expectancy)."""
        settled = [w for w in wagers if w.get("status") in ("WON", "LOST")]
        total_trades = len(settled)
        if total_trades == 0:
            return {
                "total_trades": 0,
                "win_rate_pct": 0.0,
                "profit_factor": 0.0,
                "gross_profit": 0.0,
                "gross_loss": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0
            }

        wins = [w for w in settled if w.get("status") == "WON"]
        losses = [w for w in settled if w.get("status") == "LOST"]

        win_count = len(wins)
        loss_count = len(losses)
        win_rate = (win_count / total_trades) * 100.0

        gross_profit = sum(max(0.0, w.get("payout", 0.0) - w.get("stake", 0.0)) for w in wins)
        gross_loss = sum(w.get("stake", 0.0) for w in losses)

        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)
        avg_win = round(gross_profit / win_count, 2) if win_count > 0 else 0.0
        avg_loss = round(gross_loss / loss_count, 2) if loss_count > 0 else 0.0

        return {
            "total_trades": total_trades,
            "win_rate_pct": round(win_rate, 2),
            "profit_factor": profit_factor,
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "avg_win": avg_win,
            "avg_loss": avg_loss
        }

    @classmethod
    def calculate_risk_adjusted_score(cls, twr_pct: float, max_drawdown_pct: float, sharpe: float) -> float:
        """Calculates holistic fund manager score penalizing drawdown and volatility."""
        mdd_factor = max(0.0, 1.0 - (max_drawdown_pct / 100.0))
        sharpe_factor = max(0.2, min(2.5, (sharpe + 1.0) / 2.0))
        score = twr_pct * mdd_factor * sharpe_factor
        return round(float(score), 2)
