from heapq import heappush, heappop

class FrontierBestFirstWidth():
    
    def __init__(self, heuristic: 'Heuristic'):
        self.heuristic = heuristic
        self.queue = []
        self.set = []
        self.counter = 0
        self.explored = []
    
    def add(self, state: 'State'):
        self.heuristic.get_w(self.explored, state)     
        priority = (self.heuristic.f(state))
        heappush(self.queue, (priority, self.counter, state))
        self.counter += 1
        self.set.append(state)
    
    def pop(self) -> 'State':
        if not self.queue:
            return None
        _, _, state = heappop(self.queue)
        self.set.remove(state)
        return state    
    
    def is_empty(self) -> 'bool':
        return len(self.queue) == 0
    
    def size(self) -> 'int':
        return len(self.queue)
    
    def contains(self, state: 'State') -> 'bool':
        return state in self.set
    
    def get_name(self):
        return 'best-first width search with custom priority'.format(self.heuristic)