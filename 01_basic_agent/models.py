from dataclasses import dataclass
from functools import total_ordering

@total_ordering
@dataclass
class Finding:
    pod: str
    issue: str
    severity: int
    fix: str

    def __lt__(self, other):
        if not isinstance(other, Finding):
            raise NotImplemented
        return self.severity < other.severity
    
    def __eq__(self, other):
        if not isinstance(other, Finding):
            raise NotImplemented
        return f"{self.pod} + {self.issue}" == f"{other.pod} + {other.issue}"

    def __str__(self):
        return f"[{Finding.get_sev_text(self.severity)}] pod/{self.pod} - {self.issue} | Fix: {self.fix}"

    @staticmethod
    def get_sev_text(severity:int):
        sev_text_map = {
            1   :   "LOW",
            2   :   "MEDIUM",
            3   :   "HIGH"
        }
        return sev_text_map[severity]

class Report:

    def __init__(self, cluster_id: str, findings: list[Finding]):
        self.cluster_id = cluster_id
        self._findings = sorted(findings, reverse=True)
    
    def __len__(self):
        return len(self._findings)
    
    def __bool__(self):
        return len(self._findings) > 0

    def __iter__(self):
        return iter(self._findings)

    def __contains__(self, item):
        if isinstance(item, int):
            return any(f.severity == item for f in self._findings)
        if isinstance(item,str):
            return any(f.pod == item for f in self._findings)
        return False
        

    def __str__(self):
        h_count = 0
        m_count = 0
        l_count = 0
        for f in self._findings:
            if f.severity == 3:
                h_count += 1
            elif f.severity == 2:
                m_count +=1
            elif f.severity == 1:
                l_count +=1
        
        return f"Report({self.cluster_id}, {len(self._findings)} findings: {h_count} high {m_count} med, {l_count} low)"

