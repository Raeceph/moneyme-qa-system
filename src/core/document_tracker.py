import sqlite3
import hashlib


class DocumentTracker:
    """Tracks processed documents using an SQLite database."""

    def __init__(self, db_path="processed_documents.db"):
        """Initializes the DocumentTracker with a database connection."""
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        """Creates the documents table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute(
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
        self.conn.commit()

    def get_file_hash(self, file_path):
        """Generates an MD5 hash for the given file."""
        with open(file_path, "rb") as file:
            return hashlib.md5(file.read()).hexdigest()

    def is_document_processed(self, file_path):
        """Checks if a document has already been processed."""
        file_hash = self.get_file_hash(file_path)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE file_hash = ?", (file_hash,))
        return cursor.fetchone() is not None

    def add_document(self, file_path, file_name):
        """Adds a document's details to the database."""
        file_hash = self.get_file_hash(file_path)
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO documents (file_hash, file_path, file_name) VALUES (?, ?, ?)",
            (file_hash, file_path, file_name),
        )
        self.conn.commit()

    def get_all_documents(self):
        """Retrieves the names of all processed documents."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT file_name FROM documents")
        return [row[0] for row in cursor.fetchall()]

    def close(self):
        """Closes the database connection."""
        self.conn.close()
