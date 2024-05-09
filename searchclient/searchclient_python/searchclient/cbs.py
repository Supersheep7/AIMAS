from state import State, Constraint, Conflict
from frontier import FrontierBestFirstWidth
from heuristic import HeuristicBFWS
from graphsearch import search
from action import Action
import numpy as np
import copy

def plans_from_states(initial_states):

        plans = []
        plans_repr = []

        for num, initial_state in enumerate(initial_states):
            frontier = FrontierBestFirstWidth(HeuristicBFWS(initial_state))
            searching = search(initial_state, frontier)
            plan, plan_repr = searching
            plans.append(plan) 
            plans_repr.append(plan_repr)
            # print("Ended search for initial state number", num)
            # print()
            # print("Plan extracted. Plan:", plan)
            # print()

        plans = agents_to_rest(plans)
        return plans, plans_repr

class Node():

    def __init__(self, states, single_agent = None, constraints = []):
        self.initial_states = states
        self.constraints = constraints
        if single_agent is not None:
            # Select worker for a singleton search
            state = next((state for state in self.initial_states if state.worker_name == single_agent), None)
            state = [state]
            self.plans, self.paths = plans_from_states(state)
            state[0].constraints = self.constraints
            for constraint in self.constraints:
                print(constraint.loc_to)
        else:
            for state in self.initial_states:
                state.constraints = self.constraints
            self.plans, self.paths = plans_from_states(self.initial_states)

        self.cost = sum([len(plan) for plan in self.plans]) # sum of costs
    
    def get_single_search(self, single_agent):
        state = next((state for state in self.initial_states if state.worker_name == single_agent), None)
        state.constraints = self.constraints
        state = [state]
        return plans_from_states(state)

def match_length(arr1, arr2):
    len_diff = abs(len(arr2) - len(arr1))
    if len(arr1) < len(arr2):
        last_value = arr1[-1]
        arr1 += [last_value] * len_diff
    elif len(arr2) < len(arr1):
        last_value = arr2[-1]
        arr2 += [last_value] * len_diff
    return arr1, arr2

def agents_to_rest(plans):
    longest = max([len(plan) for plan in plans])
    filtered_plans = [plan for plan in plans if len(plan) <= longest]
    plans_with_rest = []
    for plan in filtered_plans:
        len_diff = longest - len(plan)
        plan += [[Action.NoOp]] * len_diff
        plans_with_rest.append(plan)
    return plans_with_rest

def validate(plan, plan_list):
    """
    Generates constraints based on conflicts between the given plan and other plans in the plan_list,
    including illegal crossings.

    Parameters:
    - plan: The plan to validate for conflicts.
    - plan_list: List of all plans to compare against.

    Returns:
    - Conflict: First conflict found during the validation process
    """
    # print("VALIDATE", plan)
    agent_i_full = plan[0][0][0]  # Something like 'AgentAt0'
    # print(agent_i_full)
    agent_i = agent_i_full.split('AgentAt')[-1]  # Extract just the number after 'AgentAt'

    other_plans = [lst for lst in plan_list if lst is not plan]

    for other_plan in other_plans:

        agent_j_full = other_plan[0][0][0]
        agent_j = agent_j_full.split('AgentAt')[-1]

        # Ensure both plans are of equal length
        plan, other_plan = match_length(plan, other_plan)

        for j in range(1, len(plan)-1):
            # Get current and previous states for both plans
            agent_state_current = plan[j][0][1]
            agent_state_previous = plan[j - 1][0][1]
            box_state_current = plan[j][1][1] if len(plan[j]) > 1 else None
            box_state_previous = plan[j - 1][1][1] if len(plan[j - 1]) > 1 else None
            agent_state_next = plan[j+1][0][1]
            box_state_next = plan[j+1][1][1]

            other_agent_state_current = other_plan[j][0][1]
            other_agent_state_previous = other_plan[j - 1][0][1]
            other_box_state_current = other_plan[j][1][1] if len(other_plan[j]) > 1 else None
            other_box_state_previous = other_plan[j - 1][1][1] if len(other_plan[j - 1]) > 1 else None
            other_agent_state_next = other_plan[j+1][0][1]
            other_box_state_next = other_plan[j+1][1][1]
            t=j+1

            # Conflicting agent positions
            if agent_state_current == other_agent_state_current:
                conflict = Conflict(agent_i, agent_j, agent_state_current, t)
                return conflict

            # Conflicting box positions
            if box_state_current is not None and box_state_current == other_box_state_current:
                conflict = Conflict(agent_i, agent_j, box_state_current, t)
                return conflict

            # Illegal crossing detection
            # Agents crossing each other
            if agent_state_current == other_agent_state_previous and agent_state_previous == other_agent_state_current:
                conflict = Conflict(agent_i, agent_j, agent_state_current, t)
                return conflict


            # Boxes crossing each other
            if box_state_current is not None and box_state_previous is not None and \
                    box_state_current == other_box_state_previous and box_state_previous == other_box_state_current:
                conflict = Conflict(agent_i, agent_j, box_state_current, t)
                return conflict

            # Agent and Box crossing
            if box_state_current is not None and \
                    (agent_state_current == other_box_state_previous and agent_state_previous == other_box_state_current):
                conflict = Conflict(agent_i, agent_j, agent_state_current, t)
                return conflict

    return None    # [ConstraintObject0, ..., ConstraintObjectn]

def CBS(initial_states):
    is_single = False
    root = Node(initial_states)
    open_set = set()
    open_set.add(root)

    while open_set:
        P = min(open_set, key=lambda x: x.cost)
        print("Opening node with cost", P.cost)
        print("Length of path:", len(P.paths[0]))
        print("Constraint of the node:", P.constraints)
        C = None

        for path in P.paths:
            C = validate(path, P.paths)     
            if C is not None:
                break

        if not C:
            print(P.plans)
            print("Found solution")
            print("Positions:", P.paths)
            if len(P.plans) == 1:
                print("Single agent")
                solution = P.plans[0]
                is_single = True
            else:
                print("Multi agent")
                solution = [list(x) for x in zip(*P.plans)]
            return solution, is_single  # Found solution, return solution in joint action normal form

        for agent_i in C.agents:
            A = copy.deepcopy(P)
            A.agent = agent_i
            A.constraints.append(Constraint(agent_i, C.v, C.t))
            for constraint in A.constraints:
                print(constraint.agent, constraint.loc_to, constraint.time)
            plan_i, path_i = A.get_single_search(agent_i)
            plan_i = plan_i[0]
            path_i = path_i[0]
            A.plans[int(agent_i)] = plan_i
            A.paths[int(agent_i)] = path_i
            A.cost = sum([len(plan) for plan in A.plans])
            print(A.cost)
            if A.cost < np.inf:
                open_set.add(A)

    return None