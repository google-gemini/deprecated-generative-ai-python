# -*- coding: utf-8 -*-
# Copyright 2023 Google LLC
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

import collections
import sys
from collections.abc import Iterable
import os
from typing import Any
import unittest


from google.generativeai import client as client_lib
from google.generativeai import generative_models
from google.generativeai.types import content_types
from google.generativeai import protos

from absl.testing import absltest
from absl.testing import parameterized


def simple_response(text: str) -> protos.GenerateContentResponse:
    return protos.GenerateContentResponse(
        {"candidates": [{"content": {"parts": [{"text": text}]}}]}
    )


class AsyncTests(parameterized.TestCase, unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = unittest.mock.MagicMock()

        client_lib._client_manager.clients["generative_async"] = self.client

        def add_client_method(f):
            name = f.__name__
            setattr(self.client, name, f)
            return f

        self.observed_requests = []
        self.responses = collections.defaultdict(list)

        @add_client_method
        async def generate_content(
            request: protos.GenerateContentRequest,
            **kwargs,
        ) -> protos.GenerateContentResponse:
            self.assertIsInstance(request, protos.GenerateContentRequest)
            self.observed_requests.append(request)
            response = self.responses["generate_content"].pop(0)
            return response

        @add_client_method
        async def stream_generate_content(
            request: protos.GetModelRequest,
            **kwargs,
        ) -> Iterable[protos.GenerateContentResponse]:
            self.observed_requests.append(request)
            response = self.responses["stream_generate_content"].pop(0)
            return response

        @add_client_method
        async def count_tokens(
            request: protos.CountTokensRequest,
            **kwargs,
        ) -> Iterable[protos.GenerateContentResponse]:
            self.observed_requests.append(request)
            response = self.responses["count_tokens"].pop(0)
            return response

    async def test_basic(self):
        # Generate text from text prompt
        model = generative_models.GenerativeModel(model_name="gemini-1.5-flash")

        self.responses["generate_content"] = [simple_response("world!")]

        response = await model.generate_content_async("Hello")

        self.assertEqual(self.observed_requests[0].contents[0].parts[0].text, "Hello")
        self.assertEqual(response.candidates[0].content.parts[0].text, "world!")

        self.assertEqual(response.text, "world!")

    async def test_generate_content_async_with_extra_headerss(self):
        self.client.generate_content = unittest.mock.AsyncMock()
        request = unittest.mock.ANY
        extra_headers = {
            "Helicone-User-Id": "test-user-123",
            "Custom-Header": "test-value"
        }

        model = generative_models.GenerativeModel(model_name="gemini-1.5-flash")
        await model.generate_content_async("Hello", extra_headers=extra_headers)

        expected_request_options = {"metadata": list(extra_headers.items())}

        self.client.generate_content.assert_called_once_with(
            request, **expected_request_options
        )

    async def test_extra_headers_with_existing_request_optionss(self):
        self.client.generate_content = unittest.mock.AsyncMock()
        request = unittest.mock.ANY

        extra_headers = {"Helicone-User-Id": "test-user-456"}
        request_options = {
            "timeout": 30,
            "metadata": [("Existing-Header", "existing-value")]
        }

        model = generative_models.GenerativeModel(model_name="gemini-1.5-flash")

        await model.generate_content_async("Hello", extra_headers=extra_headers, request_options=request_options)

        expected_metadata = [("Existing-Header", "existing-value")] + list(extra_headers.items())
        expected_request_options = {"timeout": 30, "metadata": expected_metadata}

        self.client.generate_content.assert_called_once_with(
            request, **expected_request_options
        )

    async def test_streaming(self):
        # Generate text from text prompt
        model = generative_models.GenerativeModel(model_name="gemini-1.5-flash")

        async def responses():
            for c in "world!":
                yield simple_response(c)

        self.responses["stream_generate_content"] = [responses()]

        response = await model.generate_content_async("Hello", stream=True)

        it = iter("world!")
        async for chunk in response:
            c = next(it)
            self.assertEqual(chunk.text, c)

        self.assertEqual(response.text, "world!")

    @parameterized.named_parameters(
        dict(
            testcase_name="test_FunctionCallingMode_str",
            tool_config={"function_calling_config": "any"},
            expected_tool_config={
                "function_calling_config": {
                    "mode": content_types.FunctionCallingMode.ANY,
                    "allowed_function_names": [],
                }
            },
        ),
        dict(
            testcase_name="test_FunctionCallingMode_int",
            tool_config={"function_calling_config": 1},
            expected_tool_config={
                "function_calling_config": {
                    "mode": content_types.FunctionCallingMode.AUTO,
                    "allowed_function_names": [],
                }
            },
        ),
        dict(
            testcase_name="test_FunctionCallingMode",
            tool_config={"function_calling_config": content_types.FunctionCallingMode.NONE},
            expected_tool_config={
                "function_calling_config": {
                    "mode": content_types.FunctionCallingMode.NONE,
                    "allowed_function_names": [],
                }
            },
        ),
        dict(
            testcase_name="test_protos.FunctionCallingConfig",
            tool_config={
                "function_calling_config": protos.FunctionCallingConfig(
                    mode=content_types.FunctionCallingMode.AUTO
                )
            },
            expected_tool_config={
                "function_calling_config": {
                    "mode": content_types.FunctionCallingMode.AUTO,
                    "allowed_function_names": [],
                }
            },
        ),
        dict(
            testcase_name="test_FunctionCallingConfigDict",
            tool_config={
                "function_calling_config": {
                    "mode": "mode_auto",
                    "allowed_function_names": ["datetime", "greetings", "random"],
                }
            },
            expected_tool_config={
                "function_calling_config": {
                    "mode": content_types.FunctionCallingMode.AUTO,
                    "allowed_function_names": ["datetime", "greetings", "random"],
                }
            },
        ),
        dict(
            testcase_name="test_protos.ToolConfig",
            tool_config=protos.ToolConfig(
                function_calling_config=protos.FunctionCallingConfig(
                    mode=content_types.FunctionCallingMode.NONE
                )
            ),
            expected_tool_config={
                "function_calling_config": {
                    "mode": content_types.FunctionCallingMode.NONE,
                    "allowed_function_names": [],
                }
            },
        ),
    )
    async def test_tool_config(self, tool_config, expected_tool_config):
        tools = dict(
            function_declarations=[
                dict(name="datetime", description="Returns the current UTC date and time."),
                dict(name="greetings", description="Returns a greeting."),
                dict(name="random", description="Returns a random number."),
            ]
        )
        self.responses["generate_content"] = [simple_response("echo echo")]

        model = generative_models.GenerativeModel("gemini-1.5-flash", tools=tools)
        _ = await model.generate_content_async("Hello", tools=[tools], tool_config=tool_config)

        req = self.observed_requests[0]

        self.assertLen(type(req.tools[0]).to_dict(req.tools[0]).get("function_declarations"), 3)
        self.assertEqual(type(req.tool_config).to_dict(req.tool_config), expected_tool_config)

    @parameterized.named_parameters(
        ["basic", "Hello"],
        ["list", ["Hello"]],
        [
            "list2",
            [{"text": "Hello"}, {"inline_data": {"data": b"PNG!", "mime_type": "image/png"}}],
        ],
        ["contents", [{"role": "user", "parts": ["hello"]}]],
    )
    async def test_count_tokens_smoke(self, contents):
        self.responses["count_tokens"] = [protos.CountTokensResponse(total_tokens=7)]
        model = generative_models.GenerativeModel("gemini-1.5-flash")
        response = await model.count_tokens_async(contents)
        self.assertEqual(
            type(response).to_dict(response, including_default_value_fields=False),
            {"total_tokens": 7},
        )

    async def test_stream_generate_content_called_with_request_options(self):
        self.client.stream_generate_content = unittest.mock.AsyncMock()
        request = unittest.mock.ANY
        request_options = {"timeout": 120}

        model = generative_models.GenerativeModel()

        try:
            response = await model.generate_content_async(
                contents=[""],
                stream=True,
                request_options=request_options,
            )
        except StopAsyncIteration:
            pass

        self.client.stream_generate_content.assert_called_once_with(request, **request_options)

    async def test_generate_content_called_with_request_options(self):
        self.client.generate_content = unittest.mock.AsyncMock()
        request = unittest.mock.ANY
        request_options = {"timeout": 120}

        model = generative_models.GenerativeModel()
        response = await model.generate_content_async(
            contents=[""], request_options=request_options
        )

        self.client.generate_content.assert_called_once_with(request, **request_options)

    async def test_count_tokens_called_with_request_options(self):
        self.client.count_tokens = unittest.mock.AsyncMock()
        request = unittest.mock.ANY
        request_options = {"timeout": 120}

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        response = await model.count_tokens_async(
            contents=["Hello?"], request_options=request_options
        )

        self.client.count_tokens.assert_called_once_with(request, **request_options)


if __name__ == "__main__":
    absltest.main()
