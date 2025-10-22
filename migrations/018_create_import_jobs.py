#!/usr/bin/env python3
"""
数据库迁移：创建 import_jobs 表并添加必要索引
"""

import sqlite3
import os

def create_import_jobs_table(db_path=None):
    if not db_path:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'inventory.db')

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if not os.path.exists(db_path):
        # 数据库可能尚未初始化，由应用启动时自动创建
        pass

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 创建表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS import_jobs (
                id TEXT PRIMARY KEY,
                uploader_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                progress INTEGER DEFAULT 0,
                total_rows INTEGER DEFAULT 0,
                processed_rows INTEGER DEFAULT 0,
                error_summary TEXT,
                created_at DATETIME DEFAULT (datetime('now')),
                started_at DATETIME,
                finished_at DATETIME,
                FOREIGN KEY (uploader_id) REFERENCES users (id)
            )
            """
        )

        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_jobs_status ON import_jobs (status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_jobs_created_at ON import_jobs (created_at)")

        conn.commit()
        print("✅ import_jobs 表创建完成")
        return True
    except Exception as e:
        print(f"❌ 创建 import_jobs 表失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("🔄 开始创建 import_jobs 表...")
    ok = create_import_jobs_table()
    if ok:
        print("🎉 迁移完成")
    else:
        print("⚠️ 迁移失败")
