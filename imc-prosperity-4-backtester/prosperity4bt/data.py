from collections import defaultdict
from dataclasses import dataclass, field

from prosperity4bt.datamodel import Symbol, Trade
from prosperity4bt.file_reader import FileReader

# Prosperity 4 position limits per product.
# Tutorial round products:
#   EMERALDS: 80, TOMATOES: 80
# Future round products will be added here as they are announced.
# If a product is encountered in the data but not in this dict,
# the backtester will warn and use a default limit of 50.
LIMITS: dict[str, int] = {
    # Tutorial round
    "EMERALDS": 80,
    "TOMATOES": 80,
    # Round 1
    "ASH_COATED_OSMIUM": 80,
    "INTARIAN_PEPPER_ROOT": 80,
}

DEFAULT_POSITION_LIMIT = 50


def get_limit(product: str) -> int:
    """Get position limit for a product, with fallback and warning."""
    if product in LIMITS:
        return LIMITS[product]
    print(f"Warning: No position limit defined for '{product}', using default of {DEFAULT_POSITION_LIMIT}. "
          f"Add it to LIMITS in data.py for accurate backtesting.")
    LIMITS[product] = DEFAULT_POSITION_LIMIT
    return DEFAULT_POSITION_LIMIT


@dataclass
class PriceRow:
    day: int
    timestamp: int
    product: Symbol
    bid_prices: list[int]
    bid_volumes: list[int]
    ask_prices: list[int]
    ask_volumes: list[int]
    mid_price: float
    profit_loss: float


def get_column_values(columns: list[str], indices: list[int]) -> list[int]:
    values = []

    for index in indices:
        value = columns[index]
        if value == "":
            break

        values.append(int(float(value)))

    return values


@dataclass
class ObservationRow:
    """Generic observation row that stores all fields as a dict.

    This avoids hardcoding P3-specific field names and supports
    whatever observation columns future P4 rounds may introduce.
    """
    timestamp: int
    product: str
    fields: dict[str, float] = field(default_factory=dict)

    # Convenience accessors for known conversion observation fields
    @property
    def bidPrice(self) -> float:
        return self.fields.get("bidPrice", 0.0)

    @property
    def askPrice(self) -> float:
        return self.fields.get("askPrice", 0.0)

    @property
    def transportFees(self) -> float:
        return self.fields.get("transportFees", 0.0)

    @property
    def exportTariff(self) -> float:
        return self.fields.get("exportTariff", 0.0)

    @property
    def importTariff(self) -> float:
        return self.fields.get("importTariff", 0.0)

    @property
    def sugarPrice(self) -> float:
        return self.fields.get("sugarPrice", 0.0)

    @property
    def sunlightIndex(self) -> float:
        return self.fields.get("sunlightIndex", 0.0)


@dataclass
class BacktestData:
    round_num: int
    day_num: int

    prices: dict[int, dict[Symbol, PriceRow]]
    trades: dict[int, dict[Symbol, list[Trade]]]
    observations: dict[int, list[ObservationRow]]
    products: list[Symbol]
    profit_loss: dict[Symbol, float]


def create_backtest_data(
    round_num: int, day_num: int, prices: list[PriceRow], trades: list[Trade], observations: list[ObservationRow]
) -> BacktestData:
    prices_by_timestamp: dict[int, dict[Symbol, PriceRow]] = defaultdict(dict)
    for row in prices:
        prices_by_timestamp[row.timestamp][row.product] = row

    trades_by_timestamp: dict[int, dict[Symbol, list[Trade]]] = defaultdict(lambda: defaultdict(list))
    for trade in trades:
        trades_by_timestamp[trade.timestamp][trade.symbol].append(trade)

    products = sorted(set(row.product for row in prices))
    profit_loss = {product: 0.0 for product in products}

    # Group observations by timestamp (multiple products possible per timestamp)
    observations_by_timestamp: dict[int, list[ObservationRow]] = defaultdict(list)
    for obs in observations:
        observations_by_timestamp[obs.timestamp].append(obs)

    return BacktestData(
        round_num=round_num,
        day_num=day_num,
        prices=prices_by_timestamp,
        trades=trades_by_timestamp,
        observations=observations_by_timestamp,
        products=products,
        profit_loss=profit_loss,
    )


