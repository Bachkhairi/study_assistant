from app.chains.generation_chain import GenerationChain
from app.chains.reflection_chain import ReflectionChain
from app.memory.chat_history import ChatHistory
from app.memory.chunker import SummaryChunker
from app.utils.headingtree import HeadingTreeBuilder
from app.services.notion_manager import NotionManager
from app.utils.descriptor import Descriptor
from app.memory.session_manager import SessionManager
from app.utils.markdown_parser import parse_between_delimiters

class SummaryPipeline:
    def __init__(self):
        self.generation_chain = GenerationChain()
        self.reflection_chain = ReflectionChain()
        self.chunker = SummaryChunker()


    def run_with_descriptor(
        self,
        raw_notes: str,
        established_summary: str,
        old_descriptor: Descriptor,
        session_manager: SessionManager,
        push_to_notion: bool = False,
        first_time: bool = False,
    ) -> dict:
        """
        NEW ARCHITECTURE: Full summarization workflow using descriptor-based context.

        Steps:
        1. Generate initial summary from raw notes.
        2. Use the descriptor (one-phrase-per-section representation of established summary)
        instead of retrieval/condensed context to guide reflection.
        3. Critique and regenerate final summary.
        4. Generate updated descriptor from old_descriptor + headings of established summary

        Args:
            raw_notes (str): The new raw notes to be summarized.
            old_descriptor (Descriptor): Current descriptor string representing the established summary.
            push_to_notion (bool, optional): Whether to push final summary to Notion.

        Returns:
            dict: Contains initial_summary, critique, final_summary_markdown, new_descriptor.
        """

     # Clear separation of state
        initial_summary = ""
        critique = ""
        final_summary_markdown = ""
        new_descriptor = ""

        if not first_time:
            # 1. Generate initial summary
            initial_summary = self.generation_chain.summarize(raw_notes)
            headings = self.chunker.chunk_by_heading(established_summary)
            
            # Save to chat history
            session_manager.chat_history.add_turn(raw_notes, initial_summary,role_1="user", role_2="generation_chain")

            heading_tree = HeadingTreeBuilder(headings).build_tree()

            # 2. Critique using descriptor 
            critique = self.reflection_chain.reflect(
                initial_summary=initial_summary,
                retrieved_context=old_descriptor.content,
                heading_tree=heading_tree
            )
            session_manager.chat_history.add_turn(initial_summary, critique, role_1="generation_chain", role_2="reflection_chain")

            # 3. Regenerate final summary
            final_summary_markdown = self.generation_chain.regenerate(
                initial_summary=initial_summary,
                critique=critique
            )
            session_manager.chat_history.add_turn(critique, final_summary_markdown, role_1="reflection_chain", role_2="generation_chain")

            # 4. Update descriptor
            new_descriptor = old_descriptor.update(final_summary=final_summary_markdown)

        else:
            # First time generation
            final_summary_markdown = self.generation_chain.summarize(
                raw_notes, prompt_type="generation_init"
            )
            headings = self.chunker.chunk_by_heading(final_summary_markdown)
            heading_tree = HeadingTreeBuilder(headings).build_tree()

            session_manager.chat_history.add_turn(raw_notes, final_summary_markdown,role_1="user", role_2="generation_chain")

            new_descriptor = old_descriptor.update(final_summary=final_summary_markdown)

        session_manager.chat_history.add_turn(final_summary_markdown, new_descriptor,role_1="generation_chain", role_2="generation_chain")
        

        # Save chat history to disk
        session_manager.save()

        # 5. Push to Notion (optional)
        if push_to_notion:
            final_summary_markdown = parse_between_delimiters(final_summary_markdown)
            session_manager.notion.write_to_notion(final_summary_markdown)

        return {
            "initial_summary": initial_summary,
            "critique": critique,
            "final_summary_markdown": final_summary_markdown,
            "new_descriptor": new_descriptor
        }