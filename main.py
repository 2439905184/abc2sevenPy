import argparse
import music21

from PIL import Image, ImageDraw, ImageFont, ImageColor

def parse(filePath:str):
    if filePath.endswith(".abc") or filePath.endswith(".musicxml"):
        return music21.converter.parse(filePath)
    else:
        print("Invalid file type")

def getMetaData(score: music21.stream.Score):
    return {
        "title": score.metadata.title,
        "composer": score.metadata.composer,
    }
def drawStaff(outputPath: str):
    with Image.open(outputPath) as im:
        ImageDraw.Draw(im)
        y = 0
        for line in 7:
            ImageDraw.line([(0,y),(0,y)],ImageColor.getrgb("black"))
            y += 100
        im.show()
        im.save(outputPath)
        print(f'Saved to {args.output}')
        
if __name__ == "__main__":
    print("main.py --input <xxx.abc> --output <xxx.png>")
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()
    inputPath = args.input
    outputPath = args.output
    # <music21.stream.Score 0x5aa0190>
    """
    Score 像一个乐谱，里面有 Part（声部）和 Measure（小节）。
Note 是具体的音符对象，而 notesAndRests、flat 和 recurse() 这三个工具能帮你高效地“打捞”到里面你需要的信息。
新手很容易混淆 Score 和 Part。
Score：可以理解为总谱，它是乐谱的“容器”。
Part：表示乐谱中的单个声部。
    """
    score = parse(inputPath)
    metaData = getMetaData(score)
    声部 = score.parts
    print(len(声部))
    keys_in_piece = score.flat.getElementsByClass(music21.key.KeySignature)
    if keys_in_piece:
        调号 = keys_in_piece[0]
        print(f"调号: {调号}")
    # 2. 提取拍号 (Time Signature)
    time_sigs_in_piece = score.flat.getElementsByClass(music21.meter.TimeSignature)
    if time_sigs_in_piece:
        拍号 = time_sigs_in_piece[0]
        print(f"拍号: {拍号}")
    # 3. 提取旋律信息
    # 遍历所有声部的所有音符和休止符
    for part in score.parts:
        print(f"\n--- 声部: {part.partName} ---")
        for element in part.flat.notesAndRests:
            if element.isNote:
                print(f"音符: {element.pitch.nameWithOctave}, 时值: {element.quarterLength}")
            elif element.isRest:
                print(f"休止符: (无音高), 时值: {element.quarterLength}")
    drawStaff(outputPath)
    #print(f'Saved to {args.output}')