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
#
# pylint: disable=bad-continuation, line-too-long, protected-access
"""Classes for working with vision models."""

import base64
import collections
import dataclasses
import io
import json
import os
import pathlib
import typing
from typing import Any, Dict, List, Literal, Optional, Union

from google.generativeai import client
from google.generativeai import protos
from google.generativeai.types import content_types

from google.protobuf import struct_pb2

from proto.marshal.collections import maps
from proto.marshal.collections import repeated


# pylint: disable=g-import-not-at-top\
if typing.TYPE_CHECKING:
    from IPython import display as IPython_display
else:
    try:
        from IPython import display as IPython_display
    except ImportError:
        IPython_display = None

if typing.TYPE_CHECKING:
    import PIL.Image as PIL_Image
else:
    try:
        from PIL import Image as PIL_Image
    except ImportError:
        PIL_Image = None


# This is to get around https://github.com/googleapis/proto-plus-python/issues/488
def to_value(value) -> struct_pb2.Value:
    """Return a protobuf Value object representing this value."""
    if isinstance(value, struct_pb2.Value):
        return value
    if value is None:
        return struct_pb2.Value(null_value=0)
    if isinstance(value, bool):
        return struct_pb2.Value(bool_value=value)
    if isinstance(value, (int, float)):
        return struct_pb2.Value(number_value=float(value))
    if isinstance(value, str):
        return struct_pb2.Value(string_value=value)
    if isinstance(value, collections.abc.Sequence):
        return struct_pb2.Value(list_value=to_list_value(value))
    if isinstance(value, collections.abc.Mapping):
        return struct_pb2.Value(struct_value=to_mapping_value(value))
    raise ValueError("Unable to coerce value: %r" % value)


def to_list_value(value) -> struct_pb2.ListValue:
    # We got a proto, or else something we sent originally.
    # Preserve the instance we have.
    if isinstance(value, struct_pb2.ListValue):
        return value
    if isinstance(value, repeated.RepeatedComposite):
        return struct_pb2.ListValue(values=[v for v in value.pb])

    # We got a list (or something list-like); convert it.
    return struct_pb2.ListValue(values=[to_value(v) for v in value])


def to_mapping_value(value) -> struct_pb2.Struct:
    # We got a proto, or else something we sent originally.
    # Preserve the instance we have.
    if isinstance(value, struct_pb2.Struct):
        return value
    if isinstance(value, maps.MapComposite):
        return struct_pb2.Struct(
            fields={k: v for k, v in value.pb.items()},
        )

    # We got a dict (or something dict-like); convert it.
    return struct_pb2.Struct(fields={k: to_value(v) for k, v in value.items()})


AspectRatio = Literal["1:1", "9:16", "16:9", "4:3", "3:4"]
ASPECT_RATIOS = AspectRatio.__args__  # type: ignore

OutputMimeType = Literal["image/png", "image/jpeg"]
OUTPUT_MIME_TYPES = OutputMimeType.__args__  # type: ignore

SafetyFilterLevel = Literal["block_low_and_above", "block_medium_and_above", "block_only_high"]
SAFETY_FILTER_LEVELS = SafetyFilterLevel.__args__  # type: ignore

PersonGeneration = Literal["dont_allow", "allow_adult"]
PERSON_GENERATIONS = PersonGeneration.__args__  # type: ignore

ImageLikeType = Union["Image", pathlib.Path, content_types.ImageType]


def check_watermark(
    img: ImageLikeType, model_id: str = "models/image-verification-001"
) -> "CheckWatermarkResult":
    """Checks if an image has a Google-AI watermark.

    Args:
        img: can be a `pathlib.Path` or a `PIL.Image.Image`, `IPython.display.Image`, or `google.generativeai.Image`.
        model_id: Which version of the image-verification model to send the image to.

    Returns:

    """
    if isinstance(img, Image):
        pass
    elif isinstance(img, pathlib.Path):
        img = Image.load_from_file(img)
    elif IPython_display is not None and isinstance(img, IPython_display.Image):
        img = Image(image_bytes=img.data)
    elif PIL_Image is not None and isinstance(img, PIL_Image.Image):
        blob = content_types._pil_to_blob(img)
        img = Image(image_bytes=blob.data)
    elif isinstance(img, protos.Blob):
        img = Image(image_bytes=img.data)
    else:
        raise TypeError(
            f"Not implemented: Could not convert a {type(img)} into `Image`\n    {img=}"
        )

    prediction_client = client.get_default_prediction_client()
    if not model_id.startswith("models/"):
        model_id = f"models/{model_id}"

    instance = {"image": {"bytesBase64Encoded": base64.b64encode(img._loaded_bytes).decode()}}
    parameters = {"watermarkVerification": True}

    # This is to get around https://github.com/googleapis/proto-plus-python/issues/488
    pr = protos.PredictRequest.pb()
    request = pr(model=model_id, instances=[to_value(instance)], parameters=to_value(parameters))

    response = prediction_client.predict(request)

    return CheckWatermarkResult(response.predictions)