def has_day_data(file_reader: FileReader, round_num: int, day_num: int) -> bool:
    with file_reader.file([f"round{round_num}", f"prices_round_{round_num}_day_{day_num}.csv"]) as file:
        return file is not None


def read_day_data(file_reader: FileReader, round_num: int, day_num: int, no_names: bool) -> BacktestData:
    prices = []
    with file_reader.file([f"round{round_num}", f"prices_round_{round_num}_day_{day_num}.csv"]) as file:
        if file is None:
            raise ValueError(f"Prices data is not available for round {round_num} day {day_num}")

        for line in file.read_text(encoding="utf-8").splitlines()[1:]:
            columns = line.split(";")

            prices.append(
                PriceRow(
                    day=int(columns[0]),
                    timestamp=int(columns[1]),
                    product=columns[2],
                    bid_prices=get_column_values(columns, [3, 5, 7]),
                    bid_volumes=get_column_values(columns, [4, 6, 8]),
                    ask_prices=get_column_values(columns, [9, 11, 13]),
                    ask_volumes=get_column_values(columns, [10, 12, 14]),
                    mid_price=float(columns[15]),
                    profit_loss=float(columns[16]),
                )
            )

    trades = []
    with file_reader.file([f"round{round_num}", f"trades_round_{round_num}_day_{day_num}.csv"]) as file:
        if file is not None:
            for line in file.read_text(encoding="utf-8").splitlines()[1:]:
                columns = line.split(";")

                trades.append(
                    Trade(
                        symbol=columns[3],
                        price=int(float(columns[5])),
                        quantity=int(columns[6]),
                        buyer=columns[1],
                        seller=columns[2],
                        timestamp=int(columns[0]),
                    )
                )

    observations = []
    with file_reader.file([f"round{round_num}", f"observations_round_{round_num}_day_{day_num}.csv"]) as file:
        if file is not None:
            lines = file.read_text(encoding="utf-8").splitlines()
            if len(lines) > 1:
                header = lines[0].split(",")

                # Detect if there's a 'product' column in the CSV
                product_col_idx = None
                for i, col_name in enumerate(header):
                    if col_name.strip().lower() == "product":
                        product_col_idx = i
                        break

                for line in lines[1:]:
                    columns = line.split(",")
                    timestamp = int(columns[0])

                    if product_col_idx is not None:
                        # Format with explicit product column
                        product = columns[product_col_idx]
                        field_cols = {}
                        for i in range(1, len(header)):
                            if i != product_col_idx and i < len(columns) and columns[i].strip():
                                try:
                                    field_cols[header[i].strip()] = float(columns[i])
                                except ValueError:
                                    pass
                    else:
                        # Legacy format: no product column, fields start at index 1
                        field_cols = {}
                        for i in range(1, min(len(header), len(columns))):
                            col_name = header[i].strip()
                            if columns[i].strip():
                                try:
                                    field_cols[col_name] = float(columns[i])
                                except ValueError:
                                    pass

                        # Determine which product this observation belongs to
                        product = _detect_observation_product(round_num)

                    observations.append(
                        ObservationRow(
                            timestamp=timestamp,
                            product=product,
                            fields=field_cols,
                        )
                    )

    return create_backtest_data(round_num, day_num, prices, trades, observations)


# Map round numbers to the product that has conversion observations.
# Update this as new rounds with conversions are released.
OBSERVATION_PRODUCTS: dict[int, str] = {
    # Will be populated as rounds are released, e.g.:
    # 3: "SOME_PRODUCT",
}


def _detect_observation_product(round_num: int) -> str:
    """Determine which product conversion observations belong to for a given round."""
    if round_num in OBSERVATION_PRODUCTS:
        return OBSERVATION_PRODUCTS[round_num]
    return "UNKNOWN_OBSERVATION_PRODUCT"
