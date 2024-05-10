from frontier import FrontierBestFirstWidth
from heuristic import HeuristicBFWS
from graphsearch import search
from action import Action
from state import Conflict, EdgeConflict, Constraint, EdgeConstraint
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
        
        return plans, plans_repr

class Node():

    def __init__(self, states, single_agent = None, constraints = []):
        self.initial_states = states
        self.constraints = constraints
        self.agent = None
        if single_agent is not None:
            # Select worker for a singleton search
            state = next((state for state in self.initial_states if state.worker_name == single_agent), None)
            state = [state]
            self.plans, self.paths = plans_from_states(state) # Has to be consistent with constraints
            state[0].constraints = self.constraints
        else:
            for state in self.initial_states:
                state.constraints = [constraint for constraint in self.constraints if constraint.agent == state.worker_name]
            self.plans, self.paths = plans_from_states(self.initial_states)     # Has to be consistent with constraints

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
    print("Putting idle agents to rest")
    longest = max([len(plan) for plan in plans])
    result_plans = [plan for plan in plans if len(plan) == longest]
    filtered_plans = [plan for plan in plans if len(plan) < longest]
    if len(filtered_plans) > 0:
        for plan in  filtered_plans:
            len_diff = longest - len(plan)
            plan += [[Action.NoOp]] * len_diff
            result_plans.append(plan)
    return result_plans

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

        for j in range(1, len(plan)):
            # Get current and previous states for both plans
            agent_state_current = plan[j][0][1]
            agent_state_previous = plan[j - 1][0][1]
            box_state_current = plan[j][1][1] if len(plan[j]) > 1 else None
            box_state_previous = plan[j - 1][1][1] if len(plan[j - 1]) > 1 else None

            other_agent_state_current = other_plan[j][0][1]
            other_agent_state_previous = other_plan[j - 1][0][1]
            other_box_state_current = other_plan[j][1][1] if len(other_plan[j]) > 1 else None
            other_box_state_previous = other_plan[j - 1][1][1] if len(other_plan[j - 1]) > 1 else None
            t=j+1


            # Illegal crossing detection
            # Agents crossing each other
            if agent_state_current == other_agent_state_previous and agent_state_previous == other_agent_state_current:
                conflict = EdgeConflict(agent_i, agent_j, agent_state_current, other_agent_state_current, t)
                return conflict 

            # Conflicting agent positions
            if agent_state_current == other_agent_state_current:
                conflict = Conflict(agent_i, agent_j, agent_state_current, t)
                print("Returning conflict between agents", agent_i, agent_j, "at tile", agent_state_current)
                return conflict

            # Conflicting box positions
            if box_state_current is not None and box_state_current == other_box_state_current:
                conflict = Conflict(agent_i, agent_j, box_state_current, t)
                return conflict

            # Follow conflict
            if agent_state_current == other_agent_state_previous:
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
    root.agent = None
    open_set = set()
    open_set.add(root)
    closed_set = set()
    iterations = 0

    while open_set:
        iterations += 1
        filtered_set = [p for p in open_set if p not in closed_set]
        P = min(filtered_set, key=lambda x: (x.cost, x.agent))
        open_set.remove(P)
        closed_set.add(P)
        print("Opening node with cost", P.cost, "agent", P.agent, "No of Constraint of the node:", len(P.constraints), "iteration number", iterations, "frontier size", len(open_set))
        print("Length of path:", len(P.paths[0]))
        C = None

        for path in P.paths:
            C = validate(path, P.paths) # Consistent path needs to be valid
            if C is not None:   # Found conflict, path invalid, non goal node
                break

        if not C:
            print(P.plans)
            print("Found solution")
            print("Plans:", P.plans)
            if len(P.plans) == 1:
                print("Single agent")
                solution = P.plans[0]
                is_single = True
            else:
                print("Multi agent")
                agents_to_rest(P.plans)
                solution = [x for x in zip(*P.plans)]
                print(solution)
            return solution, is_single  # Found solution, return solution in joint action normal form

        for i, agent_i in enumerate(C.agents):
            A = copy.deepcopy(P)
            A.agent = agent_i
            if isinstance(C, EdgeConflict):
                if i == 1:
                    A.constraints.append(EdgeConstraint(agent_i, C.v, C.v1, C.t))
                    # print("appended constraint for agent", agent_i, "parameters (loc_from, loc_to, time):", C.v, C.v1, C.t)
                else:
                    A.constraints.append(EdgeConstraint(agent_i, C.v1, C.v, C.t))
                    # print("appended constraint for agent", agent_i, "parameters (loc_from, loc_to, time):", C.v1, C.v, C.t)
            elif not isinstance(C, EdgeConflict):
                A.constraints.append(Constraint(agent_i, C.v, C.t))
                # print("appended constraint for agent", agent_i, "parameters (loc, time):", C.v, C.t)
            plan_i, path_i = A.get_single_search(agent_i)
            plan_i = plan_i[0]
            path_i = path_i[0]
            A.plans[int(agent_i)] = plan_i
            A.paths[int(agent_i)] = path_i
            A.cost = sum([len(plan) for plan in A.plans]) + int(agent_i)
            # print("Cost for agent", agent_i, ":", A.cost)
            # print("Adding node to set")
            open_set.add(A)

    return None