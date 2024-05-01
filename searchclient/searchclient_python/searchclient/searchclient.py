import argparse
import io
import sys
import time
import cProfile
import memory
from color import Color
from state import State, Constraint
from frontier import FrontierBFS, FrontierDFS, FrontierBestFirst, FrontierBestFirstWidth
from heuristic import HeuristicAStar, HeuristicWeightedAStar, HeuristicGreedy, HeuristicBFWS
from graphsearch import search

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

        print(teams)            # example = [('red', '0, A'), ('green', '1, B')]

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
            initial_states.append(State(agent_rows, agent_cols, boxes, goals, team_constraints))
            # print("end loop for team", team, flush=True)
            # print("agent at", agent_rows, agent_cols)
            # print("box position", boxes)
            # print("goal position", goals)

        return initial_states
    
    ''' Function for single-agent levels '''

    @staticmethod
    def parse_level(server_messages) -> 'State':

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
        while not line.startswith('#'):
            split = line.split(':')
            color = Color.from_string(split[0].strip()) 
            entities = [e.strip() for e in split[1].split(',')]
            for e in entities:
                if '0' <= e <= '9':
                    agent_colors[ord(e) - ord('0')] = color
                elif 'A' <= e <= 'Z':
                    box_colors[ord(e) - ord('A')] = color
            line = server_messages.readline()
        

        # Read initial state.
        # line is currently "#initial".
        num_rows = 0
        num_cols = 0
        level_lines = []
        line = server_messages.readline()
        while not line.startswith('#'):
            level_lines.append(line)
            num_cols = max(num_cols, len(line))
            num_rows += 1
            line = server_messages.readline()

        num_agents = 0
        agent_rows = [None for _ in range(10)]
        agent_cols = [None for _ in range(10)]
        walls = [[False for _ in range(num_cols)] for _ in range(num_rows)]
        boxes = [['' for _ in range(num_cols)] for _ in range(num_rows)]
        row = 0
        for line in level_lines:
            for col, c in enumerate(line):
                if '0' <= c <= '9':
                    agent_rows[ord(c) - ord('0')] = row
                    agent_cols[ord(c) - ord('0')] = col
                    num_agents += 1
                elif 'A' <= c <= 'Z':
                    boxes[row][col] = c
                elif c == '+':
                    walls[row][col] = True
            
            row += 1
        del agent_rows[num_agents:]
        del agent_rows[num_agents:]
        
        # Read goal state.
        # line is currently "#goal".
        goals = [['' for _ in range(num_cols)] for _ in range(num_rows)]
        line = server_messages.readline()
        row = 0
        while not line.startswith('#'):
            for col, c in enumerate(line):
                if '0' <= c <= '9' or 'A' <= c <= 'Z':
                    goals[row][col] = c
            
            row += 1
            line = server_messages.readline()
        
        # End.
        # line is currently "#end".
        
        State.agent_colors = agent_colors
        State.walls = walls
        State.box_colors = box_colors

        return State(agent_rows, agent_cols, boxes, goals)
    
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


        # Select search strategy.
        

        plans = []
        for num, initial_state in enumerate(initial_states):

            frontier = None
            if args.bfs:
                frontier = FrontierBFS()
            elif args.dfs:
                frontier = FrontierDFS()
            elif args.astar:
                frontier = FrontierBestFirst(HeuristicAStar(initial_state))
            elif args.wastar:
                frontier = FrontierBestFirst(HeuristicWeightedAStar(initial_state, args.wastar))
            elif args.greedy:
                frontier = FrontierBestFirst(HeuristicGreedy(initial_state))
            elif args.bfws:
                frontier = FrontierBestFirstWidth(HeuristicBFWS(initial_state))
            else:
                # Default to BFS search.
                frontier = FrontierBFS()
                print('Defaulting to BFS search. Use arguments -bfs, -dfs, -astar, -wastar, or -greedy to set the search strategy.', file=sys.stderr, flush=True)            
            plan, plan_repr = search(initial_state, frontier)
            plans.append(plan) 
            print("Ended search for initial state number", num)
            print()
            print("Plan extracted:")
            print(plan_repr)
            print()
        

        # Search for a plan.
        # print('Starting {}.'.format(frontier.get_name()), file=sys.stderr, flush=True)
        # plan = search(initial_state, frontier)

        ''' Here we should fed the plans to a conflict manager '''

        # Print plan to server.
        # if plan is None:
        #     print('Unable to solve level.', file=sys.stderr, flush=True)
        #     sys.exit(0)
        # else:
        #     print('Found solution of length {}.'.format(len(plan)), file=sys.stderr, flush=True)
            
        #     for joint_action in plan:
        #         print("|".join(a.name_ for a in joint_action), flush=True)
        #         # We must read the server's response to not fill up the stdin buffer and block the server.
        #         response = server_messages.readline()

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
    
    args = parser.parse_args()
    
    # Set max memory usage allowed (soft limit).
    memory.max_usage = args.max_memory
    
    # Run client.
    SearchClient.main(args)
