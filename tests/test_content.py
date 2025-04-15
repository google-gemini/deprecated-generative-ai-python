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
import dataclasses
import enum
import pathlib
import typing_extensions
from typing import Any, Union, Iterable

from absl.testing import absltest
from absl.testing import parameterized
from google.generativeai import protos
from google.generativeai.types import content_types
import IPython.display
import PIL.Image

import numpy as np

HERE = pathlib.Path(__file__).parent
TEST_PNG_PATH = HERE / "test_img.png"
TEST_PNG_URL = "https://storage.googleapis.com/generativeai-downloads/data/test_img.png"
TEST_PNG_DATA = TEST_PNG_PATH.read_bytes()

TEST_JPG_PATH = HERE / "test_img.jpg"
TEST_JPG_URL = "https://storage.googleapis.com/generativeai-downloads/data/test_img.jpg"
TEST_JPG_DATA = TEST_JPG_PATH.read_bytes()

TEST_GIF_PATH = HERE / "test_img.gif"
TEST_GIF_URL = "https://storage.googleapis.com/generativeai-downloads/data/test_img.gif"
TEST_GIF_DATA = TEST_GIF_PATH.read_bytes()


# simple test function
def datetime():
    "Returns the current UTC date and time."


class ATypedDict(typing_extensions.TypedDict):
    a: int


@dataclasses.dataclass
class ADataClass:
    a: int


@dataclasses.dataclass
class Nested:
    x: ADataClass


@dataclasses.dataclass
class ADataClassWithNullable:
    a: Union[int, None]


@dataclasses.dataclass
class ADataClassWithList:
    a: list[int]


class Choices(enum.Enum):
    A = "a"
    B = "b"
    C = "c"
    D = "d"


@dataclasses.dataclass
class HasEnum:
    choice: Choices


