import argparse
import music21
from PIL import Image, ImageDraw, ImageFont

def parse(filePath: str):
    if filePath.endswith(".abc") or filePath.endswith(".musicxml"):
        return music21.converter.parse(filePath)
    else:
        print("Invalid file type")
        return None

def getMetaData(score: music21.stream.Score):
    return {
        "title": score.metadata.title,
        "composer": score.metadata.composer,
    }

def drawStaff(score: music21.stream.Score, outputPath: str):
    """
    根据 music21 解析出的乐谱，绘制七线谱（自然音阶谱）。
    七条线固定对应 C D E F G A B (从下往上)。
    音符的 Y 坐标根据音名映射到对应线。
    """
    # 七线谱参数
    staff_base_y = 280      # C 线（最低）的 Y 坐标
    line_spacing = 12       # 线间距 (px)
    start_x = 80            # 第一个音符 X 起始位置
    pixels_per_beat = 38    # 每拍宽度

    # 音名 → 线索引（0=C最低, 6=B最高）
    pitch_name_to_index = {'C':0, 'D':1, 'E':2, 'F':3, 'G':4, 'A':5, 'B':6}

    # 获取所有音符和休止符（按时间顺序）
    all_notes = []
    max_time = 0
    for part in score.parts:
        for element in part.flat.notesAndRests:
            if element.isNote:
                pitch = element.pitch.nameWithOctave   # e.g. "C4"
                base = pitch[0]  # C, D, E, F, G, A, B
                idx = pitch_name_to_index.get(base, 3)  # 默认 F 线
                y = staff_base_y - idx * line_spacing
                duration = element.quarterLength
                start = element.offset
                all_notes.append({
                    'type': 'note',
                    'x': start_x + start * pixels_per_beat,
                    'y': y,
                    'pitch_name': base,
                    'duration': duration,
                    'start': start
                })
                if start + duration > max_time:
                    max_time = start + duration
            elif element.isRest:
                duration = element.quarterLength
                start = element.offset
                all_notes.append({
                    'type': 'rest',
                    'x': start_x + start * pixels_per_beat,
                    'y': staff_base_y - 3 * line_spacing,  # 放在中间
                    'duration': duration,
                    'start': start
                })
                if start + duration > max_time:
                    max_time = start + duration

    if not all_notes:
        print("没有找到任何音符或休止符")
        return

    # 计算画布宽度
    canvas_width = max(1000, start_x + max_time * pixels_per_beat + 100)
    canvas_height = 360
    img = Image.new('RGB', (canvas_width, canvas_height), 'white')
    draw = ImageDraw.Draw(img)

    # 1. 画七条线，左侧标注音名
    for i, name in enumerate(['C','D','E','F','G','A','B']):
        y = staff_base_y - i * line_spacing
        draw.line((40, y, canvas_width-40, y), fill='black', width=1)
        draw.text((12, y-6), name, fill='black')

    # 2. 画小节线（从 music21 提取）
    measures = score.flat.getElementsByClass(music21.stream.Measure)
    for m in measures:
        x = start_x + m.offset * pixels_per_beat
        if start_x - 10 < x < canvas_width - 30:
            draw.line((x, staff_base_y-6*line_spacing-6, x, staff_base_y+6), fill='gray', width=1)

    # 3. 画所有音符和休止符
    for item in all_notes:
        if item['type'] == 'rest':
            # 休止符：画一个矩形 + 文字 '𝄽'
            x = item['x']
            y = item['y']
            draw.rectangle([x-6, y-5, x+6, y+3], fill='#5f7f9e')
            draw.text((x-4, y-2), '𝄽', fill='white')
        else:
            # 音符符头
            x = item['x']
            y = item['y']
            draw.ellipse([x-6, y-6, x+6, y+6], fill='black')
            # 显示音名（白字）
            draw.text((x-3, y-3), item['pitch_name'], fill='white')

    # 可选：显示标题
    title = score.metadata.title or "Untitled"
    draw.text((20, 20), f"🎵 {title}", fill='#2c6280')

    # 保存图片
    img.save(outputPath)
    print(f"✅ 七线谱已保存到: {outputPath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    score = parse(args.input)
    if score is None:
        exit(1)

    # 打印基本信息（调试用）
    print(f"标题: {score.metadata.title}")
    print(f"作曲家: {score.metadata.composer}")
    keys = score.flat.getElementsByClass(music21.key.KeySignature)
    if keys:
        print(f"调号: {keys[0]}")
    time_sigs = score.flat.getElementsByClass(music21.meter.TimeSignature)
    if time_sigs:
        print(f"拍号: {time_sigs[0]}")
    print(f"声部数量: {len(score.parts)}")

    drawStaff(score, args.output)