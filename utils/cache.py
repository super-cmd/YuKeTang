# utils/leaf_cache.py
import json
import os

CACHE_DIR = "cache"  # 缓存目录


class LeafCache:
    """通用课件缓存，支持视频、图文及其他类型完成状态"""

    def __init__(self, cookie_file: str):
        os.makedirs(CACHE_DIR, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(cookie_file))[0]
        self.file_path = os.path.join(CACHE_DIR, f"completed_leaf_{base_name}.json")

        # 使用 dict 存储 {leaf_id: True}，便于扩展
        self.completed = {}
        self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.completed = data
            except Exception:
                self.completed = {}

    def save(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.completed, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def is_completed(self, leaf_id):
        return self.completed.get(str(leaf_id), False)

    def mark_completed(self, leaf_id):
        self.completed[str(leaf_id)] = True
        self.save()