class Image:
    """Image."""

    __module__ = "vertexai.vision_models"

    _loaded_bytes: Optional[bytes] = None
    _loaded_image: Optional["PIL_Image.Image"] = None

    def __init__(
        self,
        image_bytes: Optional[bytes],
    ):
        """Creates an `Image` object.

        Args:
            image_bytes: Image file bytes. Image can be in PNG or JPEG format.
        """
        self._image_bytes = image_bytes

    @staticmethod
    def load_from_file(location: os.PathLike) -> "Image":
        """Loads image from local file or Google Cloud Storage.

        Args:
            location: Local path or Google Cloud Storage uri from where to load
                the image.

        Returns:
            Loaded image as an `Image` object.
        """
        # Load image from local path
        image_bytes = pathlib.Path(location).read_bytes()
        image = Image(image_bytes=image_bytes)
        return image

    @property
    def _image_bytes(self) -> bytes:
        return self._loaded_bytes

    @_image_bytes.setter
    def _image_bytes(self, value: bytes):
        self._loaded_bytes = value

    @property
    def _pil_image(self) -> "PIL_Image.Image":  # type: ignore
        if self._loaded_image is None:
            if not PIL_Image:
                raise RuntimeError(
                    "The PIL module is not available. Please install the Pillow package."
                )
            self._loaded_image = PIL_Image.open(io.BytesIO(self._image_bytes))
        return self._loaded_image

    @property
    def _size(self):
        return self._pil_image.size

    @property
    def _mime_type(self) -> str:
        """Returns the MIME type of the image."""
        if PIL_Image:
            return PIL_Image.MIME.get(self._pil_image.format, "image/jpeg")
        # Fall back to jpeg
        return "image/jpeg"

    def show(self):
        """Shows the image.

        This method only works when in a notebook environment.
        """
        if PIL_Image and IPython_display:
            IPython_display.display(self._pil_image)

    def save(self, location: str):
        """Saves image to a file.

        Args:
            location: Local path where to save the image.
        """
        pathlib.Path(location).write_bytes(self._image_bytes)

    def _as_base64_string(self) -> str:
        """Encodes image using the base64 encoding.

        Returns:
            Base64 encoding of the image as a string.
        """
        # ! b64encode returns `bytes` object, not `str`.
        # We need to convert `bytes` to `str`, otherwise we get service error:
        # "received initial metadata size exceeds limit"
        return base64.b64encode(self._image_bytes).decode("ascii")

    def _repr_png_(self):
        return self._pil_image._repr_png_()  # type:ignore

    check_watermark = check_watermark


class CheckWatermarkResult:
    def __init__(self, predictions):
        self._predictions = predictions

    @property
    def decision(self):
        return self._predictions[0]["decision"]

    def __str__(self):
        return f"CheckWatermarkResult([{{'decision': {self.decision!r}}}])"

    def __bool__(self):
        decision = self.decision
        if decision == "ACCEPT":
            return True
        elif decision == "REJECT":
            return False
        else:
            raise ValueError(f"Unrecognized result: {decision}")


