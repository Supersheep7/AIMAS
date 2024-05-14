from utils import match_length

''' Defining Conflicts '''

class Conflict:
    def __init__(self, ai, aj, v, t):
        self.ai = ai
        self.aj = aj
        self.v = v
        self.t = t
        self.agents = [ai, aj]

    def __eq__(self, other):
        return isinstance(other, Conflict) and \
               self.ai == other.ai and self.aj == other.aj and \
               self.v == other.v and self.t == other.t

    def __hash__(self):
        return hash((self.ai, self.aj, self.v, self.t))
    
class AgentFollowConflict:
    def __init__(self, ai, aj, v, t):
        self.ai = ai
        self.aj = aj
        self.v = v
        self.t = t
        self.agents = [ai, aj]

    def __eq__(self, other):
        return isinstance(other, AgentFollowConflict) and \
               self.ai == other.ai and self.aj == other.aj and \
               self.v == other.v and self.t == other.t

    def __hash__(self):
        return hash((self.ai, self.aj, self.v, self.t))
    
class AgentBoxFollowConflict:
    def __init__(self, ai, aj, box, v, t,follower):
        self.ai = ai
        self.aj = aj
        self.box = box
        self.v = v
        self.t = t
        self.agents = [ai, aj]
        self.follower = follower
    
    def __eq__(self, other):
        return isinstance(other, AgentBoxFollowConflict) and \
               self.ai == other.ai and self.aj == other.aj and \
               self.box == other.box and self.v == other.v and self.t == other.t
    def __hash__(self):
        return hash((self.ai, self.aj, self.box, self.v, self.t))
    
class BoxBoxFollowConflict:
    def __init__(self, ai, aj, box_i, box_j, v, t):
        self.ai = ai
        self.aj = aj
        self.box = [box_i, box_j]
        self.v = v
        self.t = t
        self.agents = [ai, aj]
    
    def __eq__(self, other):
        return isinstance(other, BoxBoxFollowConflict) and \
               self.ai == other.ai and self.aj == other.aj and \
               self.box == other.box and self.v == other.v and self.t == other.t
    def __hash__(self):
        return hash((self.ai, self.aj, self.box, self.v, self.t))
    
class BoxConflict:
    def __init__(self, agent_i,agent_j, box_i,box_j, loc_to, time):
        self.agents = [agent_i, agent_j]
        self.box = [box_i, box_j]
        self.loc_to = loc_to
        self.time = time

    def __eq__(self, other):
        return isinstance(other, BoxConflict) and \
               self.agents == other.agents and self.box == other.box and \
               self.loc_to == other.loc_to and self.time == other.time

    def __hash__(self):
        return hash((self.agents, self.box, self.loc_to, self.time))
    
class mixedConflict:
    def __init__(self, ai, aj, box, v, t):
        self.ai = ai
        self.aj = aj
        self.box = box
        self.v = v
        self.t = t
        self.agents = [ai, aj]

    def __eq__(self, other):
        return isinstance(other, mixedConflict) and \
               self.ai == other.ai and self.aj == other.aj and \
               self.box == other.box and self.v == other.v and self.t == other.t

    def __hash__(self):
        return hash((self.ai, self.aj, self.box, self.v, self.t))
    
class whatConflict:
    def __init__(self, ai, aj, box, loc_from, loc_to, t):
        self.ai = ai
        self.aj = aj
        self.box = box
        self.loc_from = loc_from
        self.loc_to = loc_to
        self.t = t
    
''' Defining Constraints '''

class Constraint:
    def __init__(self, agent, loc_to, time):
        self.agent = agent
        self.loc_to = loc_to
        self.time = time

    def __eq__(self, other):
        return isinstance(other, Constraint) and \
               self.agent == other.agent and self.loc_to == other.loc_to and self.time == other.time

    def __hash__(self):
        return hash((self.agent, self.loc_to, self.time))
    
class BoxConstraint:
    def __init__(self, agent, box, loc_to, time):
        self.agent = agent
        self.box = box
        self.loc_to = loc_to
        self.time = time

    def __eq__(self, other):
        return isinstance(other, BoxConstraint) and \
               self.agent == other.agent and self.box == other.box and \
               self.loc_to == other.loc_to and self.time == other.time

    def __hash__(self):
        return hash((self.agent, self.box, self.loc_to, self.time))

