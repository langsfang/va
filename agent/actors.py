from context_state import ContextState
from gym_sts.spaces.observations import Observation
from model import LLMModel
from utils import wrapper
from prompts.combat import COMBAT_PROMPT
import json
import re

BIN = "/Users/lancefang/work/va/3rd/sts_lightspeed/build/battle-sim"
class CombatActor:
    def __init__(self, state: ContextState, log_dir: str):
        self.log_dir = log_dir
        self.type = "MCTS" # or LLM
        self.value = 0.9

    def get_action(self, obs: Observation, ctx: dict, room_num, room_step):
        # first if hard run, check to use potion or not
        # FIXME here
        # then use mcts
        actsobj = self.get_action_mcts(obs, room_num, room_step)
        score = actsobj.get("score")

        if score > self.value: # use the search result
            self.type = "MCTS"
            acts = actsobj.get("actions")
            next_act = None
            if len(acts) > 1 and acts[1].startswith("choose"):
                match = re.search(r'\((.*?)\)', acts[1])
                if match:
                    cardname = match.group(1).lower()
                    next_act = f"next_turn_choose {cardname}"

            return acts[0], next_act

        # now we need to use LLM
        return self.get_action_llm(obs, ctx, room_num, room_step)

    def extract_action(self, resp: str) -> str:
        target_key = "FinalAction"

        data = None

        start_index = resp.find(target_key)
        if start_index == -1:
            return ""
        colon_index = resp.find(":", start_index)
        if colon_index == -1:
            return ""
        
        potential_json_str = resp[colon_index + 1:].strip()
        
        try:
            decoder = json.JSONDecoder()
            data, end_pos = decoder.raw_decode(potential_json_str)
        except json.JSONDecodeError as e:
            print(f"解析 JSON 失败: {e}")
            return ""

        if not data:
            return ""

        action = data.get("action")
        if action == "play":
            idx = data.get("index")
            target = data.get("target_id")
            ret = f"{action} {idx}"
            if target is not None:
                ret += f" {target}"
        elif action == "potion":
            use = data.get("type")
            slot = data.get("potion_slot")
            target = data.get("target_id")
            ret = f"{action} {use} {slot}"
            if target is not None:
                ret += f" {target}"
        elif action == "end":
            ret = "end"
        elif action == "choose":
            idx = data.get("id")
            if idx is not None:
                ret = f"{action} {idx}"
            else:
                ret = f"{action}"

        return ret

    def get_action_llm(self, obs: Observation, ctx: dict, room_num, room_step):
        self.type = "LLM"
        sys = COMBAT_PROMPT
        user = json.dumps(ctx)

        llm = LLMModel()
        messages = [
            {"role": "system", "content": sys},
            {"role": "user", "content": user}
        ]

        # dump prompt to debug
        with open(f"{self.log_dir}/{room_num}-{room_step}-COMBAT", "w") as fn:
            for msg in messages:
                fn.write(f"----{msg.get('role')}---\n")
                fn.write(msg.get("content"))

        answer = llm.llm_stream(messages)

        act = self.extract_action(answer)
        print(act)

        return act, None

    def get_action_mcts(self, obs: Observation, room_num, room_step):
        state_file = f"{self.log_dir}/{room_num}-{room_step}.json"
        with open(state_file, "w") as f:
            f.write(json.dumps(obs.state))
        acts_str = wrapper(BIN, state_file)
        print("search:", acts_str)
        actsobj = json.loads(acts_str)
        return actsobj

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
