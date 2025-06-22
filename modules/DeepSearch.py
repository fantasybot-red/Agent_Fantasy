import asyncio
import io
import json
import os
import traceback
from typing import Dict, List, Optional, Any

import aiohttp
import numpy as np
from numpy.linalg import norm
from markitdown import MarkItDown, DocumentConverterResult, StreamInfo

from classs import Module, tool
from classs.AIContext import AIContext
from google_custom_search import Item


class DeepSearch(Module):

    def __init__(self, client):
        super().__init__(client)
        self.md = MarkItDown(enable_plugins=True, enable_builtins=True)
        self.feature_extraction_model = os.getenv('HUGGINGFACE_MODEL_FEATURE_EXTRACTION')
        self.openai_model = os.getenv('OPENAI_API_MODAL')

    async def process_body(self, item: Item) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(item.url) as response:
                    if response.status != 200:
                        return None
                    stream_info = StreamInfo(mimetype=response.content_type, charset=response.charset)
                    io_body = io.BytesIO(await response.read())
                    content: DocumentConverterResult = await asyncio.to_thread(
                        self.md.convert, io_body, stream_info=stream_info
                    )
                    return content.markdown
        except Exception as e:
            print(f"Error processing {item.url}: {str(e)}")
            return None

    async def process_search_results(self, context: str, search_results: List[Item]) -> str:

        documents_raw = await asyncio.gather(*[self.process_body(result) for result in search_results])
        cleaned_documents = [doc for doc in documents_raw if doc is not None]

        if not cleaned_documents:
            return "No valid documents found in search results."

        try:
            context_features = await self.client.huggingface.feature_extraction(
                model=self.feature_extraction_model,
                text=context
            )
        except Exception as e:
            print(f"Error extracting features from context: {str(e)}")
            return "\n\n---\n\n".join(cleaned_documents[:3])

        similarity_results = []
        for doc in cleaned_documents:
            try:
                doc_features = await self.client.huggingface.feature_extraction(
                    model=self.feature_extraction_model,
                    text=doc
                )
                similarity = self._calculate_similarity(context_features, doc_features)
                similarity_results.append({"text": doc, "similarity": similarity})
            except Exception as e:
                print(f"Error processing document: {str(e)}")
                continue

        if not similarity_results:
            return "\n\n---\n\n".join(cleaned_documents[:3])

        similarity_results.sort(key=lambda x: x["similarity"], reverse=True)
        relevant_context = "\n\n---\n\n".join([doc["text"] for doc in similarity_results[:3]])
        return relevant_context

    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        n1 = norm(v1)
        n2 = norm(v2)
        if n1 == 0 or n2 == 0:
            return 0.0

        return np.dot(v1, v2) / (n1 * n2)

    @tool(
        prompt="Search query for deep search",
        target_context="Content to search for in the results"
    )
    async def deep_search(self, ctx: AIContext, search_query: str, target_context: str) -> Dict[str, Any]:
        """
        Execute targeted web search based on user prompt:

        REQUIREMENTS:
        - Call `set_status` before search
        - Use English queries only
        - Make queries concise yet specific for optimal results
        - Define detailed target context for content filtering
        - Request clarification for ambiguous prompts
        - No NSFW content searches allowed

        OUTPUT RULES:
        - Use only information from search results - no fabrication
        - Return error message if search fails or format is unexpected
        - Preserve original context and language when possible
        - Translate/reformat only when necessary for readability
        """

        if (self.client.google_search_client is None or
                self.client.huggingface is None or
                not self.feature_extraction_model):
            return {
                "success": False,
                "reason": "Deep search is not enabled. Missing required dependencies."
            }

        results = []
        current_target = target_context
        max_iterations = 20
        iterations = 0

        while iterations < max_iterations:
            iterations += 1

            search_results = []
            try:
                async for result in self.client.google_search_client.asearch(search_query, limit=5):
                    search_results.append(result)
            except Exception as e:
                print(f"Search error: {str(e)}")
                return {
                    "success": False,
                    "reason": f"Search failed: {str(e)}",
                    "results": results
                }

            if not search_results:
                return {
                    "success": False,
                    "reason": "No search results found.",
                    "results": results
                }

            list_results = [{
                "title": result.title,
                "url": result.url,
                "snippet": result.snippet
            } for result in search_results]

            evaluation_message = self._create_evaluation_message(
                target_context, current_target, search_query, results, list_results
            )

            try:
                evaluation_response = await self.client.openai.chat.completions.create(
                    model=self.openai_model,
                    messages=evaluation_message
                )

                evaluation_data = json.loads(evaluation_response.choices[0].message.content)

                if evaluation_data["rating"] >= 90 or len(results) >= 30:
                    break

                search_query = evaluation_data["query"]
                current_target = evaluation_data.get("target_context", current_target)

                for index in evaluation_data["store"]:
                    if index < len(list_results):
                        results.append(list_results[index])

            except Exception as e:
                print(f"Evaluation error: {str(e)}")
                traceback.print_exc()
                break

        try:
            relevant_context = await self.process_search_results(current_target, results)

            summary_message = self._create_summary_message(
                target_context, current_target, relevant_context
            )

            summary_response = await self.client.openai.chat.completions.create(
                model=self.openai_model,
                messages=summary_message
            )

            return {
                "success": True,
                "reason": "Deep search completed successfully.",
                "results": summary_response.choices[0].message.content
            }

        except Exception as e:
            return {
                "success": False,
                "reason": f"Error during summary generation: {str(e)}"
            }

    def _create_evaluation_message(
            self,
            original_target: str,
            current_target: str,
            search_query: str,
            stored_results: List[Dict],
            new_results: List[Dict]
    ) -> List[Dict]:
        return [
            {
                "role": "system",
                "content": f"""
                Rating the results based on the provided content and context.
                Original Target context: {original_target}
                Current target context: {current_target}
                Current search query: {search_query}
                You MUST return improved search query based on the results and rating.
                - Rating should be between 1 to 100.
                Response MUST be in JSON format with the following structure Example:
                {{
                    "query": "...", // Improved search query for next search
                    "store": [1,4,5], // Indexes of the results to store from unfiltered data. Start with 0
                    "target_context": "..." // Target context for next search
                    "rating": 0 -> 100 // Rating quality of the selected context and filtered data
                }}
                Context Selected:
                {json.dumps(stored_results)}
                """
            },
            {
                "role": "user",
                "content": json.dumps(new_results)
            }
        ]

    def _create_summary_message(
            self,
            original_target: str,
            current_target: str,
            relevant_context: str
    ) -> List[Dict]:
        """Create messages for the final summary generation."""
        return [
            {
                "role": "system",
                "content": f"""
                From the provided content and context, extract the most relevant information.
                Original Target context: {original_target}
                Current target context: {current_target}
                Extract the most relevant information from the content.
                Response MUST be detailed about the content.
                Never make up information, only use the information provided in the response.
                """
            },
            {
                "role": "user",
                "content": relevant_context
            }
        ]


async def setup(client):
    """Register the DeepSearch module with the client."""
    await client.add_module(DeepSearch(client))
