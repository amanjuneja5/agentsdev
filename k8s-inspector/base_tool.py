import json
from abc import ABC, abstractmethod

class BaseTool(ABC):

    @property
    @abstractmethod
    def schema(self):
        ...

    @property
    def name(self):
        return self.schema["name"]

    @property
    def is_write(self):
        return False

    @abstractmethod
    def execute(self,input):
        ...
    
    def safe_execute(self, input):

        try:
            return self.execute(input)
        except Exception as e:
            return json.dumps({
                "error": f"{type(e).__name__}: {str(e)}",
                "tool": self.name,
                "input": input
            })
    

