from frontier import FrontierBestFirstWidth
from heuristic import HeuristicBFWS
from graphsearch import search
from action import Action
import copy
from conflictmodule import validate, add_constraint
import random

class Node():

    def __init__(self, states, single_agent = None, constraints = []):
        self.initial_states = states
        self.constraints = constraints
        self.agent = None
        self.boxes = []
        if single_agent is not None:
            # Select worker for a singleton search
            state = next((state for state in self.initial_states if state.worker_name == single_agent), None)
            state = [state]
            self.plans, self.paths = self.plans_from_states(state) # Has to be consistent with constraints
            state[0].constraints = self.constraints
        else:
            for state in self.initial_states:
                state.constraints = [constraint for constraint in self.constraints if constraint.agent == state.worker_name]
            self.plans, self.paths = self.plans_from_states(self.initial_states)     # Has to be consistent with constraints
        self.workers = [state.worker_name for state in self.initial_states]
        self.cost = 0 # sum of costs

    def plans_from_states(self, states):

        plans = []
        plans_repr = []

        states = sorted(states, key=lambda x:x.worker_name)

        for state in states:
            frontier = FrontierBestFirstWidth(HeuristicBFWS(state))
            searching = search(state, frontier)
            plan, plan_repr = searching
            plans.append(plan)
            plans_repr.append(plan_repr)
        
        return plans, plans_repr

    def get_single_search(self, single_agent):

        state = next((state for state in self.initial_states if state.worker_name == single_agent), None)
        state.constraints = self.constraints
        state = [state]
        return self.plans_from_states(state)
    
    def get_constraints_tuple(self):
        # Convert each constraint into a tuple based on its properties
        return tuple(self.constraint_to_tuple(constraint) for constraint in self.constraints)

    def constraint_to_tuple(self, constraint):
        # Create a tuple representation of the constraint
        if hasattr(constraint, 'box'):
            return (constraint.agent, constraint.box, constraint.loc_to, constraint.time)
        else:
            return (constraint.agent, constraint.loc_to, constraint.time)
        
    def agents_to_rest(self):
        longest = max([len(plan) for plan in self.plans])
        result_plans = [plan for plan in self.plans if len(plan) == longest]
        filtered_plans = [plan for plan in self.plans if len(plan) < longest]
        if len(filtered_plans) > 0:
            for plan in  filtered_plans:
                len_diff = longest - len(plan)
                plan += [[Action.NoOp]] * len_diff
                result_plans.append(plan)
        return result_plans
    
    def __hash__(self):
        plan_tuple = tuple(tuple(tuple(action) for action in plan) for plan in self.plans)
        constraints_tuple = self.get_constraints_tuple()
        return hash((self.agent, constraints_tuple, plan_tuple))
    
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return (self.agent == other.agent and
                self.constraints == other.constraints and
                self.plans == other.plans)

def CBS(initial_states):

    ''' Setup search '''

    is_single = False
    root = Node(initial_states)
    root.agent = None
    open_set = set()
    open_set.add(root)
    closed_set = set()
    iterations = 0
    path_rank = {}
    goal_conflict_rank = {} 
    C = None
    agents_ok = set()

    ''' Prepare lookup tables for agent rank '''

    for worker in root.workers:
        goal_conflict_rank[worker] = 0
        path_rank[worker] = len(root.plans[worker])

    for worker, path in zip(root.workers, root.paths):
        steps = [step for step in path]
        tuplez = [list(y for _, y in sublist) for sublist in steps]
        cells = []
        [cells.extend(sublist) for sublist in tuplez]
        for other_path in root.paths:
            if other_path == path:
                continue
            last_step = other_path[-1]
            last_coords = [element[1] for element in last_step]
            for element in last_coords:
                if element in cells:
                    goal_conflict_rank[worker] += 1
    
    ''' Start search '''

    while open_set:
        iterations += 1
        filtered_set = [p for p in open_set if p not in closed_set]

        P = min(filtered_set, key=lambda x: (x.cost))
        open_set.remove(P)
        closed_set.add(P)

        print("#Opening node cost", P.cost, "agent", P.agent, \
            "explored", len(closed_set), "frontier", len(filtered_set), flush=True)

        # P.paths = [ [ ] [ ] [ ] ]

        for agent_i, path in enumerate(P.paths):
            C = validate(path, P.paths) # Consistent path needs to be valid
            if C is None:
                agents_ok.add(agent_i)
            if C is not None:   # Found conflict, path invalid, non goal node
                break

        # Found solution
        if not C:
            ("Found solution")
            if len(P.plans) == 1:
                solution = P.plans[0]
                is_single = True
            else:
                P.agents_to_rest()
                solution = [x for x in zip(*P.plans)]
                # print(solution)
            return solution, is_single
        
        # Deal with one conflict at a time
        for i, agent_i in enumerate(C.agents):
            if agent_i is None:
                continue
            
            else:
                A = copy.deepcopy(P)
                A.agent = agent_i
                
                # Add constraint
                A = add_constraint(C, A, agent_i)
                if A == None:
                    continue

                # Replan    
                plan_i, path_i = A.get_single_search(agent_i)
                plan_i = plan_i[0]
                path_i = path_i[0]
                if plan_i is None:
                    continue
                
                A.plans[agent_i] = plan_i
                A.paths[agent_i] = path_i
                # Get cost
                plan_lengths = [len(plan) for plan in A.plans]
                penalty = 1
                if agent_i in agents_ok:
                    penalty = len(agents_ok)/2
                A.cost = (penalty / iterations, goal_conflict_rank[agent_i], path_rank[agent_i],  sum(plan_lengths)* agent_i, len(A.constraints))
                
                ''' 
                Agent with less conflicts in first plan's goal state
                    Tie break for agents with the longest path
                        Tie break in lexicographic order
                            Tie break for compound plans
                                Tie break for length of constraints

                '''

                #removing duplicates:
                unique_constraints = set()
                new_constraints_list = []

                for constraint in A.constraints:
                    # Check if the constraint is a BoxConstraint and adjust the tuple to include the box
                    if hasattr(constraint, 'box'):
                        constraint_key = (constraint.agent, constraint.loc_to, constraint.time, constraint.box)
                    else:
                        constraint_key = (constraint.agent, constraint.loc_to, constraint.time)
                    
                    # Add to the new list only if the tuple is not in the set
                    if constraint_key not in unique_constraints:
                        unique_constraints.add(constraint_key)
                        new_constraints_list.append(constraint)

                A.constraints = new_constraints_list

                open_set.add(A)

    return None