from __future__ import annotations
from typing import Dict, List
import time
import html

from config import Config
from src import messages
from deps.oaquery import oaquery



class GlobalSnapshot:
    """Global snapshot containing the ServerSnapshots of all servers"""
    def __init__(self):
        self.servers_snaps: Dict[str, ServerSnapshot] = {}
        self.timestamp = None

    def capture(self, oldsnap: GlobalSnapshot) -> GlobalSnapshot:
        """Capture a global snapshot"""
        self.timestamp = time.time()
        infos: List[oaquery.ServerInfo] = oaquery.query_servers(
                Config.OAQuery.hosts, Config.OAQuery.timeout, Config.OAQuery.retries)
        for info in infos:
            server_id = "{}:{}".format(info.ip, str(info.port))
            try:
                last_state = oldsnap.servers_snaps[server_id].state
            except KeyError:
                last_state = ServerSnapshotState(self.timestamp, self.timestamp)
            snapshot = DefaultServerSnapshot(info, self.timestamp, last_state)
            # get rid of city asap :)
            if 'city' in snapshot.get_servername_text().lower():
                snapshot = CityServerSnapshot(info, self.timestamp, last_state)
            elif snapshot.get_game_mode() in ("TOURNAMENT", "MULTITOURNAMENT"):
                snapshot = DuelServerSnapshot(info, self.timestamp, last_state)
            self.servers_snaps[server_id] = snapshot

        return self

    def filter_by_servername(self, patterns: List[str], show_empty = Config.OAQuery.showempty) -> List[ServerSnapshot]:
        """Return a list of server shanpshots with a name matching patterns

        Patterns are and-ed
        """
        return [s for s in self.servers_snaps.values() if
                (all(k in s.get_servername_text().lower() for k in patterns) and
                    (show_empty or s.get_num_players()))]

    def filter_by_players(self, patterns: List[str]) -> List[ServerSnapshot]:
        """Return a list of server snapshots with players matching patterns

        Patterns are or-ed
        """
        return [s for s in self.servers_snaps.values() if
                any(k in name for name in [p.lower() for p in s.get_players_text()]
                    for k in patterns)]



# Server snapshot

class ServerSnapshotState:
    """State of a snapshot"""
    def __init__(self, last_threshold: float, last_duration: float):
        # last time a threshold rule matched
        self.last_threshold = last_threshold
        # last time the duration rule matched
        self.last_duration = last_duration

class ServerSnapshot:
    """Base class for server snapshots"""
    def __init__(self, info: oaquery.ServerInfo, timestamp: float, last_state: ServerSnapshotState):
        if type(self) is ServerSnapshot:
            raise NotImplementedError
        self.info = info
        self.timestamp = timestamp
        self.state = last_state
        self.relevance_rules: List[RelevanceRule] = []

    def get_servername(self) -> messages.MessageArenaString:
        return messages.MessageArenaString(self.info.name().strip())

    def get_servername_text(self) -> str:
        return self.get_servername().get_text()

    def get_servername_term(self) -> str:
        return self.get_servername().get_term()

    def get_servername_html(self) -> str:
        return self.get_servername().get_html()

    def get_game_mode(self) -> str:
        return self.info.gametype().name

    def get_map_text(self) -> str:
        return self.info.map()

    def get_map_term(self) -> str:
        return self.get_map_text()

    def get_map_html(self) -> str:
        return html.escape(self.get_map_text())

    def get_num_players(self) -> int:
        return self.info.num_humans()

    def get_players(self) -> List[messages.MessageArenaString]:
        return [messages.MessageArenaString(player.name.strip()) for player in self.info.likely_human_players()]

    def get_players_text(self) -> List[str]:
        return [player.get_text() for player in self.get_players()]

    def get_players_term(self) -> List[str]:
        return [player.get_term() for player in self.get_players()]

    def get_players_html(self) -> List[str]:
        return [player.get_html() for player in self.get_players()]

    def compare(self, prev_snap: ServerSnapshot) -> List[RelevanceRule]:
        """Compare with a previous snapshot

        Every subclass matches against appropriate relevance rules
        """

    def attach_rules(self, *rules: RelevanceRule) -> ServerSnapshot:
        """Add a relevance rule to be later evaluated for this snapshot"""
        for rule in rules:
            self.relevance_rules.append(rule)
        return self

    def evaluate_rules(self, prev_snap: ServerSnapshot) -> List[RelevanceRule]:
        """Evaluate all of the relevance rules set for this snapshot"""
        matched_rules = []
        for rule in self.relevance_rules:
            if rule.evaluate(prev_snap, self):
                matched_rules.append(rule)
                rule._post_match(self)
        return matched_rules