''' Utils '''

# Used in here in the validation functions

# Experimental feature

def big_validation(node):

    plan_list = node.paths
    priority = {}

    for plan, worker in zip(plan_list, node.workers):

        count = 0

        for other_plan, other_worker in zip(plan_list, node.workers):
            if plan == other_plan:
                continue 
            plan_copy, other_plan = match_length(plan, other_plan)
            for j in range(1, len(plan)):
                agent_state_current = plan_copy[j][0][1]

                other_agent_state_current = other_plan[j][0][1]

                other_agent_state_previous = other_plan[j - 1][0][1]
                t=j

                box_states_current = [state[1] for state in plan_copy[j][1:] if len(state) > 1]
                box_states_current = [state[1] for state in plan_copy[j][1:] if len(state) > 1]
                other_box_states_previous = [state[1] for state in other_plan[j - 1][1:] if len(state) > 1]
                other_box_states_current = [state[1] for state in other_plan[j][1:] if len(state) > 1]
                
                if agent_state_current == other_agent_state_current:
                    count += 1

                # Follow conflict
                if agent_state_current == other_agent_state_previous:
                    count +=1
                
                # Box going into other Box
                for idx, box_current in enumerate(box_states_current):
                    count +=1

                #Agent going into other box
                for idx, other_box_current in enumerate(other_box_states_current):
                    if agent_state_current == other_box_current:
                        count +=1
                
                #Box going into other agent
                for idx, box_current in enumerate(box_states_current):
                    if box_current == other_agent_state_current:
                        count +=1
                
                # Agent to Box Following

                for idx, other_box_current in enumerate(other_box_states_previous):
                    if agent_state_current == other_box_current:
                        count +=1
                
                # Box to Box following
                for idx, box_current in enumerate(box_states_current):
                    for other_idx, other_box_current in enumerate(other_box_states_previous):
                        count +=1
                #Box to agent following
                for idx, box_current in enumerate(box_states_current):
                    if box_current == other_agent_state_previous:
                        count +=1
        
        priority[worker] = count

    return priority

# Used in CBS line 109 - > C = validate(path, P.paths)

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

    agent_i_full = plan[0][0][0]  # Something like 'AgentAt0'
    agent_i = int(agent_i_full.split('AgentAt')[-1])
    other_plans = [lst for lst in plan_list if lst is not plan]
    for other_plan in other_plans:
        if other_plan == [] or other_plan == []:
            continue
        agent_j_full = other_plan[0][0][0]
        agent_j = int(agent_j_full.split('AgentAt')[-1])
        # Ensure both plans are of equal length
        plan_copy, other_plan = match_length(plan, other_plan)
        for j in range(1, len(plan)):
            # Get current and previous states for both plans
            agent_state_current = plan_copy[j][0][1]

            other_agent_state_current = other_plan[j][0][1]

            other_agent_state_previous = other_plan[j - 1][0][1]
            t=j

            box_states_current = [state[1] for state in plan_copy[j][1:] if len(state) > 1]
            box_names_current = [state[0].split('BoxAt')[-1] for state in plan_copy[j][1:] if len(state) > 1]
            box_states_current = [state[1] for state in plan_copy[j][1:] if len(state) > 1]
            box_names_current = [state[0].split('BoxAt')[-1] for state in plan_copy[j][1:] if len(state) > 1]
            other_box_states_previous = [state[1] for state in other_plan[j - 1][1:] if len(state) > 1]
            other_box_states_current = [state[1] for state in other_plan[j][1:] if len(state) > 1]
            other_box_names_current = [state[0].split('BoxAt')[-1] for state in other_plan[j][1:] if len(state) > 1]

            # Agent going into other agent
            if agent_state_current == other_agent_state_current:
                conflict = Conflict(agent_i, agent_j, agent_state_current, t)
                return conflict

            # Follow conflict
            if agent_state_current == other_agent_state_previous:
                conflict = AgentFollowConflict(agent_i, agent_j, agent_state_current, t)
                return conflict
                    
            #Agent going into other box
            for idx, other_box_current in enumerate(other_box_states_current):
                if agent_state_current == other_box_current:
                    conflict = mixedConflict(agent_i, agent_j, other_box_names_current[idx], other_box_current, t)
                    return conflict
            
            # Box going into other agent
            for idx, box_current in enumerate(box_states_current):
                if box_current == other_agent_state_current:
                    conflict = mixedConflict(agent_j, agent_i,box_names_current[idx], box_current, t)
                    return conflict
            
            # Agent to Box Following
            for idx, other_box_current in enumerate(other_box_states_previous):
                if agent_state_current == other_box_current:
                    conflict = AgentBoxFollowConflict(agent_i, agent_j, other_box_names_current[idx],  agent_state_current, t,0)
                    return conflict

            # Box to Box following
            for idx, box_current in enumerate(box_states_current):
                for other_idx, other_box_current in enumerate(other_box_states_previous):
                    if box_current == other_box_current:
                        return BoxBoxFollowConflict(agent_i, agent_j, box_names_current[idx], other_box_names_current[other_idx], box_current, t)
           
            #Box to agent following
            for idx, box_current in enumerate(box_states_current):
                if box_current == other_agent_state_previous:
                    return AgentBoxFollowConflict(agent_j, agent_i, box_names_current[idx], box_current, t,1)

            # Box going into other Box
            for idx, box_current in enumerate(box_states_current):
                for other_idx, other_box_current in enumerate(other_box_states_current):
                    if box_current == other_box_current:
                        conflict = BoxConflict(agent_i, agent_j, box_names_current[idx], other_box_names_current[other_idx], box_current, t)
                        return conflict
    return None    

