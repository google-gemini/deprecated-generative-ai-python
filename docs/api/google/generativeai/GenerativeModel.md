
# google.generativeai.GenerativeModel

<!-- Insert buttons and diff -->

<table class="tfo-notebook-buttons tfo-api nocontent">
<td>
  <a target="_blank" href="https://github.com/google/generative-ai-python/blob/master/google/generativeai/generative_models.py#L27-L478">
    <img src="https://www.tensorflow.org/images/GitHub-Mark-32px.png" />
    View source on GitHub
  </a>
</td>
</table>



The `genai.GenerativeModel` class wraps default parameters for calls to <a href="../../google/generativeai/GenerativeModel.md#generate_content"><code>GenerativeModel.generate_content</code></a>, <a href="../../google/generativeai/GenerativeModel.md#count_tokens"><code>GenerativeModel.count_tokens</code></a>, and <a href="../../google/generativeai/GenerativeModel.md#start_chat"><code>GenerativeModel.start_chat</code></a>.

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>google.generativeai.GenerativeModel(
    model_name: str = &#x27;gemini-1.5-flash-002&#x27;,
    safety_settings: (safety_types.SafetySettingOptions | None) = None,
    generation_config: (generation_types.GenerationConfigType | None) = None,
    tools: (content_types.FunctionLibraryType | None) = None,
    tool_config: (content_types.ToolConfigType | None) = None,
    system_instruction: (content_types.ContentType | None) = None
)
</code></pre>



<!-- Placeholder for "Used in" -->

This family of functionality is designed to support multi-turn conversations, and multimodal
requests. What media-types are supported for input and output is model-dependant.

```
>>> import google.generativeai as genai
>>> genai.configure(api_key='YOUR_API_KEY')
>>> model = genai.GenerativeModel('models/gemini-1.5-flash')
>>> result = model.generate_content('Tell me a story about a magic backpack')
>>> result.text
"In the quaint little town of Lakeside, there lived a young girl named Lily..."
```

#### Multimodal input:



```
>>> model = genai.GenerativeModel('models/gemini-1.5-flash')
>>> result = model.generate_content([
...     "Give me a recipe for these:", PIL.Image.open('scones.jpeg')])
>>> result.text
"**Blueberry Scones** ..."
```

Multi-turn conversation:

```
>>> chat = model.start_chat()
>>> response = chat.send_message("Hi, I have some questions for you.")
>>> response.text
"Sure, I'll do my best to answer your questions..."
```

To list the compatible model names use:

```
>>> for m in genai.list_models():
...     if 'generateContent' in m.supported_generation_methods:
...         print(m.name)
```

<!-- Tabular view -->
 <table class="responsive fixed orange">
<colgroup><col width="214px"><col></colgroup>
<tr><th colspan="2"><h2 class="add-link">Arguments</h2></th></tr>

<tr>
<td>

`model_name`<a id="model_name"></a>

</td>
<td>

The name of the model to query. To list compatible models use

</td>
</tr><tr>
<td>

`safety_settings`<a id="safety_settings"></a>

</td>
<td>

Sets the default safety filters. This controls which content is blocked
by the api before being returned.

</td>
</tr><tr>
<td>

`generation_config`<a id="generation_config"></a>

</td>
<td>

A `genai.GenerationConfig` setting the default generation parameters to
use.

</td>
</tr>
</table>





<!-- Tabular view -->
 <table class="responsive fixed orange">
<colgroup><col width="214px"><col></colgroup>
<tr><th colspan="2"><h2 class="add-link">Attributes</h2></th></tr>

<tr>
<td>

`cached_content`<a id="cached_content"></a>

</td>
<td>



</td>
</tr><tr>
<td>

`model_name`<a id="model_name"></a>

</td>
<td>



</td>
</tr>
</table>



## Methods

<h3 id="count_tokens"><code>count_tokens</code></h3>

<a target="_blank" class="external" href="https://github.com/google/generative-ai-python/blob/master/google/generativeai/generative_models.py#L399-L424">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>count_tokens(
    contents: content_types.ContentsType = None,
    *,
    generation_config: (generation_types.GenerationConfigType | None) = None,
    safety_settings: (safety_types.SafetySettingOptions | None) = None,
    tools: (content_types.FunctionLibraryType | None) = None,
    tool_config: (content_types.ToolConfigType | None) = None,
    request_options: (helper_types.RequestOptionsType | None) = None
) -> protos.CountTokensResponse
</code></pre>




<h3 id="count_tokens_async"><code>count_tokens_async</code></h3>

<a target="_blank" class="external" href="https://github.com/google/generative-ai-python/blob/master/google/generativeai/generative_models.py#L426-L451">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>count_tokens_async(
    contents=None,
    *,
    generation_config=None,
    safety_settings=None,
    tools=None,
    tool_config=None,
    request_options=None
)
</code></pre>




<h3 id="from_cached_content"><code>from_cached_content</code></h3>

<a target="_blank" class="external" href="https://github.com/google/generative-ai-python/blob/master/google/generativeai/generative_models.py#L204-L235">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>@classmethod</code>
<code>from_cached_content(
    cached_content: (str | caching.CachedContent),
    *,
    generation_config: (generation_types.GenerationConfigType | None) = None,
    safety_settings: (safety_types.SafetySettingOptions | None) = None
) -> GenerativeModel
</code></pre>

Creates a model with `cached_content` as model's context.


<!-- Tabular view -->
 <table class="responsive fixed orange">
<colgroup><col width="214px"><col></colgroup>
<tr><th colspan="2">Args</th></tr>

<tr>
<td>

`cached_content`

</td>
<td>

context for the model.

</td>
</tr><tr>
<td>

`generation_config`

