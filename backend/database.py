from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL =os.getenv("DATABASE_URL")

engine= create_engine(DATABASE_URL)
SessionLocal =sessionmaker(bind =engine)


def get_session():
  """ Use this in FastAPI routes to get a DB session."""

  session= SessionLocal()
  try:
    yield session
  finally: 
    session.close()

def get_schema():

  """ Reads the live schema from PostgreSQL.
    This string gets injected into the LangChain SQL tool in Phase 3
    so the LLM knows exactly what tables and columns exist."""
  
  with engine.connect() as conn:
    result =conn.execute(text(
      """
      SELECT 
          table_name,
          column_name,
          data_type
      FROM information_schema.columns
      WHERE table_schema = 'public'
      ORDER BY table_name , ordinal_position
      """
    ))
    rows= result.fetchall()

  schema = {}
  for table, column, dtype in rows:
        schema.setdefault(table, []).append(f"{column} ({dtype})")

  lines = []
  for table, cols in schema.items():
      lines.append(f"{table}:\n  " + "\n  ".join(cols))

  return "\n\n".join(lines)


if __name__ == "__main__":
    print(get_schema())


