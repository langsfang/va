from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
THIRD = ROOT / "3rd" / "gym-sts"
sys.path.insert(0, str(THIRD))

import time
import argparse
from gym_sts.envs.base import SlayTheSpireGymEnv
from gym_sts.spaces.observations import ObservationError

from llm_agent import LLMAgent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("lib_dir")
    parser.add_argument("mods_dir")
    parser.add_argument("out_dir")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--build_image", action="store_true")
    args = parser.parse_args()

    agent = LLMAgent()

    env = SlayTheSpireGymEnv(
        args.lib_dir, args.mods_dir, args.out_dir, headless=args.headless,
        character= agent.character, ascension=agent.ascension, sts_seed = "0"
    )
    observation = env.reset()

    action = "choose 0" # click start
    while True:
        observation = env._do_action(action)

        time.sleep(1)
        observation = env._do_action("state")
        # print(observation.state)

        action = agent.get_action(observation)

        act = input("Enter an action: ")

        try:
            commands = observation._available_commands
            print("AVAILABLE COMMANDS:")
            print(commands)
        except ObservationError as e:
            print("ERROR")
            print(e)

if __name__ == "__main__":
    main()
