from database import get_database_engine, init_db

if __name__ == "__main__":
    # Локал SQLite датабааз ашиглаж байна (хожим production дээр postgresql://... холбоос руу солиход л хангалттай)
    engine = get_database_engine("sqlite:///gerchain.db")
    init_db(engine)
    print("Database and tables initialized successfully using SQLite abstraction!")
