from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
THIRD = ROOT / "3rd" / "gym-sts"
sys.path.insert(0, str(THIRD))

import argparse
import json
import os

from llm_agent import LLMAgent
from remote_env import RemoteEnv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    parser.add_argument("log_dir")
    parser.add_argument("--character")
    parser.add_argument("--ascension", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--sts-seed")
    args = parser.parse_args()

    agent = LLMAgent(args.log_dir)
    env = RemoteEnv(args.host, args.port)
    obs_path = os.path.join(agent.log_dir, "obs.json")

    character = args.character or agent.character
    ascension = args.ascension if args.ascension is not None else agent.ascension

    observation = env.reset(
        seed=args.seed,
        character=character,
        ascension=ascension,
        sts_seed=args.sts_seed,
    )

    action = "state"
    while True:
        if action == "over":
            break

        observation = env._do_action(action)
        observation = env._do_action("state")

        with open(obs_path, "w") as json_file:
            json_file.write(json.dumps(observation.state, indent=4))

        action = agent.get_action(observation)
        print(f"playing {action}")


if __name__ == "__main__":
    main()
