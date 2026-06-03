import argparse
import pyabc2

from PIL import Image, ImageDraw, ImageFont

if __name__ == "__main__":
    print("main.py --input <xxx.abc> --output <xxx.png>")
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()
    abcFile = args.input
    outputFile = args.output
    tune = pyabc2.load(abcFile)
    render()
    print(f'Saved to {args.output}')