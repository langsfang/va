from context_state import ContextState
from gym_sts.spaces.observations import Observation
from utils import wrapper
import json

BIN = "/Users/lancefang/work/va/3rd/sts_lightspeed/build/battle-sim"
class Actor:
    def __init__(self, state: ContextState):
        pass

    def get_action(self, obs: Observation):
        state_file = "out/combat.json"
        with open(state_file, "w") as f:
            f.write(json.dumps(obs.state))
        acts_str = wrapper(BIN, state_file)
        actsobj = json.loads(acts_str)
        acts = actsobj.get("actions")
        print(acts[0])
        return acts[0]
