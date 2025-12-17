import collections
from collections.abc import Iterable
import copy
import datetime
import pathlib
import textwrap
from absl.testing import absltest
from absl.testing import parameterized
from google.generativeai import protos
from google.generativeai import client as client_lib
from google.generativeai import generative_models
from google.generativeai import caching
from google.generativeai.types import content_types
from google.generativeai.types import generation_types
from google.generativeai.types import helper_types

import PIL.Image

HERE = pathlib.Path(__file__).parent
TEST_IMAGE_PATH = HERE / "test_img.png"
TEST_IMAGE_URL = "https://storage.googleapis.com/generativeai-downloads/data/test_img.png"
TEST_IMAGE_DATA = TEST_IMAGE_PATH.read_bytes()


def simple_part(text: str) -> protos.Content:
    return protos.Content({"parts": [{"text": text}]})


def noop(x: int):
    return x


def iter_part(texts: Iterable[str]) -> protos.Content:
    return protos.Content({"parts": [{"text": t} for t in texts]})


def simple_response(text: str) -> protos.GenerateContentResponse:
    return protos.GenerateContentResponse({"candidates": [{"content": simple_part(text)}]})


class MockGenerativeServiceClient:
    def __init__(self, test):
        self.test = test
        self.observed_requests = []
        self.observed_kwargs = []
        self.responses = collections.defaultdict(list)

    def generate_content(
        self,
        request: protos.GenerateContentRequest,
        *,
        extra_headers: dict[str, str] | None = None,
        **kwargs,
    ) -> protos.GenerateContentResponse:
        self.test.assertIsInstance(request, protos.GenerateContentRequest)
        self.observed_requests.append(request)
        # Convert extra_headers to metadata format and ensure it's in kwargs
        if extra_headers:
            metadata = [(k, v) for k, v in extra_headers.items()]
            kwargs.setdefault("metadata", []).extend(metadata) 
        self.observed_kwargs.append(kwargs)
        response = self.responses["generate_content"].pop(0)
        return response

    def stream_generate_content(
        self,
        request: protos.GetModelRequest,
        *,
        extra_headers: dict[str, str] | None = None,
        **kwargs,
    ) -> Iterable[protos.GenerateContentResponse]:
        self.observed_requests.append(request)
        # Convert extra_headers to metadata format and ensure it's in kwargs
        if extra_headers:
            metadata = [(k, v) for k, v in extra_headers.items()]
            kwargs.setdefault("metadata", []).extend(metadata)
        self.observed_kwargs.append(kwargs)
        response = self.responses["stream_generate_content"].pop(0)
        return response

    def count_tokens(
        self,
        request: protos.CountTokensRequest,
        **kwargs,
    ) -> Iterable[protos.GenerateContentResponse]:
        self.observed_requests.append(request)
        self.observed_kwargs.append(kwargs)
        response = self.responses["count_tokens"].pop(0)
        return response

    def get_cached_content(
        self,
        request: protos.GetCachedContentRequest,
        **kwargs,
    ) -> protos.CachedContent:
        self.observed_requests.append(request)
        return protos.CachedContent(
            name="cachedContents/test-cached-content",
            model="models/gemini-1.5-pro",
            display_name="Cached content for test",
            usage_metadata={"total_token_count": 1},
            create_time="2000-01-01T01:01:01.123456Z",
            update_time="2000-01-01T01:01:01.123456Z",
            expire_time="2000-01-01T01:01:01.123456Z",
        )


