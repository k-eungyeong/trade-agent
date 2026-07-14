"""
SQLite 데이터베이스 연결 설정
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./data/trade_agent.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 의존성 주입용 - 요청마다 DB 세션을 열고, 끝나면 자동으로 닫음"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()