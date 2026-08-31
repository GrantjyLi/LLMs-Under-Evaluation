import sys
import os
import importlib.util

# Get the project root and Prompts directory
project_root = os.path.dirname(__file__)
prompts_dir = os.path.join(project_root, "Prompts")

# Add Prompts directory to sys.path for LLMSession imports
sys.path.insert(0, prompts_dir)

# Change to project root for relative file paths
os.chdir(project_root)

# Load prompting.py as a module
spec = importlib.util.spec_from_file_location("prompting", os.path.join(prompts_dir, "prompting.py"))
prompting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prompting)

if __name__ == "__main__":
    prompting.main()
