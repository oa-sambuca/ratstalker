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
            servername = info.name().strip().getstr()
            gametype = info.gametype().name
            try:
                last_threshold = oldsnap.servers_snaps[servername].last_threshold
            except KeyError:
                last_threshold = self.timestamp
            # get rid of city asap :)
            if 'city' in servername.lower():
                snapshot = CityServerSnapshot(info, self.timestamp, last_threshold)
            elif gametype in ("TOURNAMENT", "MULTITOURNAMENT"):
                snapshot = DuelServerSnapshot(info, self.timestamp, last_threshold)
            else:
                snapshot = DefaultServerSnapshot(info, self.timestamp, last_threshold)

            self.servers_snaps[servername] = snapshot
        return self



# Server snapshot

class ServerSnapshot:
    """Base class for server snapshots"""
    def __init__(self, info: oaquery.ServerInfo, timestamp: float, last_threshold: float):
        if type(self) is ServerSnapshot:
            raise NotImplementedError
        self.info = info
        self.timestamp = timestamp
        # last time the threshold was crossed
        self.last_threshold = last_threshold
        self.relevance_rules: List[RelevanceRule] = []

    def compare(self, prev_snap: ServerSnapshot) -> List[RelevanceRule]:
        """Compare with a previous snapshot

        Every subclass matches against appropriate relevance rules
        """

    def attach_rules(self, *rules: RelevanceRule) -> SnapshotDiff:
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
    # This class must override all of the attributes/methods that the
    # SnapshotDiff class operates with. Override the minimum of ServerInfo
    # class as much as it's necessary to fake a reset state from the
    # SnapshotDiff point of view (i.e. just override the attributes and methods
    # used in the SnapshotDiff initializer)
    def __init__(self):
        pass

    def num_humans(self):
        return 0

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



# Relevance rules

class RelevanceRule:
    """Base class for a relevance rule

    Relevance rules represent different rules to check for diff relevance
    """
    def __init__(self, *args):
        if type(self) is RelevanceRule:
            raise NotImplementedError

    def evaluate(self, prev: ServerSnapshot, curr: ServerSnapshot) -> bool:
        """Evaluate the rule on the diff"""

    def _post_match(self, snapshot: ServerSnapshot):
        """Actions to take after the rule is matched, e.g. change snapshot state"""
        pass

class OverThresholdRule(RelevanceRule):
    """Number of players just passed over the threshold"""
    def __init__(self, threshold: int):
        self.threshold = threshold

    def evaluate(self, prev: ServerSnapshot, curr: ServerSnapshot) -> bool:
        return (prev.info.num_humans() < self.threshold and curr.info.num_humans() >= self.threshold)

    def _post_match(self, snapshot: ServerSnapshot):
        snapshot.last_threshold = snapshot.timestamp

class UnderThresholdRule(RelevanceRule):
    """Number of players just passed under the threshold"""
    def __init__(self, threshold: int):
        self.threshold = threshold

    def evaluate(self, prev: ServerSnapshot, curr: ServerSnapshot) -> bool:
        return (prev.info.num_humans() >= self.threshold and curr.info.num_humans() < self.threshold)

    def _post_match(self, snapshot: ServerSnapshot):
        snapshot.last_threshold = snapshot.timestamp

class DurationRule(RelevanceRule):
    """Number of players has been over threshold for some time"""
    def __init__(self, threshold: int):
        self.threshold = threshold
        self.duration = Config.Thresholds.duration_time * 60

    def evaluate(self, prev: ServerSnapshot, curr: ServerSnapshot) -> bool:
        nplayers_check  = curr.info.num_humans() >= self.threshold
        duration_check  = curr.timestamp - curr.last_threshold >= self.duration
        return (duration_check and nplayers_check)

    def _post_match(self, snapshot: ServerSnapshot):
        # TODO: don't modify last_threshold! it will break other rules sooner
        # or later... use a separate variable for duration asap
        snapshot.last_threshold = snapshot.timestamp
