# Running Small LLMs Locally for PDF Processing with Ollama


## Background

Ollama is a framework for running large language models (LLMs) locally on personal hardware. Its desktop application (Mac/Windows) allows users to select a model, interact with it via a chat interface and even drag-and-drop files for analysis. An article reviewing the latest Ollama release notes that the app can accept `.pdf`, `.md` and `.txt` files and the selected model will analyse the contents of the file – making it useful for summarising or extracting key points from lengthy documents.

For more advanced workflows, developers can use the Ollama CLI or local API server and combine it with tools like LangChain to process documents.

However, the Ollama library itself does not natively accept PDF files as input. A March 2025 blog on structured extraction with Ollama explains that "Ollama does not support PDF files directly as input, so we need to convert them to markdown first". This means users must either convert a PDF to text (or images) themselves or rely on the desktop app's built-in extraction.

## Alternative Approaches for Processing PDFs with Local Models

### 1. Use Ollama's Desktop App (Drag-and-Drop)

**How it works:** Select a model (e.g., llama3, mistral or dolphin3) in the Ollama desktop app. Drag a `.pdf` into the chat window and ask the model to summarise or extract information. The app extracts the text behind the scenes and feeds it into the model.

**Advantages:**
- **Simplicity:** No coding or preprocessing; works offline; privacy-friendly
- **Fast setup:** Useful for quick summaries, extracting key points, or asking questions about the document
- **Model-agnostic:** Works with any text-only model in Ollama (e.g., llama3, mistral, dolphin3, qwen2.5)

**Disadvantages:**
- **Limited control:** You cannot customise how the document is chunked or summarised. Large PDFs may exceed the context window of smaller models
- **Non-customisable extraction:** The built-in extraction may not handle complex formatting (tables, charts or scanned pages) and cannot perform retrieval-augmented generation (RAG)
- **Requires the GUI:** Not suitable for automated workflows or integration into existing applications

### 2. Text-Based Processing via LangChain (convert PDF to text)

**How it works:** Use a Python script or LangChain pipeline to load a PDF file, split it into pages (e.g., via PyPDFLoader), generate embeddings and feed the text to a local LLM served by Ollama. A tutorial by Pantelis Vratsalis demonstrates such a workflow: a PyPDFLoader extracts pages from a PDF, the pages are embedded using an embedding model (bge:small), and a local llama3 model answers questions using a retrieval chain. This is essentially a RAG pipeline that can be adapted for summarisation or question answering.

**Advantages:**
- **Full control:** You decide how to split documents, what embeddings to use and how to craft prompts (stuffing, map-reduce, or retrieval). This allows targeted queries (e.g., "show me all dates in the document")
- **Scalable:** You can handle documents longer than the model's context by chunking or using the map-reduce summarisation approach (LangChain's load_summarize_chain)
- **Composable with other tools:** Integrates with vector stores, query filters, and pipelines for multi-document corpora

**Disadvantages:**
- **Requires coding:** Must set up a Python environment, install packages (langchain, pypdf, etc.) and write the pipeline
- **Preprocessing overhead:** Extracting and embedding pages takes time; external dependencies may need configuration (e.g., PyPDF fails with scanned images)
- **Purely text-based:** Cannot interpret diagrams, charts or scanned text unless additional OCR or vision models are used

### 3. Vision-Language Models on PDF Pages (convert to images)

For scanned PDFs or documents containing tables and diagrams, a text-only model may miss important information. In such cases, you can convert each PDF page to an image (e.g., using pdf2image) and feed the images to a vision-language model supported by Ollama.

#### Notable Vision Models

