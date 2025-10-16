import aiomysql
from app.config import settings

async def get_db():
    conn = await aiomysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASS,
        db=settings.DB_NAME,
        autocommit=True
    )
    return conn
