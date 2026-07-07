from datetime import datetime
from typing import List
from ..config.settings import Settings
from ..models.cycle import Cycle, CycleStatus
from ..models.incident import Incident
from ..observe.runner import observe_all
from ..analyzer.registry import get_analyzers
from ..diagnosis.engine import DiagnosisEngine
# I run one full observe -> detect -> diagnose cycle
class CycleRunner:
    def __init__(self):
        self.diagnoser = DiagnosisEngine()
    def run(self, cfg: Settings, trigger: str="manual") -> tuple[Cycle, List[Incident]]:
        from ..models.cycle import CycleTrigger
        try:
            ct = CycleTrigger(trigger)
        except Exception:
            ct = CycleTrigger.manual
        cycle = Cycle(trigger=ct, status=CycleStatus.running)
        cycle.observe_at = datetime.utcnow()
        results = observe_all(cfg)
        cycle.detect_at = datetime.utcnow()
        # I run all registered analyzers
        incidents: List[Incident] = []
        analyzers = get_analyzers()
        for r in results:
            for a in analyzers:
                try:
                    found = a.analyze(r)
                    incidents.extend(found)
                except Exception as e:
                    cycle.errors.append(f"{a.name}:{e}")
        cycle.incidents_detected = len(incidents)
        # I diagnose
        cycle.diagnose_at = datetime.utcnow()
        diagnosed = []
        for inc in incidents:
            # find signals for this target
            sigs = []
            for res in results:
                if res.target_name == inc.target_id:
                    sigs = res.signals
                    break
            try:
                d = self.diagnoser.diagnose(inc, sigs)
                diagnosed.append(d)
            except Exception as e:
                cycle.errors.append(f"diagnose:{e}")
                diagnosed.append(inc)
        cycle.completed_at = datetime.utcnow()
        cycle.status = CycleStatus.completed if not cycle.errors else CycleStatus.failed
        return cycle, diagnosed
def run_cycle(cfg: Settings, trigger: str="manual"):
    runner = CycleRunner()
    cyc, incs = runner.run(cfg, trigger)
    # I persist if DB configured
    if cfg.database.dsn:
        try:
            from ..db.base import Database
            from ..db.session import CycleStore, IncidentStore
            db = Database(cfg.database.dsn)
            db.migrate()
            sess = db.get_session()
            try:
                cs = CycleStore(sess); cs.create(cyc)
                istore = IncidentStore(sess)
                for inc in incs:
                    inc.cycle_id = cyc.id
                    try:
                        istore.create(inc)
                    except Exception:
                        pass
            finally:
                sess.close(); db.close()
        except Exception:
            pass
    return cyc
