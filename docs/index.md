description: Google AI Python SDK

<div itemscope itemtype="http://developers.google.com/ReferenceObject">
<meta itemprop="name" content="google.generativeai" />
<meta itemprop="path" content="Stable" />
<meta itemprop="property" content="__version__"/>
<meta itemprop="property" content="annotations"/>
</div>

# Module: google.generativeai

<!-- Insert buttons and diff -->

<table class="tfo-notebook-buttons tfo-api nocontent" align="left">
<td>
  <a target="_blank" href="https://github.com/google/generative-ai-python/blob/master/google/generativeai/__init__.py">
    <img src="https://www.tensorflow.org/images/GitHub-Mark-32px.png" />
    View source on GitHub
  </a>
</td>
</table>



Google AI Python SDK



## Setup

```posix-terminal
pip install google-generativeai
```

## GenerativeModel

Use `genai.GenerativeModel` to access the API:

```
import google.generativeai as genai
import os

genai.configure(api_key=os.environ['API_KEY'])

model = genai.GenerativeModel(model_name='gemini-1.5-flash')
response = model.generate_content('Teach me about how an LLM works')

print(response.text)
```

See the [python quickstart](https://ai.google.dev/tutorials/python_quickstart) for more details.

## Modules

[`protos`](../google/generativeai/protos.md) module: This module provides low level access to the ProtoBuffer "Message" classes used by the API.

[`types`](../google/generativeai/types.md) module: A collection of type definitions used throughout the library.

## Classes

[`class ChatSession`](../google/generativeai/ChatSession.md): Contains an ongoing conversation with the model.

[`class GenerationConfig`](../google/generativeai/types/GenerationConfig.md): A simple dataclass used to configure the generation parameters of <a href="../google/generativeai/GenerativeModel.md#generate_content"><code>GenerativeModel.generate_content</code></a>.

[`class GenerativeModel`](../google/generativeai/GenerativeModel.md): The `genai.GenerativeModel` class wraps default parameters for calls to <a href="../google/generativeai/GenerativeModel.md#generate_content"><code>GenerativeModel.generate_content</code></a>, <a href="../google/generativeai/GenerativeModel.md#count_tokens"><code>GenerativeModel.count_tokens</code></a>, and <a href="../google/generativeai/GenerativeModel.md#start_chat"><code>GenerativeModel.start_chat</code></a>.

## Functions

[`chat(...)`](../google/generativeai/chat.md): Calls the API to initiate a chat with a model using provided parameters

[`chat_async(...)`](../google/generativeai/chat_async.md): Calls the API to initiate a chat with a model using provided parameters

[`configure(...)`](../google/generativeai/configure.md): Captures default client configuration.

[`count_message_tokens(...)`](../google/generativeai/count_message_tokens.md): Calls the API to calculate the number of tokens used in the prompt.

[`count_text_tokens(...)`](../google/generativeai/count_text_tokens.md): Calls the API to count the number of tokens in the text prompt.

[`create_tuned_model(...)`](../google/generativeai/create_tuned_model.md): Calls the API to initiate a tuning process that optimizes a model for specific data, returning an operation object to track and manage the tuning progress.

[`delete_file(...)`](../google/generativeai/delete_file.md): Calls the API to permanently delete a specified file using a supported file service.

[`delete_tuned_model(...)`](../google/generativeai/delete_tuned_model.md): Calls the API to delete a specified tuned model

[`embed_content(...)`](../google/generativeai/embed_content.md): Calls the API to create embeddings for content passed in.

[`embed_content_async(...)`](../google/generativeai/embed_content_async.md): Calls the API to create async embeddings for content passed in.

[`generate_embeddings(...)`](../google/generativeai/generate_embeddings.md): Calls the API to create an embedding for the text passed in.

[`generate_text(...)`](../google/generativeai/generate_text.md): Calls the API to generate text based on the provided prompt.

[`get_base_model(...)`](../google/generativeai/get_base_model.md): Calls the API to fetch a base model by name.

[`get_file(...)`](../google/generativeai/get_file.md): Calls the API to retrieve a specified file using a supported file service.

[`get_model(...)`](../google/generativeai/get_model.md): Calls the API to fetch a model by name.

[`get_operation(...)`](../google/generativeai/get_operation.md): Calls the API to get a specific operation

[`get_tuned_model(...)`](../google/generativeai/get_tuned_model.md): Calls the API to fetch a tuned model by name.

[`list_files(...)`](../google/generativeai/list_files.md): Calls the API to list files using a supported file service.

[`list_models(...)`](../google/generativeai/list_models.md): Calls the API to list all available models.

[`list_operations(...)`](../google/generativeai/list_operations.md): Calls the API to list all operations

[`list_tuned_models(...)`](../google/generativeai/list_tuned_models.md): Calls the API to list all tuned models.

[`update_tuned_model(...)`](../google/generativeai/update_tuned_model.md): Calls the API to push updates to a specified tuned model where only certain attributes are updatable.

[`upload_file(...)`](../google/generativeai/upload_file.md): Calls the API to upload a file using a supported file service.



<!-- Tabular view -->
 <table class="responsive fixed orange">
<colgroup><col width="214px"><col></colgroup>
<tr><th colspan="2"><h2 class="add-link">Other Members</h2></th></tr>

<tr>
<td>
__version__<a id="__version__"></a>
</td>
<td>
`'0.7.2'`
</td>
</tr><tr>
<td>
annotations<a id="annotations"></a>
</td>
<td>
Instance of `__future__._Feature`
</td>
</tr>
</table>

