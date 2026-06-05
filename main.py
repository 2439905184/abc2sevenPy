import argparse
import music21
from PIL import Image, ImageDraw, ImageFont

# --------------------------------- 辅助函数 ---------------------------------
def get_time_sorted_events(stream, event_class):
    events = stream.flat.getElementsByClass(event_class)
    return sorted(events, key=lambda e: e.offset)

def get_rest_shape(duration):
    if duration >= 3.9:
        return ('full', '𝄻')
    elif duration >= 1.9:
        return ('half', '𝄼')
    elif duration >= 0.9:
        return ('quarter', '𝄽')
    elif duration >= 0.45:
        return ('eighth', '𝄾')
    elif duration >= 0.225:
        return ('16th', '𝄿')
    else:
        return ('other', '𝄿')

# --------------------------------- 谱表配置 ---------------------------------
class StaffConfig:
    def __init__(self, base_midi, name):
        self.base_midi = base_midi   # 第一线（最下线）的 MIDI 编号
        self.name = name

# 高音谱：第一线 = C4 (60)
TREBLE = StaffConfig(60, "高音")
# 低音谱：第一线 = C3 (48)
BASS = StaffConfig(48, "低音")

# --------------------------------- 全局布局 ---------------------------------
LINE_SPACING = 12
NOTE_HEAD_R = 6
PIXELS_PER_BEAT = 38

# 谱表垂直间距
STAFF_TOP_Y = 50          # 高音谱第一条线 Y
STAFF_GAP = 80            # 两谱表第一条线之间的距离（高音第一条线到低音第一条线）
BASS_TOP_Y = STAFF_TOP_Y + STAFF_GAP

# --------------------------------- 绘制函数 ---------------------------------
def draw_staff(draw, config: StaffConfig, staff_y, notes_and_rests, key_timeline,
               start_x, canvas_width, font, music_font, measures, offset_map):
    """
    在指定 Y 位置绘制一个谱表（七条线+音符/休止符/加线/临时记号/调号标记/拍号）。
    offset_map 用于将 music21 的 offset 换算为 X 坐标。
    """
    base_midi = config.base_midi
    # 七条线的 Y 坐标 (线1=最下)
    line_y = [staff_y - i * LINE_SPACING for i in range(7)]

    # 画七条线
    for i, y in enumerate(line_y):
        draw.line((40, y, canvas_width - 40, y), fill='black', width=1)

    # 画拍号（只在该谱表的小节开始处画）
    time_num_y = (line_y[3] + line_y[6]) / 2
    time_den_y = (line_y[0] + line_y[2]) / 2
    # 提取拍号变化点（可以从 measures 或 time_events 获取）
    # 这里简单从整个 score 的拍号事件处理，但为避免重复绘制，只在高音谱画拍号
    if config.name == "高音":
        time_events = get_time_sorted_events(score, music21.meter.TimeSignature)
        for ts in time_events:
            x = start_x + ts.offset * PIXELS_PER_BEAT
            draw.text((x - 20, time_num_y - 10), str(ts.numerator), fill='black', font=font)
            draw.text((x - 20, time_den_y - 10), str(ts.denominator), fill='black', font=font)

    # 画调号标记（只在调性变化处上方标注）
    # 取 key_timeline 去重
    prev_key = None
    for offset, tonic_name, mode in key_timeline:
        if (tonic_name, mode) != prev_key:
            label = f"Key: {tonic_name}" + ("m" if mode == 'minor' else "")
            x = start_x + offset * PIXELS_PER_BEAT
            draw.text((x - 30, line_y[6] - 18), label, fill='darkblue', font=font)
            prev_key = (tonic_name, mode)

    # 画小节线（每个谱表独立）
    for m in measures:
        x = start_x + m.offset * PIXELS_PER_BEAT
        if start_x - 10 < x < canvas_width - 30:
            draw.line((x, line_y[0] - 6, x, line_y[6] + 6), fill='gray', width=1)

    # 处理音符/休止符
    for el in notes_and_rests:
        offset = el.offset
        x = start_x + offset * PIXELS_PER_BEAT

        if el.isRest:
            shape, symbol = get_rest_shape(el.quarterLength)
            line3_y = line_y[2]  # 第三条线
            if shape == 'full':
                y = line3_y - LINE_SPACING
            elif shape == 'half':
                y = line3_y + LINE_SPACING
            else:
                y = line3_y
            draw.rectangle([x - 6, y - 6, x + 6, y + 4], fill='#5f7f9e')
            draw.text((x - 4, y - 2), symbol, fill='white', font=music_font)
            continue

        # 音符
        midi = el.pitch.midi
        line_index = midi - base_midi   # 0 = 线1, 6 = 线7

        # 计算符头 Y
        note_y = staff_y - line_index * LINE_SPACING

        # -------- 加线绘制 --------
        def draw_ledger_lines(low_line, high_line, exclude):
            """在 low_line 和 high_line 之间的整数线位置画短线，排除 exclude 线"""
            if low_line > high_line:
                low_line, high_line = high_line, low_line
            for l in range(low_line, high_line + 1):
                if l == exclude:
                    continue
                ledger_y = staff_y - l * LINE_SPACING
                draw.line((x - NOTE_HEAD_R - 2, ledger_y, x + NOTE_HEAD_R + 2, ledger_y),
                          fill='black', width=1)

        # 基本线范围 [0, 6]
        if line_index < 0:
            # 下加线
            draw_ledger_lines(line_index, -1, exclude=line_index)
        elif line_index > 6:
            # 上加线
            draw_ledger_lines(7, line_index, exclude=line_index)

        # -------- 符头 --------
        draw.ellipse([x - NOTE_HEAD_R, note_y - NOTE_HEAD_R,
                      x + NOTE_HEAD_R, note_y + NOTE_HEAD_R], fill='black')

        # -------- 临时变音记号 --------
        acc = el.pitch.accidental
        if acc is not None and acc.alter != 0:
            symbol = '♯' if acc.alter == 1 else '♭' if acc.alter == -1 else ''
            if symbol:
                draw.text((x + NOTE_HEAD_R + 2, note_y - NOTE_HEAD_R),
                          symbol, fill='red', font=font)
        # 还原记号（显式 natural）
        elif acc is not None and acc.name == 'natural':
            draw.text((x + NOTE_HEAD_R + 2, note_y - NOTE_HEAD_R),
                      '♮', fill='red', font=font)

