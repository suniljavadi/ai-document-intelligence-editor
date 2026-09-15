from app.core.db import Base, engine
import app.models

Base.metadata.create_all(bind=engine)
print("Database schema initialized")