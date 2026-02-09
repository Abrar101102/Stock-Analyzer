from app.core.exceptions import ValidationError

def assert_valid_fiscal_year(fiscal_year: int, symbol: str):
    if fiscal_year < 1990 or fiscal_year > 2100:
        raise ValidationError(
        code = "INVALID_PERIOD",
        message = "The FISCAL YEAR SHOULD BE GREATER THAN 1900",
        details = {"received" :f"{fiscal_year} for {symbol}"}
      )