| Vision Model | Key Capabilities | Pros | Cons |
|-------------|------------------|------|------|
| **LLaVA 1.6** (llava:7b, 13b, 34b) | End-to-end multimodal model combining vision encoder and Vicuna for general-purpose visual and language understanding. Version 1.6 increases input image resolution and improves visual reasoning and OCR. | Good general-purpose model; supports text + image input; improved OCR for reading charts and diagrams; easily called via API | Larger variants (13B and 34B) consume significant GPU memory; still limited context window (4K–32K); may not handle long documents without chunking |
| **MiniCPM-V 2.6** (minicpm-v:8b) | Built on SigLip-400M and Qwen2-7B (8B parameters). Achieves strong performance on OCR benchmarks and surpasses proprietary models like GPT-4V in single image understanding. Offers multi-image reasoning and strong OCR across any aspect ratio, producing only 640 tokens for a 1.8M-pixel image. | Excellent OCR performance and can process large images; supports multi-image reasoning; efficient token density reduces latency | Requires Ollama ≥ 0.3.10; still relatively large (5.5 GB). Multimodal context limited to ~32K tokens |
| **Qwen 2.5-VL** (qwen2.5vl:3b/7b/32b/72b) | Flagship vision-language model; proficient at recognizing objects and analysing texts, charts and layouts. Can act as a visual agent, localize objects (bounding boxes) and generate structured outputs (JSON) for invoices, forms and tables. | Provides structured outputs and bounding boxes for documents; good for extracting tabular data and layouts; supports large context (125K tokens) and smaller parameter versions (3B, 7B) | Requires Ollama ≥ 0.7.0; models are large (3–49 GB) and need a GPU. Only English supported for image+text tasks |
| **Llama 3.2 Vision** (llama3.2-vision:11b/90b) | Instruction-tuned image reasoning models that excel in visual recognition, captioning and answering general questions about images. Supports 128K context windows and multiple languages for text-only tasks. | High context window (up to 128K tokens); good at image reasoning and captioning; integrated Python/JS API examples provided | Large models (7.8–55 GB); image-support currently limited to English; not specialised for OCR or structured outputs |
| **Gemma 3 Multimodal** (gemma3:4b/12b/27b) | Lightweight multimodal models built on Google's Gemini technology; 128K context window; support over 140 languages. Excel at question answering, summarisation and reasoning and can run on resource-limited devices. | Efficient models with quantization-aware versions; broad language support; can process images and text; suitable for summarisation and reasoning on single GPU | OCR and structured extraction capabilities are less advanced than MiniCPM-V or Qwen2.5-VL; vision support only in the 4B+ variants |

#### Workflow

