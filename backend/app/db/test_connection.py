from app.db.session import engine

with engine.connect() as connection:
  print("DataBase Connected ")