from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine

# Tự động định vị tệp .env trong thư mục backend
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

# Kiểm tra xem có thiếu biến môi trường nào không
required_names = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
missing = [name for name in required_names if not os.getenv(name)]
if missing:
    missing_text = ", ".join(missing)
    raise RuntimeError(f"Thieu bien moi truong: {missing_text}")

# Tạo URL kết nối tới PostgreSQL dùng pg8000 (Pure Python - không bị AppLocker chặn)
database_url = URL.create(
    drivername="postgresql+pg8000",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    database=os.environ["DB_NAME"],
)

# Tạo Engine đồng bộ
engine = create_engine(database_url, pool_pre_ping=True)