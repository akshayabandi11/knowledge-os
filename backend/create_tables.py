from app.infrastructure.db.session import Base, engine

import app.infrastructure.db.models

print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Done!")