# --------------------------------- 主入口 ---------------------------------
def draw_seven_staff(score: music21.stream.Score, output_path: str):
    global score_ref
    score_ref = score

    # 获取 parts
    parts = list(score.parts)
    if len(parts) == 1:
        # 只有一个声部，当作高音谱
        treble_part = parts[0]
        bass_part = None
    else:
        # 一般钢琴谱：第一部分高音，第二部分低音
        treble_part = parts[0]
        bass_part = parts[1]

    # 收集所有音符/休止符
    treble_notes = list(treble_part.flat.notesAndRests) if treble_part else []
    bass_notes = list(bass_part.flat.notesAndRests) if bass_part else []

    # 获取小节
    measures = list(score.flat.getElementsByClass(music21.stream.Measure))

    # 计算最大时间
    all_notes = treble_notes + bass_notes
    max_time = max((el.offset + el.quarterLength for el in all_notes), default=4)
    canvas_width = max(1000, 80 + max_time * PIXELS_PER_BEAT + 100)
    canvas_height = BASS_TOP_Y + 7 * LINE_SPACING + 80
    img = Image.new('RGB', (canvas_width, canvas_height), 'white')
    draw = ImageDraw.Draw(img)

    try:
        chineseFont = ImageFont.truetype("assets/puhuiti.otf", 16)
        #chineseFont = ImageFont.truetype("", 36)
        music_font = ImageFont.truetype("assets/bravura.ttf", 20)
    except:
        #chineseFont = ImageFont.load_default()
        #music_font = chineseFont
        pass
    # 标题
    title = score.metadata.title or "Untitled"
    draw.text((0, 0), title, font=chineseFont,fill='black', )
    print(chineseFont)
    # 构建调性时间线（只用于显示标签）
    key_events = get_time_sorted_events(score, music21.key.KeySignature)
    key_timeline = []
    for k in key_events:
        kobj = k.asKey()
        tonic = kobj.tonic.name
        mode = kobj.mode
        key_timeline.append((k.offset, tonic, mode))
    # 确保默认 C 大调
    if not key_timeline or key_timeline[0][0] > 0:
        key_timeline.insert(0, (0.0, 'C', 'major'))

    # 绘制高音谱
    draw_staff(draw, TREBLE, STAFF_TOP_Y, treble_notes, key_timeline,
    80, canvas_width, chineseFont, music_font, measures, None)

    #绘制低音谱（如果有）
    if bass_part:
        draw_staff(draw, BASS, BASS_TOP_Y, bass_notes, key_timeline,
                   80, canvas_width, chineseFont, music_font, measures, None)

    

    img.save(output_path)
    img.show()
    print(f"✅ 七线谱已保存到: {output_path}")

# --------------------------------- 文件解析 ---------------------------------
def parse(filePath: str):
    if filePath.endswith(".abc") or filePath.endswith(".musicxml"):
        return music21.converter.parse(filePath)
    else:
        print("Invalid file type")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    score = parse(args.input)
    if score is None:
        exit(1)

    print(f"标题: {score.metadata.title}")
    print(f"声部数量: {len(score.parts)}")
    draw_seven_staff(score, args.output)