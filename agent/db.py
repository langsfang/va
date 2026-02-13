import pandas as pd
from pathlib import Path

class StSDB:
    def __init__(self):
        info_dir = Path(__file__).resolve().parent / "info"
        self.cards = pd.read_csv(f"{info_dir}/cards.csv")
        self.monsters = pd.read_csv(f"{info_dir}/monsters.csv")
        self.relics = pd.read_csv(f"{info_dir}/relics.csv")
        self.potions = pd.read_csv(f"{info_dir}/potions.csv")

    def query_card(self, name: str):
        result = self.cards[self.cards['Name'] == name]

        if not result.empty:
            return result.iloc[0].to_dict()
        else:
            return None

    def query_potion(self, name: str):
        result = self.potions[self.potions['Name'] == name]

        if not result.empty:
            return result.iloc[0].to_dict()
        else:
            return None

    def query_relic(self, name: str):
        result = self.relics[self.relics['Name'] == name]

        if not result.empty:
            return result.iloc[0].to_dict()
        else:
            return None

    def query_monster(self, name: str):
        result = self.monsters[self.monsters['Name'] == name]

        if not result.empty:
            return result.iloc[0].to_dict()
        else:
            return None

        monster_dict = {
            "GremlinNob":"GREMLIN_NOB",
            "GremlinTsundere":"MAD_GREMLIN",
            "FungiBeast":"FUNGI_BEAST",
            "GremlinThief":"SNEAKY_GREMLIN",
            "TheGuardian":"THE_GUARDIAN",
            "FuzzyLouseNormal":"RED_LOUSE",
            "GremlinWarrior":"SHIELD_GREMLIN",
            "Looter":"LOOTER",
            "Lagavulin":"LAGAVULIN",
            "AcidSlime_L":"ACID_SLIME_L",
            "HexaghostOrb":"HexaghostOrb",
            "Hexaghost":"HEXAGHOST",
            "SlaverBlue":"BLUE_SLAVER",
            "Sentry":"SENTRY",
            "AcidSlime_S":"ACID_SLIME_S",
            "SpikeSlime_S":"SPIKE_SLIME_S",
            "GremlinWizard":"GREMLIN_WIZARD",
            "FuzzyLouseDefensive":"GREEN_LOUSE",
            "SpikeSlime_M":"SPIKE_SLIME_M",
            "AcidSlime_M":"ACID_SLIME_M",
            "Cultist":"CULTIST",
            "Apology Slime":"ApologySlime",
            "SlimeBoss":"SLIME_BOSS",
            "HexaghostBody":"HexaghostBody",
            "SpikeSlime_L":"SPIKE_SLIME_L",
            "GremlinFat":"FAT_GREMLIN",
            "SlaverRed":"RED_SLAVER",
            "JawWorm":"JAW_WORM",
            "BronzeOrb":"BRONZE_ORB",
            "BookOfStabbing":"BOOK_OF_STABBING",
            "TheCollector":"THE_COLLECTOR",
            "Snecko":"SNECKO",
            "BanditBear":"BEAR",
            "SlaverBoss":"TASKMASTER",
            "TorchHead":"TORCH_HEAD",
            "Shelled Parasite":"SHELLED_PARASITE",
            "Centurion":"CENTURION",
            "Chosen":"CHOSEN",
            "BronzeAutomaton":"BRONZE_AUTOMATON",
            "Healer":"MYSTIC",
            "BanditChild":"POINTY",
            "BanditLeader":"ROMEO",
            "SphericGuardian":"SPHERIC_GUARDIAN",
            "SnakePlant":"SNAKE_PLANT",
            "Champ":"THE_CHAMP",
            "Mugger":"MUGGER",
            "Byrd":"BYRD",
            "GremlinLeader":"GREMLIN_LEADER",
            "Serpent":"SERPENT",
            "Darkling":"DARKLING",
            "Orb Walker":"ORB_WALKER",
            "Donu":"DONU",
            "Maw":"THE_MAW",
            "Spiker":"SPIKER",
            "AwakenedOne":"AWAKENED_ONE",
            "TimeEater":"TIME_EATER",
            "Repulsor":"REPULSOR",
            "WrithingMass":"WRITHING_MASS",
            "Deca":"DECA",
            "Exploder":"EXPLODER",
            "Reptomancer":"REPTOMANCER",
            "Transient":"TRANSIENT",
            "Nemesis":"NEMESIS",
            "Dagger":"DAGGER",
            "GiantHead":"GIANT_HEAD",
            "SpireShield":"SPIRE_SHIELD",
            "SpireSpear":"SPIRE_SPEAR",
            "CorruptHeart":"CORRUPT_HEART",
        }

