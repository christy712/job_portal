import os
import aiomysql
import asyncio

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "db": os.getenv("DB_NAME", "job_portal"),
}

MIGRATIONS_DIR = "app/migrations"

async def apply_migrations():
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor() as cur:
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                filename VARCHAR(255) UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.commit()

        await cur.execute("SELECT filename FROM schema_migrations")
        applied = {row[0] for row in await cur.fetchall()}

        files = sorted(os.listdir(MIGRATIONS_DIR))
        for file in files:
            if file not in applied and file.endswith(".sql"):
                print(f"Applying {file} ...")
                sql = open(os.path.join(MIGRATIONS_DIR, file)).read()
                await cur.execute(sql)
                await cur.execute("INSERT INTO schema_migrations (filename) VALUES (%s)", (file,))
                await conn.commit()

    conn.close()
    print("All migrations applied!")

if __name__ == "__main__":
    asyncio.run(apply_migrations())
