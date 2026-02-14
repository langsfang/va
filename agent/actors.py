from context_state import ContextState
from gym_sts.spaces.observations import Observation
from utils import wrapper
import json
import re

BIN = "/Users/lancefang/work/va/3rd/sts_lightspeed/build/battle-sim"
class CombatActor:
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

from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
THIRD = ROOT / "3rd" / "bottled_ai"
sys.path.insert(0, str(THIRD))

from rs.game.map import Map
from rs.game.path import PathHandlerConfig
from rs.machine.state import GameState
from rs.machine.the_bots_memory_book import TheBotsMemoryBook

class MapActor:
    def __init__(self, obs: dict):
        raw_map = obs.get("game_state").get("map")
        floor = obs.get("game_state").get("floor")
        n = obs.get("game_state").get("screen_state").get("current_node")
        current_position = str(n["x"]) + "_" + str(n["y"])
        self.map = Map(raw_map, current_position, floor)

        config = PathHandlerConfig(
            hallway_fight_base_reward=1,
            hallway_fight_prayer_wheel=0.3,
            hallway_question_card_reward=0.15,
            hallway_fight_gold=15,
            hallway_fight_health_loss=lambda state: state.game_state()['act'] * 5,
            elite_base_reward=1,  # this does not include the relic, that's added separately
            elite_question_card_reward=0.15,
            elite_fight_gold=30,
            elite_fight_health_loss=lambda state: (state.game_state()['act'] + 1) * 15,
            relic_reward=1.5,
            curse_reward_loss=1.5,
            upgrade_reward=1.1,
            event_value_reward=lambda state: 1 if state.game_state()['act'] == 1 else 1.5,
            gold_at_shop_reward=lambda state, gold_to_spend: gold_to_spend / 100,
            gold_after_boss_reward=lambda state: state.game_state()['gold'] / 200,
            survivability_reward_calculation=lambda reward, survivability: reward + (survivability - 1) * 15,
        )

        self.state = GameState(obs, TheBotsMemoryBook())
        # Sort the paths by our priorities
        self.map.sort_paths_by_reward_to_survivability(self.state, config)

    def get_path_info(self):
        paths = self.map.show_path()
        return paths

    def get_action(self, path_idx: int):
        #return "choose " + str(self.map.get_path_choice_from_path_idx(path_idx, self.state.get_choice_list()))
        return "choose " + str(self.map.get_path_choice_from_choices(self.state.get_choice_list()))