# Used in CBS line 136 - > A = add_constraint(C, A, agent_i)

def add_constraint(conflict, node, agent):

    if isinstance(conflict, Conflict):
        node.constraints.append(Constraint(agent, conflict.v, conflict.t))

    elif isinstance(conflict, mixedConflict): 
        if node.agent == conflict.agents[0]:
            node.constraints.append(Constraint(agent, conflict.v, conflict.t))                    
        elif node.agent == conflict.agents[1]:
            node.constraints.append(BoxConstraint(agent, conflict.box, conflict.v, conflict.t))  

    elif isinstance(conflict, BoxConflict):
        if node.agent == conflict.agents[0]:
            node.constraints.append(BoxConstraint(agent,conflict.box[0], conflict.loc_to, conflict.time))
        elif node.agent == conflict.agents[1]:
            node.constraints.append(BoxConstraint(agent,conflict.box[1], conflict.loc_to, conflict.time))

    elif isinstance(conflict, AgentFollowConflict):
        if node.agent == conflict.agents[0]:
            node.constraints.append(Constraint(agent, conflict.v, conflict.t))
        elif node.agent == conflict.agents[1]:
            if conflict.t == 1:
                return None
            node.constraints.append(Constraint(agent, conflict.v, conflict.t-1))

    elif isinstance(conflict, AgentBoxFollowConflict):
        if node.agent == conflict.agents[0]:
            if conflict.follower == 0:
                node.constraints.append(Constraint(agent, conflict.v, conflict.t))
            elif conflict.follower == 1:
                if conflict.t == 1:
                    return None
                node.constraints.append(Constraint(agent, conflict.v, conflict.t-1))
        elif node.agent == conflict.agents[1]:
            if conflict.follower == 0:
                if conflict.t == 1:
                    return None
                node.constraints.append(BoxConstraint(agent,conflict.box, conflict.v, conflict.t-1))
            elif conflict.follower == 1:
                node.constraints.append(BoxConstraint(agent, conflict.box, conflict.v, conflict.t))

    elif isinstance(conflict, BoxBoxFollowConflict):
        if node.agent == conflict.agents[0]:
            node.constraints.append(BoxConstraint(agent, conflict.box[0], conflict.v, conflict.t))
        elif node.agent == conflict.agents[1]:
            if conflict.t == 1:
                return None
            node.constraints.append(BoxConstraint(agent, conflict.box[1], conflict.v, conflict.t-1))

    return node