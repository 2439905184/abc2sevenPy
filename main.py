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

def pitch_to_staff_position(note_midi, tonic_midi, mode='major'):
    """
    根据音符的 MIDI 编号和当前调性的主音 MIDI，计算：
    - degree: 1~7 自然音级
    - octave_offset: 相对于基准八度的偏移（整数）
    - alter: 临时变音记号，1=#，-1=b，0=无
    返回 (degree, octave_offset, alter)
    """
    # 自然大/小调半音模式
    if mode == 'major':
        steps = [0, 2, 4, 5, 7, 9, 11]
    else:  # 默认自然小调
        steps = [0, 2, 3, 5, 7, 8, 10]

    diff = note_midi - tonic_midi
    octave_offset = diff // 12
    half_step = diff % 12

    # 检查是否属于自然音级
    if half_step in steps:
        degree = steps.index(half_step) + 1
        alter = 0
    else:
        # 临时变音：找最近的步骤，计算 alter
        # 升半音 alter=1，降半音 alter=-1
        for i, step in enumerate(steps):
            if step == (half_step - 1) % 12:
                degree = i + 1
                alter = 1
                break
            if step == (half_step + 1) % 12:
                degree = i + 1
                alter = -1
                break
        else:
            # 极端情况，回退
            degree = 1
            alter = 0
    return degree, octave_offset, alter

def get_tonic_midi(key_signature):
    """将调号强制固定在八度 4，返回主音的 MIDI 编号和 mode"""
    k = key_signature.asKey()
    tonic_name = k.tonic.name  # C, D, F#, Bb 等
    # 构造八度 4 的音高
    tonic_pitch = music21.pitch.Pitch(f"{tonic_name}4")
    return tonic_pitch.midi, k.mode

# --------------------------------- 主绘制函数 ---------------------------------

