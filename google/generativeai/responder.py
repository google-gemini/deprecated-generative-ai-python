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
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import inspect
import typing
from typing import Any, Callable, Union
from typing_extensions import TypedDict

import pydantic

from google.generativeai import protos

Type = protos.Type

TypeOptions = Union[int, str, Type]

_TYPE_TYPE: dict[TypeOptions, Type] = {
    Type.TYPE_UNSPECIFIED: Type.TYPE_UNSPECIFIED,
    0: Type.TYPE_UNSPECIFIED,
    "type_unspecified": Type.TYPE_UNSPECIFIED,
    "unspecified": Type.TYPE_UNSPECIFIED,
    Type.STRING: Type.STRING,
    1: Type.STRING,
    "type_string": Type.STRING,
    "string": Type.STRING,
    Type.NUMBER: Type.NUMBER,
    2: Type.NUMBER,
    "type_number": Type.NUMBER,
    "number": Type.NUMBER,
    Type.INTEGER: Type.INTEGER,
    3: Type.INTEGER,
    "type_integer": Type.INTEGER,
    "integer": Type.INTEGER,
    Type.BOOLEAN: Type.BOOLEAN,
    4: Type.INTEGER,
    "type_boolean": Type.BOOLEAN,
    "boolean": Type.BOOLEAN,
    Type.ARRAY: Type.ARRAY,
    5: Type.ARRAY,
    "type_array": Type.ARRAY,
    "array": Type.ARRAY,
    Type.OBJECT: Type.OBJECT,
    6: Type.OBJECT,
    "type_object": Type.OBJECT,
    "object": Type.OBJECT,
}


def to_type(x: TypeOptions) -> Type:
    if isinstance(x, str):
        x = x.lower()
    return _TYPE_TYPE[x]


def _rename_schema_fields(schema: dict[str, Any]):
    if schema is None:
        return schema

    schema = schema.copy()

    type_ = schema.pop("type", None)
    if type_ is not None:
        schema["type_"] = type_
    type_ = schema.get("type_", None)
    if type_ is not None:
        schema["type_"] = to_type(type_)

    format_ = schema.pop("format", None)
    if format_ is not None:
        schema["format_"] = format_

    items = schema.pop("items", None)
    if items is not None:
        schema["items"] = _rename_schema_fields(items)

    properties = schema.pop("properties", None)
    if properties is not None:
        schema["properties"] = {k: _rename_schema_fields(v) for k, v in properties.items()}

    return schema
