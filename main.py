import argparse
import music21
from PIL import Image, ImageDraw, ImageFont

if __name__ == "__main__":
    print("main.py --input <xxx.abc> --output <xxx.png>")
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()
    render()
    print(f'Saved to {args.output}')