class DuelServerSnapshot(ServerSnapshot):
    def compare(self, prev_snap: ServerSnapshot) -> List[RelevanceRule]:
        threshold = Config.Thresholds.duel
        self.attach_rules(
                UnderThresholdRule(threshold),
                OverThresholdRule(threshold),
                DurationRule(threshold))
                #PlayerLeaveRule(),
                #PlayerEnterRule())
        return self.evaluate_rules(prev_snap)

class CityServerSnapshot(ServerSnapshot):
    def compare(self, prev_snap: ServerSnapshot) -> List[RelevanceRule]:
        threshold = Config.Thresholds.City
        self.attach_rules(
                UnderThresholdRule(threshold),
                OverThresholdRule(threshold),
                DurationRule(threshold))
        return self.evaluate_rules(prev_snap)

class DefaultServerSnapshot(ServerSnapshot):
    def compare(self, prev_snap: ServerSnapshot) -> List[RelevanceRule]:
        threshold = Config.Thresholds.default
        self.attach_rules(
                UnderThresholdRule(threshold),
                OverThresholdRule(threshold),
                DurationRule(threshold))
                #PlayerLeaveRule(),
                #PlayerEnterRule())
        return self.evaluate_rules(prev_snap)

class DummyServerSnapshot(ServerSnapshot):
    """Dummy snapshot to be used as first server snapshot"""
    # NOTE: This is useful as fallback snapshot when there is no previous
    # snapshot to compare against for a paticular server (like when the bot
    # starts or when a server has just came up), so we use this empty
    # DummyServerSnapshot providing some fallback values.
    # This class must override all of the attributes/methods that RelevanceRule
    # objects operates with. Override as much as it's necessary to fake a reset
    # state from the RelevanceRule's evaluate() point of view (i.e. just
    # override the attributes and methods used by prev)
    def __init__(self, timestamp: float):
        super().__init__(None, timestamp, timestamp)

    def get_num_players(self) -> int:
        return 0

    def get_players(self):
        return []



# Relevance rules

class RelevanceRule:
    """Base class for a relevance rule

    Relevance rules represent different rules to check for snapshot relevance
    """
    def __init__(self, *args):
        if type(self) is RelevanceRule:
            raise NotImplementedError

    def evaluate(self, prev: ServerSnapshot, curr: ServerSnapshot) -> bool:
        """Evaluate the rule on two consecutive snapshots"""

    def _post_match(self, snapshot: ServerSnapshot):
        """Actions to take after the rule is matched, e.g. change snapshot state"""
        pass

class OverThresholdRule(RelevanceRule):
    """Number of players just passed over the threshold"""
    def __init__(self, threshold: int):
        self.threshold = threshold

    def evaluate(self, prev: ServerSnapshot, curr: ServerSnapshot) -> bool:
        return (prev.get_num_players() < self.threshold and
                curr.get_num_players() >= self.threshold)

    def _post_match(self, snapshot: ServerSnapshot):
        snapshot.state.last_threshold = snapshot.timestamp

class UnderThresholdRule(RelevanceRule):
    """Number of players just passed under the threshold"""
    def __init__(self, threshold: int):
        self.threshold = threshold

    def evaluate(self, prev: ServerSnapshot, curr: ServerSnapshot) -> bool:
        return (prev.get_num_players() >= self.threshold and
                curr.get_num_players() < self.threshold)

    def _post_match(self, snapshot: ServerSnapshot):
        snapshot.state.last_threshold = snapshot.timestamp

class DurationRule(RelevanceRule):
    """Number of players has been over threshold for some time"""
    def __init__(self, threshold: int):
        self.threshold = threshold
        self.duration = Config.Thresholds.duration_time * 60

    def evaluate(self, prev: ServerSnapshot, curr: ServerSnapshot) -> bool:
        return (curr.get_num_players() >= self.threshold and
                curr.timestamp - curr.state.last_duration >= self.duration and
                curr.timestamp - curr.state.last_threshold >= self.duration)

    def _post_match(self, snapshot: ServerSnapshot):
        snapshot.state.last_duration = snapshot.timestamp

class PlayerEnterRule(RelevanceRule):
    """Some players entered the server"""
    def __init__(self):
        self.players: List[messages.MessageArenaString] = []

    def evaluate(self, prev: ServerSnapshot, curr: ServerSnapshot) -> bool:
        self.players = [p for p in curr.get_players() if (
            p.get_text() in Config.Players.stalk_list and p.get_text() not in prev.get_players_text())]
        return bool(self.players)

    def _post_match(self, snapshot: ServerSnapshot):
        pass

class PlayerLeaveRule(RelevanceRule):
    """Some players left the server"""
    def __init__(self):
        self.players: List[messages.MessageArenaString] = []

    def evaluate(self, prev: ServerSnapshot, curr: ServerSnapshot) -> bool:
        self.players = [p for p in prev.get_players() if (
            p.get_text() in Config.Players.stalk_list and p.get_text() not in curr.get_players_text())]
        return bool(self.players)

    def _post_match(self, snapshot: ServerSnapshot):
        pass
