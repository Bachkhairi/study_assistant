import importlib

class PromptHandler:
    def __init__(self, feature: str, prompt_type: str, **kwargs):
        """
        feature: e.g. 'summarization'
        prompt_type: e.g. 'generation'
        kwargs: data needed to build the prompt (e.g. raw_notes)
        """
        self.feature = feature
        self.prompt_type = prompt_type
        self.kwargs = kwargs
        self.prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        """
        Dynamically loads the prompt generator function from the module.
        """
        module_path = f"app.prompts.{self.feature}.{self.prompt_type}_prompt"
        module = importlib.import_module(module_path)

        if not hasattr(module, "build_prompt"):
            raise AttributeError(f"Module {module_path} must define a build_prompt(**kwargs) function.")

        return module.build_prompt(**self.kwargs)

    def get_prompt(self) -> str:
        return self.prompt



