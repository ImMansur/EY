# config.py
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

def get_azure_client():
    """
    Create Azure OpenAI client using only the required parameters.
    Compatible with openai 1.0 → 1.55+
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key  = os.getenv("AZURE_OPENAI_API_KEY")
    version  = os.getenv("AZURE_OPENAI_API_VERSION")

    if not endpoint or not api_key or not version:
        missing = []
        if not endpoint: missing.append("AZURE_OPENAI_ENDPOINT")
        if not api_key:  missing.append("AZURE_OPENAI_API_KEY")
        if not version:  missing.append("AZURE_OPENAI_API_VERSION")
        raise ValueError(f"Missing required env variables: {', '.join(missing)}")

    return AzureOpenAI(
        azure_endpoint = endpoint,
        api_key        = api_key,
        api_version    = version
        # IMPORTANT: do NOT add timeout, http_client, proxies, etc. here
        # unless you explicitly need them — they cause the error in newer versions
    )


def get_deployment_name():
    name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    if not name:
        raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME is not set in .env")
    return name


# Quick debug helper (run this file directly to test)
if __name__ == "__main__":
    try:
        client = get_azure_client()
        print("AzureOpenAI client created successfully.")
        print("Deployment name:", get_deployment_name())
    except Exception as e:
        print("Error:", str(e))
        print("Unexpected error:", e)
