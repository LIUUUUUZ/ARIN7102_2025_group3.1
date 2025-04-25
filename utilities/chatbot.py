import openai
from openai import OpenAI
from typing import Iterator, Dict, Any
from utilities.rag import RAG, NextQuestionGenerator
import json

"""
The response example for deepseek-reasoner:

{
  "id": "53264158-2a2f-4412-90ea-b5b6e995edda",
  "object": "chat.completion",
  "created": 1745352851,
  "model": "deepseek-reasoner",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I assist you today?",
        "reasoning_content": "Okay, the user just said \"Hi\". I should respond in a friendly and welcoming manner. Let me make sure to keep it open-ended so they feel comfortable to ask anything. Maybe say something like, \"Hello! How can I assist you today?\" That sounds good. I'll go with that."
      },
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 72,
    "total_tokens": 84,
    "prompt_tokens_details": {
      "cached_tokens": 0
    },
    "completion_tokens_details": {
      "reasoning_tokens": 61
    },
    "prompt_cache_hit_tokens": 0,
    "prompt_cache_miss_tokens": 12
  },
  "system_fingerprint": "fp_5417b77867_prod0225"
}
"""


class ChatBot:
    def __init__(
        self,
        api_key: str = "",
        init_prompt: str = "",
        model: str = "deepseek-reasoner",
        api_base: str = "https://api.deepseek.com",
        rag: RAG = None,
        biomarker_path="user_data/biomarker.json"
    ) -> None:
        self.client = OpenAI(
            base_url=api_base,
            api_key=api_key
        )
        self.init_prompt = init_prompt
        self.model = model
        self.messages = [{
            "role": "system",
            "content": init_prompt
        }]
        self.abort_generation = False
        self.rag = rag
        self.biomarker_path = biomarker_path
        self.nq = NextQuestionGenerator(
            api_key=api_key, base_url=api_base, model="deepseek-chat")

    def _parse_chunk(self, chunk) -> Dict[str, str]:
        delta = chunk.choices[0].delta
        if self.model == "deepseek-reasoner":
            return {
                "content": delta.content,
                "reasoning": delta.reasoning_content,
            }
        elif self.model == "deepseek-chat":
            return {
                "content": delta.content,
            }
        else:
            raise ValueError()

    def load_json(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.dumps(json.load(f), indent=2)
        except FileNotFoundError:
            print(f"文件 {filename} 不存在")
            return {}
        except json.JSONDecodeError:
            print("JSON格式错误")
            return {}

    def _chat(self, human_input: str) -> Iterator[Dict[str, str]]:
        self.abort_generation = False
        self.messages.append({
            "role": "user",
            "content": human_input
        })
        full_response = ""
        full_reasoning = ""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=True
            )

            for chunk in response:
                if self.abort_generation:
                    break

                parsed = self._parse_chunk(chunk)
                if parsed.get("content"):
                    full_response += parsed["content"]
                if parsed.get("reasoning"):
                    full_reasoning += parsed["reasoning"]

                yield parsed

            if not self.abort_generation:
                self.messages.append({
                    "role": "assistant",
                    "content": full_response,
                })
                self.messages = self.messages[-20:]

        finally:
            self.abort_generation = False

    def generate_response(self, human_input: str, use_rag: bool = True) -> Iterator[Dict[str, str]]:
        if use_rag:
            human_input = self.rag.rag_query(human_input)
        return self._chat(human_input, use_rag)

    def generate_response_with_biomarker(self, human_input: str, use_rag: bool = True) -> Iterator[Dict[str, str]]:
        if use_rag:
            human_input = self.rag.rag_query(human_input)
        biomarker = self.load_json(self.biomarker_path)
        human_input += ("\n Except those reference, the following is some of the health metric of the user. I hope you can give more specific answer based on that. \n" + biomarker)
        return self._chat(human_input, use_rag)

    def generate_nq(self) -> list[str]:
        query = self.messages[-2].get("content")
        answer = self.messages[-1].get("content")
        result_nq = self.nq.generate_next_questions(
            query, answer)
        return result_nq

    def set_api_key(self, api_key: str) -> None:
        openai.api_key = api_key
        self.client = OpenAI(
            base_url="https://api.deepseek.com",
            api_key=openai.api_key
        )

    def reset(self) -> None:
        self.messages = [{
            "role": "system",
            "content": self.init_prompt
        }]

    def __str__(self) -> str:
        return "Online Health Science Knowledge Chatbot"
