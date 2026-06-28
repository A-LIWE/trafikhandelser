import aiosqlite
from models import TrafficIncident
from datetime import datetime

DB_PATH = "store.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                header TEXT,
                description TEXT,
                lat REAL,
                lon REAL,
                start_time TEXT,
                county TEXT,
                raw_text TEXT,
                formatted_text TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS device_tokens (
                token TEXT PRIMARY KEY,
                created_at TEXT
            )
        """)
        await db.commit()

async def get_change_id() -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM meta WHERE key = 'changeid'") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "0"

async def save_change_id(change_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('changeid', ?)",
            (change_id,)
        )
        await db.commit()

async def save_incident(incident: TrafficIncident):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO incidents
            (id, header, description, lat, lon, start_time, county, raw_text, formatted_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident.id,
            incident.header,
            incident.description,
            incident.lat,
            incident.lon,
            incident.start_time.isoformat(),
            incident.county,
            incident.raw_text,
            incident.formatted_text
        ))
        await db.commit()

async def save_formatted_text(incident_id: str, formatted_text: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE incidents SET formatted_text = ? WHERE id = ?",
            (formatted_text, incident_id)
        )
        await db.commit()

async def save_device_token(token: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO device_tokens (token, created_at) VALUES (?, ?)",
            (token, datetime.utcnow().isoformat())
        )
        await db.commit()

async def delete_device_token(token: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM device_tokens WHERE token = ?", (token,))
        await db.commit()

async def get_all_device_tokens() -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT token FROM device_tokens") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]