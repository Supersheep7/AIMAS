from color import Color
from state import State
import numpy as np


class Worker:

    def __init__(self, color, name, boxes, num_cols, num_rows):
        self.name = name
        self.movable = boxes
        self.agent_rows = [None for _ in range(10)]
        self.agent_cols = [None for _ in range(10)]
        self.goals = [['' for _ in range(num_cols)] for _ in range(num_rows)]
        self.boxes = [['' for _ in range(num_cols)] for _ in range(num_rows)]
        self.color = color
        self.constraints = None

def parse(server_messages): 
        
        initial_states = []

        ''' Read head '''

        server_messages.readline() # #domain
        server_messages.readline() # hospital
        server_messages.readline() # #levelname
        server_messages.readline() # <name>
        server_messages.readline() # #colors
        agent_colors = [None for _ in range(10)]
        box_colors = [None for _ in range(26)]
        line = server_messages.readline()

        # Get teams from the level
        teams = []
        while not line.startswith('#'):
            split = line.split(':')
            color = Color.from_string(split[0].strip())
            entities = [e.strip() for e in split[1].split(',')]
            agentz = []
            boxez = []
            for e in entities:
                if '0' <= e <= '9':
                    agent_colors[ord(e) - ord('0')] = color
                    agentz.append(e)
                elif 'A' <= e <= 'Z':
                    box_colors[ord(e) - ord('A')] = color
                    boxez.append(e)
            teams.append([(split[0]), agentz, boxez])
            line = server_messages.readline()

        ''' Read initial state '''
        
        initial_line = server_messages.readline() 
        level_lines = []
        line = initial_line
        num_rows = 0
        num_cols = 0
        while not line.startswith('#'):
            level_lines.append(line)
            num_cols = max(num_cols, len(line))
            num_rows += 1
            line = server_messages.readline()

        ''' Read goal state '''

        initial_goal_line = server_messages.readline()
        goal_level_lines = []
        line = initial_goal_line   
        while not line.startswith('#'):
            goal_level_lines.append(line)
            line = server_messages.readline()

        ''' Loop and build a different level representation for each worker '''

        # Initialize our workers

        workers = []
        movable_boxes = []

        for team in teams: 
            color = team[0]
            agents = team[1]
            movable = team[2]
            movable_boxes.append(movable)
            for agent in agents:
                workers.append(Worker(color, agent, movable, num_cols, num_rows))

        movable_boxes = [element for sublist in movable_boxes for element in sublist]
        walls = [[False for _ in range(num_cols)] for _ in range(num_rows)]

        # While we build the level representation we put goals and boxes in a set
        # to be assigned later at each worker

        goals_to_assign = set()
        boxes_to_assign = set()
        
        for worker in workers:
            for row, line in enumerate(level_lines):
                for col, c in enumerate(line):
                    if c == worker.name:
                        worker.agent_rows[ord(c) - ord('0')] = row
                        worker.agent_cols[ord(c) - ord('0')] = col
                    elif c.isalpha():
                        if c not in movable_boxes:
                            c = '+'
                        else: 
                            boxes_to_assign.add((c, (row, col)))
                    elif c == '+':
                        walls[row][col] = True
            
            worker.agent_rows = [row for row in worker.agent_rows if row is not None]
            worker.agent_cols = [col for col in worker.agent_cols if col is not None]
    
        for row, line in enumerate(goal_level_lines):
            for col, c in enumerate(line):
                    if c.isalpha():
                        goals_to_assign.add((c, (row, col)))  
                    elif c.isdigit():
                        goals_to_assign.add((c, (row, col)))     
            
        # Now we assign goals and boxes for each worker
        # Part 1: assign goals and box per goal
       
        current_worker_index = -1

        while goals_to_assign:
            goal = goals_to_assign.pop()
            row, col = goal[1]
            chosen_worker = None

            for _ in range(len(workers)):
                current_worker_index = (current_worker_index + 1) % len(workers)
                if goal[0] in workers[current_worker_index].movable or goal[0] == workers[current_worker_index].name:
                    chosen_worker = workers[current_worker_index]
                    chosen_worker.goals[row][col] = goal[0]

                    if goal[0].isalpha():
                        box_for_goal = next(box for box in boxes_to_assign if box[0] == goal[0])
                        boxes_to_assign.remove(box_for_goal)
                        row, col = box_for_goal[1]
                        chosen_worker.boxes[row][col] = box_for_goal[0]
                        workers[current_worker_index] = chosen_worker
                        break

        # Part 2: assign the remaining boxes

        current_worker_index = -1

        while boxes_to_assign:
            box = boxes_to_assign.pop()
            row, col = box[1]
            chosen_worker = None

            for _ in range(len(workers)):
                if box[0] in workers[current_worker_index].movable:
                    chosen_worker = workers[current_worker_index]
                current_worker_index = (current_worker_index + 1) % len(workers) 
                chosen_worker.boxes[row][col] = box[0]
                workers[current_worker_index] = chosen_worker
                break

        State.agent_colors = agent_colors
        State.walls = walls
        State.box_colors = box_colors
            
        ''' We finished the state building for a single worker '''

        for worker in workers:
            stringoals = ''.join([str(element) for row in worker.goals for element in row]) 
            if len(stringoals) < 1: # Has no goals
                worker.goals[worker.agent_rows[0]][worker.agent_cols[0]] = worker.name 
            initial_states.append(State(worker.agent_rows, worker.agent_cols, worker.boxes, worker.goals, worker.name))
            print("#Initialized state for worker Name", worker.name, flush=True)

        return initial_states