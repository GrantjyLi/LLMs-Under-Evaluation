import ollama
import time

"""Represents one loaded Ollama model. Supports multiple instances at once."""
class LLMSession:
    NUM_PROMPT_ATTEMPTS = 3
    MAX_TOKENS = 128

    def __init__(self, model_name, pull_if_missing = True):
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

    def prompt(self, text, thinking = True) -> str:
        options = {"num_predict": -1}
        if thinking: options["num_predict"] = self.MAX_TOKENS

        for attempt in range(self.NUM_PROMPT_ATTEMPTS):
            try:
                response = ollama.chat(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": text
                        }
                    ],
                    keep_alive=-1,
                    think=thinking
                    # options=options
                )

                # answer = response.get("response", "").strip()
                answer = response.message.content.strip()

                if answer:
                    return answer
                print(f"Empty response (attempt {attempt + 1})")
                print(response)

            except Exception as e:
                print(f"Generation error (attempt {attempt + 1}): {e}")

            time.sleep(1)

        return ""

    def end(self):
        ollama.generate(model=self.model_name, prompt="", keep_alive=0)
        print("==================================================")
        print(f"'{self.model_name}' unloaded.")
        print("==================================================\n")