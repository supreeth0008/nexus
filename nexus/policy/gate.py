from ..models.action import Action
from ..models.incident import Incident
from ..utils.metrics import inc as metrics_inc
from .opa import OPAClient


# I am the policy gate – every autonomous action passes through me
class PolicyGate:
    def __init__(self):
        self.opa = OPAClient()
    def evaluate(self, incident: Incident, action: Action, autonomy_level: int):
        result = self.opa.evaluate(incident, action, autonomy_level)
        metrics_inc(
            "nexus_policy_decisions_total",
            labels={"decision": result.get("decision", "deny")},
        )
        return result["decision"], result["reason"]
