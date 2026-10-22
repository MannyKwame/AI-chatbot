from database import Base, engine
import models  # Registers Conversation and Message with Base.

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")