def drawSevenStaff(score: music21.stream.Score, output_path: str):
    # ---------- 画布与谱表参数 ----------
    staff_base_y = 280          # 第一条线（音级1）的 Y 坐标（最低线）
    line_spacing = 12           # 线间距
    start_x = 80                # 左侧起始 X
    pixels_per_beat = 38        # 每拍像素宽度
    note_head_r = 6

    # 七条线的 Y 位置（线1~线7，从下往上 Y 递减）
    line_y = [staff_base_y - i * line_spacing for i in range(7)]  # 线1~7

    # ---------- 获取事件 ----------
    key_events = get_time_sorted_events(score, music21.key.KeySignature)
    time_events = get_time_sorted_events(score, music21.meter.TimeSignature)
    measures = list(score.flat.getElementsByClass(music21.stream.Measure))

    notes_and_rests = []
    for part in score.parts:
        for el in part.flat.notesAndRests:
            notes_and_rests.append(el)

    max_time = max(
        (el.offset + (el.quarterLength if hasattr(el, 'quarterLength') else 0)
         for el in notes_and_rests),
        default=4
    )
    canvas_width = max(1000, start_x + max_time * pixels_per_beat + 100)
    canvas_height = 400

    img = Image.new('RGB', (canvas_width, canvas_height), 'white')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("assets/puhuiti.otf", 16)
        music_font = ImageFont.truetype("assets/bravura.ttf", 20)
    except:
        font = ImageFont.load_default()
        music_font = font

    # ---------- 画七条线 ----------
    for i, y in enumerate(line_y):
        draw.line((40, y, canvas_width - 40, y), fill='black', width=1)
        draw.text((12, y - 6), str(i + 1), fill='black', font=font)  # 音级数字

    # ---------- 拍号 ----------
    time_num_y = (line_y[3] + line_y[6]) / 2   # 4~7 线中间（分子）
    time_den_y = (line_y[0] + line_y[2]) / 2   # 1~3 线中间（分母）
    for ts in time_events:
        x = start_x + ts.offset * pixels_per_beat
        draw.text((x - 20, time_num_y - 10), str(ts.numerator), fill='black', font=font)
        draw.text((x - 20, time_den_y - 10), str(ts.denominator), fill='black', font=font)

    # ---------- 小节线 ----------
    for m in measures:
        x = start_x + m.offset * pixels_per_beat
        if start_x - 10 < x < canvas_width - 30:
            draw.line((x, line_y[0] - 6, x, line_y[6] + 6), fill='gray', width=1)

    # ---------- 调号标记 ----------
    if not key_events:
        # 至少有一条默认 C 大调
        key_events = [music21.key.KeySignature(0)]
        key_events[0].offset = 0.0
    key_timeline = []  # (offset, tonic_midi, mode)
    for ke in key_events:
        tonic_midi, mode = get_tonic_midi(ke)
        key_timeline.append((ke.offset, tonic_midi, mode))
    key_timeline.sort(key=lambda x: x[0])

    prev_tonic = None
    prev_mode = None
    for offset, tonic_midi, mode in key_timeline:
        if (tonic_midi, mode) != (prev_tonic, prev_mode):
            tonic_pitch = music21.pitch.Pitch()
            tonic_pitch.midi = tonic_midi
            label = f"1={tonic_pitch.name}"
            x = start_x + offset * pixels_per_beat
            draw.text((x - 40, line_y[0] - 20), label, fill='darkblue', font=font)
            prev_tonic, prev_mode = tonic_midi, mode

    # ---------- 收集音符信息 ----------
    note_data = []
    for el in notes_and_rests:
        offset = el.offset
        # 查找当前调性
        current_tonic = key_timeline[0][1]
        current_mode = key_timeline[0][2]
        for t, tm, m in key_timeline:
            if t <= offset:
                current_tonic = tm
                current_mode = m
            else:
                break
        if el.isNote:
            midi = el.pitch.midi
            degree, octave_offset, alter = pitch_to_staff_position(midi, current_tonic, current_mode)
            note_data.append({
                'type': 'note',
                'start': offset,
                'duration': el.quarterLength,
                'degree': degree,
                'octave_offset': octave_offset,
                'alter': alter,
            })
        elif el.isRest:
            note_data.append({
                'type': 'rest',
                'start': offset,
                'duration': el.quarterLength,
            })
    note_data.sort(key=lambda x: x['start'])

    # ---------- 绘制音符与休止符 ----------
    for nd in note_data:
        x = start_x + nd['start'] * pixels_per_beat

        if nd['type'] == 'rest':
            shape, symbol = get_rest_shape(nd['duration'])
            line3_y = line_y[2]  # 第三条线
            if shape == 'full':
                y = line3_y - line_spacing
            elif shape == 'half':
                y = line3_y + line_spacing
            else:
                y = line3_y
            draw.rectangle([x - 6, y - 6, x + 6, y + 4], fill='#5f7f9e')
            draw.text((x - 4, y - 2), symbol, fill='white', font=music_font)
            continue

        # 音符
        degree = nd['degree']
        octave_offset = nd['octave_offset']
        # 垂直位置（单位：线间距，0=线1，-6=线7）
        posY = -(degree - 1) - octave_offset * 7
        # 实际绘制的 Y 坐标
        note_y = staff_base_y + posY * line_spacing

        # ---------- 画加线 ----------
        # 基本七线范围： [ -6 , 0 ] （线7 ~ 线1）
        top_line_pos = -6
        bottom_line_pos = 0
        def draw_ledger_lines(min_pos, max_pos, exclude_pos=None):
            """在 min_pos 与 max_pos 之间的所有整数位置上画加线"""
            if min_pos > max_pos:
                min_pos, max_pos = max_pos, min_pos
            for p in range(min_pos, max_pos + 1):
                if exclude_pos is not None and p == exclude_pos:
                    continue
                ledger_y = staff_base_y + p * line_spacing
                draw.line(
                    (x - note_head_r - 2, ledger_y, x + note_head_r + 2, ledger_y),
                    fill='black', width=1
                )
        if posY > bottom_line_pos:
            # 下加线：画在 posY 与 bottom_line_pos 之间的整数位置（不含音符所在的线）
            draw_ledger_lines(bottom_line_pos + 1, int(posY) if posY != int(posY) else int(posY)-1,
                              exclude_pos=int(posY) if posY == int(posY) else None)
        elif posY < top_line_pos:
            # 上加线：画在 top_line_pos 与 posY 之间的整数位置
            draw_ledger_lines(int(posY)+1 if posY == int(posY) else int(posY), top_line_pos - 1,
                              exclude_pos=int(posY) if posY == int(posY) else None)

        # ---------- 符头 ----------
        draw.ellipse(
            [x - note_head_r, note_y - note_head_r, x + note_head_r, note_y + note_head_r],
            fill='black'
        )

        # ---------- 临时变音记号 ----------
        if nd['alter'] != 0:
            acc_map = {1: '♯', -1: '♭', 0: '♮'}
            draw.text(
                (x + note_head_r + 2, note_y - note_head_r),
                acc_map.get(nd['alter'], ''),
                fill='red', font=font
            )

    # ---------- 标题 ----------
    title = score.metadata.title or "Untitled"
    draw.text((20, 20), title, fill='#2c6280', font=font)

    img.save(output_path)
    img.show()
    print(f"✅ 七线谱已保存到: {output_path}")


# --------------------------------- 入口 ---------------------------------

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
    print(f"作曲家: {score.metadata.composer}")
    ks = score.flat.getElementsByClass(music21.key.KeySignature)
    if ks:
        print(f"调号数量: {len(ks)}")
    ts = score.flat.getElementsByClass(music21.meter.TimeSignature)
    if ts:
        print(f"拍号数量: {len(ts)}")
    print(f"声部数量: {len(score.parts)}")

    drawSevenStaff(score, args.output)