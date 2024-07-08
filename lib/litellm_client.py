import tiktoken
from litellm import completion, embedding
from config import get_api_keys
import requests
import json
from lib.shell_util import LIGHT_ORANGE, LIGHT_RED, RESET_COLOR


class LitellmEmbeddings:
    def __init__(self, model, api_key, api_base=None, api_version=None):
        """
        Initialize LitellmEmbeddings.

        Args:
            model (str): The embedding model to use.
            api_key (str): API key for authentication.
            api_base (str, optional): Base URL for the API. Defaults to None.
            api_version (str, optional): Version of the API to use. Defaults to None.
        """
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.api_version = api_version

    def embed_documents(self, texts):
        """
        Embed a list of documents.

        Args:
            texts (list): List of document texts to embed.

        Returns:
            list: List of embeddings for the provided texts.
        """
        if self.model.startswith("azure/"):
            f"{self.api_base}/{self.api_version}/embeddings"

        response = embedding(
            model=self.model,
            input=texts,
            api_key=self.api_key,
            api_base=self.api_base,
            api_version=self.api_version,
        )
        embeddings = [item["embedding"] for item in response["data"]]
        return embeddings

    def embed_query(self, query):
        """
        Embed a single query.

        Args:
            query (str): The query text to embed.

        Returns:
            list: Embedding for the query.
        """
        if self.model.startswith("azure/"):
            f"{self.api_base}/{self.api_version}/embeddings"

        response = embedding(
            model=self.model,
            input=[query],
            api_key=self.api_key,
            api_base=self.api_base,
            api_version=self.api_version,
        )
        embedding_result = response["data"][0]["embedding"]
        return embedding_result


def create_litellm_client(model):
    """
    Create a LiteLLM client for the specified model.

    Args:
        model (str): The model to be used.

    Returns:
        function: The LiteLLM completion function.
    """
    # Just validate the model once, get API keys
    get_api_keys(model)

    return completion


def create_litellm_client_embeddings(
    model, api_key, api_base=None, api_version=None
):
    """
    Create a LiteLLM client for embeddings.

    Args:
        model (str): The embedding model to use.
        api_key (str): API key for authentication.
        api_base (str, optional): Base URL for the API. Defaults to None.
        api_version (str, optional): Version of the API to use. Defaults to None.

    Returns:
        LitellmEmbeddings: The LitellmEmbeddings instance.
    """
    return LitellmEmbeddings(model, api_key, api_base, api_version)


def calculate_token_count(model, messages, encoding):
    """
    Calculate the token count for the input and output.

    Args:
        model (str): The model to be used.
        messages (list): List of messages.
        encoding (tiktoken.Encoding): The encoding to use for token counting.

    Returns:
        tuple: Total input tokens, total output tokens, and combined total tokens.
    """
    total_input = 0
    total_output = 0
    for message in messages:
        if message["role"] == "user":
            if isinstance(message["content"], list):
                for content_item in message["content"]:
                    if content_item["type"] == "text":
                        total_input += len(encoding.encode(content_item["text"], disallowed_special=()))
            else:
                total_input += len(encoding.encode(message["content"], disallowed_special=()))
        else:
            if isinstance(message["content"], list):
                for content_item in message["content"]:
                    if content_item["type"] == "text":
                        total_output += len(encoding.encode(content_item["text"], disallowed_special=()))
            else:
                total_output += len(encoding.encode(message["content"], disallowed_special=()))
    return total_input, total_output, total_input + total_output


def raw_token_count(text, model):
    try:
        encoding = tiktoken.encoding_for_model(model.split("/")[-1])
    except Exception as e:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text, disallowed_special=()))


def get_available_models(filter_text=None):
    """
    Fetch and optionally filter available models from LiteLLM.

    Args:
        filter_text (str, optional): Text to filter models. If None, return all models.

    Returns:
        list: List of available models in the format "provider/model".
    """
    url = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
    response = requests.get(url)
    models_data = json.loads(response.text)

    available_models = set()
    for model, data in models_data.items():
        if filter_text is None or (filter_text.lower() in model.lower()):
            available_models.add(model)

    return sorted(list(available_models))