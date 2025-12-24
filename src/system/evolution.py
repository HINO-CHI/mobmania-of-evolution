# src/system/evolution.py
import random
import config # <--- configを読み込んで、基本ステータスを参照できるようにする

class EvolutionManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_next_generation_stats(self, biome, num_children):
        """
        DBから親を選び、次世代の敵のステータスリストを生成する
        """
        # 1. 選択 (Selection): 上位の親を取得
        parents = self.db.get_top_survivors(biome, limit=10)
        
        # 親がまだいない場合はNoneを返す -> ランダム生成させる
        if not parents:
            return None

        next_gen_stats = []
        
        for _ in range(num_children):
            # 2. 交叉 (Crossover): ランダムに2体の親を選ぶ
            parent_a = random.choice(parents)
            parent_b = random.choice(parents)
            
            # ★修正点: まずランダムな「種族（ボディ）」を選ぶ
            # (これがないと defense_rate や image が空っぽになってエラーになる)
            type_id = random.choice(list(config.MOB_BASE_STATS.keys()))
            base_data = config.MOB_BASE_STATS[type_id]

            # 遺伝するステータス（スピードとHP）を計算
            evolved_speed = (parent_a["speed"] + parent_b["speed"]) // 2
            evolved_hp = (parent_a["hp"] + parent_b["hp"]) // 2

            child_stats = {
                # --- 種族固有のデータ ---
                "type_id": type_id,
                "name": base_data["name"],
                "image": base_data["image"],
                "attack": base_data["attack"],
                "defense_rate": base_data["defense_rate"], # <--- これがエラーの原因でした！
                "attack_type": base_data["attack_type"],

                # --- 進化したデータ (種族値を上書き) ---
                "speed": evolved_speed,
                "hp": evolved_hp,
                "max_hp": evolved_hp # HPバー等のためにmaxも更新
            }

            # 3. 突然変異 (Mutation): 10%の確率
            if random.random() < 0.1:
                # 速度を -10 ~ +10 変化させる
                child_stats["speed"] += random.randint(-10, 10)
                child_stats["speed"] = max(20, child_stats["speed"]) # 下限設定
                
            next_gen_stats.append(child_stats)
            
        print(f"--- Evolution Complete: Generated {len(next_gen_stats)} mobs for {biome} ---")
        return next_gen_stats