# -*- coding: utf-8 -*-
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
import json
import string
import textwrap
from typing_extensions import TypedDict

from absl.testing import absltest
from absl.testing import parameterized
from google.generativeai import protos
from google.generativeai.types import generation_types


class Date(TypedDict):
    day: int
    month: int
    year: int


class Person(TypedDict):
    name: str
    favorite_color: str
    birthday: Date


class UnitTests(parameterized.TestCase):
    maxDiff = None

    @parameterized.named_parameters(
        [
            "protos.GenerationConfig",
            protos.GenerationConfig(
                temperature=0.1,
                stop_sequences=["end"],
                response_schema=protos.Schema(type="STRING"),
            ),
        ],
        [
            "GenerationConfigDict",
            {"temperature": 0.1, "stop_sequences": ["end"], "response_schema": {"type": "STRING"}},
        ],
        [
            "GenerationConfig",
            generation_types.GenerationConfig(
                temperature=0.1, stop_sequences=["end"], response_schema={"type": "STRING"}
            ),
        ],
    )
    def test_to_generation_config(self, config):
        gd = generation_types.to_generation_config_dict(config)
        self.assertIsInstance(gd, dict)
        self.assertEqual(gd["temperature"], 0.1)
        self.assertEqual(gd["stop_sequences"], ["end"])

    def test_join_citation_metadatas(self):
        citations = [
            protos.CitationMetadata(
                citation_sources=[
                    protos.CitationSource(start_index=3, end_index=21, uri="https://google.com"),
                ]
            ),
            protos.CitationMetadata(
                citation_sources=[
                    protos.CitationSource(start_index=3, end_index=33, uri="https://google.com"),
                    protos.CitationSource(start_index=55, end_index=92, uri="https://google.com"),
                ]
            ),
        ]

        result = generation_types._join_citation_metadatas(citations)

        expected = {
            "citation_sources": [
                {"start_index": 3, "end_index": 33, "uri": "https://google.com"},
                {"start_index": 55, "end_index": 92, "uri": "https://google.com"},
            ]
        }
        self.assertEqual(expected, type(result).to_dict(result))

    def test_join_safety_ratings_list(self):
        ratings = [
            [
                protos.SafetyRating(category="HARM_CATEGORY_DANGEROUS", probability="LOW"),
                protos.SafetyRating(category="HARM_CATEGORY_MEDICAL", probability="LOW"),
                protos.SafetyRating(category="HARM_CATEGORY_SEXUAL", probability="MEDIUM"),
            ],
            [
                protos.SafetyRating(category="HARM_CATEGORY_DEROGATORY", probability="LOW"),
                protos.SafetyRating(category="HARM_CATEGORY_SEXUAL", probability="LOW"),
                protos.SafetyRating(
                    category="HARM_CATEGORY_DANGEROUS",
                    probability="HIGH",
                    blocked=True,
                ),
            ],
        ]

        result = generation_types._join_safety_ratings_lists(ratings)

        expected = [
            {"category": 6, "probability": 4, "blocked": True},
            {"category": 5, "probability": 2, "blocked": False},
            {"category": 4, "probability": 2, "blocked": False},
            {"category": 1, "probability": 2, "blocked": False},
        ]
        self.assertEqual(expected, [type(r).to_dict(r) for r in result])

    def test_join_contents(self):
        contents = [
            protos.Content(role="assistant", parts=[protos.Part(text="Tell me a story about a ")]),
            protos.Content(
                role="assistant",
                parts=[protos.Part(text="magic backpack that looks like this: ")],
            ),
            protos.Content(
                role="assistant",
                parts=[protos.Part(inline_data=protos.Blob(mime_type="image/png", data=b"DATA!"))],
            ),
        ]
        result = generation_types._join_contents(contents)
        expected = {
            "parts": [
                {"text": "Tell me a story about a magic backpack that looks like" " this: "},
                {"inline_data": {"mime_type": "image/png", "data": "REFUQSE="}},
            ],
            "role": "assistant",
        }

        self.assertEqual(expected, type(result).to_dict(result))

    def test_join_parts(self):
        contents = [
            protos.Content(role="assistant", parts=[protos.Part(text="A")]),
            protos.Content(role="assistant", parts=[protos.Part(text="B")]),
            protos.Content(role="assistant", parts=[protos.Part(executable_code={"code": "C"})]),
            protos.Content(role="assistant", parts=[protos.Part(executable_code={"code": "D"})]),
            protos.Content(
                role="assistant", parts=[protos.Part(code_execution_result={"output": "E"})]
            ),
            protos.Content(
                role="assistant", parts=[protos.Part(code_execution_result={"output": "F"})]
            ),
            protos.Content(role="assistant", parts=[protos.Part(text="G")]),
            protos.Content(role="assistant", parts=[protos.Part(text="H")]),
        ]
        g = generation_types._join_contents(contents=contents)
        expected = protos.Content(
            role="assistant",
            parts=[
                protos.Part(text="AB"),
                protos.Part(executable_code={"code": "CD"}),
                protos.Part(code_execution_result={"output": "EF"}),
                protos.Part(text="GH"),
            ],
        )
        self.assertEqual(expected, g)

    def test_code_execution_text(self):
        content = protos.Content(
            role="assistant",
            parts=[
                protos.Part(text="AB"),
                protos.Part(executable_code={"language": "PYTHON", "code": "CD"}),
                protos.Part(code_execution_result={"outcome": "OUTCOME_OK", "output": "EF"}),
                protos.Part(text="GH"),
            ],
        )
        response = generation_types.GenerateContentResponse(
            done=True,
            iterator=None,
            result=protos.GenerateContentResponse({"candidates": [{"content": content}]}),
        )
        expected = textwrap.dedent(
            """\
            AB
            ``` python
            CD
            ```
            ```
            EF
            ```
            GH"""
        )
        self.assertEqual(expected, response.text)

    def test_many_join_contents(self):
        import string

        contents = [
            protos.Content(role="assistant", parts=[protos.Part(text=a)])
            for a in string.ascii_lowercase
        ]

        result = generation_types._join_contents(contents)
        expected = {
            "parts": [{"text": string.ascii_lowercase}],
            "role": "assistant",
        }

        self.assertEqual(expected, type(result).to_dict(result))

    def test_join_candidates(self):
        candidates = [
            protos.Candidate(
                index=0,
                content=protos.Content(
                    role="assistant",
                    parts=[protos.Part(text="Tell me a story about a ")],
                ),
                citation_metadata=protos.CitationMetadata(
                    citation_sources=[
                        protos.CitationSource(
                            start_index=55, end_index=85, uri="https://google.com"
                        ),
                    ]
                ),
            ),
            protos.Candidate(
                index=0,
                content=protos.Content(
                    role="assistant",
                    parts=[protos.Part(text="magic backpack that looks like this: ")],
                ),
                citation_metadata=protos.CitationMetadata(
                    citation_sources=[
                        protos.CitationSource(
                            start_index=55, end_index=92, uri="https://google.com"
                        ),
                        protos.CitationSource(
                            start_index=3, end_index=21, uri="https://google.com"
                        ),
                    ]
                ),
            ),
            protos.Candidate(
                index=0,
                content=protos.Content(
                    role="assistant",
                    parts=[
                        protos.Part(inline_data=protos.Blob(mime_type="image/png", data=b"DATA!"))
                    ],
                ),
                citation_metadata=protos.CitationMetadata(
                    citation_sources=[
                        protos.CitationSource(
                            start_index=55, end_index=92, uri="https://google.com"
                        ),
                        protos.CitationSource(
                            start_index=3, end_index=21, uri="https://google.com"
                        ),
                    ]
                ),
                finish_reason="STOP",
            ),
        ]
        result = generation_types._join_candidates(candidates)

        expected = {
            "content": {
                "parts": [
                    {"text": "Tell me a story about a magic backpack that looks like" " this: "},
                    {"text": ""},
                ],
                "role": "assistant",
            },
            "finish_reason": 1,
            "citation_metadata": {
                "citation_sources": [
                    {
                        "start_index": 55,
                        "end_index": 92,
                        "uri": "https://google.com",
                    },
                    {
                        "start_index": 3,
                        "end_index": 21,
                        "uri": "https://google.com",
                    },
                ]
            },
            "index": 0,
            "safety_ratings": [],
            "token_count": 0,
        }

        self.assertEqual(expected, type(result).to_dict(result))

    def test_join_prompt_feedbacks(self):
        feedbacks = [
            protos.GenerateContentResponse.PromptFeedback(
                block_reason="SAFETY",
                safety_ratings=[
                    protos.SafetyRating(category="HARM_CATEGORY_DANGEROUS", probability="LOW"),
                ],
            ),
            protos.GenerateContentResponse.PromptFeedback(),
            protos.GenerateContentResponse.PromptFeedback(),
            protos.GenerateContentResponse.PromptFeedback(
                safety_ratings=[
                    protos.SafetyRating(category="HARM_CATEGORY_MEDICAL", probability="HIGH"),
                ]
            ),
        ]
        result = generation_types._join_prompt_feedbacks(feedbacks)
        expected = feedbacks[0]
        self.assertEqual(type(expected).to_dict(expected), type(result).to_dict(result))

    CANDIDATE_LISTS = [
        [
            {
                "content": {
                    "parts": [{"text": "Here is a photo of a magic backpack:"}],
                    "role": "assistant",
                },
                "index": 0,
                "finish_reason": 0,
                "safety_ratings": [],
                "token_count": 0,
            },
            {
                "content": {
                    "parts": [{"text": "Tell me a story about a magic backpack"}],
                    "role": "assistant",
                },
                "index": 1,
                "finish_reason": 0,
                "safety_ratings": [],
                "token_count": 0,
            },
            {
                "content": {
                    "parts": [{"text": "Tell me a story about a "}],
                    "role": "assistant",
                },
                "index": 2,
                "citation_metadata": {"citation_sources": []},
                "finish_reason": 0,
                "safety_ratings": [],
                "token_count": 0,
            },
        ],
        [
            {
                "content": {
                    "parts": [{"text": "magic backpack that looks like this: "}],
                    "role": "assistant",
                },
                "index": 2,
                "citation_metadata": {
                    "citation_sources": [
                        {
                            "start_index": 3,
                            "end_index": 21,
                            "uri": "https://google.com",
                        }
                    ]
                },
                "finish_reason": 0,
                "safety_ratings": [],
                "token_count": 0,
            },
            {
                "content": {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": "REFUQSE=",
                            }
                        }
                    ],
                    "role": "assistant",
                },
                "index": 0,
                "finish_reason": 0,
                "safety_ratings": [],
                "token_count": 0,
            },
        ],
        [
            {
                "content": {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": "REFUQSE=",
                            }
                        }
                    ],
                    "role": "assistant",
                },
                "index": 2,
                "citation_metadata": {
                    "citation_sources": [
                        {
                            "start_index": 3,
                            "end_index": 21,
                            "uri": "https://google.com",
                        }
                    ]
                },
                "finish_reason": 0,
                "safety_ratings": [],
                "token_count": 0,
            }
        ],
    ]
    MERGED_CANDIDATES = [
        {
            "content": {
                "parts": [
                    {"text": "Here is a photo of a magic backpack:"},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": "REFUQSE=",
                        }
                    },
                ],
                "role": "assistant",
            },
            "index": 0,
            "citation_metadata": {},
        },
        {
            "content": {
                "parts": [{"text": "Tell me a story about a magic backpack"}],
                "role": "assistant",
            },
            "index": 1,
            "citation_metadata": {},
        },
        {
            "content": {
                "parts": [
                    {"text": "Tell me a story about a magic backpack" " that looks like this: "},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": "REFUQSE=",
                        }
                    },
                ],
                "role": "assistant",
            },
            "index": 2,
            "citation_metadata": {
                "citation_sources": [
                    {
                        "start_index": 3,
                        "end_index": 21,
                        "uri": "https://google.com",
                    },
                ]
            },
        },
    ]

    def test_join_candidates(self):
        candidate_lists = [[protos.Candidate(c) for c in cl] for cl in self.CANDIDATE_LISTS]
        result = generation_types._join_candidate_lists(candidate_lists)
        self.assertEqual(
            self.MERGED_CANDIDATES,
            [type(r).to_dict(r, including_default_value_fields=False) for r in result],
        )

    def test_join_chunks(self):
        chunks = [protos.GenerateContentResponse(candidates=cl) for cl in self.CANDIDATE_LISTS]

        chunks[0].prompt_feedback = protos.GenerateContentResponse.PromptFeedback(
            block_reason="SAFETY",
            safety_ratings=[
                protos.SafetyRating(category="HARM_CATEGORY_DANGEROUS", probability="LOW"),
            ],
        )

        chunks[-1].usage_metadata = protos.GenerateContentResponse.UsageMetadata(
            prompt_token_count=5
        )

        chunks[-1].model_version = "gemini-1.5-flash-002"

        result = generation_types._join_chunks(chunks)

        expected = protos.GenerateContentResponse(
            {
                "candidates": self.MERGED_CANDIDATES,
                "prompt_feedback": {
                    "block_reason": 1,
                    "safety_ratings": [
                        {
                            "category": 6,
                            "probability": 2,
                            "blocked": False,
                        }
                    ],
                },
                "usage_metadata": {"prompt_token_count": 5},
                "model_version": "gemini-1.5-flash-002",
            },
        )

        expected = json.dumps(
            type(expected).to_dict(expected, including_default_value_fields=False), indent=4
        )
        result = json.dumps(
            type(result).to_dict(result, including_default_value_fields=False), indent=4
        )

        self.assertEqual(expected, result)

    def test_generate_content_response_iterator_end_to_end(self):
        chunks = [protos.GenerateContentResponse(candidates=cl) for cl in self.CANDIDATE_LISTS]
        merged = generation_types._join_chunks(chunks)

        response = generation_types.GenerateContentResponse.from_iterator(iter(chunks))

        # Initially property access fails.
        with self.assertRaises(generation_types.IncompleteIterationError):
            _ = response.candidates

        # It yields the chunks as given.
        for c1, c2 in zip(chunks, response):
            c2 = c2._result
            self.assertEqual(type(c1).to_dict(c1), type(c2).to_dict(c2))

        # The final result is identical to _join_chunks's output.
        self.assertEqual(
            type(merged).to_dict(merged),
            type(response._result).to_dict(response._result),
        )

    def test_generate_content_response_multiple_iterators(self):
        chunks = [
            protos.GenerateContentResponse({"candidates": [{"content": {"parts": [{"text": a}]}}]})
            for a in string.ascii_lowercase
        ]
        response = generation_types.GenerateContentResponse.from_iterator(iter(chunks))

        # Do a partial iteration.
        it1 = iter(response)
        for i, chunk, a in zip(range(5), it1, string.ascii_lowercase):
            self.assertEqual(a, chunk.candidates[0].content.parts[0].text)

        # Iterate past the first iterator.
        it2 = iter(response)
        for i, chunk, a in zip(range(10), it2, string.ascii_lowercase):
            self.assertEqual(a, chunk.candidates[0].content.parts[0].text)

        # Resume the first iterator.
        for i, chunk, a in zip(range(5), it1, string.ascii_lowercase[5:]):
            self.assertEqual(a, chunk.candidates[0].content.parts[0].text)

        # Do a full iteration
        chunks = list(response)
        joined = "".join(chunk.candidates[0].content.parts[0].text for chunk in chunks)
        self.assertEqual(joined, string.ascii_lowercase)

        parts = response.candidates[0].content.parts
        self.assertLen(parts, 1)
        self.assertEqual(parts[0].text, string.ascii_lowercase)

    def test_generate_content_response_resolve(self):
        chunks = [
            protos.GenerateContentResponse({"candidates": [{"content": {"parts": [{"text": a}]}}]})
            for a in "abcd"
        ]
        response = generation_types.GenerateContentResponse.from_iterator(iter(chunks))

        # Initially property access fails.
        with self.assertRaises(generation_types.IncompleteIterationError):
            _ = response.candidates

        response.resolve()

        self.assertEqual(response.candidates[0].content.parts[0].text, "abcd")

    def test_generate_content_response_from_response(self):
        raw_response = protos.GenerateContentResponse(
            {"candidates": [{"content": {"parts": [{"text": "Hello world!"}]}}]}
        )
        response = generation_types.GenerateContentResponse.from_response(raw_response)

        self.assertEqual(response.candidates[0], raw_response.candidates[0])
        self.assertLen(list(response), 1)

        for chunk in response:
            self.assertEqual(
                type(raw_response).to_dict(raw_response), type(chunk._result).to_dict(chunk._result)
            )

    def test_repr_for_generate_content_response_from_response(self):
        raw_response = protos.GenerateContentResponse(
            {"candidates": [{"content": {"parts": [{"text": "Hello world!"}]}}]}
        )
        response = generation_types.GenerateContentResponse.from_response(raw_response)

        result = repr(response)
        expected = textwrap.dedent(
            """\
            response:
            GenerateContentResponse(
                done=True,
                iterator=None,
                result=protos.GenerateContentResponse({
                  "candidates": [
                    {
                      "content": {
                        "parts": [
                          {
                            "text": "Hello world!"
                          }
                        ]
                      }
                    }
                  ]
                }),
            )"""
        )
        self.assertEqual(expected, result)

    def test_repr_for_generate_content_response_from_iterator(self):
        chunks = [
            protos.GenerateContentResponse({"candidates": [{"content": {"parts": [{"text": a}]}}]})
            for a in "abcd"
        ]
        response = generation_types.GenerateContentResponse.from_iterator(iter(chunks))

        result = repr(response)
        expected = textwrap.dedent(
            """\
            response:
            GenerateContentResponse(
                done=False,
                iterator=<list_iterator>,
                result=protos.GenerateContentResponse({
                  "candidates": [
                    {
                      "content": {
                        "parts": [
                          {
                            "text": "a"
                          }
                        ]
                      }
                    }
                  ]
                }),
            )"""
        )
        self.assertEqual(expected, result)

    @parameterized.named_parameters(
        [
            "protos.Schema",
            protos.Schema(type="STRING"),
            protos.Schema(type="STRING"),
        ],
        [
            "SchemaDict",
            {"type": "STRING"},
            protos.Schema(type="STRING"),
        ],
        [
            "str",
            str,
            protos.Schema(type="STRING"),
        ],
        ["list_of_str", list[str], protos.Schema(type="ARRAY", items=protos.Schema(type="STRING"))],
        [
            "fancy",
            Person,
            protos.Schema(
                type="OBJECT",
                properties=dict(
                    name=protos.Schema(type="STRING"),
                    favorite_color=protos.Schema(type="STRING"),
                    birthday=protos.Schema(
                        type="OBJECT",
                        properties=dict(
                            day=protos.Schema(type="INTEGER"),
                            month=protos.Schema(type="INTEGER"),
                            year=protos.Schema(type="INTEGER"),
                        ),
                        required=["day", "month", "year"],
                    ),
                ),
                required=["name", "favorite_color", "birthday"],
            ),
        ],
    )
    def test_response_schema(self, schema, expected):
        gd = generation_types.to_generation_config_dict(dict(response_schema=schema))
        actual = gd["response_schema"]
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    absltest.main()
