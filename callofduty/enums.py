from enum import Enum


class Platform(Enum):
    Activision = "uno"
    PlayStation = "psn"
    Xbox = "xbl"
    Steam = "steam"
    BattleNet = "battle"


class Title(Enum):
    ModernWarfare = "mw"
    BlackOps4 = "bo4"
    WWII = "wwii"
    InfiniteWarfare = "iw"
    BlackOps3 = "bo3"


class Mode(Enum):
    Multiplayer = "mp"
    Zombies = "zm"
    Blackout = "wz"


class Language(Enum):
    English = "en"
    French = "fr"
    German = "de"
    Italian = "it"
    Spanish = "es"


class TimeFrame(Enum):
    AllTime = "alltime"
    Monthly = "monthly"
    Weekly = "weekly"


class GameType(Enum):
    Core = "core"
    Hardcore = "hc"
    WorldLeague = "arena"
