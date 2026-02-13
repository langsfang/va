from gym_sts.spaces.observations import Observation
import json
from context_state import ContextState
from logger import Logger
from prompts.event import EVENT_PROMPT
from prompts.reward import REWARD_PROMPT
from prompts.rest import REST_PROMPT
from prompts.shop import SHOP_PROMPT
from prompts.deck_eval import DECK_EVAL_PROMPT

from model import LLMModel
from map_feature import get_path_features
from actors import Actor
from utils import extract_json
from db import StSDB

class LLMAgent:
    def __init__(self, log_dir: str):
        self.actions = {
            "EVENT" : self._action_event,
            "MAP" : self._action_map,
            "COMBAT_REWARD" : self._action_reward,
            "CARD_REWARD" : self._action_card_reward,
            "REST" : self._action_rest,
            "SHOP_ROOM" : self._action_shop,
            "SHOP_SCREEN" : self._action_shop,
            "CHEST" : self._action_chest,
            "GRID" : self._action_grid_select,
            "HAND_SELECT" : self._action_hand_select,
            "GAME_OVER" : self._action_game_over,
            "NONE": self._action_combat,
        }

        self.prompts = {
            ContextState.EVENT : EVENT_PROMPT,
            ContextState.REWARD : REWARD_PROMPT,
            ContextState.REST : REST_PROMPT,
            ContextState.SHOP : SHOP_PROMPT,
        }
        import os
        cdir = os.getcwd()
        self.log_dir = f"{cdir}/{log_dir}"
        os.makedirs(self.log_dir, exist_ok=True)

        self.db = StSDB()

        self.hist = []

        self.state = ContextState.INVALID
        self.room_num = 0
        self.room_step = 0

        self.character = "IRONCLAD"
        self.ascension = 20

        self.logger = Logger(f"{self.log_dir}/log")

        self.skip_commands = ['key', 'click', 'wait', 'state']

        self.actor = None

        self.next_act = None

    def get_ctx(self) -> dict:
        return {
            "character": self.character,
            "ascension": self.ascension,
        }

    def is_replaying(self):
        return self.logger.need_replay()

    def get_action(self, obs: Observation):

        print(obs.screen_type)
        if obs.screen_type == "MAP":
            self.room_num += 1
            self.room_step = 0

        if self.logger.need_replay():
            return self.logger.replay()

        act = self.fast_action(obs) # no need for LLM
        if act:
            self.logger.add(act)
            return act

        act = self.actions.get(obs.screen_type)(obs)
    
        print("play:", act)
        self.logger.add(act)
        return act

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
        if action == "potion":
            use = data.get("type")
            slot = data.get("potion_slot")
            ret = f"{action} {use} {slot}"
        elif action == "skip":
            ret = "skip"
        else:
            idx = data.get("id")
            if idx is not None:
                ret = f"{action} {idx}"
            else:
                ret = f"{action}"

        return ret
    
    def deck_eval(self, ctx: dict) -> str:
        sys = DECK_EVAL_PROMPT
        user = json.dumps(ctx)

        llm = LLMModel()
        messages = [
            {"role": "system", "content": sys},
            {"role": "user", "content": user}
        ]

        answer = llm.llm_stream(messages)
        strategy = extract_json(answer, "Strategy")
        print(strategy)
        return strategy

    def evaluate_llm(self, ctx: dict) -> str:
        sys = self.prompts.get(self.state, "")
        if not sys:
            assert(False)

        user = json.dumps(ctx)

        if not self.hist:
            self.hist = [{"role": "system", "content": sys}]

        self.hist.append({"role": "user", "content": user})

        # dump prompt
        with open(f"{self.log_dir}/{self.room_num}-{self.room_step}-{self.state}", "w") as fn:
            for msg in self.hist:
                fn.write(f"----{msg.get('role')}---\n")
                fn.write(msg.get("content"))
            
        llm = LLMModel()

        answer = llm.llm_stream(self.hist)
        self.hist.append({"role": "assistant", "content": answer})

        act = self.extract_action(answer)
        print(act)

        self.room_step += 1
        return act

    def get_general_info(self, info: dict) -> dict:

        deck = info.get("deck")
        deck_info = [self.db.query_card(i.get("name")) for i in deck]
        info["deck_info"] = deck_info

        relics = info.get("relics")
        relic_info = [self.db.query_relic(i) for i in relics]
        info["relic_info"] = relic_info

        potions = info.get("potions")
        potion_info = [self.db.query_potion(i.get("potion")) for i in potions if i.get("potion") != "Potion Slot"]
        if potion_info:
            info["potion_info"] = relic_info

        return info

    def _enter_state(self, new_state: ContextState) -> None:
        print(f"in state: {new_state}")
        #self.logger.note(f"in state {new_state}")
        if self.state is new_state:
            return
        self.state = new_state
        self.hist.clear()
        self.actor = Actor(new_state, self.log_dir)

    def _action_map(self, obs: Observation):
        self._enter_state(ContextState.MAP)

        self.logger.note(f"new room {self.room_num}")
        ctx = self.get_ctx()
        ctx["game_state"] = self.get_general_info(obs.persistent_state.readable())
        ctx["map_feature"] = get_path_features(obs.state.get("game_state").get("map"), 0, 0)

        print(json.dumps(ctx))
        self.logger.note(ctx.get("game_state").get("health"))

        # act = self.evaluate_llm(ctx)
        act = "choose 0"

        return act

    def fast_action(self, obs: Observation):

        #print(f"fast action: next act: {self.next_act}")
        if self.next_act:
            if self.next_act.startswith("next_turn_choose"):
                card_name = self.next_act.split(" ")[1]
                for i, name in enumerate(obs.choice_list):
                    if card_name == name:
                        self.next_act = None
                        return f"choose {i}"
                assert(False)

            act = self.next_act
            self.next_act = None
            return act

        ac = [i for i in obs._available_commands if not i in self.skip_commands]
        cl = obs.choice_list

        print("="*10)
        print(ac)
        print("="*10)
        print(cl)
        print("="*10)

        ret = ""
        if len(cl) == 0:
            if len(ac) == 1:
                ret = ac[0] 
            else:
                real_action = [i for i in ac if i not in ["choose", "potion"]]
                if len(real_action) == 1:
                    ret = real_action[0]

        if not ret:
            if "confirm" in ac:
                ret = "confirm"
            elif "choose" in ac and len(cl) == 1:
                ret = "choose 0"

        if ret == "leave" and obs.screen_type == "SHOP_SCREEN":
            self.next_act = "proceed"

        return ret

    def _action_event(self, obs: Observation):
        self._enter_state(ContextState.EVENT)
        ctx = self.get_ctx()
        ctx["game_state"] = self.get_general_info(obs.persistent_state.readable())
        ctx["event_state"] = obs.event_state.readable()

        ctx["available_command"] = [i for i in obs._available_commands if not i in self.skip_commands]
        ctx["choice_list"] = obs.choice_list
        self.logger.note(str(obs.choice_list))
        print(json.dumps(ctx, indent=4))

        act = self.evaluate_llm(ctx)

        return act

    def _action_combat(self, obs: Observation):
        self._enter_state(ContextState.COMBAT)

        act, self.next_act = self.actor.get_action(obs, self.room_num, self.room_step)

        #ctx = self.get_general_info(obs.persistent_state.readable())
        #act = self.evaluate_llm(ctx)
        self.room_step += 1
        return act

    def _action_reward(self, obs: Observation):
        self._enter_state(ContextState.REWARD)

        # select reward one by one
        act = "choose 0"

        return act

    def _action_card_reward(self, obs: Observation):
        self._enter_state(ContextState.REWARD)

        ctx = self.get_ctx()
        ctx["game_state"] = self.get_general_info(obs.persistent_state.readable())

        ctx["choose_strategy"] = self.deck_eval(ctx)

        ctx["card_reward"] = obs.card_reward_state.readable()

        ctx["available_command"] = [i for i in obs._available_commands if not i in self.skip_commands]
        ctx["choice_list"] = [{"id": i, "name": c} for i, c in enumerate(obs.choice_list)]
        self.logger.note(str(obs.choice_list))
        print(json.dumps(ctx))

        act = self.evaluate_llm(ctx)
        if act == "skip":
            self.next_act = "proceed"

        return act

    def _action_rest(self, obs: Observation):
        self._enter_state(ContextState.REST)

        ctx = self.get_ctx()
        ctx["game_state"] = self.get_general_info(obs.persistent_state.readable())

        ctx["available_command"] = [i for i in obs._available_commands if not i in self.skip_commands]
        ctx["choice_list"] = [{"id": i, "name": c} for i, c in enumerate(obs.choice_list)]
        self.logger.note(str(obs.choice_list))
        print(json.dumps(ctx))

        act = self.evaluate_llm(ctx)

        return act

    def _action_shop(self, obs: Observation):
        self._enter_state(ContextState.SHOP)

        ctx = self.get_ctx()

        if not self.hist: # only did first time
            ctx["game_state"] = self.get_general_info(obs.persistent_state.readable())
            ctx["shop_strategy"] = self.deck_eval(ctx)

        ctx["available_command"] = [i for i in obs._available_commands if not i in self.skip_commands]
        ctx["choice_list"] = [{"id": i, "name": c} for i, c in enumerate(obs.choice_list)]
        self.logger.note(str(obs.choice_list))
        print(json.dumps(ctx))

        act = self.evaluate_llm(ctx)
        if act == "leave":
            self.next_act = "proceed"

        return act

    def _action_chest(self, obs: Observation):
        self._enter_state(ContextState.REWARD)

        # select reward one by one
        act = "choose 0"
        return act

    def _action_grid_select(self, obs: Observation):
        # no change state, in order to keep the context

        ctx = self.get_ctx()
        # ctx["game_state"] = self.get_general_info(obs.persistent_state.readable())

        ctx["available_command"] = [i for i in obs._available_commands if not i in self.skip_commands]
        ctx["choice_list"] = [{"id": i, "name": c} for i, c in enumerate(obs.choice_list)]
        self.logger.note(str(obs.choice_list))
        print(json.dumps(ctx))

        act = self.evaluate_llm(ctx)

        return act

    def _action_hand_select(self, obs: Observation):
        # no change state, in order to keep the context

        print("in action_hand_select")
        ctx = self.get_general_info(obs.persistent_state.readable())
        act = self.evaluate_llm(ctx)

        return act

    def _action_game_over(self, obs: Observation):
        act = "over"

        return act
