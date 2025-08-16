from app.utils.llm import GroqModel
from app.prompts.base import PromptHandler
from app.utils.descriptor import Descriptor


class GenerationChain:
    def __init__(self):
        self.model = GroqModel()

    def run(self, context_history: list[dict[str, str]] = None, prompt_type: str = "generation",feature: str="summarization", **kwargs) -> str:
        """
        Run the generation chain with the current notes and optional chat history.

        Args:
            notes (str): User-provided notes.
            context_history (list): Optional past messages for context.
            prompt_type (str): Type of prompt ('generation', 'condensed', etc.)
            **kwargs: Additional keyword arguments for prompt building (e.g. retrieved_context)

        Returns:
            str: Generated summary content.
        """
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

        response = self.model.chat_completion(history)

        history.append({"role": "assistant", "content": response})

        return response

    def summarize(self, notes: str, prompt_type: str = "generation") -> str:
        """
        Simple wrapper for initial summarization of raw notes.

        Args:
            notes (str): Raw notes from user.

        Returns:
            str: Cleaned summary.
        """
        return self.run(input=notes, prompt_type=prompt_type)

    def condense(self, retrieved_context: str) -> str:
        """
        Use retrieved context to generate a condensed summary.

        Args:
            notes (str): The new user-provided raw notes.
            retrieved_context (str): Context retrieved from previous summary.

        Returns:
            str: Condensed and coherent summary extension.
        """
        return self.run(input=retrieved_context, prompt_type="condensed")
    
    def regenerate(self, initial_summary: str, critique: str) -> str:
        """
        Use retrieved context to generate a condensed summary.

        Args:
            notes (str): The new user-provided raw notes.
            retrieved_context (str): Context retrieved from previous summary.

        Returns:
            str: Condensed and coherent summary extension.
        """

        final_summary_markdown = self.run(initial_summary=initial_summary, critique=critique, prompt_type="regeneration")
        return final_summary_markdown
    

    def build_descriptor(self, old_descriptor: Descriptor, final_summary: str):
        """
        Builds an updated global descriptor for the entire summary.

        This method takes the previous descriptor (a compact hierarchical representation
        of the existing summary) and the newly generated `final_summary_json`. It then
        calls the generation chain (`self.run`) with the "descriptor" prompt type to 
        merge both inputs into a refreshed descriptor.

        Args:
            old_descriptor (Descriptor): The current descriptor instance containing the 
                                        existing one-phrase-per-section summary.
            final_summary_json (str): The latest final summary in structured JSON format.

        Returns:
            str: A newly generated descriptor string reflecting the entire updated summary.
        """

        return self.run(
            old_descriptor=old_descriptor.content, 
            final_summary = final_summary,
            prompt_type="descriptor"
        )

    def question_answering(self, context: str, question: str):

        return self.run(context=context, 
                        question=question,
                        feature="question_answering",
                        prompt_type="qa"
                    )
    def question_answering_video(self, context: str, question: str):

        return self.run(context=context, 
                        question=question,
                        feature="qa_video",
                        prompt_type="qa"
                    )