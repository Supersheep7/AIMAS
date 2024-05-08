import random

from action import Action, ActionType

class Constraint:
    def __init__(self, agent, loc_from, loc_to, time):
        self.agent = agent
        self.loc_from = loc_from  # Assuming loc_from is a list of starting locations
        self.loc_to = loc_to      # Assuming loc_to is a list of ending locations
        self.time = time

def atoms(state: 'State'):
        """
        Generates a set of atoms that represent the current state.

        Args:
        - state (State): The current state of the environment.

        Returns:
        - Set[Tuple[str, Tuple[int, int]]]: A set of tuples representing the state atoms.
        """
        atoms = set()
        for index, row, col in zip(state.worker_name, state.agent_rows, state.agent_cols):
            atoms.add((f'AgentAt{index}', (row, col)))

        for (row_index, row) in enumerate(state.boxes):
            for col_index, box in enumerate(row):
                if box:  
                    atoms.add((f'BoxAt{box}', (row_index, col_index)))

        return frozenset(atoms)     # Need the frozenset so I can add the state representation to the novelty set

class State:
    _RNG = random.Random(1)
    
    def __init__(self, agent_rows, agent_cols, boxes, goals, worker_name, constraints = None):
        '''
        Constructs an initial state.
        Arguments are not copied, and therefore should not be modified after being passed in.
        
        The lists walls, boxes, and goals are indexed from top-left of the level, row-major order (row, col).
               Col 0  Col 1  Col 2  Col 3
        Row 0: (0,0)  (0,1)  (0,2)  (0,3)  ...
        Row 1: (1,0)  (1,1)  (1,2)  (1,3)  ...
        Row 2: (2,0)  (2,1)  (2,2)  (2,3)  ...
        ...
        
        For example, State.walls[2] is a list of booleans for the third row.
        State.walls[row][col] is True if there's a wall at (row, col).
        
        The agent rows and columns are indexed by the agent number.
        For example, State.agent_rows[0] is the row location of agent '0'.
                
        Note: The state should be considered immutable after it has been hashed, e.g. added to a dictionary or set.
        '''
        self.worker_name = worker_name
        self.agent_rows = agent_rows
        self.agent_cols = agent_cols
        self.boxes = boxes
        self.parent = None
        self.joint_action = None
        self.g = 0
        self._hash = None
        self.constraint_step = False
        self.constraints = constraints if constraints else []
        ''' We passed the goals to the state to account for goal decomposition '''

        self.goals = goals
    
    def result(self, joint_action: '[Action, ...]') -> 'State':
        '''
        Returns the state resulting from applying joint_action in this state.
        Precondition: Joint action must be applicable and non-conflicting in this state.
        '''
        
        # Copy this state.
        copy_agent_rows = self.agent_rows[:]
        copy_agent_cols = self.agent_cols[:]
        copy_worker_name = self.worker_name[:]
        copy_boxes = [row[:] for row in self.boxes]

        # Apply each action.
        for agent, action in enumerate(joint_action):  
            if action.type is ActionType.NoOp:
                pass
            
            elif action.type is ActionType.Move:
                copy_agent_rows[agent] += action.agent_row_delta
                copy_agent_cols[agent] += action.agent_col_delta

            elif action.type is ActionType.Push:
                copy_agent_rows[agent] += action.agent_row_delta
                copy_agent_cols[agent] += action.agent_col_delta
                copy_boxes[copy_agent_rows[agent] + action.box_row_delta][copy_agent_cols[agent] + action.box_col_delta] = copy_boxes[copy_agent_rows[agent]][copy_agent_cols[agent]]
                copy_boxes[copy_agent_rows[agent]][copy_agent_cols[agent]] = ''

            elif action.type is ActionType.Pull:
                copy_boxes[copy_agent_rows[agent]][copy_agent_cols[agent]] = copy_boxes[copy_agent_rows[agent] - action.box_row_delta][copy_agent_cols[agent] - action.box_col_delta]
                copy_boxes[copy_agent_rows[agent] - action.box_row_delta][copy_agent_cols[agent] - action.box_col_delta] = ''
                copy_agent_rows[agent] += action.agent_row_delta
                copy_agent_cols[agent] += action.agent_col_delta

        copy_state = State(copy_agent_rows, copy_agent_cols, copy_boxes, self.goals, copy_worker_name, self.constraints)
        copy_state.parent = self
        copy_state.joint_action = joint_action[:]
        copy_state.g = self.g + 1
        copy_state.constraints = self.constraints[:]
        copy_state.constraint_step = False
        if copy_state.constraints:
            if copy_state.g == copy_state.constraints[0].time:
                copy_state.constraint_step = True
        return copy_state
    
    def is_goal_state(self) -> 'bool':
        for row in range(len(self.goals)):
            for col in range(len(self.goals[row])):
                goal = self.goals[row][col]
                if 'A' <= goal <= 'Z' and self.boxes[row][col] != goal:
                    return False
                elif '0' <= goal <= '9' and not (self.agent_rows[ord(goal) - ord('0')] == row and self.agent_cols[ord(goal) - ord('0')] == col):
                    return False
        return True
    
    def get_expanded_states(self) -> '[State, ...]':
        num_agents = len(self.agent_rows)
        
        # Determine list of applicable action for each individual agent.
        applicable_actions = [[action for action in Action if self.is_applicable(agent, action)] for agent in range(num_agents)]
        
        # Iterate over joint actions, check conflict and generate child states.
        joint_action = [None for _ in range(num_agents)]
        actions_permutation = [0 for _ in range(num_agents)]
        expanded_states = []
        while True:
            for agent in range(num_agents):
                joint_action[agent] = applicable_actions[agent][actions_permutation[agent]]
            
            if not self.is_conflicting(joint_action):
                expanded_states.append(self.result(joint_action))
            
            # Advance permutation.
            done = False
            for agent in range(num_agents):
                if actions_permutation[agent] < len(applicable_actions[agent]) - 1:
                    actions_permutation[agent] += 1
                    break
                else:
                    actions_permutation[agent] = 0
                    if agent == num_agents - 1:
                        done = True
            
            # Last permutation?
            if done:
                break
        
        State._RNG.shuffle(expanded_states)
        return expanded_states
    
    def is_applicable(self, agent: 'int', action: 'Action') -> 'bool':
        agent_row = self.agent_rows[agent]
        agent_col = self.agent_cols[agent]
        
        if action.type is ActionType.NoOp:
            return True
            
        elif action.type is ActionType.Move:
            destination_row = agent_row + action.agent_row_delta
            destination_col = agent_col + action.agent_col_delta
            return self.is_free(destination_row, destination_col, self.g + 1)
        
        elif action.type is ActionType.Push:
            destination_row = agent_row + action.agent_row_delta
            destination_col = agent_col + action.agent_col_delta
            box_destination_row =  destination_row + action.box_row_delta
            box_destination_col =  destination_col + action.box_col_delta
            return self.boxes[destination_row][destination_col] != '' and self.is_free(box_destination_row, box_destination_col, self.g + 1)
        
        elif action.type is ActionType.Pull:
            destination_row = agent_row + action.agent_row_delta
            destination_col = agent_col + action.agent_col_delta
            box_row =  agent_row  - action.box_row_delta
            box_col =  agent_col - action.box_col_delta
            return self.boxes[box_row][box_col] != '' and self.is_free(destination_row, destination_col, self.g + 1)
                
    def is_conflicting(self, joint_action: '[Action, ...]') -> 'bool':
        num_agents = len(self.agent_rows)
        
        destination_rows = [None for _ in range(num_agents)] # row of new cell to become occupied by action
        destination_cols = [None for _ in range(num_agents)] # column of new cell to become occupied by action
        box_rows = [None for _ in range(num_agents)] # current row of box moved by action
        box_cols = [None for _ in range(num_agents)] # current column of box moved by action
        
        # Collect cells to be occupied and boxes to be moved.
        for agent in range(num_agents):
            action = joint_action[agent]
            agent_row = self.agent_rows[agent]
            agent_col = self.agent_cols[agent]
            
            if action.type is ActionType.NoOp:
                pass
            
            elif action.type is ActionType.Move:
                destination_rows[agent] = agent_row + action.agent_row_delta
                destination_cols[agent] = agent_col + action.agent_col_delta
                box_rows[agent] = agent_row # Distinct dummy value.
                box_cols[agent] = agent_col # Distinct dummy value.
                    
        for a1 in range(num_agents):
            if joint_action[a1] is Action.NoOp:
                continue
            
            for a2 in range(a1 + 1, num_agents):
                if joint_action[a2] is Action.NoOp:
                    continue
                
                # Moving into same cell?
                if destination_rows[a1] == destination_rows[a2] and destination_cols[a1] == destination_cols[a2]:
                    return True
                        
        return False
    
    def is_free(self, row: 'int', col: 'int', time:'int' = 0) -> 'bool':
        if State.walls[row][col] or self.boxes[row][col] != '' or self.agent_at(row, col) is not None:
            return False
        for constraint in self.constraints:
            if (constraint.time == time and (row, col) in constraint.loc_to and constraint.agent == self.worker_name):
                print("At time", constraint.time, "This location is NOT free:", constraint.loc_to, flush=True)
                return False
        return True
    
    def agent_at(self, row: 'int', col: 'int') -> 'char':
        for agent in range(len(self.agent_rows)):
            if self.agent_rows[agent] == row and self.agent_cols[agent] == col:
                return chr(agent + ord('0'))
        return None
    
    def extract_plan(self) -> '[Action, ...]':
        plan = [None for _ in range(self.g)]
        plan_repr = plan[:]
        state = self
        while state.joint_action is not None:
            plan[state.g - 1] = state.joint_action
            plan_repr[state.g - 1] = list(sorted(atoms(state)))
            state = state.parent
        return plan, plan_repr
    
    def __hash__(self):
        if self._hash is None:
            prime = 31
            _hash = 1
            _hash = _hash * prime + hash(tuple(self.agent_rows))
            _hash = _hash * prime + hash(tuple(self.agent_cols))
            _hash = _hash * prime + hash(tuple(State.agent_colors))
            _hash = _hash * prime + hash(tuple(tuple(row) for row in self.boxes))
            _hash = _hash * prime + hash(tuple(State.box_colors))
            _hash = _hash * prime + hash(tuple(tuple(row) for row in self.goals))
            _hash = _hash * prime + hash(tuple(tuple(row) for row in State.walls))
            self._hash = _hash
        return self._hash
    
    def __eq__(self, other):
        if self is other: return True
        if not isinstance(other, State): return False
        if self.agent_rows != other.agent_rows: return False
        if self.agent_cols != other.agent_cols: return False
        if State.agent_colors != other.agent_colors: return False
        if State.walls != other.walls: return False
        if self.boxes != other.boxes: return False
        if State.box_colors != other.box_colors: return False
        if self.goals != other.goals: return False
        return True
    
    def __repr__(self):
        lines = []
        for row in range(len(self.boxes)):
            line = []
            for col in range(len(self.boxes[row])):
                if self.boxes[row][col] != '': line.append(self.boxes[row][col])
                elif State.walls[row][col] is not None: line.append('+')
                elif self.agent_at(row, col) is not None: line.append(self.agent_at(row, col))
                else: line.append(' ')
            lines.append(''.join(line))
        return '\n'.join(lines)
