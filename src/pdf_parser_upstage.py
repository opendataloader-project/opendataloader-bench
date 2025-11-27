import os
import requests
from dotenv import load_dotenv

load_dotenv()


def inference(input_path):
    api_key = os.getenv("UPSTAGE_API_KEY")
    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {"Authorization": f"Bearer {api_key}"}
    with open(input_path, "rb") as document_file:
        files = {"document": document_file}
        data = {
            "ocr": "force",
            "model": "document-parse",
            "output_formats": "['markdown']",
        }
        response = requests.post(url, headers=headers, files=files, data=data)
    response.raise_for_status()
    return response.json()


def to_markdown(doc_paths, _, output_dir):
    for doc_path in doc_paths:
        response_json = inference(doc_path)
        markdown = response_json.get("content", {}).get("markdown")

        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