class CUJTests(parameterized.TestCase):
    """Tests are in order with the design doc."""

    @property
    def observed_requests(self):
        return self.client.observed_requests

    @property
    def observed_kwargs(self):
        return self.client.observed_kwargs

    @property
    def responses(self):
        return self.client.responses

    def setUp(self):
        self.client = MockGenerativeServiceClient(self)
        client_lib._client_manager.clients["generative"] = self.client
        client_lib._client_manager.clients["cache"] = self.client

    def test_hello(self):
        # Generate text from text prompt
        model = generative_models.GenerativeModel(model_name="gemini-1.5-flash")

        self.responses["generate_content"].append(simple_response("world!"))

        response = model.generate_content("Hello")

        self.assertEqual(self.observed_requests[0].contents[0].parts[0].text, "Hello")
        self.assertEqual(response.candidates[0].content.parts[0].text, "world!")

        self.assertEqual(response.text, "world!")

    @parameterized.named_parameters(
        [
            "JustImage",
            PIL.Image.open(TEST_IMAGE_PATH),
        ],
        [
            "ImageAndText",
            ["What's in this picture?", PIL.Image.open(TEST_IMAGE_PATH)],
        ],
    )
    def test_image(self, content):
        # Generate text from image
        model = generative_models.GenerativeModel("gemini-1.5-flash")

        cat = "It's a cat"
        self.responses["generate_content"].append(simple_response(cat))

        response = model.generate_content(content)

        self.assertEqual(
            self.observed_requests[0].contents[0].parts[-1].inline_data.mime_type,
            "image/png",
        )
        self.assertEqual(
            self.observed_requests[0].contents[0].parts[-1].inline_data.data[:4],
            b"\x89PNG",
        )
        self.assertEqual(response.candidates[0].content.parts[0].text, cat)

        self.assertEqual(response.text, cat)

    @parameterized.named_parameters(
        ["dict", {"temperature": 0.0}, {"temperature": 0.5}],
        [
            "object",
            generation_types.GenerationConfig(temperature=0.0),
            generation_types.GenerationConfig(temperature=0.5),
        ],
        [
            "protos",
            protos.GenerationConfig(temperature=0.0),
            protos.GenerationConfig(temperature=0.5),
        ],
    )
    def test_generation_config_overwrite(self, config1, config2):
        # Generation config
        model = generative_models.GenerativeModel("gemini-1.5-flash", generation_config=config1)

        self.responses["generate_content"] = [
            simple_response(" world!"),
            simple_response(" world!"),
        ]

        _ = model.generate_content("hello")
        self.assertEqual(self.observed_requests[-1].generation_config.temperature, 0.0)

        _ = model.generate_content("hello", generation_config=config2)
        self.assertEqual(self.observed_requests[-1].generation_config.temperature, 0.5)

    @parameterized.named_parameters(
        ["dict", {"danger": "low"}, {"danger": "high"}],
        ["quick", "low", "high"],
        [
            "list-dict",
            [
                dict(
                    category=protos.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=protos.SafetySetting.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                ),
            ],
            [
                dict(category="danger", threshold="high"),
            ],
        ],
        [
            "object",
            [
                protos.SafetySetting(
                    category=protos.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=protos.SafetySetting.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                ),
            ],
            [
                protos.SafetySetting(
                    category=protos.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=protos.SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                ),
            ],
        ],
    )
    def test_safety_overwrite(self, safe1, safe2):
        # Safety
        model = generative_models.GenerativeModel("gemini-1.5-flash", safety_settings=safe1)

        self.responses["generate_content"] = [
            simple_response(" world!"),
            simple_response(" world!"),
        ]

        _ = model.generate_content("hello")

        danger = [
            s
            for s in self.observed_requests[-1].safety_settings
            if s.category == protos.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT
        ]
        self.assertEqual(
            danger[0].threshold,
            protos.SafetySetting.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        )

        _ = model.generate_content("hello", safety_settings=safe2)
        danger = [
            s
            for s in self.observed_requests[-1].safety_settings
            if s.category == protos.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT
        ]
        self.assertEqual(
            danger[0].threshold,
            protos.SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        )

    def test_stream_basic(self):
        # Streaming
        chunks = ["first", " second", " third"]
        self.responses["stream_generate_content"] = [(simple_response(text) for text in chunks)]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hello", stream=True)

        self.assertEqual(self.observed_requests[0].contents[0].parts[0].text, "Hello")

        for n, got in enumerate(response):
            self.assertEqual(chunks[n], got.text)

        self.assertEqual(response.text, "".join(chunks))

    def test_stream_lookahead(self):
        chunks = ["first", " second", " third"]
        self.responses["stream_generate_content"] = [(simple_response(text) for text in chunks)]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hello", stream=True)

        self.assertEqual(self.observed_requests[0].contents[0].parts[0].text, "Hello")

        for expected, got in zip(chunks, response):
            self.assertEqual(expected, got.text)

        self.assertEqual(response.text, "".join(chunks))

    def test_stream_prompt_feedback_blocked(self):
        chunks = [
            protos.GenerateContentResponse(
                {
                    "prompt_feedback": {"block_reason": "SAFETY"},
                }
            )
        ]
        self.responses["stream_generate_content"] = [(chunk for chunk in chunks)]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Bad stuff!", stream=True)

        self.assertEqual(
            response.prompt_feedback.block_reason,
            protos.GenerateContentResponse.PromptFeedback.BlockReason.SAFETY,
        )

        with self.assertRaises(generation_types.BlockedPromptException):
            for chunk in response:
                pass

    def test_stream_prompt_feedback_not_blocked(self):
        chunks = [
            protos.GenerateContentResponse(
                {
                    "prompt_feedback": {
                        "safety_ratings": [
                            {
                                "category": protos.HarmCategory.HARM_CATEGORY_DANGEROUS,
                                "probability": protos.SafetyRating.HarmProbability.NEGLIGIBLE,
                            }
                        ]
                    },
                    "candidates": [{"content": {"parts": [{"text": "first"}]}}],
                }
            ),
            protos.GenerateContentResponse(
                {
                    "candidates": [{"content": {"parts": [{"text": " second"}]}}],
                }
            ),
        ]
        self.responses["stream_generate_content"] = [(chunk for chunk in chunks)]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hello", stream=True)

        self.assertEqual(
            response.prompt_feedback.safety_ratings[0].category,
            protos.HarmCategory.HARM_CATEGORY_DANGEROUS,
        )

        text = "".join(chunk.text for chunk in response)
        self.assertEqual(text, "first second")

    @parameterized.named_parameters(
        [
            dict(testcase_name="test_cached_content_as_id", cached_content="test-cached-content"),
            dict(
                testcase_name="test_cached_content_as_CachedContent_object",
                cached_content=caching.CachedContent._from_obj(
                    dict(
                        name="cachedContents/test-cached-content",
                        model="models/gemini-1.5-pro",
                        display_name="Cached content for test",
                        usage_metadata={"total_token_count": 1},
                        create_time=datetime.datetime.now(),
                        update_time=datetime.datetime.now(),
                        expire_time=datetime.datetime.now(),
                    )
                ),
            ),
        ],
    )
    def test_model_with_cached_content_as_context(self, cached_content):
        model = generative_models.GenerativeModel.from_cached_content(cached_content=cached_content)
        cc_name = model.cached_content  # pytype: disable=attribute-error
        model_name = model.model_name
        self.assertEqual(cc_name, "cachedContents/test-cached-content")
        self.assertEqual(model_name, "models/gemini-1.5-pro")
        self.assertEqual(
            model.cached_content,  # pytype: disable=attribute-error
            "cachedContents/test-cached-content",
        )

    def test_content_generation_with_model_having_context(self):
        self.responses["generate_content"] = [simple_response("world!")]
        model = generative_models.GenerativeModel.from_cached_content(
            cached_content="test-cached-content"
        )
        response = model.generate_content("Hello")

        self.assertEqual(response.text, "world!")
        self.assertEqual(
            model.cached_content,  # pytype: disable=attribute-error
            "cachedContents/test-cached-content",
        )

    def test_fail_content_generation_with_model_having_context(self):
        model = generative_models.GenerativeModel.from_cached_content(
            cached_content="test-cached-content"
        )

        def add(a: int, b: int) -> int:
            return a + b

        with self.assertRaises(ValueError):
            model.generate_content("Hello", tools=[add])

    def test_chat(self):
        # Multi turn chat
        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()

        self.responses["generate_content"] = [
            simple_response("first"),
            simple_response("second"),
            simple_response("third"),
        ]

        msg1 = "I really like fantasy books."
        response = chat.send_message(msg1)
        self.assertEqual(response.text, "first")
        self.assertEqual(self.observed_requests[0].contents[0].parts[0].text, msg1)

        msg2 = "I also like this image."
        response = chat.send_message([msg2, PIL.Image.open(TEST_IMAGE_PATH)])

        self.assertEqual(response.text, "second")
        self.assertEqual(self.observed_requests[1].contents[0].parts[0].text, msg1)
        self.assertEqual(self.observed_requests[1].contents[1].parts[0].text, "first")
        self.assertEqual(self.observed_requests[1].contents[2].parts[0].text, msg2)
        self.assertEqual(
            self.observed_requests[1].contents[2].parts[1].inline_data.data[:4],
            b"\x89PNG",
        )

        msg3 = "What things do I like?."
        response = chat.send_message(msg3)
        self.assertEqual(response.text, "third")
        self.assertLen(chat.history, 6)

    def test_chat_roles(self):
        self.responses["generate_content"] = [simple_response("hello!")]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()
        response = chat.send_message("hello?")
        history = chat.history
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[1].role, "model")

    def test_chat_streaming_basic(self):
        # Chat streaming
        self.responses["stream_generate_content"] = [
            iter([simple_response("a"), simple_response("b"), simple_response("c")]),
            iter([simple_response("1"), simple_response("2"), simple_response("3")]),
            iter([simple_response("x"), simple_response("y"), simple_response("z")]),
        ]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()

        response = chat.send_message("letters?", stream=True)

        self.assertEqual("".join(chunk.text for chunk in response), "abc")

        response = chat.send_message("numbers?", stream=True)

        self.assertEqual("".join(chunk.text for chunk in response), "123")

        response = chat.send_message("more letters?", stream=True)

        self.assertEqual("".join(chunk.text for chunk in response), "xyz")

    def test_chat_incomplete_streaming_errors(self):
        # Chat streaming
        self.responses["stream_generate_content"] = [
            iter([simple_response("a"), simple_response("b"), simple_response("c")]),
            iter([simple_response("1"), simple_response("2"), simple_response("3")]),
            iter([simple_response("x"), simple_response("y"), simple_response("z")]),
        ]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()
        response = chat.send_message("letters?", stream=True)

        with self.assertRaises(generation_types.IncompleteIterationError):
            chat.history

        with self.assertRaises(generation_types.IncompleteIterationError):
            chat.send_message("numbers?", stream=True)

        for chunk in response:
            pass
        self.assertLen(chat.history, 2)

        response = chat.send_message("numbers?", stream=True)
        self.assertEqual("".join(chunk.text for chunk in response), "123")

    def test_edit_history(self):
        self.responses["generate_content"] = [
            simple_response("first"),
            simple_response("second"),
            simple_response("third"),
        ]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()

        response = chat.send_message("hello")
        self.assertEqual(response.text, "first")
        self.assertLen(chat.history, 2)

        response = chat.send_message("hello")
        self.assertEqual(response.text, "second")
        self.assertLen(chat.history, 4)

        chat.history[-1] = content_types.to_content("edited")
        response = chat.send_message("hello")
        self.assertEqual(response.text, "third")
        self.assertLen(chat.history, 6)

        self.assertEqual(chat.history[3], content_types.to_content("edited"))
        self.assertEqual(self.observed_requests[-1].contents[3].parts[0].text, "edited")

    def test_replace_history(self):
        self.responses["generate_content"] = [
            simple_response("first"),
            simple_response("second"),
            simple_response("third"),
        ]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()
        chat.send_message("hello1")
        chat.send_message("hello2")

        self.assertLen(chat.history, 4)
        chat.history = [{"parts": ["Goodbye"]}, {"parts": ["Later gater"]}]
        self.assertLen(chat.history, 2)

        response = chat.send_message("hello3")
        self.assertEqual(response.text, "third")
        self.assertLen(chat.history, 4)

        self.assertEqual(self.observed_requests[-1].contents[0].parts[0].text, "Goodbye")

    def test_copy_history(self):
        self.responses["generate_content"] = [
            simple_response("first"),
            simple_response("second"),
            simple_response("third"),
        ]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat1 = model.start_chat()
        chat1.send_message("hello1")

        chat2 = copy.copy(chat1)
        chat2.send_message("hello2")

        chat1.send_message("hello3")

        self.assertLen(chat1.history, 4)
        expected = [
            {"role": "user", "parts": ["hello1"]},
            {"role": "model", "parts": ["first"]},
            {"role": "user", "parts": ["hello3"]},
            {"role": "model", "parts": ["third"]},
        ]
        for content, ex in zip(chat1.history, expected):
            self.assertEqual(content, content_types.to_content(ex))

        self.assertLen(chat2.history, 4)
        expected = [
            {"role": "user", "parts": ["hello1"]},
            {"role": "model", "parts": ["first"]},
            {"role": "user", "parts": ["hello2"]},
            {"role": "model", "parts": ["second"]},
        ]
        for content, ex in zip(chat2.history, expected):
            self.assertEqual(content, content_types.to_content(ex))

    def test_chat_error_in_stream(self):
        def throw():
            for c in "123":
                yield simple_response(c)
            raise ValueError()

        def no_throw():
            for c in "abc":
                yield simple_response(c)

        self.responses["stream_generate_content"] = [
            no_throw(),
            throw(),
            no_throw(),
        ]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()

        # Send a message, the response is okay..
        chat.send_message("hello1", stream=True).resolve()

        # Send a second message, it fails
        response = chat.send_message("hello2", stream=True)
        with self.assertRaises(ValueError):
            # Iteration fails
            for chunk in response:
                pass

        # Since the response broke, we can't access the history
        with self.assertRaises(generation_types.BrokenResponseError):
            chat.history

        # or send another message.
        with self.assertRaises(generation_types.BrokenResponseError):
            chat.send_message("hello")

        # Rewind a step to before the error
        chat.rewind()

        self.assertLen(chat.history, 2)
        self.assertEqual(chat.history[0].parts[0].text, "hello1")
        self.assertEqual(chat.history[1].parts[0].text, "abc")

        # And continue
        chat.send_message("hello3", stream=True).resolve()
        self.assertLen(chat.history, 4)
        self.assertEqual(chat.history[2].parts[0].text, "hello3")
        self.assertEqual(chat.history[3].parts[0].text, "abc")

    def test_chat_prompt_blocked(self):
        self.responses["generate_content"] = [
            protos.GenerateContentResponse(
                {
                    "prompt_feedback": {"block_reason": "SAFETY"},
                }
            )
        ]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()

        with self.assertRaises(generation_types.BlockedPromptException):
            chat.send_message("hello")

        self.assertLen(chat.history, 0)

    def test_chat_candidate_blocked(self):
        # I feel like chat needs a .last so you can look at the partial results.
        self.responses["generate_content"] = [
            protos.GenerateContentResponse(
                {
                    "candidates": [{"finish_reason": "SAFETY"}],
                }
            )
        ]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()

        with self.assertRaises(generation_types.StopCandidateException):
            chat.send_message("hello")

    def test_chat_streaming_unexpected_stop(self):
        self.responses["stream_generate_content"] = [
            iter(
                [
                    simple_response("a"),
                    simple_response("b"),
                    simple_response("c"),
                    protos.GenerateContentResponse(
                        {
                            "candidates": [{"finish_reason": "SAFETY"}],
                        }
                    ),
                ]
            )
        ]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()

        response = chat.send_message("hello", stream=True)
        for chunk in response:
            # The result doesn't know it's a chat result so it can't throw.
            # Unless we give it some way to know?
            pass

        with self.assertRaises(generation_types.BrokenResponseError):
            # But when preparing the next message, we can throw:
            response = chat.send_message("hello2", stream=True)

        # It's a little bad that here it's only on send message that you find out
        # about the problem. "hello2" is never added, the `rewind` removes `hello1`.
        chat.rewind()
        self.assertLen(chat.history, 0)

    def test_tools(self):
        tools = dict(
            function_declarations=[
                dict(name="datetime", description="Returns the current UTC date and time.")
            ]
        )
        model = generative_models.GenerativeModel("gemini-1.5-flash", tools=tools)

        self.responses["generate_content"] = [
            simple_response("a"),
            simple_response("b"),
        ]

        response = model.generate_content("Hello")

        chat = model.start_chat()
        response = chat.send_message("Hello")

        expect_tools = dict(
            function_declarations=[
                dict(name="datetime", description="Returns the current UTC date and time.")
            ]
        )

        for obr in self.observed_requests:
            self.assertLen(obr.tools, 1)
            self.assertEqual(type(obr.tools[0]).to_dict(obr.tools[0]), tools)

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
    def test_tool_config(self, tool_config, expected_tool_config):
        tools = dict(
            function_declarations=[
                dict(name="datetime", description="Returns the current UTC date and time."),
                dict(name="greetings", description="Returns a greeting."),
                dict(name="random", description="Returns a random number."),
            ]
        )
        self.responses["generate_content"] = [simple_response("echo echo")]

        model = generative_models.GenerativeModel("gemini-1.5-flash", tools=tools)
        _ = model.generate_content("Hello", tools=[tools], tool_config=tool_config)

        req = self.observed_requests[0]

        self.assertLen(type(req.tools[0]).to_dict(req.tools[0]).get("function_declarations"), 3)
        self.assertEqual(type(req.tool_config).to_dict(req.tool_config), expected_tool_config)

    @parameterized.named_parameters(
        ["bare_str", "talk like a pirate", simple_part("talk like a pirate")],
        [
            "part_dict",
            {"parts": [{"text": "talk like a pirate"}]},
            protos.Content(parts=[{"text": "talk like a pirate"}]),
        ],
        ["part_list", ["talk like", "a pirate"], iter_part(["talk like", "a pirate"])],
    )
    def test_system_instruction(self, instruction, expected_instr):
        self.responses["generate_content"] = [simple_response("echo echo")]
        model = generative_models.GenerativeModel(
            "gemini-1.5-flash", system_instruction=instruction
        )

        _ = model.generate_content("test")

        [req] = self.observed_requests
        self.assertEqual(req.system_instruction, expected_instr)

    @parameterized.named_parameters(
        ["basic", {"contents": "Hello"}],
        ["list", {"contents": ["Hello"]}],
        [
            "list2",
            {
                "contents": [
                    {"text": "Hello"},
                    {"inline_data": {"data": b"PNG!", "mime_type": "image/png"}},
                ]
            },
        ],
        [
            "contents",
            {"contents": [{"role": "user", "parts": ["hello"]}]},
        ],
        ["empty", {}],
        [
            "system_instruction",
            {"system_instruction": ["You are a cat"]},
        ],
        ["tools", {"tools": [noop]}],
    )
    def test_count_tokens_smoke(self, kwargs):
        si = kwargs.pop("system_instruction", None)
        self.responses["count_tokens"] = [protos.CountTokensResponse(total_tokens=7)]
        model = generative_models.GenerativeModel("gemini-1.5-flash", system_instruction=si)
        response = model.count_tokens(**kwargs)
        self.assertEqual(
            type(response).to_dict(response, including_default_value_fields=False),
            {"total_tokens": 7},
        )

    def test_repr_for_unary_non_streamed_response(self):
        model = generative_models.GenerativeModel(model_name="gemini-1.5-flash")
        self.responses["generate_content"].append(simple_response("world!"))
        response = model.generate_content("Hello")

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
                            "text": "world!"
                          }
                        ]
                      }
                    }
                  ]
                }),
            )"""
        )

        self.assertEqual(expected, result)

    def test_repr_for_streaming_start_to_finish(self):
        chunks = ["first", " second", " third"]
        self.responses["stream_generate_content"] = [(simple_response(text) for text in chunks)]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hello", stream=True)
        iterator = iter(response)

        result1 = repr(response)
        expected1 = textwrap.dedent(
            """\
            response:
            GenerateContentResponse(
                done=False,
                iterator=<generator>,
                result=protos.GenerateContentResponse({
                  "candidates": [
                    {
                      "content": {
                        "parts": [
                          {
                            "text": "first"
                          }
                        ]
                      }
                    }
                  ]
                }),
            )"""
        )
        self.assertEqual(expected1, result1)

        next(iterator)
        result2 = repr(response)
        expected2 = textwrap.dedent(
            """\
            response:
            GenerateContentResponse(
                done=False,
                iterator=<generator>,
                result=protos.GenerateContentResponse({
                  "candidates": [
                    {
                      "content": {
                        "parts": [
                          {
                            "text": "first second"
                          }
                        ]
                      },
                      "index": 0,
                      "citation_metadata": {}
                    }
                  ],
                  "prompt_feedback": {}
                }),
            )"""
        )
        self.assertEqual(expected2, result2)

        next(iterator)
        result3 = repr(response)
        expected3 = textwrap.dedent(
            """\
            response:
            GenerateContentResponse(
                done=False,
                iterator=<generator>,
                result=protos.GenerateContentResponse({
                  "candidates": [
                    {
                      "content": {
                        "parts": [
                          {
                            "text": "first second third"
                          }
                        ]
                      },
                      "index": 0,
                      "citation_metadata": {}
                    }
                  ],
                  "prompt_feedback": {}
                }),
            )"""
        )
        self.assertEqual(expected3, result3)

    def test_repr_error_info_for_stream_prompt_feedback_blocked(self):
        # response._error => BlockedPromptException
        chunks = [
            protos.GenerateContentResponse(
                {
                    "prompt_feedback": {"block_reason": "SAFETY"},
                }
            )
        ]
        self.responses["stream_generate_content"] = [(chunk for chunk in chunks)]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Bad stuff!", stream=True)

        result = repr(response)
        expected = textwrap.dedent(
            """\
            response:
            GenerateContentResponse(
                done=False,
                iterator=<generator>,
                result=protos.GenerateContentResponse({
                  "prompt_feedback": {
                    "block_reason": "SAFETY"
                  }
                }),
            ),
            error=BlockedPromptException(prompt_feedback {
              block_reason: SAFETY
            }
            )"""
        )
        self.assertEqual(expected, result)

    def test_repr_error_info_for_chat_error_in_stream(self):
        # response._error => ValueError
        def throw():
            for c in "123":
                yield simple_response(c)
            raise ValueError()

        def no_throw():
            for c in "abc":
                yield simple_response(c)

        self.responses["stream_generate_content"] = [
            no_throw(),
            throw(),
            no_throw(),
        ]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()

        # Send a message, the response is okay..
        chat.send_message("hello1", stream=True).resolve()

        # Send a second message, it fails
        response = chat.send_message("hello2", stream=True)
        with self.assertRaises(ValueError):
            # Iteration fails
            for chunk in response:
                pass

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
                            "text": "123"
                          }
                        ]
                      },
                      "index": 0,
                      "citation_metadata": {}
                    }
                  ],
                  "prompt_feedback": {}
                }),
            ),
            error=ValueError()"""
        )
        self.assertEqual(expected, result)

    def test_repr_error_info_for_chat_streaming_unexpected_stop(self):
        # response._error => StopCandidateException
        self.responses["stream_generate_content"] = [
            iter(
                [
                    simple_response("a"),
                    simple_response("b"),
                    simple_response("c"),
                    protos.GenerateContentResponse(
                        {
                            "candidates": [{"finish_reason": "SAFETY"}],
                        }
                    ),
                ]
            )
        ]

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()

        response = chat.send_message("hello", stream=True)
        for chunk in response:
            # The result doesn't know it's a chat result so it can't throw.
            # Unless we give it some way to know?
            pass

        with self.assertRaises(generation_types.BrokenResponseError):
            # But when preparing the next message, we can throw:
            response = chat.send_message("hello2", stream=True)

        result = repr(response)
        self.assertIn("StopCandidateException", result)

    def test_repr_for_multi_turn_chat(self):
        # Multi turn chat
        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()

        self.responses["generate_content"] = [
            simple_response("first"),
            simple_response("second"),
            simple_response("third"),
        ]

        msg1 = "I really like fantasy books."
        response = chat.send_message(msg1)

        msg2 = "I also like this image."
        response = chat.send_message([msg2, PIL.Image.open(TEST_IMAGE_PATH)])

        msg3 = "What things do I like?."
        response = chat.send_message(msg3)

        result = repr(chat)
        expected = textwrap.dedent(
            """\
            ChatSession(
                model=genai.GenerativeModel(
                    model_name='models/gemini-1.5-flash',
                    generation_config={},
                    safety_settings={},
                    tools=None,
                    system_instruction=None,
                    cached_content=None
                ),
                history=[protos.Content({'parts': [{'text': 'I really like fantasy books.'}], 'role': 'user'}), protos.Content({'parts': [{'text': 'first'}], 'role': 'model'}), protos.Content({'parts': [{'text': 'I also like this image.'}, {'inline_data': {'data': 'iVBORw0KGgoA...AAElFTkSuQmCC', 'mime_type': 'image/png'}}], 'role': 'user'}), protos.Content({'parts': [{'text': 'second'}], 'role': 'model'}), protos.Content({'parts': [{'text': 'What things do I like?.'}], 'role': 'user'}), protos.Content({'parts': [{'text': 'third'}], 'role': 'model'})]
            )"""
        )
        self.assertEqual(expected, result)

    def test_repr_for_incomplete_streaming_chat(self):
        # Multi turn chat
        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()

        self.responses["stream_generate_content"] = [
            (chunk for chunk in [simple_response("a"), simple_response("b"), simple_response("c")])
        ]

        msg1 = "I really like fantasy books."
        response = chat.send_message(msg1, stream=True)

        result = repr(chat)
        expected = textwrap.dedent(
            """\
            ChatSession(
                model=genai.GenerativeModel(
                    model_name='models/gemini-1.5-flash',
                    generation_config={},
                    safety_settings={},
                    tools=None,
                    system_instruction=None,
                    cached_content=None
                ),
                history=[protos.Content({'parts': [{'text': 'I really like fantasy books.'}], 'role': 'user'}), <STREAMING IN PROGRESS>]
            )"""
        )
        self.assertEqual(expected, result)

    def test_repr_for_broken_streaming_chat(self):
        # Multi turn chat
        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()

        self.responses["stream_generate_content"] = [
            (
                chunk
                for chunk in [
                    simple_response("first"),
                    # FinishReason.SAFETY = 3
                    protos.GenerateContentResponse(
                        {
                            "candidates": [
                                {"finish_reason": 3, "content": {"parts": [{"text": "second"}]}}
                            ]
                        }
                    ),
                ]
            )
        ]

        msg1 = "I really like fantasy books."
        response = chat.send_message(msg1, stream=True)

        for chunk in response:
            pass

        result = repr(chat)
        expected = textwrap.dedent(
            """\
            ChatSession(
                model=genai.GenerativeModel(
                    model_name='models/gemini-1.5-flash',
                    generation_config={},
                    safety_settings={},
                    tools=None,
                    system_instruction=None,
                    cached_content=None
                ),
                history=[protos.Content({'parts': [{'text': 'I really like fantasy books.'}], 'role': 'user'}), <STREAMING ERROR>]
            )"""
        )
        self.assertEqual(expected, result)

    def test_repr_for_system_instruction(self):
        model = generative_models.GenerativeModel(
            "gemini-1.5-flash", system_instruction="Be excellent."
        )
        result = repr(model)
        self.assertIn("system_instruction='Be excellent.'", result)

    def test_repr_for_model_created_from_cahced_content(self):
        model = generative_models.GenerativeModel.from_cached_content(
            cached_content="test-cached-content"
        )
        result = repr(model)
        self.assertIn("cached_content=cachedContents/test-cached-content", result)
        self.assertIn("model_name='models/gemini-1.5-pro'", result)

    def test_count_tokens_called_with_request_options(self):
        self.responses["count_tokens"].append(protos.CountTokensResponse(total_tokens=7))
        request_options = {"timeout": 120}

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        model.count_tokens([{"role": "user", "parts": ["hello"]}], request_options=request_options)

        self.assertEqual(request_options, self.observed_kwargs[0])

    def test_chat_with_request_options(self):
        self.responses["generate_content"].append(
            protos.GenerateContentResponse(
                {
                    "candidates": [{"finish_reason": "STOP"}],
                }
            )
        )
        request_options = {"timeout": 120}

        model = generative_models.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat()
        chat.send_message("hello", request_options=helper_types.RequestOptions(**request_options))

        request_options["retry"] = None
        self.assertEqual(request_options, self.observed_kwargs[0])


if __name__ == "__main__":
    absltest.main()
