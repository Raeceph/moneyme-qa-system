import sqlite3
import hashlib
import asyncio
import aiosqlite
import aiofiles


class DocumentTracker:
    """Tracks processed documents using an SQLite database."""

    def __init__(self, db_path="processed_documents.db"):
        """Initializes the DocumentTracker with a database connection."""
        self.db_path = db_path
        # Do not call async methods here

    async def initialize(self):
        """Initializes the DocumentTracker asynchronously."""
        await self.create_table()

    async def create_table(self):
        """Creates the documents table if it doesn't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY,
                    file_hash TEXT UNIQUE,
                    file_path TEXT,
                    file_name TEXT,
                    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.commit()

    async def get_file_hash(self, file_path):
        """Generates an MD5 hash for the given file."""
        async with aiofiles.open(file_path, "rb") as file:
            content = await file.read()
            return hashlib.md5(content).hexdigest()

    async def is_document_processed(self, file_path):
        """Checks if a document has already been processed."""
        file_hash = await self.get_file_hash(file_path)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM documents WHERE file_hash = ?", (file_hash,)
            ) as cursor:
                result = await cursor.fetchone()
                return result is not None

    async def add_document(self, file_path, file_name):
        """Adds a document's details to the database."""
        file_hash = await self.get_file_hash(file_path)

        # Check if the document already exists before trying to insert
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT 1 FROM documents WHERE file_hash = ?", (file_hash,)
            ) as cursor:
                result = await cursor.fetchone()

            if result:
                # Document already exists, handle it (e.g., log or skip)
                logger.info(f"Document already exists in the tracker: {file_name}")
                return  # Skip the insertion to avoid the UNIQUE constraint error

            # Insert the document if it doesn't exist
            await db.execute(
                "INSERT INTO documents (file_hash, file_path, file_name) VALUES (?, ?, ?)",
                (file_hash, file_path, file_name),
            )
            await db.commit()

    async def get_all_documents(self):
        """Retrieves the names of all processed documents."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT file_name FROM documents") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def close(self):
        """Closes the database connection."""
        if hasattr(self, "conn") and self.conn:
            await self.conn.close()

    async def __aenter__(self):
        """Async context manager enter method."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit method."""
        await self.close()
