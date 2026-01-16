from gym_sts.spaces.observations import Observation
from enum import Enum, auto
import json
class ContextState(Enum):
    EVENT = 0
    MAP = auto()
    COMBAT = auto()
    REWARD = auto()
    SHOP = auto()
    REST = auto()
    INVALID = auto()

class LLMAgent:
    def __init__(self):
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

        self.hist = []

        self.state = ContextState.INVALID
        self.room_num = 0
        self.room_step = 0

        self.character = "IRONCLAD"
        self.ascension = 0

    def get_ctx(self) -> dict:
        return {
            "character": self.character,
            "ascension": self.ascension,
        }

    def get_action(self, obs: Observation):

        print(obs.screen_type)
        act = self.actions.get(obs.screen_type)(obs)
    
        act = "choose 0"
        print("play:", act)
        return act
    
    def evaluate_llm(self, ctx: dict) -> str:
        return "choose 0"

    def get_general_info(self, info: dict) -> dict:
        return info

    def _enter_state(self, new_state: ContextState) -> None:
        print(f"in state: {new_state}")
        if self.state is new_state:
            return
        self.state = new_state
        self.hist.clear()

    def _action_map(self, obs: Observation):
        self._enter_state(ContextState.MAP)

        ctx = self.get_general_info(obs.persistent_state.readable())

        act = self.evaluate_llm(ctx)
        act = "choose 0"
        return act

    def _action_event(self, obs: Observation):
        self._enter_state(ContextState.EVENT)
        ctx = self.get_ctx()
        ctx["game_state"] = self.get_general_info(obs.persistent_state.readable())
        ctx["event_state"] = obs.event_state.readable()

        ctx["available_command"] = obs._available_commands
        ctx["choice_list"] = obs.choice_list
        print(json.dumps(ctx))

        act = self.evaluate_llm(ctx)

        return act

    def _action_combat(self, obs: Observation):
        self._enter_state(ContextState.COMBAT)
        ctx = self.get_general_info(obs.persistent_state.readable())
        act = self.evaluate_llm(ctx)

        return act

    def _action_reward(self, obs: Observation):
        self._enter_state(ContextState.REWARD)

        # select reward one by one
        act = "choose 0"

        return act

    def _action_card_reward(self, obs: Observation):
        self._enter_state(ContextState.REWARD)

        ctx = self.get_general_info(obs.persistent_state.readable())
        act = self.evaluate_llm(ctx)

        return act

    def _action_rest(self, obs: Observation):
        self._enter_state(ContextState.REST)

        ctx = self.get_general_info(obs.persistent_state.readable())
        act = self.evaluate_llm(ctx)

        return act

    def _action_shop(self, obs: Observation):
        self._enter_state(ContextState.SHOP)

        ctx = self.get_general_info(obs.persistent_state.readable())
        act = self.evaluate_llm(ctx)

        return act

    def _action_chest(self, obs: Observation):
        self._enter_state(ContextState.REWARD)

        # select reward one by one
        act = "choose 0"
        return act

    def _action_grid_select(self, obs: Observation):
        # no change state, in order to keep the context

        ctx = self.get_general_info(obs.persistent_state.readable())
        act = self.evaluate_llm(ctx)

        return act

    def _action_hand_select(self, obs: Observation):
        # no change state, in order to keep the context

        ctx = self.get_general_info(obs.persistent_state.readable())
        act = self.evaluate_llm(ctx)

        return act

    def _action_game_over(self, obs: Observation):
        act = "choose 0"

        return act
