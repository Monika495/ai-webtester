"""
Basic Agent - Main coordinator
"""
from agent.parser_agent import InstructionParser
from agent.codegen_agent import CodeGenerator
from agent.executor_agent import Executor


class BasicAgent:
    """
    Main agent that coordinates everything
    """
    
    def __init__(self, gemini_api_key=None):
        self.parser = InstructionParser(api_key=gemini_api_key)
        self.codegen = CodeGenerator()
        self.executor = Executor()
    
    def process_instructions(self, instruction: str, headless=True):
        """
        Process instruction and return all results
        """
        # Step 1: Parse instruction
        parsed = self.parser.parse(instruction)
        
        # Step 2: Execute actions
        execution = self.executor.run(parsed, headless=headless)
        
        # Step 3: Generate code
        generated_code = self.codegen.generate(parsed)
        
        return {
            "instruction": instruction,
            "parsed": parsed,
            "generated_code": generated_code,
            "execution": execution
        }