# Importing required libraries
from datasets import load_dataset
from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.components.builders import PromptBuilder
from haystack_integrations.components.generators.ollama import OllamaGenerator
from haystack import Pipeline
import gradio as gr

# Load dataset and create documents
dataset = load_dataset("bilgeyucel/seven-wonders", split="train")
docs = [Document(content=doc["content"], meta=doc["meta"]) for doc in dataset]

# Initialize document store and write documents
document_store = InMemoryDocumentStore()
document_store.write_documents(docs)

# Initialize retriever
retriever = InMemoryBM25Retriever(document_store)

# Define prompt template
template = """
Given the following information, answer the question.

Context:
{% for document in documents %}
    {{ document.content }}
{% endfor %}

Question: {{question}}
Answer:
"""

# Initialize prompt builder
prompt_builder = PromptBuilder(template=template)

generator = OllamaGenerator(model="gemma2:2b",
                            url = "http://localhost:11434",
                            generation_kwargs={
                              "num_predict": 1000,
                              "temperature": 0.9,
                              })


# Create and configure pipeline
basic_rag_pipeline = Pipeline()
basic_rag_pipeline.add_component("retriever", retriever)
basic_rag_pipeline.add_component("prompt_builder", prompt_builder)
basic_rag_pipeline.add_component("llm", generator)
basic_rag_pipeline.connect("retriever", "prompt_builder.documents")
basic_rag_pipeline.connect("prompt_builder", "llm")

# Visualize pipeline (optional)
# basic_rag_pipeline.draw("basic-rag-pipeline.png")

# Define function to run pipeline with Gradio
def ask_question(question):
    response = basic_rag_pipeline.run(
        {
            "retriever": {"query": question}, 
            "prompt_builder": {"question": question}
        }
    )
    return response["llm"]["replies"][0]

# Create Gradio interface
gr_interface = gr.Interface(
    fn=ask_question,
    inputs=gr.components.Textbox(lines=2, placeholder="Enter your question here..."),
    outputs="text"
)

gr_interface.launch()