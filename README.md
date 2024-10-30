# bus_copilot
 Co pilot for business owners. Create your database about business. Chat or Call the co-pilot to become your social media manager, website content manager, lead generator, market researcher, competitor analyser, outbound/inbound support specialist and much more.
Created from the great open source repo from https://www.quivr.com (Apache license).
Limitations:
1. Currently only supports OpenAI embeddings out of the box
2. No local embedding options available by default
3. Limited configuration options for embedding parameters
To add new embedding functionality, you would need to:
1. Create a new embedder class implementing the `Embeddings` interface from langchain_core
2. Update the `EmbedderConfig` to support new embedding types
3. Add appropriate configuration in the `LLMModelConfig