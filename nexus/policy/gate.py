from .opa import OPAClient
from ..models.incident import Incident
from ..models.action import Action
# I am the policy gate – every autonomous action passes through me
class PolicyGate:
    def __init__(self):
        self.opa = OPAClient()
    def evaluate(self, incident: Incident, action: Action, autonomy_level: int):
        result = self.opa.evaluate(incident, action, autonomy_level)
        return result["decision"], result["reason"]
