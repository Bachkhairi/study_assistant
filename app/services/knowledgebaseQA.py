from app.memory.chunker import SummaryChunker
from app.services.notion_manager import NotionManager
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from app.memory.chunker import SummaryChunker
from app.chains.generation_chain import GenerationChain
from app.chains.reflection_chain import ReflectionChain
from app.utils.markdown_parser import parse_between_delimiters
from app.memory.vector_store_chroma import VectorStore
import os, json, re, ast
import webbrowser
import warnings

warnings.filterwarnings("ignore")  # Ignore all warnings




def make_notion_urls(page_title: str, page_id: str, block_ids=None):
    # Remove emojis & special symbols
    clean_title = re.sub(r'[^\w\s-]', '', page_title).strip()

    # Replace multiple spaces/hyphens with single hyphen
    slug = re.sub(r'[\s-]+', '-', clean_title)

    # Remove accidental consecutive duplicates in titles
    # Example: "Page-1-Introduction-Page-1-Introduction" → "Page-1-Introduction"
    parts = slug.split('-')
    half = len(parts) // 2
    if len(parts) % 2 == 0 and parts[:half] == parts[half:]:
        slug = '-'.join(parts[:half])

    clean_page_id = page_id.replace("-", "")
    base = f"https://www.notion.so/{slug}-{clean_page_id}"

    urls = []

    if block_ids:
        # If block_ids is given as a string like "['id1', 'id2']", parse it
        if isinstance(block_ids, str):
            try:
                block_ids = ast.literal_eval(block_ids)
            except:
                raise ValueError("block_ids is a string but not a valid list literal")

        if not isinstance(block_ids, (list, tuple)):
            raise TypeError("block_ids must be a list or tuple of IDs")

        for bid in block_ids:
            clean_bid = bid.replace("-", "")
            urls.append(f"{base}#{clean_bid}")
    else:
        urls.append(base)

    return urls


def open_url_in_existing_tab(url):
    # Try to open URL in the same tab/window (new=0)
    webbrowser.open(url, new=0)










class QueryPipeline:
    def __init__(self, data_path: str = "/home/khairi/ai_assistant/data/AI-assistant", notion_project_id:str = "23cd95d8323d80f88765cce2de644966", persist_directory: str = "chroma_db"):
        self.vector_store = VectorStore()
        self.generation_chain = GenerationChain()
        self.reflection_chain = ReflectionChain()
        self.data_path = data_path
        self.notion = NotionManager(folder_id=notion_project_id)
        self.chunker = SummaryChunker()
        self.embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.persist_directory = persist_directory

    def index_knowlegde_base(self, folder_name:str = ""):
        
        CHUNKS_PATH = os.path.join(self.data_path,"chunks.json")
        # check if data already exists
        if not os.path.exists(CHUNKS_PATH):
    
            #metadata.json
            pages = self.notion.get_pages_hierarchy(parent_id=self.notion.folder_id,folder_name=folder_name)
            #chunks.json
            results = self.notion.get_all_pages_in_hierarchy_grouped(pages, folder_name=folder_name)
            all_chunks = self.chunker.semantic_subchunk_paragraph(data_items=results)


            # Save chunks locally
            with open(CHUNKS_PATH, "w") as f:
                json.dump(all_chunks, f, indent=2)

        # Step 2: Embedding setup
        with open(CHUNKS_PATH, "r") as f:
            data = json.load(f)
            #print(f"======\n\n {CHUNKS_PATH} \n\n =======")
            #print(data)
        
        # Step 3: Index the chunks into Chroma

        vector_store = VectorStore(persist_directory=self.persist_directory)
        vector_store.index_documents(data)

        print("[✔] Data indexed successfully into Chroma.")

    def answer_question(self, question: str):

        # load the vectordb

        vector_store = VectorStore(persist_directory=self.persist_directory)

        results = vector_store.retrieve(
            query=question,
            k=10
        )

        context = ""
        blocks_list = []
        for doc, score in results:
            paragraph = doc.metadata.get("paragraph", "")
            block_ids = doc.metadata.get("block_ids", "").split(",")
            
            page = doc.metadata.get("page", "")
            page_id = doc.metadata.get("page_id", "")
            blocks_list.append({
                "content": paragraph,
                "page_title": page,
                "page_id": page_id,
                "block_ids": block_ids
            })
            #print("Paragraph:", paragraph)
            #print("Block IDs:", block_ids)
            #print("Page:", page)
            #print("Page_id:", page_id)
            #print(f"Similarity Score: {score:.4f}")  # Lower is better if it's cosine distance
            #print("------")

            # Optionally include the score in the context too
            context += f"{paragraph.strip()}\n(Similarity Score: {score:.4f})\n\n"


        answer = self.generation_chain.question_answering(context=context, question=question)
        #print("block ids:", blocks_list)
        reflector_response = self.reflection_chain.select_block(question=question, retrieved_blocks=blocks_list)
        #print("reflector response: ", reflector_response)
        block_ids = parse_between_delimiters(output=reflector_response, delimiter="<<blockids>>").strip("'")
        page_id = parse_between_delimiters(output=reflector_response, delimiter="<<pageid>>").strip("'")
        page_title = parse_between_delimiters(output=reflector_response, delimiter="<<pagetitle>>").strip("'")
        print("\n")
        print("LLM Answer: \n")
        print(answer)
        print("\n")
        print("block ids: \n")
        print(block_ids)

        urls = make_notion_urls(page_title=page_title, page_id=page_id, block_ids=block_ids)
       # print("Generated URLs:", urls)

        
        for url in urls: 
            open_url_in_existing_tab(url)
        

        return results  
    
