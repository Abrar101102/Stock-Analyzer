class FundamentalIngestionService:
  def __init__(self,provider_service,persistance_service):
    
    self.provider_service = provider_service
    self.persistance_service = persistance_service

  def ingest_symbol_year(self,db,symbol,fiscal_year):
    snapshot = self.provider_service.get_fundamental_snapshot(
      symbol=symbol,
      fiscal_year=fiscal_year
    )

    data_dict = snapshot

    filing_date = snapshot.filing_date

    return self.persistance_service.ingest_fundamental_snapshot(
      db=db,
      symbol=symbol,
      fiscal_year=fiscal_year,
      filing_date=filing_date,
      data=data_dict
    )