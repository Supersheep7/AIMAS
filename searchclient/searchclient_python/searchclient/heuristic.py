from abc import ABCMeta, abstractmethod
from collections import Counter, deque
from state import atoms
import numpy as np
import string   

class Heuristic(metaclass=ABCMeta):
    def __init__(self, initial_state: 'State'):
        # Here's a chance to pre-process the static parts of the level.
        self.goal_matrix = np.array(initial_state.goals)
        self.wall_matrix = np.array(initial_state.walls).astype(int)
        self.current_agent = None
        self.current_box = None
        self.alphabet = string.ascii_uppercase
        self.latest_state = initial_state
        self.novelty_sets = set()                             # We assume PDDL tuples
        self.w = 1

        def get_neighbors(grid, pos):
            
            neighbors = []
            rows, cols = len(grid), len(grid[0])
            x, y = pos
            
            # Define offsets for possible movements (up, down, left, right)
            movements = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            
            for dx, dy in movements:
                nx, ny = x + dx, y + dy
                # Check if the neighboring position is within the grid boundaries
                if 0 <= nx < rows and 0 <= ny < cols:
                    # Check if the neighboring position is not a wall (assuming 0 represents free space)
                    if grid[nx][ny] == 0:
                        neighbors.append((nx, ny))

            return neighbors

        def get_path(grid, goal_pos):
            # Initialize an array to store shortest path distances
            distances = np.zeros_like(grid)           
            # Backtrack
            queue = deque([goal_pos])
            while queue:
                current_pos = queue.popleft()
                for neighbor in get_neighbors(grid, current_pos):
                    # Populate distances
                    if distances[neighbor] == 0:
                        distances[neighbor] = distances[current_pos] + 1
                        queue.append(neighbor)

            # Fill remaining cells (walls) with 999
            distances[distances == 0] = 999

            # And return goal position value to 0
            distances[goal_pos] = 0
            return distances
        
        # Get location of each goal

        goal_positions = []

        # Agents
        for goal in range(10):
            goal_pos = np.where(self.goal_matrix == str(goal))
            if goal_pos[0].size > 0:
                goal_pos = (int(goal_pos[0][0]), int(goal_pos[1][0]))
                goal_positions.append((goal, goal_pos))
        # Boxes
        for goal in self.alphabet:
            goal_positions.extend([(goal, (x, y)) for x, y in zip(*np.where(self.goal_matrix == goal))])

        # Get grids on a lookup table

        self.grids = {}

        for goal_name, goal_pos in goal_positions:
            if type(goal_name) == str:
                unique_goal_id = f"{goal_name}_({goal_pos[0]}, {goal_pos[1]})"
                self.grids[unique_goal_id] = get_path(self.wall_matrix, goal_pos)
            else:
                self.grids[goal_name] = get_path(self.wall_matrix, goal_pos)
    
    # Manhattan
    def manhattan(self, agent, goal):
        return abs(agent[0] - goal[0]) + abs(agent[1] - goal[1])

    def h(self, state: 'State') -> 'int':
        
        count = 0
        k = 1

        ''' SAboxes '''           

        # Default to boxes
        if any(isinstance(key, str) for key in self.grids.keys()):
            boxes = []
            grids = []
            for x, row in enumerate(state.boxes):
                for y, box in enumerate(row):
                    # Filters empty tiles and unassigned boxes
                    if box != '' and any(key.startswith(box) for key in self.grids.keys()):
                        box_pos = (x, y)
                        boxes.append((box, box_pos))
            boxes = sorted(boxes, key=lambda box: box[0])
            for key, grid in self.grids.items():
                grids.append(grid)  
            # Loop through boxes and grids, alphabetically. Assigns each box to its grid, so it works also when they are not specifically labeled
            for box, grid in zip(boxes, grids):
                grid = np.array(grid)
                ''' If we want to add nearest box heuristic in the mix '''
                count += self.manhattan((box[1][0], box[1][1]), (state.agent_rows[0], state.agent_cols[0]))
                count += grid[box[1][0]][box[1][1]] * k

        # Default to pathfinding
        else:
            agents = []
            for agent_row in state.agent_rows:
                agent_num = state.worker_name
                agent_col = state.agent_cols[0]
                agent_pos = (agent_row, agent_col)
                if agent_num in self.grids:
                    grid = self.grids[agent_num]
                    # count += grid[agent_pos]
                    agents.append(grid[agent_pos])
                    count = max(agents)
                else: 
                    count += self.manhattan(agent_pos, (agent_num, agent_num))

        return count

    def get_w(self, frontier, state: 'State') -> 'int':
        
        ''' For efficiency,
        as discussed before, we don’t compute the value
        w(s) exactly. Instead, except when stated otherwise, we just
        determine whether w(s) is 1 or greater than 1. As a result, a
        state s will not be preferred to a state s' when the two states
        have the same heuristic values and both states have novelty
        measures greater than 1. 
        '''

        w = self.w
        
        if len(frontier) < 1:
            return w

        state_repr = atoms(state)

        heuristic_val = self.h(state)
        filtered_seen_states = [seen_state[2] for seen_state in frontier if self.h(seen_state[2]) == heuristic_val]
        for seen_state in filtered_seen_states:
            self.novelty_sets.add(atoms(seen_state))      # This should populate the set with a set for each seen state with the same h
  
        for novel_set in self.novelty_sets:
            if state_repr - novel_set:        # If one atom is novel
                w = 0
                self.w = w

        return w

    @abstractmethod
    def f(self, state: 'State') -> 'int': pass
    
    @abstractmethod
    def __repr__(self): raise NotImplementedError

class HeuristicAStar(Heuristic):
    def __init__(self, initial_state: 'State'):
        super().__init__(initial_state)
    
    def f(self, state: 'State') -> 'int':
        return state.g + self.h(state)
    
    def __repr__(self):
        return 'A* evaluation'

class HeuristicWeightedAStar(Heuristic):
    def __init__(self, initial_state: 'State', w: 'int'):
        super().__init__(initial_state)
        self.w = w
    
    def f(self, state: 'State') -> 'int':
        return state.g + self.w * self.h(state)
    
    def __repr__(self):
        return 'WA*({}) evaluation'.format(self.w)

class HeuristicGreedy(Heuristic):
    def __init__(self, initial_state: 'State'):
        super().__init__(initial_state)
    
    def f(self, state: 'State') -> 'int':
        return self.h(state)
    
    def __repr__(self):
        return 'greedy evaluation'

# Greedy BFWS

class HeuristicBFWS(Heuristic):
    def __init__(self, initial_state: 'State'):
        super().__init__(initial_state)
    
    '''
    Remarkably, however, BFWS with evaluation function
    f2 = <w, h>, where the preference order between heuristics
    and novelties are reversed, performs much better than
    both BFWS(f1) with f1 = <h,w> and GBFS-W. The preferred
    states in f2 = <w, h> are not picked among the ones
    with lowest h but among those with lowest novelty measure
    w(s) = wh(s), with the heuristic h being used as a
    tie breaker.
    '''

    def f(self, state: 'State') -> 'int':
        return state.g + self.h(state)

    def __repr__(self):
        return 'BFWS evaluation'