Convert each PDF page to an image and send it as base64 to the model through the Ollama API. For example, llava can be run via:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llava", 
  "prompt": "Describe the main figures on this page", 
  "images": ["<base64-encoded page image>"]
}'
```

**Advantages:**
- **Handles scanned documents and diagrams:** Vision models can read charts, tables and handwritten notes
- **OCR and layout awareness:** Models like Qwen 2.5-VL and MiniCPM-V provide strong OCR and can output structured JSON, making them suitable for invoices or forms
- **Agentic interactions:** Qwen 2.5-VL can localize objects and act as a visual agent, enabling complex tasks like highlighting a region or extracting fields

**Disadvantages:**
- **Resource intensive:** Vision models are larger (3–55 GB) and typically require a GPU. Processing many pages may be slow
- **Limited language support:** Image+text tasks are usually limited to English
- **Still require preprocessing:** Need to convert PDF pages to images and encode them into base64; long documents may need chunking and iterative calls

### 4. External OCR + Text Models

**How it works:** Use an open-source OCR library (e.g., Tesseract or pdf2text) to extract text from scanned PDFs. Once text is extracted, feed it into a small text-only LLM through Ollama. Because Ollama does not accept PDFs directly, this approach replicates the extraction stage yourself. You can then apply RAG or summarisation as in approach 2.

**Advantages:**
- **Flexibility:** You can choose the OCR engine and adjust language and quality settings
- **Lightweight:** OCR plus a 1–3B parameter model (e.g., qwen2.5:1.5b or phi3) can run on CPU-only systems
- **Good for simple scanned documents:** Works well when PDF pages are straightforward text with minimal layout complexity

**Disadvantages:**
- **Preprocessing complexity:** You must manage OCR errors, page segmentation and language detection
- **No visual understanding:** Cannot interpret charts or images; accuracy depends on OCR quality

### 5. Structured Extraction using RAG or Agentic Models

**How it works:** For extracting specific fields (e.g., invoice numbers, totals) from PDFs, combine conversion, an extraction routine and a model capable of structured outputs. The CocoIndex blog shows an example where a PDF is converted to markdown via a custom function (using PdfConverter), then an LLM extracts structured data (e.g., classes and methods). Alternatively, vision-language models like Qwen 2.5-VL can directly generate structured JSON containing table or form contents.

#### Possible Approaches:

1. **Convert PDF to markdown/text:** Use a text model (e.g., qwen2.5 or deepseek-r1) with function-calling support to extract fields. Mistral 0.3 supports function calling and can call custom functions to process data

2. **Use Qwen 2.5-VL:** Analyze scans, localize key fields and output structured JSON for each page

3. **Combine RAG with embedding model:** Use an embedding model such as bge:small-en-v1.5 for retrieval and a small LLM for answering queries

**Advantages:**
- **Structured outputs:** Suitable for building pipelines to extract data into databases or spreadsheets
- **Scalable to multiple documents:** Embedding-based retrieval can handle many files

**Disadvantages:**
- **Complex pipeline:** Requires multiple steps (conversion, embedding, extraction) and integration of external libraries
- **Computational cost:** Vision-language models for structured outputs are large; function-calling may require additional engineering

## Choosing an Ollama Model for PDF Processing

Selecting the right model depends on your hardware and the nature of your PDFs. Below is a summary of some notable models and their suitability for various tasks.

| Task | Recommended Models | Reasoning |
|------|-------------------|-----------|
| **General summarisation / Q&A on text** | • llama3 (8B/70B) – state-of-the-art open model; instruction-tuned for chat<br>• mistral:7b – 7B model outperforming Llama 2 13B and supporting function calling<br>• qwen2.5 (1.5–14B) – supports long context (up to 128K tokens) and excels at structured outputs and multilingual tasks<br>• dolphin3 – an 8B instruct model designed as a steerable general-purpose assistant with function-calling and agentic abilities | These models provide strong language understanding, good reasoning and relatively small sizes (1–8B). qwen2.5 offers the longest context (128K tokens) and improved structured data handling. mistral includes function-calling, which can be useful when building pipelines. |
| **Large document summarisation / long context** | • qwen2.5 or deepseek-r1 – both support very long contexts (128K tokens)<br>• dolphin3 also offers a 128K context window | When a PDF's text runs into tens of thousands of tokens, a long-context model prevents truncation. deepseek-r1 emphasises reasoning and has strong benchmark results. |
| **Scanned PDFs, charts and diagrams** | • qwen2.5-vl – excels at analysing texts, charts, icons, graphics and layouts, can localize objects and output structured JSON<br>• minicpm-v – strong OCR and multi-image reasoning; efficient token density<br>• llava – general-purpose vision model with improved OCR | Vision-language models allow processing of images; use them when the PDF contains scans or complex layouts. They can produce structured outputs and handle diagrams. Convert pages to images for input. |
| **Resource-constrained systems** | • gemma3:1b (32K context, text-only) or quantization-aware versions (*-it-qat) – built on Gemini technology; multimodal versions start at 4B and can run on a single GPU<br>• qwen2.5:0.5b – small parameter size with 32K context | These models provide decent summarisation and reasoning while requiring less VRAM. Quantization-aware models reduce memory usage by ~3×. |
| **Agentic tasks / function calling** | • mistral v0.3 – supports function calling via raw mode<br>• dolphin3 – emphasises agentic abilities and allows custom system prompts<br>• qwen2.5-vl – can act as a visual agent and direct tools | Use these models when you need the LLM to call external functions (e.g., send emails, query a database) or behave as an autonomous agent. |

## Practical Workflow Suggestions

### Quick Document Summaries
For quick document summaries on a single machine, install the Ollama desktop app. Pull llama3 or mistral, drag the PDF into the chat and ask the model to summarise. This is the fastest path for occasional use.

### Automated Pipelines
For automated pipelines or long documents, build a Python script using LangChain. Extract text with PyPDFLoader, split into chunks, and run a RAG pipeline with embeddings (nomic-embed-text or bge-small) and a local model (e.g., qwen2.5:7b). If the document is scanned, apply OCR first.

### Documents with Tables/Forms/Diagrams
For documents containing tables, forms or diagrams, convert each page to an image and use a vision-language model:
- **qwen2.5-vl** provides structured JSON outputs for invoices and forms
- **minicpm-v** offers strong OCR and multi-image reasoning
- **llava** is a general-purpose multimodal assistant

### Structured Field Extraction
For extracting specific fields (e.g., invoice totals), design a function-calling workflow. Use a text-only model with long context (e.g., mistral or qwen2.5) and call a function that parses the extracted text. Alternatively, rely on qwen2.5-vl to return a JSON with the required fields.

## Conclusion

Ollama offers a growing ecosystem of small and medium-sized models that can be run locally. The system itself does not read PDFs natively; instead, it provides extraction within the desktop app or requires you to convert PDFs into text or images. 

The choice of method depends on the complexity of the document and your hardware:

- **Text-only models** like Llama 3, Mistral and Qwen 2.5 are excellent for general summarisation and question answering
- **Vision-language models** like Qwen 2.5-VL, MiniCPM-V, LLaVA and Llama 3.2 Vision are indispensable for scanned documents, forms, diagrams and structured extraction

Combining these models with frameworks such as LangChain or custom OCR pipelines allows you to build flexible, privacy-preserving PDF-processing solutions on your own computer.