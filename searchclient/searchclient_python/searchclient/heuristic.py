from abc import ABCMeta
from collections import deque
import numpy as np
import string   
from itertools import chain
from utils import manhattan

class Heuristic(metaclass=ABCMeta):
    def __init__(self, initial_state: 'State'):
        # Here's a chance to pre-process the static parts of the level.
        self.goal_matrix = np.array(initial_state.goals)
        self.wall_matrix = np.array(initial_state.walls).astype(int)
        self.current_agent = None
        self.current_box = None
        self.alphabet = string.ascii_uppercase
        self.latest_state = initial_state

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

    def pathfinding(self, state):

        count = 0
        agent_pos = (state.agent_rows[0], state.agent_cols[0])
        grid = self.grids[state.worker_name]
        count += grid[agent_pos]

        return count
    
    def h(self, state: 'State') -> 'int':
        
        count0 = 0
        count1 = 0
        count = 0

        ''' SAboxes '''           

        # Default to boxes
        if any(isinstance(key, str) for key in self.grids.keys()):
            boxes = []
            for x, row in enumerate(state.boxes):
                for y, box in enumerate(row):
                    # Filters empty tiles and unassigned boxes
                    if box != '' and any(str(key).startswith(box) for key in self.grids.keys()):
                        box_pos = (x, y)
                        boxes.append((box, box_pos))
            boxes = sorted(boxes, key=lambda box: box[0])
            grids = [grid for key, grid in self.grids.items() if type(key) is not int]
            # Loop through boxes and grids, alphabetically. Assigns each box to its grid, so it works also when they are not specifically labeled
            for box, grid in zip(boxes, grids):
                grid = np.array(grid)
                ''' If we want to add nearest box heuristic in the mix '''
                count0 += grid[box[1][0]][box[1][1]]
                manhattan_distance = manhattan((box[1][0], box[1][1]), (state.agent_rows[0], state.agent_cols[0]))
                count1 += manhattan_distance

            if count0 == 0 and not state.is_goal_state():
                count = int(self.pathfinding(state))
                return count
            
            elif count0 == 0 and state.is_goal_state():
                return 0

            return (count0, count1)

        # Default to pathfinding
        else:
            if state.is_goal_state():
                return 0
            count = self.pathfinding(state)
            return (int(count))

    def get_w(self, explored, state: 'State') -> 'int':

        ''' experimenting with this, pay no mind to the comments '''
        state_repr = state.atoms
        # explored_atom_form = list(chain.from_iterable(explored))

        if state_repr not in explored:
            state.r = 0

        else: 
            state.r = explored.count(state_repr)

        # for atom in state_repr:
        #     if atom not in explored_atom_form:        # If one atom is novel
        #         state.w = 0
        #         break

        #     else:
        #         state.w = explored_atom_form.count(atom)

        return

# Mixed BFWS

class HeuristicBFWS(Heuristic):
    def __init__(self, initial_state: 'State'):
        super().__init__(initial_state)

    def f(self, state: 'State') -> 'int':
        heuristic_value = self.h(state)
        if type(heuristic_value) == int:        # MAPF, we can be greedy
            return (-1/(heuristic_value+1), -1/(heuristic_value+1))
        else:
            f = ((state.r + heuristic_value[0], heuristic_value[1]))
            return f
    
    def __repr__(self):
        return 'BFWS evaluation'