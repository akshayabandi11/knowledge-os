from app.infrastructure.db.session import engine, Base
import app.infrastructure.db.base  # Imports all models

print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Done!")
