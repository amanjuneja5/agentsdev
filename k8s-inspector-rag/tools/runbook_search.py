from base_tool import BaseTool


class RunbookSearch(BaseTool):

    def __init__(self, retreiver=None):
        self.retreiver = retreiver
    
    @property
    def schema(self):
        return {
            "name": "search_runbooks",
            "description": "Search the infrastructure runbook knowledge base for relevant procedures, troubleshooting steps, and best practices. Use when you need guidance on how to diagnose or fix an issue",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search for in the runbooks"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "The number of matching top results to return from the runbooks. default to 3"
                    }
                },
                "required": ["query", "top_k"]
            }
        }

    def execute(self, input):

        query = input.get("query", "")
        top_k = input.get("top_k", 3)

        result = self.retreiver.search(query, top_k)            
        
        return result