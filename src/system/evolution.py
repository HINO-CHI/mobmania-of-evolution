# src/system/evolution.py
import random

class EvolutionManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_next_generation_stats(self, biome, num_children):
        """
        DBから親を選び、次世代の敵のステータスリストを生成する
        """
        # 1. 選択 (Selection): 上位50%のエリート親を取得
        parents = self.db.get_top_survivors(biome, limit=10)
        
        # 親がまだいない（初回）場合はNoneを返す -> ランダム生成させる
        if not parents:
            return None

        next_gen_stats = []
        
        for _ in range(num_children):
            # 2. 交叉 (Crossover): ランダムに2体の親を選ぶ
            parent_a = random.choice(parents)
            parent_b = random.choice(parents)
            
            child_stats = {
                # 親Aと親Bの平均値をとる（またはランダム継承）
                "speed": (parent_a["speed"] + parent_b["speed"]) // 2,
                "hp": (parent_a["hp"] + parent_b["hp"]) // 2,
                
                # 色などは固定（または遺伝させることも可能）
                "size": 30,
                "color": (0, 255, 0) # 緑
            }

            # 3. 突然変異 (Mutation): 10%の確率で能力が大きく変化
            if random.random() < 0.1:
                # 速度を -10 ~ +10 変化させる
                child_stats["speed"] += random.randint(-10, 10)
                # 速度が遅くなりすぎないよう制限
                child_stats["speed"] = max(50, child_stats["speed"])
                
                # 変異したら色を少し変える（赤っぽくする）視覚効果
                child_stats["color"] = (50, 200, 0) 

            next_gen_stats.append(child_stats)
            
        print(f"--- Evolution Complete: Generated {len(next_gen_stats)} mobs for {biome} ---")
        return next_gen_stats