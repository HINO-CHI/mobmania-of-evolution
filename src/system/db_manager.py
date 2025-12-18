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
    
    def get_top_survivors(self, biome, limit=10):
        """
        指定されたバイオームで、生存時間が長かった上位の個体のステータスを取得する
        """
        query = """
        SELECT speed, hp 
        FROM mob_history 
        WHERE biome = ? 
        ORDER BY survival_time DESC 
        LIMIT ?
        """
        self.cursor.execute(query, (biome, limit))
        rows = self.cursor.fetchall()
        
        # 辞書型のリストに変換して返す
        survivors = []
        for r in rows:
            survivors.append({"speed": r[0], "hp": r[1]})
            
        return survivors

    def close(self):
        self.conn.close()