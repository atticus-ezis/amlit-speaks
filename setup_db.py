from database import engine, Base
from config import get_settings

settings = get_settings()

# run once to initialize empty dev datatable
if settings.development_mode:
    Base.metadata.create_all(engine)
    print("Tables created.")
else:
    print("You are in production mode. Tables will not be created.")
