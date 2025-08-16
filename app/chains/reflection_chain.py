from app.utils.llm import GroqModel
from app.prompts.base import PromptHandler
  

class ReflectionChain:
    def __init__(self):
        self.model = GroqModel()

    def run(self, context_history: list[dict[str, str]] = None,prompt_type="reflection",feature="summarization", **kwargs) -> str:

        if context_history is None:
            context_history = []

        prompt_args = {**kwargs}

        prompt = PromptHandler(
            feature=feature,  
            prompt_type=prompt_type,
            **prompt_args
        )._load_prompt()

        history = context_history.copy()
        history.append({"role": "user", "content": prompt})

        critique = self.model.chat_completion(history)

        history.append({"role": "assistant", "content": critique})

        return critique

    def reflect(self, initial_summary: str, retrieved_context: str, heading_tree: str) -> str:
        
        return self.run(initial_summary=initial_summary, retrieved_context=retrieved_context, heading_tree=heading_tree)

    def select_block(self, question: str, retrieved_blocks: str) -> str:
        
        return self.run(question=question, retrieved_blocks=retrieved_blocks, prompt_type="relevant_block",feature="question_answering")
