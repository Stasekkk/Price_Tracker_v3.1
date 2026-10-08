import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, BigInteger, text, event
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# 1. Read environment variables from .env
load_dotenv()

# 2. Database connection URL (falls back to local SQLite if not provided)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///fallback.db")

# Ensure directory exists if SQLite file path is nested (e.g. data/tracker.db)
if DATABASE_URL.startswith("sqlite:///"):
    db_file = DATABASE_URL.replace("sqlite:///", "")
    if os.path.isdir(db_file):
        # Guard against Docker creating fallback.db as a directory when mounting
        DATABASE_URL = f"sqlite:///{os.path.join(db_file, 'tracker.db')}"
    else:
        db_dir = os.path.dirname(db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

# 3. Create SQLAlchemy engine
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Enable Foreign Key support for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- DATABASE MODELS ---

class Phone(Base):
    __tablename__ = "phones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # Product title
    url = Column(String, unique=True)  # Product URL
    current_price = Column(Integer, nullable=True)  # Latest price
    is_available = Column(Integer, default=1)  # 1 - in stock, 0 - out of stock

    # Relationship with price history (cascades delete on item removal)
    history = relationship("PriceHistory", back_populates="phone", cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    phone_id = Column(Integer, ForeignKey("phones.id"))
    price = Column(Integer)
    check_date = Column(DateTime, default=datetime.now)  # Check timestamp

    phone = relationship("Phone", back_populates="history")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)  # Telegram User ID
    is_admin = Column(Integer, default=0)  # 1 - Admin, 0 - regular viewer
    language = Column(String, default="uk")  # Interface language: 'uk' or 'en'


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    check_time = Column(String, default="07:00")  # Scheduled daily check time (HH:MM)


def get_user_language(telegram_id: int) -> str:
    """Retrieves user interface language from database (default 'uk')"""
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user and user.language:
            return user.language
    return "uk"


def set_user_language(telegram_id: int, language: str) -> str:
    """Sets user interface language ('uk' or 'en')"""
    if language not in ("uk", "en"):
        language = "uk"
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.language = language
        else:
            user = User(telegram_id=telegram_id, is_admin=0, language=language)
            db.add(user)
        db.commit()
    return language


# --- INITIALIZATION FUNCTION ---
def init_db():
    print("⏳ Checking database connection...")
    try:
        # Create tables if they do not exist
        Base.metadata.create_all(bind=engine)

        # Automatically add new columns if database already existed
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE phones ADD COLUMN is_available INTEGER DEFAULT 1"))
                conn.commit()
            except Exception:
                pass

            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN language VARCHAR DEFAULT 'uk'"))
                conn.commit()
            except Exception:
                pass

        print("✅ Database tables successfully verified/initialized!")
    except Exception as e:
        print(f"❌ Database connection error: {e}")


# Run table initialization if executed directly
if __name__ == "__main__":
    init_db()