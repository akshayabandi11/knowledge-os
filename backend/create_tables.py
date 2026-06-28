from app.infrastructure.db.session import Base, engine

print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Done!")
