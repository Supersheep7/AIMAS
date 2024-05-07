import argparse
import sys
import time
import memory
from color import Color
from state import State, Constraint
from cbs import CBS

def match_length(arr1, arr2):
    len_diff = abs(len(arr2) - len(arr1))
    if len(arr1) < len(arr2):
        last_value = arr1[-1]
        arr1 += [last_value] * len_diff
    elif len(arr2) < len(arr1):
        last_value = arr2[-1]
        arr2 += [last_value] * len_diff
    return arr1, arr2

class SearchClient:

    ''' We will use this function for multi-agent levels '''
    @staticmethod
    def parse_filtered_levels(server_messages) -> 'list': 
        # We can assume that the level file is conforming to specification, since the server verifies this.
        # Read domain.
        server_messages.readline() # #domain
        server_messages.readline() # hospital
        
        # Read Level name.
        server_messages.readline() # #levelname
        server_messages.readline() # <name>
        
        # Read colors.
        server_messages.readline() # #colors
        agent_colors = [None for _ in range(10)]
        box_colors = [None for _ in range(26)]
        line = server_messages.readline()
        teams = []
        while not line.startswith('#'):
            split = line.split(':')
            teams.append((split[0], split[1].strip()))
            color = Color.from_string(split[0].strip())
            entities = [e.strip() for e in split[1].split(',')]
            for e in entities:
                if '0' <= e <= '9':
                    agent_colors[ord(e) - ord('0')] = color
                elif 'A' <= e <= 'Z':
                    box_colors[ord(e) - ord('A')] = color
            line = server_messages.readline()


        ''' Now we need to store the server messages in level_lines and goal_level_lines '''

        initial_states = []

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
        #predefined_constraints = []
        predefined_constraints = [Constraint(agent='0', loc_from=[(1, 2)], loc_to=[(1, 2)], time=1), Constraint(agent='0', loc_from=[(1, 2)], loc_to=[(2, 2)], time=2)]
        intial_goal_line = server_messages.readline()
        goal_level_lines = []
        line = intial_goal_line
        
        while not line.startswith('#'):
            goal_level_lines.append(line)
            line = server_messages.readline()

        ''' Loop and build a different level representation for each color '''

        for team in teams:
            # Read initial state.
            # line is currently "#initial".
            team_constraints = []
            team_list = team[1].split(', ')
            agents_in_team = [x for x in team_list if x.isdigit()]
            boxes_in_team = [x for x in team_list if x.isalpha()]
            num_agents = 0
            for predefined_constraint in predefined_constraints:
                if predefined_constraint.agent in agents_in_team:
                    team_constraints.append(predefined_constraint)
            agent_rows = [None for _ in range(10)]
            agent_cols = [None for _ in range(10)]
            walls = [[False for _ in range(num_cols)] for _ in range(num_rows)]
            boxes = [['' for _ in range(num_cols)] for _ in range(num_rows)]
            row = 0
            for line in level_lines:
                for col, c in enumerate(line):
                    if c in agents_in_team:
                        agent_rows[ord(c) - ord('0')] = row
                        agent_cols[ord(c) - ord('0')] = col
                        num_agents += 1
                    elif c in boxes_in_team:
                        boxes[row][col] = c
                    elif c == '+':
                        walls[row][col] = True
                
                row += 1
            
            # Strip from None values
            agent_rows = [row for row in agent_rows if row is not None]
            agent_cols = [col for col in agent_cols if col is not None]
            
            # Read goal state.
            # line is currently "#goal".
            goals = [['' for _ in range(num_cols)] for _ in range(num_rows)]
            row = 0
            for line in goal_level_lines:
                for col, c in enumerate(line):
                    if c in agents_in_team or c in boxes_in_team:
                        goals[row][col] = c
                
                row += 1
            # End.
            # line is currently "#end".
            State.agent_colors = agent_colors
            State.walls = walls
            State.box_colors = box_colors
            initial_states.append(State(agent_rows, agent_cols, boxes, goals, agents_in_team, team_constraints))
        return initial_states
    
    @staticmethod
    def print_search_status(start_time: 'int', explored: '{State, ...}', frontier: 'Frontier') -> None:
        status_template = '#Expanded: {:8,}, #Frontier: {:8,}, #Generated: {:8,}, Time: {:3.3f} s\n[Alloc: {:4.2f} MB, MaxAlloc: {:4.2f} MB]'
        elapsed_time = time.perf_counter() - start_time
        print(status_template.format(len(explored), frontier.size(), len(explored) + frontier.size(), elapsed_time, memory.get_usage(), memory.max_usage), file=sys.stderr, flush=True)

    @staticmethod
    def main(args) -> None:
        # Use stderr to print to the console.
        print('SearchClient initializing. I am sending this using the error output stream.', file=sys.stderr, flush=True)
        
        # Send client name to server.
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding='ASCII')
        print('SearchClient', flush=True)
        
        # We can also print comments to stdout by prefixing with a #.
        print('#This is a comment.', flush=True)
        
        # Parse the level.
        server_messages = sys.stdin
        if hasattr(server_messages, "reconfigure"):
            server_messages.reconfigure(encoding='ASCII')
        
        initial_states = SearchClient.parse_filtered_levels(server_messages)
        #  initial_state = SearchClient.parse_level(server_messages)
        if args.cbs:
            joint_plan, is_single = CBS(initial_states) 

        # Print plan to server.
        if joint_plan is None:
            print('Unable to solve level.', file=sys.stderr, flush=True)
            sys.exit(0)
        else:
            print('Found solution of length {}.'.format(len(joint_plan)), file=sys.stderr, flush=True)
            
            for joint_action in joint_plan:
                if is_single:
                    print("|".join(a.name_ for a in joint_action), flush=True)
                else:
                    print("|".join(a[0].name_ for a in joint_action), flush=True)
                # We must read the server's response to not fill up the stdin buffer and block the server.
                response = server_messages.readline()

if __name__ == '__main__':
    # Program arguments.
    parser = argparse.ArgumentParser(description='Simple client based on state-space graph search.')
    parser.add_argument('--max-memory', metavar='<MB>', type=float, default=2048.0, help='The maximum memory usage allowed in MB (soft limit, default 2048).')
    
    strategy_group = parser.add_mutually_exclusive_group()
    strategy_group.add_argument('-bfs', action='store_true', dest='bfs', help='Use the BFS strategy.')
    strategy_group.add_argument('-dfs', action='store_true', dest='dfs', help='Use the DFS strategy.')
    strategy_group.add_argument('-astar', action='store_true', dest='astar', help='Use the A* strategy.')
    strategy_group.add_argument('-wastar', action='store', dest='wastar', nargs='?', type=int, default=False, const=5, help='Use the WA* strategy.')
    strategy_group.add_argument('-greedy', action='store_true', dest='greedy', help='Use the Greedy strategy.')
    strategy_group.add_argument('-bfws', action='store_true', dest='bfws', help='Use the BFWS strategy.')
    strategy_group.add_argument('-cbs', action='store_true', dest='cbs', help='Use the CBS strategy.')
    
    args = parser.parse_args()
    
    # Set max memory usage allowed (soft limit).
    memory.max_usage = args.max_memory
    
    # Run client.
    SearchClient.main(args)
