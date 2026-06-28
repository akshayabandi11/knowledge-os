import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infrastructure.db.session import Base
from app.core.config import settings


# Engine targeting local test database or standard database URL with a test suffix
# Since tests run on local docker, we execute on the same database but wrap operations in transactions that rollback
@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(settings.DATABASE_URL)
    # Ensure vector extension is present
    with engine.connect() as conn:
        from sqlalchemy import text

        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Spins up a new database session for a test.
    Rolls back any changes at the end of the test to keep database tests isolated.
    """
    connection = db_engine.connect()
    transaction = connection.begin()

    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
