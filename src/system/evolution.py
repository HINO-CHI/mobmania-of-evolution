# src/system/evolution.py
import random
import config

class EvolutionManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_next_generation_stats(self, biome, num_children):
        parents = self.db.get_top_survivors(biome, limit=10)
        
        if not parents:
            return None

        next_gen_stats = []
        
        for _ in range(num_children):
            parent_a = random.choice(parents)
            parent_b = random.choice(parents)
            
            # まずベースとなる種族を選ぶ
            type_id = random.choice(list(config.MOB_BASE_STATS.keys()))
            base_data = config.MOB_BASE_STATS[type_id]

            # 速度とHPの継承（親の平均）
            evolved_speed = (parent_a["speed"] + parent_b["speed"]) // 2
            evolved_hp = (parent_a["hp"] + parent_b["hp"]) // 2

            # 突然変異 (10%の確率)
            if random.random() < 0.1:
                evolved_speed += random.randint(-15, 15)
                # HPも少し変動させてみる
                evolved_hp += random.randint(-5, 5)

            # ★重要: 種族ごとの限界値で速度を制限 (クランプ)
            evolved_speed = max(base_data["min_speed"], min(base_data["max_speed"], evolved_speed))
            
            # HPも1以下にならないように
            evolved_hp = max(1, evolved_hp)

            child_stats = {
                # 種族データ
                "type_id": type_id,
                "name": base_data["name"],
                "image": base_data["image"],
                "size": base_data["size"], # ★サイズを設定
                "attack": base_data["attack"],
                "defense_rate": base_data["defense_rate"],
                "attack_type": base_data["attack_type"],

                # 進化データ
                "speed": evolved_speed,
                "hp": evolved_hp,
                "max_hp": evolved_hp
            }

            next_gen_stats.append(child_stats)
            
        print(f"--- Evolution Complete: Generated {len(next_gen_stats)} mobs for {biome} ---")
        return next_gen_stats