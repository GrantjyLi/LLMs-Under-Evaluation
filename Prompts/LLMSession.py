import ollama

"""Represents one loaded Ollama model. Supports multiple instances at once."""
class LLMSession:

    def __init__(self, model_name: str, pull_if_missing: bool = True):
        self.model_name = model_name
        self._pull_if_missing = pull_if_missing

        available = [m["model"] for m in ollama.list()["models"]]
        if self.model_name not in available:
            if self._pull_if_missing:
                print(f"Pulling '{self.model_name}'...")
                ollama.pull(self.model_name)
            else:
                raise ValueError(f"'{self.model_name}' not pulled locally.")

        ollama.generate(
            model=self.model_name, 
            prompt="", 
            keep_alive=-1
        )

        print("==================================================")
        print(f"'{self.model_name}' loaded.")
        print("==================================================\n")

    def prompt(self, text: str) -> str:
        response = ollama.generate(
            model=self.model_name, 
            prompt=text, 
            keep_alive=-1,
            options={
                "num_predict": 256
            }
        )
        return response["response"]

    def end(self):
        ollama.generate(model=self.model_name, prompt="", keep_alive=0)
        print("==================================================")
        print(f"'{self.model_name}' unloaded.")
        print("==================================================\n")