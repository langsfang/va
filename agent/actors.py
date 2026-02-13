from context_state import ContextState
from gym_sts.spaces.observations import Observation
from utils import wrapper
import json
import re

BIN = "/Users/lancefang/work/va/3rd/sts_lightspeed/build/battle-sim"
class Actor:
    def __init__(self, state: ContextState, log_dir: str):
        self.log_dir = log_dir

    def get_action(self, obs: Observation, room_num, room_step):
        state_file = f"{self.log_dir}/{room_num}-{room_step}.json"
        with open(state_file, "w") as f:
            f.write(json.dumps(obs.state))
        acts_str = wrapper(BIN, state_file)
        print("search:", acts_str)
        actsobj = json.loads(acts_str)
        acts = actsobj.get("actions")
        next_act = None
        if len(acts) > 1 and acts[1].startswith("choose"):
            match = re.search(r'\((.*?)\)', acts[1])
            if match:
                cardname = match.group(1).lower()
                next_act = f"next_turn_choose {cardname}"

        return acts[0], next_act