</td>
<td>

Overrides for the model's generation config.

</td>
</tr><tr>
<td>

`safety_settings`

</td>
<td>

Overrides for the model's safety settings.

</td>
</tr>
</table>



<!-- Tabular view -->
 <table class="responsive fixed orange">
<colgroup><col width="214px"><col></colgroup>
<tr><th colspan="2">Returns</th></tr>
<tr class="alt">
<td colspan="2">

`GenerativeModel` object with `cached_content` as its context.

</td>
</tr>

</table>



<h3 id="generate_content"><code>generate_content</code></h3>

<a target="_blank" class="external" href="https://github.com/google/generative-ai-python/blob/master/google/generativeai/generative_models.py#L237-L342">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>generate_content(
    contents: content_types.ContentsType,
    *,
    generation_config: (generation_types.GenerationConfigType | None) = None,
    safety_settings: (safety_types.SafetySettingOptions | None) = None,
    stream: bool = False,
    tools: (content_types.FunctionLibraryType | None) = None,
    tool_config: (content_types.ToolConfigType | None) = None,
    request_options: (helper_types.RequestOptionsType | None) = None
) -> generation_types.GenerateContentResponse
</code></pre>

A multipurpose function to generate responses from the model.

This <a href="../../google/generativeai/GenerativeModel.md#generate_content"><code>GenerativeModel.generate_content</code></a> method can handle multimodal input, and multi-turn
conversations.

```
>>> model = genai.GenerativeModel('models/gemini-1.5-flash')
>>> response = model.generate_content('Tell me a story about a magic backpack')
>>> response.text
```

### Streaming

This method supports streaming with the `stream=True`. The result has the same type as the non streaming case,
but you can iterate over the response chunks as they become available:

```
>>> response = model.generate_content('Tell me a story about a magic backpack', stream=True)
>>> for chunk in response:
...   print(chunk.text)
```

### Multi-turn

This method supports multi-turn chats but is **stateless**: the entire conversation history needs to be sent with each
request. This takes some manual management but gives you complete control:

```
>>> messages = [{'role':'user', 'parts': ['hello']}]
>>> response = model.generate_content(messages) # "Hello, how can I help"
>>> messages.append(response.candidates[0].content)
>>> messages.append({'role':'user', 'parts': ['How does quantum physics work?']})
>>> response = model.generate_content(messages)
```

For a simpler multi-turn interface see <a href="../../google/generativeai/GenerativeModel.md#start_chat"><code>GenerativeModel.start_chat</code></a>.

### Input type flexibility

While the underlying API strictly expects a `list[protos.Content]` objects, this method
will convert the user input into the correct type. The hierarchy of types that can be
converted is below. Any of these objects can be passed as an equivalent `dict`.

* `Iterable[protos.Content]`
* <a href="../../google/generativeai/protos/Content.md"><code>protos.Content</code></a>
* `Iterable[protos.Part]`
* <a href="../../google/generativeai/protos/Part.md"><code>protos.Part</code></a>
* `str`, `Image`, or <a href="../../google/generativeai/protos/Blob.md"><code>protos.Blob</code></a>

In an `Iterable[protos.Content]` each `content` is a separate message.
But note that an `Iterable[protos.Part]` is taken as the parts of a single message.

<!-- Tabular view -->
 <table class="responsive fixed orange">
<colgroup><col width="214px"><col></colgroup>
<tr><th colspan="2">Arguments</th></tr>

<tr>
<td>

`contents`

</td>
<td>

The contents serving as the model's prompt.

</td>
</tr><tr>
<td>

`generation_config`

</td>
<td>

Overrides for the model's generation config.

</td>
</tr><tr>
<td>

`safety_settings`

</td>
<td>

Overrides for the model's safety settings.

</td>
</tr><tr>
<td>

`stream`

</td>
<td>

If True, yield response chunks as they are generated.

</td>
</tr><tr>
<td>

`tools`

</td>
<td>

`protos.Tools` more info coming soon.

</td>
</tr><tr>
<td>

`request_options`

</td>
<td>

Options for the request.

</td>
</tr>
</table>



<h3 id="generate_content_async"><code>generate_content_async</code></h3>

<a target="_blank" class="external" href="https://github.com/google/generative-ai-python/blob/master/google/generativeai/generative_models.py#L344-L396">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>generate_content_async(
    contents,
    *,
    generation_config=None,
    safety_settings=None,
    stream=False,
    tools=None,
    tool_config=None,
    request_options=None
)
</code></pre>

The async version of <a href="../../google/generativeai/GenerativeModel.md#generate_content"><code>GenerativeModel.generate_content</code></a>.


<h3 id="start_chat"><code>start_chat</code></h3>

<a target="_blank" class="external" href="https://github.com/google/generative-ai-python/blob/master/google/generativeai/generative_models.py#L455-L478">View source</a>

<pre class="devsite-click-to-copy prettyprint lang-py tfo-signature-link">
<code>start_chat(
    *,
    history: (Iterable[content_types.StrictContentType] | None) = None,
    enable_automatic_function_calling: bool = False
) -> ChatSession
</code></pre>

Returns a `genai.ChatSession` attached to this model.

```
>>> model = genai.GenerativeModel()
>>> chat = model.start_chat(history=[...])
>>> response = chat.send_message("Hello?")
```

<!-- Tabular view -->
 <table class="responsive fixed orange">
<colgroup><col width="214px"><col></colgroup>
<tr><th colspan="2">Arguments</th></tr>

<tr>
<td>

`history`

</td>
<td>

An iterable of <a href="../../google/generativeai/protos/Content.md"><code>protos.Content</code></a> objects, or equivalents to initialize the session.

</td>
</tr>
</table>





