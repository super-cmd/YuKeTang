# utils/video_cache.py
import json
import os

CACHE_DIR = "cache"  # 新建缓存目录


class VideoCache:
    def __init__(self, cookie_file: str):
        # 确保缓存目录存在
        os.makedirs(CACHE_DIR, exist_ok=True)

        # 取 cookie 文件名，不带路径和扩展名
        base_name = os.path.splitext(os.path.basename(cookie_file))[0]
        self.file_path = os.path.join(CACHE_DIR, f"completed_videos_{base_name}.json")

        self.completed_videos = set()
        self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.completed_videos = set(data)
            except Exception:
                self.completed_videos = set()

    def save(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(list(self.completed_videos), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def is_completed(self, leaf_id):
        return leaf_id in self.completed_videos

    def mark_completed(self, leaf_id):
        self.completed_videos.add(leaf_id)
        self.save()
