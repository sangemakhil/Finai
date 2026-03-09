# session_mem.py
from collections import defaultdict, deque

MAX_TURNS = 8  # keep last N exchanges per session

class SessionMemory:
    def __init__(self):
        self.store = defaultdict(lambda: deque(maxlen=MAX_TURNS))

    def get(self, sid):
        return list(self.store[sid])

    def add(self, sid, role, content):
        self.store[sid].append({"role": role, "content": content})

    def reset(self, sid):
        self.store.pop(sid, None)

SESSION = SessionMemory()
