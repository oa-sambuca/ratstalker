from __future__ import annotations
from typing import Dict, List
import time

from config import Config
from deps.oaquery import oaquery



class GlobalSnapshot:
    """Global snapshot containing the ServerSnapshots of all servers"""
    def __init__(self):
        self.servers_snaps: Dict[str, ServerSnapshot] = {}
        self.timestamp = None

    def capture(self, oldsnap: GlobalSnapshot) -> GlobalSnapshot:
        """Capture a global snapshot"""
        self.timestamp = time.time()
        infos: List[oaquery.ServerInfo] = oaquery.query_servers(Config.OAQuery.hosts)
        for info in infos:
            servername = info.name().getstr()
            gametype = info.gametype().name
            try:
                last_state = oldsnap.servers_snaps[servername].state
            except KeyError:
                last_state = ServerSnapshotState(self.timestamp, self.timestamp)
            # get rid of city asap :)
            if 'city' in servername.lower():
                snapshot = CityServerSnapshot(info, self.timestamp, last_state)
            elif gametype in ("TOURNAMENT", "MULTITOURNAMENT"):
                snapshot = DuelServerSnapshot(info, self.timestamp, last_state)
            else:
                snapshot = DefaultServerSnapshot(info, self.timestamp, last_state)

            self.servers_snaps[servername] = snapshot
        return self

    def filter_by_servername(self, patterns: List[str], show_empty = Config.OAQuery.showempty) -> List[ServerSnapshot]:
        """Return a list of server shanpshots with a name matching patterns

        Patterns are and-ed
        """
        return [s for s in self.servers_snaps.values() if
                (all(k in s.info.name().getstr().lower() for k in patterns) and
                    (show_empty or s.info.num_humans()))]

    def filter_by_players(self, patterns: List[str]) -> List[ServerSnapshot]:
        """Return a list of server snapshots with players matching patterns

        Patterns are or-ed
        """
        return [s for s in self.servers_snaps.values() if
                any(k in x for x in [n.getstr().lower()
                    for n in [p.name for p in s.info.likely_human_players()]]
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
        return self.evaluate_rules(prev_snap)

class DummyServerSnapshot(ServerSnapshot):
    """Dummy snapshot to be used as first server snapshot"""
    # NOTE: This is useful as fallback snapshot when there is no previous
    # snapshot to compare against for a paticular server (like when the bot
    # starts or when a server has just came up), so we use this empty
    # DummyServerSnapshot with a DummyServerInfo providing some fallback
    # values.
    def __init__(self, timestamp: float):
        super().__init__(DummyServerInfo(), timestamp, timestamp)

class DummyServerInfo(oaquery.ServerInfo):
    """Dummy infos to be used in a DummyServerSnapshot"""
    # This class must override all of the attributes/methods that RelevanceRule
    # objects operates with. Override the minimum of ServerInfo class as much
    # as it's necessary to fake a reset state from the RelevanceRule's
    # evaluate() point of view (i.e. just override the attributes and methods
    # used by prev)
    def __init__(self):
        pass

    def num_humans(self):
        return 0



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
        return (prev.info.num_humans() < self.threshold and
                curr.info.num_humans() >= self.threshold)

    def _post_match(self, snapshot: ServerSnapshot):
        snapshot.state.last_threshold = snapshot.timestamp

class UnderThresholdRule(RelevanceRule):
    """Number of players just passed under the threshold"""
    def __init__(self, threshold: int):
        self.threshold = threshold

    def evaluate(self, prev: ServerSnapshot, curr: ServerSnapshot) -> bool:
        return (prev.info.num_humans() >= self.threshold and
                curr.info.num_humans() < self.threshold)

    def _post_match(self, snapshot: ServerSnapshot):
        snapshot.state.last_threshold = snapshot.timestamp

class DurationRule(RelevanceRule):
    """Number of players has been over threshold for some time"""
    def __init__(self, threshold: int):
        self.threshold = threshold
        self.duration = Config.Thresholds.duration_time * 60

    def evaluate(self, prev: ServerSnapshot, curr: ServerSnapshot) -> bool:
        return (curr.info.num_humans() >= self.threshold and
                curr.timestamp - curr.state.last_duration >= self.duration and
                curr.timestamp - curr.state.last_threshold >= self.duration)

    def _post_match(self, snapshot: ServerSnapshot):
        snapshot.state.last_duration = snapshot.timestamp
