import logging

from .enums import GameType, Language, Mode, Platform, TimeFrame, Title
from .leaderboard import Leaderboard
from .match import Match
from .player import Player
from .squad import Squad
from .utils import (
    VerifyGameType,
    VerifyLanguage,
    VerifyMode,
    VerifyPlatform,
    VerifyTimeFrame,
    VerifyTitle,
)

log = logging.getLogger(__name__)


class Client:
    """Client which manages communication with the Call of Duty API."""

    def __init__(self, http: object):
        self.http = http

    async def Logout(self):
        """Close the client session."""

        await self.http.CloseSession()

    async def GetLocalize(self, language: Language = Language.English):
        """
        Get the localized strings used by the Call of Duty Companion App
        and website.

        Parameters
        ----------
        language : callofduty.Language, optional
            Language to use for localization data (default is English.)

        Returns
        -------
        dict
            JSON data containing localized strings.
        """

        VerifyLanguage(language)

        web = await self.http.GetWebLocalize(language.value)
        app = await self.http.GetAppLocalize(language.value)

        return {**web, **app}

    async def GetNewsFeed(self, language: Language = Language.English):
        """
        Get the Call of Duty franchise feed, includes blog posts and
        the Companion App message of the day.

        Parameters
        ----------
        language : callofduty.Language, optional
            Language to use for localization data (default is English.)

        Returns
        -------
        dict
            JSON data containing the Call of Duty franchise feed.
        """

        return await self.http.GetNewsFeed(language.value)

    async def GetFriendFeed(self):
        """
        Get the Friend Feed of the authenticated Call of Duty player.

        Returns
        -------
        dict
            JSON data of the player's Friend Feed.
        """

        data = (await self.http.GetFriendFeed())["data"]

        players = []

        for i in data["identities"]:
            _player = Player(
                self, {"platform": i["platform"], "username": i["username"]}
            )
            players.append(_player)

        return {
            "events": data["events"],
            "players": players,
            "metadata": data["metadata"],
        }

    async def GetMyIdentities(self):
        """
        Get the Title Identities for the authenticated Call of Duty player.

        Returns
        -------
        list
            Array of identities containing title, platform, username, and more.
        """

        data = (await self.http.GetMyIdentities())["data"]

        identities = []

        for identity in data["titleIdentities"]:
            identities.append(
                {
                    "title": Title(identity.pop("title")),
                    "platform": Platform(identity.pop("platform")),
                    "username": identity["username"],
                    "activeDate": identity["activeDate"],
                    "activityType": identity["activityType"],
                }
            )

        return identities

    async def GetMyAccounts(self):
        """
        Get the linked Accounts for the authenticated Call of Duty player.

        Returns
        -------
        list
            Array of Player objects for the linked accounts.
        """

        data = (await self.http.GetMyAccounts())["data"]

        accounts = []

        for account in data.keys():
            accounts.append(
                Player(
                    self, {"platform": account, "username": data[account]["username"]}
                )
            )

        return accounts

    async def GetMyFriends(self):
        """
        Get the Friends of the authenticated Call of Duty player.

        Returns
        -------
        list
            Array of Player objects for the friends.
        """

        data = (await self.http.GetMyFriends())["data"]

        friends = []

        for friend in data["uno"]:
            friends.append(
                Player(
                    self,
                    {
                        "platform": friend["platform"],
                        "username": friend["username"],
                        "accountId": friend.get("accountId"),
                        "online": friend["status"]["online"],
                    },
                )
            )

        for _platform in data["firstParty"]:
            for friend in data["firstParty"][_platform]:
                i = friend.get("identities", [])
                identities = []

                for _platform in i:
                    identities.append(
                        Player(
                            self,
                            {
                                "platform": friend["identities"][_platform]["platform"],
                                "username": friend["identities"][_platform]["username"],
                                "accountId": friend["identities"][_platform][
                                    "accountId"
                                ],
                                "avatarUrl": friend["identities"][_platform].get(
                                    "avatarUrlLargeSsl"
                                ),
                            },
                        )
                    )

                friends.append(
                    Player(
                        self,
                        {
                            "platform": friend["platform"],
                            "username": friend["username"],
                            "accountId": friend.get("accountId"),
                            "avatarUrl": friend.get("avatarUrlLargeSsl"),
                            "online": friend["status"]["online"],
                            "identities": identities,
                        },
                    )
                )

        return friends

    async def GetMyFriendRequests(self):
        """
        Get the incoming and outgoing Friend Requests for the authenticated
        Call of Duty player.

        Returns
        -------
        dict
            JSON data of the player's friend requests.
        """

        data = (await self.http.GetMyFriends())["data"]

        incoming = []
        outgoing = []

        for request in data["incomingInvitations"]:
            incoming.append(
                Player(
                    self,
                    {
                        "platform": request["platform"],
                        "username": request["username"],
                        "accountId": request.get("accountId"),
                        "online": request["status"]["online"],
                    },
                )
            )

        for request in data["outgoingInvitations"]:
            outgoing.append(
                Player(
                    self,
                    {
                        "platform": request["platform"],
                        "username": request["username"],
                        "accountId": request.get("accountId"),
                        "online": request["status"]["online"],
                    },
                )
            )

        return {"incoming": incoming, "outgoing": outgoing}

    async def GetPlayer(self, platform: Platform, username: str):
        """
        Get a Call of Duty player using their platform and username.

        Parameters
        ----------
        platform : callofduty.Platform
            Platform to get the player from.
        username : str
            Player's username for the designated platform.

        Returns
        -------
        object
            Player object for the requested player.
        """

        VerifyPlatform(platform)

        return Player(self, {"platform": platform.value, "username": username})

    async def SearchPlayers(self, platform: Platform, username: str, **kwargs):
        """
        Search Call of Duty players by platform and username.

        Parameters
        ----------
        platform : callofduty.Platform
            Platform to get the players from.
        username : str
            Player's username for the designated platform.
        limit : int, optional
            Number of search results to return (default is None.)

        Returns
        -------
        list
            Array of Player objects matching the query.
        """

        VerifyPlatform(platform)

        data = (await self.http.SearchPlayer(platform.value, username))["data"]

        limit = kwargs.get("limit", 0)
        if limit > 0:
            data = data[:limit]

        results = []

        for player in data:
            accountId = player.get("accountId")
            if isinstance(accountId, str):
                # The API returns the accountId as a string
                accountId = int(accountId)

            avatar = player.get("avatar")
            if isinstance(avatar, dict):
                avatar = avatar["avatarUrlLargeSsl"]

            data = {
                "platform": player["platform"],
                "username": player["username"],
                "accountId": accountId,
                "avatarUrl": avatar,
            }

            results.append(Player(self, data))

        return results

    async def GetPlayerProfile(
        self, platform: Platform, username: str, title: Title, mode: Mode
    ):
        """
        Get a Call of Duty player's profile for the specified title and mode.

        Parameters
        ----------
        platform : callofduty.Platform
            Platform to get the player from.
        username : str
            Player's username for the designated platform.
        title : callofduty.Title
            Call of Duty title to get the player's profile from.
        mode: callofduty.Mode
            Call of Duty mode to get the player's profile from.

        Returns
        -------
        dict
            JSON data of the player's complete profile for the requested
            title and mode.
        """

        VerifyPlatform(platform)
        VerifyTitle(title)
        VerifyMode(mode)

        return (
            await self.http.GetPlayerProfile(
                platform.value, username, title.value, mode.value
            )
        )["data"]

    async def GetMatch(self, title: Title, platform: Platform, matchId: int):
        """
        Get a Call of Duty match using its title, platform, mode, and ID.

        Parameters
        ----------
        title : callofduty.Title
            Call of Duty title which the match occured on.
        platform : callofduty.Platform
            Platform to get the player from.
        matchId : int
            Match ID.

        Returns
        -------
        object
            Match object representing the specified details.
        """

        VerifyTitle(title)
        VerifyPlatform(platform)

        return Match(
            self, {"id": matchId, "platform": platform.value, "title": title.value,},
        )

    async def GetPlayerMatches(
        self, platform: Platform, username: str, title: Title, mode: Mode, **kwargs
    ):
        """
        Get a Call of Duty player's match history for the specified title and mode.

        Parameters
        ----------
        platform : callofduty.Platform
            Platform to get the player from.
        username : str
            Player's username for the designated platform.
        title : callofduty.Title
            Call of Duty title to get the player's matches from.
        mode: callofduty.Mode
            Call of Duty mode to get the player's matches from.
        limit : int, optional
            Number of matches which will be returned (default is 10.)
        startTimestamp : int, optional
            Unix timestamp representing the earliest time which a returned
            match should've occured (default is None.)
        endTimestamp : int, optional
            Unix timestamp representing the latest time which a returned
            match should've occured (default is None.)

        Returns
        -------
        list
            Array of Match objects.
        """

        VerifyPlatform(platform)
        VerifyTitle(title)
        VerifyMode(mode)

        limit = kwargs.get("limit", 10)
        startTimestamp = kwargs.get("startTimestamp", 0)
        endTimestamp = kwargs.get("endTimestamp", 0)

        if platform == Platform.Activision:
            # The preferred matches endpoint does not currently support
            # the Activision (uno) platform.
            data = (
                await self.http.GetPlayerMatchesDetailed(
                    platform.value,
                    username,
                    title.value,
                    mode.value,
                    limit,
                    startTimestamp,
                    endTimestamp,
                )
            )["data"]["matches"]

            matches = []

            for _match in data:
                matches.append(
                    Match(
                        self,
                        {
                            # The API returns the matchId as a string
                            "id": int(_match["matchID"]),
                            "platform": platform.value,
                            "title": title.value,
                        },
                    )
                )
        else:
            data = (
                await self.http.GetPlayerMatches(
                    platform.value,
                    username,
                    title.value,
                    mode.value,
                    limit,
                    startTimestamp,
                    endTimestamp,
                )
            )["data"]

            matches = []

            for _match in data:
                matches.append(
                    Match(
                        self,
                        {
                            # The API returns the matchId as a string
                            "id": int(_match["matchId"]),
                            "platform": platform.value,
                            "title": title.value,
                        },
                    )
                )

        return matches

    async def GetPlayerMatchesSummary(
        self, platform: Platform, username: str, title: Title, mode: Mode, **kwargs
    ):
        """
        Get a Call of Duty player's match history summary for the specified title and mode.

        Parameters
        ----------
        platform : callofduty.Platform
            Platform to get the player from.
        username : str
            Player's username for the designated platform.
        title : callofduty.Title
            Call of Duty title to get the player's matches from.
        mode: callofduty.Mode
            Call of Duty mode to get the player's matches from.
        limit : int, optional
            Number of matches which will be returned (default is 10.)
        startTimestamp : int, optional
            Unix timestamp representing the earliest time which a returned
            match should've occured (default is None.)
        endTimestamp : int, optional
            Unix timestamp representing the latest time which a returned
            match should've occured (default is None.)

        Returns
        -------
        dict
            JSON data containing recent matches summary.
        """

        VerifyPlatform(platform)
        VerifyTitle(title)
        VerifyMode(mode)

        limit = kwargs.get("limit", 10)
        startTimestamp = kwargs.get("startTimestamp", 0)
        endTimestamp = kwargs.get("endTimestamp", 0)

        return (
            await self.http.GetPlayerMatchesDetailed(
                platform.value,
                username,
                title.value,
                mode.value,
                limit,
                startTimestamp,
                endTimestamp,
            )
        )["data"]["summary"]

    async def GetMatchDetails(self, title: Title, platform: Platform, matchId: int):
        """
        Get a Call of Duty match's details.

        Parameters
        ----------
        title : callofduty.Title
            Call of Duty title which the match occured on.
        platform : callofduty.Platform
            Platform to get the match from.
        matchId : int
            Match ID.

        Returns
        -------
        dict
            JSON data containing the full details of the requested Call of Duty match.
        """

        VerifyPlatform(platform)
        VerifyTitle(title)

        return (await self.http.GetMatch(title.value, platform.value, matchId))["data"]

    async def GetMatchTeams(self, title: Title, platform: Platform, matchId: int):
        """
        Get the teams which played in a Call of Duty match.

        Parameters
        ----------
        title : callofduty.Title
            Call of Duty title which the match occured on.
        platform : callofduty.Platform
            Platform to get the match from.
        matchId : int
            Match ID.

        Returns
        -------
        list
            Array containing two child arrays, one for each team. Each
            team's array contains Player objects which represent the
            players on the team.
        """

        VerifyPlatform(platform)
        VerifyTitle(title)

        data = (await self.http.GetMatch(title.value, platform.value, matchId))["data"][
            "teams"
        ]

        # The API does not state which team is allies/axis, so no array
        # keys will be used.
        teams = []

        for team in data:
            # Current team iterator
            i = []

            for player in team:
                i.append(
                    Player(
                        self,
                        {
                            "platform": player["provider"],
                            "username": player["username"],
                            "accountId": player["unoId"],
                        },
                    )
                )

            teams.append(i)

        return teams

    async def GetLeaderboard(self, title: Title, platform: Platform, **kwargs):
        """
        Get a Call of Duty leaderboard.

        Parameters
        ----------
        title : callofduty.Title
            Call of Duty title which the leaderboard represents.
        platform : callofduty.Platform
            Platform to get which the leaderboard represents.
        gameType : callofduty.GameType, optional
            Game type to get the leaderboard for (default is Core.)
        gameMode : str, optional
            Game mode to get the leaderboard for (default is Career.)
        timeFrame : callofduty.TimeFrame, optional
            Time Frame to get the leaderboard for (default is All-Time.)
        page : int, optional
            Leaderboard page to get (default is 1.)

        Returns
        -------
        object
            Leaderboard object representing the specified details.
        """

        gameType = kwargs.get("gameType", GameType.Core)
        gameMode = kwargs.get("gameMode", "career")
        timeFrame = kwargs.get("timeFrame", TimeFrame.AllTime)
        page = kwargs.get("page", 1)

        VerifyTitle(title)
        VerifyPlatform(platform)
        VerifyGameType(gameType)
        VerifyTimeFrame(timeFrame)

        data = (
            await self.http.GetLeaderboard(
                title.value,
                platform.value,
                gameType.value,
                gameMode,
                timeFrame.value,
                page,
            )
        )["data"]

        # Leaderboard responses don't include the timeFrame, so we'll
        # just add it manually.
        data["timeFrame"] = timeFrame.value

        return Leaderboard(self, data)

    async def GetPlayerLeaderboard(
        self, title: Title, platform: Platform, username: str, **kwargs
    ):
        """
        Get a Call of Duty leaderboard.

        Parameters
        ----------
        title : callofduty.Title
            Call of Duty title which the leaderboard represents.
        platform : callofduty.Platform
            Platform to get which the leaderboard represents.
        username : str
            Player's username for the designated platform.
        gameType : callofduty.GameType, optional
            Game type to get the leaderboard for (default is Core.)
        gameMode : str, optional
            Game mode to get the leaderboard for (default is Career.)
        timeFrame : callofduty.TimeFrame, optional
            Time Frame to get the leaderboard for (default is All-Time.)

        Returns
        -------
        object
            Leaderboard object representing the specified details.
        """

        gameType = kwargs.get("gameType", GameType.Core)
        gameMode = kwargs.get("gameMode", "career")
        timeFrame = kwargs.get("timeFrame", TimeFrame.AllTime)

        VerifyTitle(title)
        VerifyPlatform(platform)
        VerifyGameType(gameType)
        VerifyTimeFrame(timeFrame)

        data = (
            await self.http.GetPlayerLeaderboard(
                title.value,
                platform.value,
                username,
                gameType.value,
                gameMode,
                timeFrame.value,
            )
        )["data"]

        # Leaderboard responses don't include the timeFrame, so we'll
        # just add it manually.
        data["timeFrame"] = timeFrame.value

        return Leaderboard(self, data)

    async def GetLeaderboardPlayers(self, title: Title, platform: Platform, **kwargs):
        """
        Get the players from a Call of Duty leaderboard.

        Parameters
        ----------
        title : callofduty.Title
            Call of Duty title which the leaderboard represents.
        platform : callofduty.Platform
            Platform to get which the leaderboard represents.
        gameType : callofduty.GameType, optional
            Game type to get the leaderboard for (default is Core.)
        gameMode : str, optional
            Game mode to get the leaderboard for (default is Career.)
        timeFrame : callofduty.TimeFrame, optional
            Time Frame to get the leaderboard for (default is All-Time.)
        page : int, optional
            Leaderboard page to get (default is 1.)

        Returns
        -------
        list
            Array containing Player objects for each Leaderboard entry.
        """

        gameType = kwargs.get("gameType", GameType.Core)
        gameMode = kwargs.get("gameMode", "career")
        timeFrame = kwargs.get("timeFrame", TimeFrame.AllTime)
        page = kwargs.get("page", 1)

        VerifyTitle(title)
        VerifyPlatform(platform)
        VerifyGameType(gameType)
        VerifyTimeFrame(timeFrame)

        data = (
            await self.http.GetLeaderboard(
                title.value,
                platform.value,
                gameType.value,
                gameMode,
                timeFrame.value,
                page,
            )
        )["data"]

        # Leaderboard responses don't include the timeFrame, so we'll
        # just add it manually.
        data["timeFrame"] = timeFrame.value

        data = Leaderboard(self, data)

        players = []

        for _player in data.entries:
            players.append(
                Player(
                    self, {"platform": platform.value, "username": _player["username"]}
                )
            )

        return players

    async def GetAvailableMaps(
        self,
        title: Title,
        platform: Platform = Platform.PlayStation,
        mode: Mode = Mode.Multiplayer,
    ):
        """
        Get the Maps available in the specified Title for Heat Map use.

        Parameters
        ----------
        title : callofduty.Title
            Call of Duty title which the maps originate.
        platform : callofduty.Platform, optional
            Platform which the maps are available on (default is PlayStation.)
        mode: callofduty.Mode, optional
            Call of Duty mode to get the maps from (default is Multiplayer.)

        Returns
        -------
        list
            Array of Maps and the Game Modes which are available each map.
        """

        return (
            await self.http.GetAvailableMaps(title.value, platform.value, mode.value)
        )["data"]

    async def GetLootSeason(self, title: Title, season: int, **kwargs):
        """
        Get a Call of Duty Loot Season by its title and number.

        Parameters
        ----------
        title : callofduty.Title
            Call of Duty title which the loot season originates.
        season : int
            Loot season number.
        platform : callofduty.Platform, optional
            Platform which the loot season is available on (default is PlayStation.)
        language : callofduty.Language, optional
            Language which the loot data should be in (default is English.)

        Returns
        -------
        dict
            JSON data representing the requested loot season.
        """

        platform = kwargs.get("platform", Platform.PlayStation)
        language = kwargs.get("language", Language.English)

        VerifyPlatform(platform)
        VerifyLanguage(language)

        return (
            await self.http.GetLootSeason(
                title.value, season, platform.value, language.value
            )
        )["data"]

    async def GetSquad(self, name: str):
        """
        Get a Call of Duty Squad using its name.

        Parameters
        ----------
        name : str
            Name of Squad.

        Returns
        -------
        object
            Squad object for the requested Squad.
        """

        return Squad(self, (await self.http.GetSquad(name))["data"])

    async def GetPlayerSquad(self, platform: Platform, username: str):
        """
        Get a Call of Duty player's Squad using their platform and username.

        Parameters
        ----------
        platform : callofduty.Platform
            Platform to get the player from.
        username : str
            Player's username for the designated platform.

        Returns
        -------
        object
            Squad object for the requested Squad.
        """

        VerifyPlatform(platform)

        return Squad(
            self, (await self.http.GetPlayerSquad(platform.value, username))["data"]
        )

    async def GetMySquad(self):
        """
        Get the Squad of the authenticated Call of Duty player.

        Returns
        -------
        object
            Squad object for the requested Squad.
        """

        return Squad(self, (await self.http.GetMySquad())["data"])

    async def JoinSquad(self, name: str):
        """
        Join a Call of Duty Squad using its name.

        Parameters
        ----------
        name : str
            Name of Squad.
        """

        await self.http.JoinSquad(name)

    async def LeaveSquad(self):
        """
        Leave the Call of Duty Squad of the authenticated player.
        Upon leaving a Squad, the player is automatically placed into
        a random Squad.

        Returns
        -------
        object
            Squad object for the randomly-joined Squad.
        """

        await self.http.LeaveSquad()

        return await self.GetMySquad()
