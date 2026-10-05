"""
SQLAlchemy engine + session management.
Every router gets a DB session via the get_db() dependency.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    # pool_pre_ping: checks a connection is still alive before handing it
    # out, transparently reconnecting if not. Without this, a connection
    # that's gone stale (idle timeout from a managed Postgres provider, a
    # load balancer, or just the DB restarting) surfaces as a confusing
    # "SSL connection has been closed unexpectedly" error on whatever
    # request happens to draw it next — exactly the kind of "worked in
    # dev, silently breaks in prod after a while" bug this project should
    # not ship with.
    pool_pre_ping=True,
    # Recycle connections older than 30 min — a second safety net for
    # providers that kill idle connections server-side before Postgres's
    # own (much longer) default timeout would.
    pool_recycle=1800,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
