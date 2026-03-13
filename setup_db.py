from database import engine, Base
from config import get_settings
from models import ShortStory, Chapter, ChildrenStory

settings = get_settings()


# run once to initialize empty dev datatable
def setup_db():
    if settings.use_supabase:
        print("Tables in metadata:", Base.metadata.tables.keys())
        Base.metadata.create_all(engine)
        print("Connecting to:", settings.database_url)
        print("Tables created.")
    else:
        print("You are not using supabase. Tables will not be created.")


if __name__ == "__main__":
    setup_db()
