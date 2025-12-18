# src/system/db_manager.py
import sqlite3
import os

DB_PATH = "assets/database/game_data.db"

class DBManager:
    def __init__(self):
        # フォルダがない場合は作成
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # モブの戦績履歴テーブル
        # generation: 世代 (今は全部1)
        # fitness: 適応度 (生存時間など)
        query = """
        CREATE TABLE IF NOT EXISTS mob_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generation INTEGER,
            biome TEXT,
            speed INTEGER,
            hp INTEGER,
            spawn_time REAL,
            death_time REAL,
            survival_time REAL
        )
        """
        self.cursor.execute(query)
        self.conn.commit()

    def log_mob_death(self, mob, generation=1, biome="grass"):
        """モブが死んだ時にデータを保存する"""
        survival_time = mob.death_time - mob.spawn_time
        
        query = """
        INSERT INTO mob_history (generation, biome, speed, hp, spawn_time, death_time, survival_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(query, (
            generation,
            biome,
            mob.stats["speed"],
            mob.stats["hp"],
            mob.spawn_time,
            mob.death_time,
            survival_time
        ))
        self.conn.commit()
        # デバッグ用: コンソールに生存時間を表示
        print(f"Mob logged: Speed={mob.stats['speed']}, Survived={survival_time:.2f}s")

    def close(self):
        self.conn.close()