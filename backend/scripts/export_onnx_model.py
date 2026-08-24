"""One-time export of all-MiniLM-L6-v2 to ONNX format for torch-free runtime inference.

Run this once (locally or in CI) before deploying. Requires optimum[onnxruntime] and
torch as build-time dependencies only - they are NOT required by the deployed service,
which loads the exported model.onnx + tokenizer.json via onnxruntime + tokenizers alone.
Install with: pip install "optimum[onnxruntime]" torch --index-url https://download.pytorch.org/whl/cpu
"""
import argparse
import os

from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer

DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "all-MiniLM-L6-v2-onnx")


def export_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2", output_dir: str = DEFAULT_OUTPUT_DIR):
    os.makedirs(output_dir, exist_ok=True)
    model = ORTModelForFeatureExtraction.from_pretrained(model_name, export=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Exported {model_name} to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Export a sentence-transformers model to ONNX for runtime use.")
    parser.add_argument("--model-name", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    export_model(args.model_name, args.output_dir)


if __name__ == "__main__":
    main()