class UnitTests(parameterized.TestCase):

    @parameterized.named_parameters(
        ["RGBA", PIL.Image.fromarray(np.zeros([6, 6, 4], dtype=np.uint8))],
        ["RGB", PIL.Image.fromarray(np.zeros([6, 6, 3], dtype=np.uint8))],
        ["P", PIL.Image.fromarray(np.zeros([6, 6, 3], dtype=np.uint8)).convert("P")],
    )
    def test_numpy_to_blob(self, image):
        blob = content_types.image_to_blob(image)
        self.assertIsInstance(blob, protos.Blob)
        self.assertEqual(blob.mime_type, "image/webp")
        self.assertStartsWith(blob.data, b"RIFF \x00\x00\x00WEBPVP8L")

    @parameterized.named_parameters(
        ["PIL", PIL.Image.open(TEST_PNG_PATH)],
        ["IPython", IPython.display.Image(filename=TEST_PNG_PATH)],
    )
    def test_png_to_blob(self, image):
        blob = content_types.image_to_blob(image)
        self.assertIsInstance(blob, protos.Blob)
        self.assertEqual(blob.mime_type, "image/png")
        self.assertStartsWith(blob.data, b"\x89PNG")

    @parameterized.named_parameters(
        ["PIL", PIL.Image.open(TEST_JPG_PATH)],
        ["IPython", IPython.display.Image(filename=TEST_JPG_PATH)],
    )
    def test_jpg_to_blob(self, image):
        blob = content_types.image_to_blob(image)
        self.assertIsInstance(blob, protos.Blob)
        self.assertEqual(blob.mime_type, "image/jpeg")
        self.assertStartsWith(blob.data, b"\xff\xd8\xff\xe0\x00\x10JFIF")

    @parameterized.named_parameters(
        ["PIL", PIL.Image.open(TEST_GIF_PATH)],
        ["IPython", IPython.display.Image(filename=TEST_GIF_PATH)],
    )
    def test_gif_to_blob(self, image):
        blob = content_types.image_to_blob(image)
        self.assertIsInstance(blob, protos.Blob)
        self.assertEqual(blob.mime_type, "image/gif")
        self.assertStartsWith(blob.data, b"GIF87a")

    @parameterized.named_parameters(
        ["BlobDict", {"mime_type": "image/png", "data": TEST_PNG_DATA}],
        ["protos.Blob", protos.Blob(mime_type="image/png", data=TEST_PNG_DATA)],
        ["Image", IPython.display.Image(filename=TEST_PNG_PATH)],
    )
    def test_to_blob(self, example):
        blob = content_types.to_blob(example)
        self.assertIsInstance(blob, protos.Blob)
        self.assertEqual(blob.mime_type, "image/png")
        self.assertStartsWith(blob.data, b"\x89PNG")

    @parameterized.named_parameters(
        ["dict", {"text": "Hello world!"}],
        ["protos.Part", protos.Part(text="Hello world!")],
        ["str", "Hello world!"],
    )
    def test_to_part(self, example):
        part = content_types.to_part(example)
        self.assertIsInstance(part, protos.Part)
        self.assertEqual(part.text, "Hello world!")

    @parameterized.named_parameters(
        ["Image", IPython.display.Image(filename=TEST_PNG_PATH)],
        ["BlobDict", {"mime_type": "image/png", "data": TEST_PNG_DATA}],
        [
            "PartDict",
            {"inline_data": {"mime_type": "image/png", "data": TEST_PNG_DATA}},
        ],
    )
    def test_img_to_part(self, example):
        blob = content_types.to_part(example).inline_data
        self.assertIsInstance(blob, protos.Blob)
        self.assertEqual(blob.mime_type, "image/png")
        self.assertStartsWith(blob.data, b"\x89PNG")

    @parameterized.named_parameters(
        ["protos.Content", protos.Content(parts=[{"text": "Hello world!"}])],
        ["ContentDict", {"parts": [{"text": "Hello world!"}]}],
        ["ContentDict-str", {"parts": ["Hello world!"]}],
        ["list[parts]", [{"text": "Hello world!"}]],
        ["list[str]", ["Hello world!"]],
        ["iterator[parts]", iter([{"text": "Hello world!"}])],
        ["part", {"text": "Hello world!"}],
        ["str", "Hello world!"],
    )
    def test_to_content(self, example):
        content = content_types.to_content(example)
        part = content.parts[0]

        self.assertLen(content.parts, 1)
        self.assertIsInstance(part, protos.Part)
        self.assertEqual(part.text, "Hello world!")

    @parameterized.named_parameters(
        ["ContentDict", {"parts": [PIL.Image.open(TEST_PNG_PATH)]}],
        ["list[Image]", [PIL.Image.open(TEST_PNG_PATH)]],
        ["Image", PIL.Image.open(TEST_PNG_PATH)],
    )
    def test_img_to_content(self, example):
        content = content_types.to_content(example)
        blob = content.parts[0].inline_data
        self.assertLen(content.parts, 1)
        self.assertIsInstance(blob, protos.Blob)
        self.assertEqual(blob.mime_type, "image/png")
        self.assertStartsWith(blob.data, b"\x89PNG")

    @parameterized.named_parameters(
        ["protos.Content", protos.Content(parts=[{"text": "Hello world!"}])],
        ["ContentDict", {"parts": [{"text": "Hello world!"}]}],
        ["ContentDict-str", {"parts": ["Hello world!"]}],
    )
    def test_strict_to_content(self, example):
        content = content_types.strict_to_content(example)
        part = content.parts[0]

        self.assertLen(content.parts, 1)
        self.assertIsInstance(part, protos.Part)
        self.assertEqual(part.text, "Hello world!")

    @parameterized.named_parameters(
        ["list[parts]", [{"text": "Hello world!"}]],
        ["list[str]", ["Hello world!"]],
        ["iterator[parts]", iter([{"text": "Hello world!"}])],
        ["part", {"text": "Hello world!"}],
        ["str", "Hello world!"],
    )
    def test_strict_to_contents_fails(self, examples):
        with self.assertRaises(TypeError):
            content_types.strict_to_content(examples)

    @parameterized.named_parameters(
        ["protos.Content", [protos.Content(parts=[{"text": "Hello world!"}])]],
        ["ContentDict", [{"parts": [{"text": "Hello world!"}]}]],
        ["ContentDict-unwraped", [{"parts": ["Hello world!"]}]],
        ["ContentDict+str-part", [{"parts": "Hello world!"}]],
    )
    def test_to_contents(self, example):
        contents = content_types.to_contents(example)
        part = contents[0].parts[0]

        self.assertLen(contents, 1)

        self.assertLen(contents[0].parts, 1)
        self.assertIsInstance(part, protos.Part)
        self.assertEqual(part.text, "Hello world!")

    def test_dict_to_content_fails(self):
        with self.assertRaises(KeyError):
            content_types.to_content({"bad": "dict"})

    @parameterized.named_parameters(
        [
            "ContentDict",
            [{"parts": [{"inline_data": PIL.Image.open(TEST_PNG_PATH)}]}],
        ],
        ["ContentDict-unwraped", [{"parts": [PIL.Image.open(TEST_PNG_PATH)]}]],
        ["Image", PIL.Image.open(TEST_PNG_PATH)],
    )
    def test_img_to_contents(self, example):
        contents = content_types.to_contents(example)
        blob = contents[0].parts[0].inline_data

        self.assertLen(contents, 1)
        self.assertLen(contents[0].parts, 1)
        self.assertIsInstance(blob, protos.Blob)
        self.assertEqual(blob.mime_type, "image/png")
        self.assertStartsWith(blob.data, b"\x89PNG")

    @parameterized.named_parameters(
        [
            "FunctionLibrary",
            content_types.FunctionLibrary(
                tools=protos.Tool(
                    function_declarations=[
                        protos.FunctionDeclaration(
                            name="datetime", description="Returns the current UTC date and time."
                        )
                    ]
                )
            ),
        ],
        [
            "IterableTool-Tool",
            [
                content_types.Tool(
                    function_declarations=[
                        protos.FunctionDeclaration(
                            name="datetime", description="Returns the current UTC date and time."
                        )
                    ]
                )
            ],
        ],
        [
            "IterableTool-protos.Tool",
            [
                protos.Tool(
                    function_declarations=[
                        protos.FunctionDeclaration(
                            name="datetime",
                            description="Returns the current UTC date and time.",
                        )
                    ]
                )
            ],
        ],
        [
            "IterableTool-ToolDict",
            [
                dict(
                    function_declarations=[
                        dict(
                            name="datetime",
                            description="Returns the current UTC date and time.",
                        )
                    ]
                )
            ],
        ],
        [
            "IterableTool-IterableFD",
            [
                [
                    protos.FunctionDeclaration(
                        name="datetime",
                        description="Returns the current UTC date and time.",
                    )
                ]
            ],
        ],
        [
            "IterableTool-FD",
            [
                protos.FunctionDeclaration(
                    name="datetime",
                    description="Returns the current UTC date and time.",
                )
            ],
        ],
        [
            "Tool",
            content_types.Tool(
                function_declarations=[
                    protos.FunctionDeclaration(
                        name="datetime", description="Returns the current UTC date and time."
                    )
                ]
            ),
        ],
        [
            "protos.Tool",
            protos.Tool(
                function_declarations=[
                    protos.FunctionDeclaration(
                        name="datetime", description="Returns the current UTC date and time."
                    )
                ]
            ),
        ],
        [
            "ToolDict",
            dict(
                function_declarations=[
                    dict(name="datetime", description="Returns the current UTC date and time.")
                ]
            ),
        ],
        [
            "IterableFD-FD",
            [
                content_types.FunctionDeclaration(
                    name="datetime", description="Returns the current UTC date and time."
                )
            ],
        ],
        [
            "IterableFD-CFD",
            [
                content_types.CallableFunctionDeclaration(
                    name="datetime",
                    description="Returns the current UTC date and time.",
                    function=datetime,
                )
            ],
        ],
        [
            "IterableFD-dict",
            [dict(name="datetime", description="Returns the current UTC date and time.")],
        ],
        ["IterableFD-Callable", [datetime]],
        [
            "FD",
            content_types.FunctionDeclaration(
                name="datetime", description="Returns the current UTC date and time."
            ),
        ],
        [
            "CFD",
            content_types.CallableFunctionDeclaration(
                name="datetime",
                description="Returns the current UTC date and time.",
                function=datetime,
            ),
        ],
        [
            "protos.FD",
            protos.FunctionDeclaration(
                name="datetime", description="Returns the current UTC date and time."
            ),
        ],
        ["dict", dict(name="datetime", description="Returns the current UTC date and time.")],
        ["Callable", datetime],
    )
    def test_to_tools(self, tools):
        function_library = content_types.to_function_library(tools)
        if function_library is None:
            raise ValueError("This shouldn't happen")
        tools = function_library.to_proto()

        tools = type(tools[0]).to_dict(tools[0], including_default_value_fields=False)
        tools["function_declarations"][0].pop("parameters", None)

        expected = dict(
            function_declarations=[
                dict(name="datetime", description="Returns the current UTC date and time.")
            ]
        )

        self.assertEqual(tools, expected)

    def test_empty_function(self):
        def no_args():
            print("hello")

        fd = content_types.to_function_library(no_args).to_proto()[0]  # type: ignore
        fd = type(fd).to_dict(fd, including_default_value_fields=False)
        # parameters are not set.
        self.assertEqual({"function_declarations": [{"name": "no_args"}]}, fd)

    @parameterized.named_parameters(
        ["string", "code_execution"],
        ["proto_object", protos.CodeExecution()],
        ["proto_passed_in", protos.Tool(code_execution=protos.CodeExecution())],
        ["empty_dictionary", {"code_execution": {}}],
        ["string_list", ["code_execution"]],
        ["proto_object_list", [protos.CodeExecution()]],
        ["proto_passed_in_list", [protos.Tool(code_execution=protos.CodeExecution())]],
        ["empty_dictionary_list", [{"code_execution": {}}]],
    )
    def test_code_execution(self, tools):
        t = content_types._make_tools(tools)
        self.assertIsInstance(t[0].code_execution, protos.CodeExecution)

    @parameterized.named_parameters(
        ["string", "google_search_retrieval"],
        ["empty_dictionary", {"google_search_retrieval": {}}],
        [
            "empty_dictionary_with_dynamic_retrieval_config",
            {"google_search_retrieval": {"dynamic_retrieval_config": {}}},
        ],
        [
            "dictionary_with_mode_integer",
            {"google_search_retrieval": {"dynamic_retrieval_config": {"mode": 0}}},
        ],
        [
            "dictionary_with_mode_string",
            {"google_search_retrieval": {"dynamic_retrieval_config": {"mode": "DYNAMIC"}}},
        ],
        [
            "dictionary_with_dynamic_retrieval_config",
            {
                "google_search_retrieval": {
                    "dynamic_retrieval_config": {"mode": "unspecified", "dynamic_threshold": 0.5}
                }
            },
        ],
        [
            "proto_object",
            protos.GoogleSearchRetrieval(
                dynamic_retrieval_config=protos.DynamicRetrievalConfig(
                    mode="MODE_UNSPECIFIED", dynamic_threshold=0.5
                )
            ),
        ],
        [
            "proto_passed_in",
            protos.Tool(
                google_search_retrieval=protos.GoogleSearchRetrieval(
                    dynamic_retrieval_config=protos.DynamicRetrievalConfig(
                        mode="MODE_UNSPECIFIED", dynamic_threshold=0.5
                    )
                )
            ),
        ],
        [
            "proto_object_list",
            [
                protos.GoogleSearchRetrieval(
                    dynamic_retrieval_config=protos.DynamicRetrievalConfig(
                        mode="MODE_UNSPECIFIED", dynamic_threshold=0.5
                    )
                )
            ],
        ],
        [
            "proto_passed_in_list",
            [
                protos.Tool(
                    google_search_retrieval=protos.GoogleSearchRetrieval(
                        dynamic_retrieval_config=protos.DynamicRetrievalConfig(
                            mode="MODE_UNSPECIFIED", dynamic_threshold=0.5
                        )
                    )
                )
            ],
        ],
    )
    def test_search_grounding(self, tools):
        if self._testMethodName == "test_search_grounding_empty_dictionary":
            pass
        t = content_types._make_tools(tools)
        self.assertIsInstance(t[0].google_search_retrieval, protos.GoogleSearchRetrieval)

    def test_two_fun_is_one_tool(self):
        def a():
            pass

        def b():
            pass

        function_library = content_types.to_function_library([a, b])
        if function_library is None:
            raise ValueError("This shouldn't happen")
        tools = function_library.to_proto()

        self.assertLen(tools, 1)
        self.assertLen(tools[0].function_declarations, 2)

    @parameterized.named_parameters(
        ["int", int, protos.Schema(type=protos.Type.INTEGER)],
        ["float", float, protos.Schema(type=protos.Type.NUMBER)],
        ["str", str, protos.Schema(type=protos.Type.STRING)],
        ["nullable_str", Union[str, None], protos.Schema(type=protos.Type.STRING, nullable=True)],
        [
            "list",
            list[str],
            protos.Schema(
                type=protos.Type.ARRAY,
                items=protos.Schema(type=protos.Type.STRING),
            ),
        ],
        [
            "list-list-int",
            list[list[int]],
            protos.Schema(
                type=protos.Type.ARRAY,
                items=protos.Schema(
                    protos.Schema(
                        type=protos.Type.ARRAY,
                        items=protos.Schema(type=protos.Type.INTEGER),
                    ),
                ),
            ),
        ],
        ["dict", dict, protos.Schema(type=protos.Type.OBJECT)],
        ["dict-str-any", dict[str, Any], protos.Schema(type=protos.Type.OBJECT)],
        [
            "dataclass",
            ADataClass,
            protos.Schema(
                type=protos.Type.OBJECT,
                properties={"a": {"type_": protos.Type.INTEGER}},
            ),
        ],
        [
            "nullable_dataclass",
            Union[ADataClass, None],
            protos.Schema(
                type=protos.Type.OBJECT,
                nullable=True,
                properties={"a": {"type_": protos.Type.INTEGER}},
            ),
        ],
        [
            "list_of_dataclass",
            list[ADataClass],
            protos.Schema(
                type="ARRAY",
                items=protos.Schema(
                    type=protos.Type.OBJECT,
                    properties={"a": {"type_": protos.Type.INTEGER}},
                ),
            ),
        ],
        [
            "dataclass_with_nullable",
            ADataClassWithNullable,
            protos.Schema(
                type=protos.Type.OBJECT,
                properties={"a": {"type_": protos.Type.INTEGER, "nullable": True}},
            ),
        ],
        [
            "dataclass_with_list",
            ADataClassWithList,
            protos.Schema(
                type=protos.Type.OBJECT,
                properties={"a": {"type_": "ARRAY", "items": {"type_": "INTEGER"}}},
            ),
        ],
        [
            "list_of_dataclass_with_list",
            list[ADataClassWithList],
            protos.Schema(
                items=protos.Schema(
                    type=protos.Type.OBJECT,
                    properties={"a": {"type_": "ARRAY", "items": {"type_": "INTEGER"}}},
                ),
                type="ARRAY",
            ),
        ],
        [
            "list_of_nullable",
            list[Union[int, None]],
            protos.Schema(
                type="ARRAY",
                items={"type_": protos.Type.INTEGER, "nullable": True},
            ),
        ],
        [
            "TypedDict",
            ATypedDict,
            protos.Schema(
                type=protos.Type.OBJECT,
                properties={
                    "a": {"type_": protos.Type.INTEGER},
                },
            ),
        ],
        [
            "nested",
            Nested,
            protos.Schema(
                type=protos.Type.OBJECT,
                properties={
                    "x": protos.Schema(
                        type=protos.Type.OBJECT,
                        properties={
                            "a": {"type_": protos.Type.INTEGER},
                        },
                    ),
                },
            ),
        ],
        ["enum", Choices, protos.Schema(type=protos.Type.STRING, enum=["a", "b", "c", "d"])],
        [
            "enum_list",
            list[Choices],
            protos.Schema(
                type="ARRAY",
                items=protos.Schema(type=protos.Type.STRING, enum=["a", "b", "c", "d"]),
            ),
        ],
        [
            "has_enum",
            HasEnum,
            protos.Schema(
                type=protos.Type.OBJECT,
                properties={
                    "choice": protos.Schema(type=protos.Type.STRING, enum=["a", "b", "c", "d"])
                },
            ),
        ],
    )
    def test_auto_schema(self, annotation, expected):
        def fun(a: annotation):
            pass

        cfd = content_types.FunctionDeclaration.from_function(fun)
        got = cfd.parameters.properties["a"]
        self.assertEqual(got, expected)


if __name__ == "__main__":
    absltest.main()
