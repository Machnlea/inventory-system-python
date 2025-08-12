#!/usr/bin/env python3
"""
Add equipment attachments table to the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

def main():
    # Get the database URL from the existing database config
    from app.core.config import settings
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Create the table using raw SQL
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS equipment_attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL,
        filename VARCHAR(255) NOT NULL,
        original_filename VARCHAR(255) NOT NULL,
        file_path VARCHAR(500) NOT NULL,
        file_size INTEGER,
        file_type VARCHAR(50),
        mime_type VARCHAR(100),
        description TEXT,
        is_certificate BOOLEAN DEFAULT 0,
        certificate_type VARCHAR(50),
        uploaded_by INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME,
        FOREIGN KEY (equipment_id) REFERENCES equipments (id),
        FOREIGN KEY (uploaded_by) REFERENCES users (id)
    )
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    
    print("Equipment attachments table created successfully")

if __name__ == "__main__":
    main()