class ImageGenerationModel:
    """Generates images from text prompt.

    Examples::

        model = ImageGenerationModel.from_pretrained("imagegeneration@002")
        response = model.generate_images(
            prompt="Astronaut riding a horse",
            # Optional:
            number_of_images=1,
        )
        response[0].show()
        response[0].save("image1.png")
    """

    def __init__(self, model_id: str):
        if not model_id.startswith("models"):
            model_id = f"models/{model_id}"
        self.model_name = model_id
        self._client = None

    @classmethod
    def from_pretrained(cls, model_name: str):
        """For vertex compatibility"""
        return cls(model_name)

    def _generate_images(
        self,
        prompt: str,
        *,
        negative_prompt: Optional[str] = None,
        number_of_images: int = 1,
        width: Optional[int] = None,
        height: Optional[int] = None,
        aspect_ratio: Optional[AspectRatio] = None,
        guidance_scale: Optional[float] = None,
        output_mime_type: Optional[OutputMimeType] = None,
        compression_quality: Optional[float] = None,
        language: Optional[str] = None,
        safety_filter_level: Optional[SafetyFilterLevel] = None,
        person_generation: Optional[PersonGeneration] = None,
    ) -> "ImageGenerationResponse":
        """Generates images from text prompt.

        Args:
            prompt: Text prompt for the image.
            negative_prompt: A description of what you want to omit in the generated
              images.
            number_of_images: Number of images to generate. Range: 1..8.
            width: Width of the image. One of the sizes must be 256 or 1024.
            height: Height of the image. One of the sizes must be 256 or 1024.
            aspect_ratio: Aspect ratio for the image. Supported values are:
                * 1:1 - Square image
                * 9:16 - Portait image
                * 16:9 - Landscape image
                * 4:3 - Landscape, desktop ratio.
                * 3:4 - Portrait, desktop ratio
            guidance_scale: Controls the strength of the prompt. Suggested values
              are - * 0-9 (low strength) * 10-20 (medium strength) * 21+ (high
              strength)
            output_mime_type: Which image format should the output be saved as.
              Supported values: * image/png: Save as a PNG image * image/jpeg: Save
              as a JPEG image
            compression_quality: Level of compression if the output mime type is
              selected to be image/jpeg. Float between 0 to 100
            language: Language of the text prompt for the image. Default: None.
              Supported values are `"en"` for English, `"hi"` for Hindi, `"ja"` for
              Japanese, `"ko"` for Korean, and `"auto"` for automatic language
              detection.
            safety_filter_level: Adds a filter level to Safety filtering. Supported
              values are:
              * "block_most" : Strongest filtering level, most strict blocking
              * "block_some" : Block some problematic prompts and responses
              * "block_few" : Block fewer problematic prompts and responses
            person_generation: Allow generation of people by the model Supported
              values are:
              * "dont_allow" : Block generation of people
              * "allow_adult" : Generate adults, but not children

        Returns:
            An `ImageGenerationResponse` object.
        """
        if self._client is None:
            self._client = client.get_default_prediction_client()
        # Note: Only a single prompt is supported by the service.
        instance = {"prompt": prompt}
        shared_generation_parameters = {
            "prompt": prompt,
            # b/295946075 The service stopped supporting image sizes.
            # "width": width,
            # "height": height,
            "number_of_images_in_batch": number_of_images,
        }

        parameters = {}
        max_size = max(width or 0, height or 0) or None
        if aspect_ratio is not None:
            if aspect_ratio not in ASPECT_RATIOS:
                raise ValueError(f"aspect_ratio not in {ASPECT_RATIOS}")
            parameters["aspectRatio"] = aspect_ratio
        elif max_size:
            # Note: The size needs to be a string
            parameters["sampleImageSize"] = str(max_size)
            if height is not None and width is not None and height != width:
                parameters["aspectRatio"] = f"{width}:{height}"

        parameters["sampleCount"] = number_of_images
        if negative_prompt:
            parameters["negativePrompt"] = negative_prompt
            shared_generation_parameters["negative_prompt"] = negative_prompt

        if guidance_scale is not None:
            parameters["guidanceScale"] = guidance_scale
            shared_generation_parameters["guidance_scale"] = guidance_scale

        if language is not None:
            parameters["language"] = language
            shared_generation_parameters["language"] = language

        parameters["outputOptions"] = {}
        if output_mime_type is not None:
            if output_mime_type not in OUTPUT_MIME_TYPES:
                raise ValueError(f"output_mime_type not in {OUTPUT_MIME_TYPES}")
            parameters["outputOptions"]["mimeType"] = output_mime_type
            shared_generation_parameters["mime_type"] = output_mime_type

        if compression_quality is not None:
            parameters["outputOptions"]["compressionQuality"] = compression_quality
            shared_generation_parameters["compression_quality"] = compression_quality

        if safety_filter_level is not None:
            if safety_filter_level not in SAFETY_FILTER_LEVELS:
                raise ValueError(f"safety_filter_level not in {SAFETY_FILTER_LEVELS}")
            parameters["safetySetting"] = safety_filter_level
            shared_generation_parameters["safety_filter_level"] = safety_filter_level

        if person_generation is not None:
            parameters["personGeneration"] = person_generation
            shared_generation_parameters["person_generation"] = person_generation

        # This is to get around https://github.com/googleapis/proto-plus-python/issues/488
        pr = protos.PredictRequest.pb()
        request = pr(
            model=self.model_name, instances=[to_value(instance)], parameters=to_value(parameters)
        )

        response = self._client.predict(request)

        generated_images: List["GeneratedImage"] = []
        for idx, prediction in enumerate(response.predictions):
            generation_parameters = dict(shared_generation_parameters)
            generation_parameters["index_of_image_in_batch"] = idx
            encoded_bytes = prediction.get("bytesBase64Encoded")
            generated_image = GeneratedImage(
                image_bytes=base64.b64decode(encoded_bytes) if encoded_bytes else None,
                generation_parameters=generation_parameters,
            )
            generated_images.append(generated_image)

        return ImageGenerationResponse(images=generated_images)

    def generate_images(
        self,
        prompt: str,
        *,
        negative_prompt: Optional[str] = None,
        number_of_images: int = 1,
        aspect_ratio: Optional[AspectRatio] = None,
        guidance_scale: Optional[float] = None,
        language: Optional[str] = None,
        safety_filter_level: Optional[SafetyFilterLevel] = None,
        person_generation: Optional[PersonGeneration] = None,
    ) -> "ImageGenerationResponse":
        """Generates images from text prompt.

        Args:
            prompt: Text prompt for the image.
            negative_prompt: A description of what you want to omit in the generated
                images.
            number_of_images: Number of images to generate. Range: 1..8.
            aspect_ratio: Changes the aspect ratio of the generated image Supported
                values are:
                * "1:1" : 1:1 aspect ratio
                * "9:16" : 9:16 aspect ratio
                * "16:9" : 16:9 aspect ratio
                * "4:3" : 4:3 aspect ratio
                * "3:4" : 3:4 aspect_ratio
            guidance_scale: Controls the strength of the prompt. Suggested values are:
                * 0-9 (low strength)
                * 10-20 (medium strength)
                * 21+ (high strength)
            language: Language of the text prompt for the image. Default: None.
                Supported values are `"en"` for English, `"hi"` for Hindi, `"ja"`
                for Japanese, `"ko"` for Korean, and `"auto"` for automatic language
                detection.
            safety_filter_level: Adds a filter level to Safety filtering. Supported
                values are:
                * "block_most" : Strongest filtering level, most strict
                blocking
                * "block_some" : Block some problematic prompts and responses
                * "block_few" : Block fewer problematic prompts and responses
            person_generation: Allow generation of people by the model Supported
                values are:
                * "dont_allow" : Block generation of people
                * "allow_adult" : Generate adults, but not children
        Returns:
            An `ImageGenerationResponse` object.
        """
        return self._generate_images(
            prompt=prompt,
            negative_prompt=negative_prompt,
            number_of_images=number_of_images,
            aspect_ratio=aspect_ratio,
            guidance_scale=guidance_scale,
            language=language,
            safety_filter_level=safety_filter_level,
            person_generation=person_generation,
        )


