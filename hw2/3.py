import numpy as np
import matplotlib.pyplot as plt
import pdb

np.random.seed(0)

class StateSpace():
    def __init__(self, time_limit):
        # absorbing and time_limit states act the same, but they are generated by two distinct processes
        self.state_idx_to_code = {
            0: "empty",
            1: "start",
            2: "goal",
            3: "absorb",
            4: "time_limit"
        }
        self.state_code_to_idx = {v: k for k, v in self.state_idx_to_code.items()}

        self.action_idx_to_code = {
            0: "N",
            1: "E",
            2: "S",
            3: "W",
            4: "P"
        }
        self.action_code_to_idx = {v: k for k, v in self.action_idx_to_code.items()}
        self.A = [k for k in self.action_idx_to_code]

        self.time_limit = time_limit
        self.S, self.start_state, self.end_state = self.generate_state_space(self.time_limit, self.state_code_to_idx)

        # generate maps for all 6 time steps
        self.state_space_list = []
        for i in range(1, self.time_limit+1):
            state_space_tmp = self.generate_time_limit_states(self.S.copy(), i, self.state_code_to_idx)
            self.state_space_list.append(state_space_tmp)

        self.problem_3(self.start_state, self.end_state, self.time_limit, self.action_code_to_idx)

    def generate_state_space(self, time_limit, state_code_to_idx):
        # make state space bigger than it needs to be
        ##  make sure it is odd in size so there is a well-defined middle for the goal to be
        state_space = np.zeros((2*time_limit + 3, 2*time_limit + 3))

        # state space reference frame starts at the top left of the time limited state space
        # place goal at the center of the "time limited" state space
        goal_pos_x = int(np.floor(len(state_space) / 2))
        goal_pos_y = goal_pos_x
        state_space[goal_pos_x, goal_pos_y] = state_code_to_idx["goal"]
        end_state = np.array([goal_pos_y, goal_pos_x,])

        # place starting state
        start_pos_x = goal_pos_x + 3
        start_pos_y = goal_pos_y + 3
        state_space[start_pos_x, start_pos_y] = state_code_to_idx["start"]
        start_state = np.array([start_pos_y, start_pos_x,])

        # place absorbing states
        absorbing_states_x = [goal_pos_x, goal_pos_x, goal_pos_x + 1, goal_pos_x + 1]
        absorbing_states_y = [goal_pos_y + 2, goal_pos_y + 3, goal_pos_y + 2, goal_pos_y + 3]

        for i in range(len(absorbing_states_x)):
            state_space[absorbing_states_y[i], absorbing_states_x[i]] = state_code_to_idx["absorb"]

        # place time_limit states
        ## introduce a distance from the goal to enforce the time limit constraint
        state_space = self.generate_time_limit_states(state_space, time_limit, state_code_to_idx)
        return state_space, start_state, end_state


    def generate_time_limit_states(self, state_space, remaining_time, state_code_to_idx):
        # everything outside a (time_limit x time_limit) square centered around the goal is an absorbing state
        goal_pos = np.where(state_space == state_code_to_idx["goal"])
        goal_pos = [goal_pos[0].item(), goal_pos[1].item()]
        time_limit_x_minus = goal_pos[0] - remaining_time
        time_limit_x_plus = goal_pos[0] + remaining_time
        time_limit_y_minus = goal_pos[0] - remaining_time
        time_limit_y_plus = goal_pos[0] + remaining_time

        for i in range(len(state_space)):
            if (i < time_limit_x_minus) or (i > time_limit_x_plus):
                state_space[i, :] = state_code_to_idx["time_limit"]

        for i in range(len(state_space)):
            if (i < time_limit_y_minus) or (i > time_limit_y_plus):
                state_space[:, i] = state_code_to_idx["time_limit"]

        return state_space


    def act(self, state, action, flag=0):
        # flag == 1: go "left"
        # flag == 2: go "right"

        # go north
        if action == 0:
            next_state = state - np.array([0, 1]).T
            if flag == 1:
                # go west
                next_state = next_state - np.array([1, 0]).T
            if flag == 2:
                # go east
                next_state = next_state + np.array([1, 0]).T

        # go east
        elif action == 1:
            next_state = state + np.array([1, 0]).T
            if flag == 1:
                # go north
                next_state = next_state - np.array([0, 1]).T
            if flag == 2:
                # go south
                next_state = next_state + np.array([0, 1]).T

        # go south
        elif action == 2:
            next_state = state + np.array([0, 1]).T
            if flag == 1:
                # go east
                next_state = next_state + np.array([1, 0]).T
            if flag == 2:
                # go west
                next_state = next_state - np.array([1, 0]).T

        # go west
        elif action == 3:
            next_state = state - np.array([1, 0]).T
            if flag == 1:
                # go south
                next_state = next_state + np.array([0, 1]).T
            if flag == 2:
                # go north
                next_state = next_state - np.array([0, 1]).T

        # do nothing
        elif action == 4:
            next_state = state

        return next_state


    def transition(self, state, action, curr_state_space):
        #TODO this might be transposed or something
        ## i was using the left-right direction of the arrays as the x-direction sometimes, and forgot that's not how you index arrays (first number = row = "y-coordinate", second number = column = "x-coordinate")

        # define absorbing state transitions s.t. you can't move from these states
        possible_states = []
        state_probabilities = []

        if (curr_state_space[state[0], state[1]] == self.state_code_to_idx["absorb"]) or (curr_state_space[state[0], state[1]] == self.state_code_to_idx["time_limit"]):
            possible_states.append(state)
            state_probabilities.append(1.0)

        # define all other normal state transition probabilities
        else:
            if action == 4:
                possible_states.append(state)
                state_probabilities.append(1.0)

            else:
                # 90% probability regular action
                next_state = self.act(state, action)
                possible_states.append(next_state)
                state_probabilities.append(0.9)

                # 5% probability action + "left"
                left_state = self.act(state, action, flag=1)
                possible_states.append(left_state)
                state_probabilities.append(0.05)

                # 5% probability action + "right"
                right_state = self.act(state, action, flag=2)
                possible_states.append(right_state)
                state_probabilities.append(0.05)

        state_probabilities = np.array(state_probabilities)
        return possible_states, state_probabilities


    def is_state_already_considered(self, curr_state, valid_states):
        return next((True for state in valid_states if np.array_equal(state, curr_state)), False)


    def get_neighbors(self, valid_states, curr_state_space, action_space):
        # valid_states = list of coordinates that we're looking for neighbors for
        # action_space = list of all possible actions (not including "actions" caused by stochastic environment transitions)
        # all_possibilities = bool, if true, samples all possible "actions" including stochastic environment transitions to enumerate all possible neighboring states

        new_states = []
        for curr_state in valid_states:
            # try all possible actions and see if they're valid to build a list of candidate states to add to the valid_states list in the next iteration
            for curr_action in action_space:
                next_possible_states, _ = self.transition(curr_state, curr_action, curr_state_space)

                for next_possible_state in next_possible_states:
                    if (next_possible_state is not None) and (not self.is_state_already_considered(next_possible_state, valid_states)) and (not self.is_state_already_considered(next_possible_state, new_states)):
                        new_states.append(next_possible_state)

        if len(new_states) == 0:
            return valid_states
        else:
            return valid_states + new_states


    def dynamic_programming(self, end_state, time_limit):
        # implements dynamic programming to compute reachability probabilities at time t around end_state wtihin time_limit time steps
        ## t counts backwards, since we start at 0 at the end state, and work backwards in time to the states where we could actually start

        # set R_{end_state}^0 (set by constraint of the ending state)
        R_curr = np.zeros([len(self.S), len(self.S)])
        policy = np.chararray((R_curr.shape))
        policy[:] = "X"

        R_out = np.zeros((time_limit, R_curr.shape[0], R_curr.shape[1]))
        policy_out = np.chararray((R_out.shape))

        # probability of reaching end_state starting in end_state
        R_curr[end_state[0], end_state[1]] = 1.0
        # placeholder action for the last timestep
        policy[end_state[0], end_state[1]] = "P"

        R_out[-1] = R_curr
        policy_out[-1] = policy

        # list of all possible states we could be in while respecting limited time horizon
        valid_states = [end_state]

        for t in range(0, time_limit):
            curr_state_space = self.state_space_list[t]

            # get all possible states the agent could have transitioned from in the previous timestep
            valid_states = self.get_neighbors(valid_states, curr_state_space, self.A)

            # R_curr = max_a \sum_{k} P(s^i, a, s^k) R_{kj}
            R_update = np.zeros(R_curr.shape)
            policy = np.chararray((R_curr.shape))
            policy[:] = "X"

            for state in valid_states:
                # since it's an infinite grid, all actions are always valid. Some of them just lead to absorbing states
                valid_actions = self.A
                action_reaching_probability = np.zeros(len(valid_actions))

                for i, action in enumerate(valid_actions):
                    possible_next_states, transition_probabilities = self.transition(state, action, curr_state_space)
                    action_reaching_probability_sum = 0

                    # sum_k P(s^i, a, s^j) R_{kj}
                    for j in range(len(possible_next_states)):
                        possible_next_state = possible_next_states[j]
                        transition_probability = transition_probabilities[j]
                        action_reaching_probability_sum += transition_probability * R_curr[possible_next_state[0], possible_next_state[1]]
                    action_reaching_probability[i] = action_reaching_probability_sum

                max_reaching_probability = np.max(action_reaching_probability)
                action_idx = np.argmax(action_reaching_probability)

                optimal_action = self.action_idx_to_code[valid_actions[action_idx]]
                R_update[state[0], state[1]] = max_reaching_probability
                policy[state[0], state[1]] = optimal_action

            R_curr = R_update
            R_out[-t-1] = R_curr
            policy_out[-t-1] = policy
        return R_out, policy_out


    def find_optimal_path(self, start_state, policy, time_limit, action_code_to_idx):
        path = [start_state]
        actions = []
        actions_str = []

        curr_state = start_state
        for i in range(time_limit):
            action = self.action_code_to_idx[policy[i, curr_state[0], curr_state[1]].decode("utf-8")]
            curr_state = self.act(curr_state, action)
            actions.append(action)
            actions_str.append(self.action_idx_to_code[action])
            path.append(curr_state)

        return path, actions, actions_str


    def problem_3(self, start_state, end_state, time_limit, action_code_to_idx):
        R, policy = self.dynamic_programming(end_state, time_limit)
        path, actions, actions_str = self.find_optimal_path(start_state, policy, time_limit, action_code_to_idx)
        print("States Visited:", path)
        print("Actions Taken:", actions_str)
        print("\n\n")
        # for i in range(len(policy)):
        #     policy_curr = policy[i]
        #     for j in range(len(policy_curr)):
        #         print(policy_curr[:, j])
        # pdb.set_trace()

def main():
    time_limit = 6
    state_space = StateSpace(time_limit)


if __name__ == "__main__":
    main()

