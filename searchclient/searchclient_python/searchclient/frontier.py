from abc import ABCMeta, abstractmethod
from collections import deque
from heapq import heappush, heappop

class Frontier(metaclass=ABCMeta):
    @abstractmethod
    def add(self, state: 'State'): raise NotImplementedError
    
    @abstractmethod
    def pop(self) -> 'State': raise NotImplementedError
    
    @abstractmethod
    def is_empty(self) -> 'bool': raise NotImplementedError
    
    @abstractmethod
    def size(self) -> 'int': raise NotImplementedError
    
    @abstractmethod
    def contains(self, state: 'State') -> 'bool': raise NotImplementedError
    
    @abstractmethod
    def get_name(self): raise NotImplementedError

class FrontierBFS(Frontier):
    def __init__(self):
        super().__init__()
        self.queue = deque()
        self.set = set()
    
    def add(self, state: 'State'):
        self.queue.append(state)
        self.set.add(state)
    
    def pop(self) -> 'State':
        state = self.queue.popleft()
        self.set.remove(state)
        return state
    
    def is_empty(self) -> 'bool':
        return len(self.queue) == 0
    
    def size(self) -> 'int':
        return len(self.queue)
    
    def contains(self, state: 'State') -> 'bool':
        return state in self.set
    
    def get_name(self):
        return 'breadth-first search'

class FrontierDFS(Frontier):
    def __init__(self):
        super().__init__()
        self.queue = deque()
        self.set = set()
    
    def add(self, state: 'State'):
        self.queue.append(state)
        self.set.add(state)

    def pop(self) -> 'State':
        state = self.queue.pop()
        self.set.remove(state)
        return state
    
    def is_empty(self) -> 'bool':
        return len(self.queue) == 0
    
    def size(self) -> 'int':
        return len(self.queue)
    
    def contains(self, state: 'State') -> 'bool':
        return state in self.set
    
    def get_name(self):
        return 'depth-first search'

class FrontierBestFirst(Frontier):
    
    def __init__(self, heuristic: 'Heuristic'):
        super().__init__()
        self.heuristic = heuristic
        self.queue = []
        self.set = []
        self.counter = 0
    
    def add(self, state: 'State'):
        priority = self.heuristic.f(state)
        heappush(self.queue, (priority, self.counter, state))
        self.counter += 1
        self.set.append(state)
    
    def pop(self) -> 'State':
        if not self.queue:
            return None
        priority, counter, state = heappop(self.queue)
        self.set.remove(state)
        return state    
    
    def is_empty(self) -> 'bool':
        return len(self.queue) == 0
    
    def size(self) -> 'int':
        return len(self.queue)
    
    def contains(self, state: 'State') -> 'bool':
        return state in self.set
    
    def get_name(self):
        return 'best-first search using {}'.format(self.heuristic)
    
class FrontierBestFirstWidth(Frontier):
    
    def __init__(self, heuristic: 'Heuristic'):
        super().__init__()
        self.heuristic = heuristic
        self.queue = []
        self.set = []
        self.counter = 0
    
    def add(self, state: 'State'):
        # Call w on frontier to update the priority | e.g. if heuristic.w finds out a novel atom w value will drop to 0
        self.heuristic.get_w(self.queue, state)
        # Here priority is <w, h>         
        priority = self.heuristic.f(state)
        print(priority)
        heappush(self.queue, (priority, self.counter, state))
        self.counter += 1
        self.set.append(state)
    
    def pop(self) -> 'State':
        if not self.queue:
            return None
        priority, counter, state = heappop(self.queue)
        self.set.remove(state)
        return state    
    
    def is_empty(self) -> 'bool':
        return len(self.queue) == 0
    
    def size(self) -> 'int':
        return len(self.queue)
    
    def contains(self, state: 'State') -> 'bool':
        return state in self.set
    
    def get_name(self):
        return 'best-first width search <w, h>'.format(self.heuristic)