@dataclasses.dataclass
class ImageGenerationResponse:
    """Image generation response.

    Attributes:
        images: The list of generated images.
    """

    __module__ = "vertexai.preview.vision_models"

    images: List["GeneratedImage"]

    def __iter__(self) -> typing.Iterator["GeneratedImage"]:
        """Iterates through the generated images."""
        yield from self.images

    def __getitem__(self, idx: int) -> "GeneratedImage":
        """Gets the generated image by index."""
        return self.images[idx]


_EXIF_USER_COMMENT_TAG_IDX = 0x9286
_IMAGE_GENERATION_PARAMETERS_EXIF_KEY = (
    "google.cloud.vertexai.image_generation.image_generation_parameters"
)


class GeneratedImage(Image):
    """Generated image."""

    __module__ = "google.generativeai"

    def __init__(
        self,
        image_bytes: Optional[bytes],
        generation_parameters: Dict[str, Any],
    ):
        """Creates a `GeneratedImage` object.

        Args:
            image_bytes: Image file bytes. Image can be in PNG or JPEG format.
            generation_parameters: Image generation parameter values.
        """
        super().__init__(image_bytes=image_bytes)
        self._generation_parameters = generation_parameters

    @property
    def generation_parameters(self):
        """Image generation parameters as a dictionary."""
        return self._generation_parameters

    @staticmethod
    def load_from_file(location: os.PathLike) -> "GeneratedImage":
        """Loads image from file.

        Args:
            location: Local path from where to load the image.

        Returns:
            Loaded image as a `GeneratedImage` object.
        """
        base_image = Image.load_from_file(location=location)
        exif = base_image._pil_image.getexif()  # pylint: disable=protected-access
        exif_comment_dict = json.loads(exif[_EXIF_USER_COMMENT_TAG_IDX])
        generation_parameters = exif_comment_dict[_IMAGE_GENERATION_PARAMETERS_EXIF_KEY]
        return GeneratedImage(
            image_bytes=base_image._image_bytes,  # pylint: disable=protected-access
            generation_parameters=generation_parameters,
        )

    def save(self, location: str, include_generation_parameters: bool = True):
        """Saves image to a file.

        Args:
            location: Local path where to save the image.
            include_generation_parameters: Whether to include the image
                generation parameters in the image's EXIF metadata.
        """
        if include_generation_parameters:
            if not self._generation_parameters:
                raise ValueError("Image does not have generation parameters.")
            if not PIL_Image:
                raise ValueError("The PIL module is required for saving generation parameters.")

            exif = self._pil_image.getexif()
            exif[_EXIF_USER_COMMENT_TAG_IDX] = json.dumps(
                {_IMAGE_GENERATION_PARAMETERS_EXIF_KEY: self._generation_parameters}
            )
            self._pil_image.save(location, exif=exif)
        else:
            super().save(location=location)
