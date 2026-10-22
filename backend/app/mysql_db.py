"""MySQL connection helper. Credentials are supplied through environment variables."""
import os

from fastapi import HTTPException


def get_mysql_connection():
    """Create a connection when an endpoint needs MySQL."""
    try:
        import mysql.connector

        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv(
                "MYSQL_DATABASE", "legal_citation_analyzer"
            ),
            connection_timeout=5,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="MySQL is unavailable. Check the server and MYSQL_* settings.",
        ) from exc
