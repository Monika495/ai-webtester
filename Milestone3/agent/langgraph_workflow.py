from typing import Dict, Any
from agent.parser_agent import InstructionParser
from agent.codegen_agent import CodeGenerator
from agent.executor_agent import Executor

class Workflow:
    """
    LangGraph-style workflow for test automation
    """
    
    def __init__(self):
        self.parser = InstructionParser()
        self.executor = Executor()
        self.codegen = CodeGenerator()

    def run(self, instruction: str, headless: bool = True) -> Dict[str, Any]:
        """
        Run complete workflow
        """
        # Parse
        parsed = self.parser.parse(instruction)
        
        # Execute
        results = self.executor.run(parsed, headless=headless)
        
        # Generate code
        code = self.codegen.generate(parsed)
        
        return {
            "instruction": instruction,
            "parsed": parsed,
            "generated_code": code,
            "execution": results
        }
