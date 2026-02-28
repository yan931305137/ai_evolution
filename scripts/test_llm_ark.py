
import os
import sys
import logging

# Add src to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.llm import LLMClient
from dotenv import load_dotenv

# Load env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(level=logging.INFO)

def test_ark_text():
    print("Testing Ark Text Generation...")
    client = LLMClient(provider="ark")
    messages = [{"role": "user", "content": "你好，请介绍一下你自己。"}]
    response = client.generate(messages)
    print(f"Response: {response.content}\n")

def test_ark_multimodal():
    print("Testing Ark Multimodal Generation...")
    client = LLMClient(provider="ark")
    # User's example format (Ark format)
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_image",
                    "image_url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png"
                },
                {
                    "type": "input_text",
                    "text": "你看见了什么？"
                },
            ],
        }
    ]
    try:
        response = client.generate(messages)
        print(f"Response: {response.content}\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ark_text()
    test_ark_multimodal()
