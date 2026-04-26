from tools.pod_status import PodStatus
from tools.deploys import RecentDeploys
from tools.metrics import QueryMetrics
from tools.error_logs import ErrorLogs
from tools.rollback import RollbackDeployment
from tools.scale import ScaleReplicas
from tools.runbook_search import RunbookSearch

_TOOLS = [
    PodStatus(),
    RecentDeploys(),
    QueryMetrics(),
    ErrorLogs(),
    RollbackDeployment(),
    ScaleReplicas(),
    RunbookSearch()
]

ALL_SCHEMAS = [t.schema for t in _TOOLS]

TOOL_MAP = {t.name: t for t in _TOOLS}