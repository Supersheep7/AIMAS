import random

from action import Action, ActionType
from conflictmodule import Constraint, BoxConstraint

class State:
    _RNG = random.Random(1)
    
    def __init__(self, agent_rows, agent_cols, boxes, goals, worker_name, constraints = None):
        
        self.worker_name = int(worker_name)
        self.agent_rows = agent_rows
        self.agent_cols = agent_cols
        self.boxes = boxes
        self.parent = None
        self.joint_action = None
        self.g = 0
        self._hash = None
        self.constraint_step = False
        self.constraints = constraints if constraints else []
        self.goals = goals
        self.w = 1
        def atoms(self):
            """
            Generates a set of atoms that represent the current state.

            Args:
            - state (State): The current state of the environment.

            Returns:
            - Set[Tuple[str, Tuple[int, int]]]: A set of tuples representing the state atoms.
            """
            atoms = set()
            for index, row, col in zip(str(self.worker_name), self.agent_rows, self.agent_cols):
                atoms.add((f'AgentAt{index}', (row, col)))

            for (row_index, row) in enumerate(self.boxes):
                for col_index, box in enumerate(row):
                    if box:  
                        atoms.add((f'BoxAt{box}', (row_index, col_index)))

            return frozenset(atoms)     # Need the frozenset so I can add the state representation to the novelty set
        self.atoms = atoms(self)
    
    def result(self, joint_action):

        '''
        Returns the state resulting from applying joint_action in this state.
        Precondition: Joint action must be applicable and non-conflicting in this state.
        '''
        
        # Copy this state.
        copy_agent_rows = self.agent_rows[:]
        copy_agent_cols = self.agent_cols[:]
        copy_worker_name = self.worker_name
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
        
        for constraint in copy_state.constraints:
            if isinstance(constraint, Constraint):
                if (constraint.time == copy_state.g and (copy_agent_rows[0], copy_agent_cols[0]) == constraint.loc_to):
                    copy_state.constraint_step = True
            elif isinstance(constraint, BoxConstraint) and constraint.time == copy_state.g and copy_boxes[constraint.loc_to[0]][constraint.loc_to[1]] != '':
                copy_state.constraint_step = True

        return copy_state
    
    def is_goal_state(self):
        
        for row in range(len(self.goals)):
            for col in range(len(self.goals[row])):
                goal = self.goals[row][col]
                if 'A' <= goal <= 'Z' and self.boxes[row][col] != goal:
                    return False
                elif '0' <= goal <= '9' and not (self.agent_rows[0] == row and self.agent_cols[0] == col):
                    return False
        return True
    
    def get_expanded_states(self):
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
    
    def is_applicable(self, agent, action):
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
                
    def is_conflicting(self, joint_action):
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
    
    def is_free(self, row, col, time = 0):
        if State.walls[row][col] or self.boxes[row][col] != '' or self.agent_at(row, col) is not None:
            return False
        return True
    
    def agent_at(self, row, col):
        for agent in range(len(self.agent_rows)):
            if self.agent_rows[agent] == row and self.agent_cols[agent] == col:
                return chr(agent + ord('0'))
        return None
    
    def extract_plan(self):
        plan = [None for _ in range(self.g)]
        plan_repr = [None for _ in range(self.g + 1)]
        state = self
        while state.joint_action is not None:
            plan[state.g - 1] = state.joint_action
            plan_repr[state.g] = list(sorted(state.atoms))
            state = state.parent
        # state.joint_action is None. State should be state.parent of first joint_action
        plan_repr[state.g] = list(sorted(state.atoms))
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