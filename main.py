import argparse

import music21

from PIL import Image, ImageDraw, ImageFont, features

import freetype

# --------------------------------- 辅助函数 ---------------------------------

def render_glyph_to_image(font_path, char_code, font_size=80):
    """
    使用 FreeType 渲染一个字符（通过 Unicode 码点）为 PIL Image（灰度图，透明背景）。
    返回 (image, bearing_y) 其中 bearing_y 是字形顶部的偏移（相对于基线）。
    """
    face = freetype.Face(font_path)
    face.set_char_size(font_size * 64)

    face.load_char(char_code, freetype.FT_LOAD_RENDER)

    glyph = face.glyph
    bitmap = glyph.bitmap

    width = bitmap.width
    height = bitmap.rows
    pitch = bitmap.pitch

    buffer_data = bitmap.buffer
    if isinstance(buffer_data, list):
        buffer_data = bytes(buffer_data)
    else:
        buffer_data = bytes(buffer_data)

    # 【修复】正确处理 bitmap pitch（行步长）：当 pitch != width 时，逐行去除填充字节
    if height > 0 and width > 0 and pitch != width:
        rows_data = []
        for row in range(height):
            start = row * pitch
            rows_data.append(buffer_data[start:start + width])
        buffer_data = b''.join(rows_data)

    # 1. 创建 Alpha 通道：FreeType 的 buffer 直接就是 Alpha 掩码
    alpha = Image.frombytes('L', (width, height), buffer_data)

    # 2. 创建颜色通道：我们要黑色的字
    black_layer = Image.new('L', (width, height), 0)

    # 3. 合并
    img_rgba = Image.merge('LA', (black_layer, alpha))
    bearing_y = glyph.bitmap_top
    return img_rgba, bearing_y


def get_time_sorted_events(stream, event_class):
    events = stream.flat.getElementsByClass(event_class)
    return sorted(events, key=lambda e: e.offset)


def get_rest_shape(duration):
    if duration >= 3.9:
        char_code = "\uE4E5"
        rest_type = "full"
    elif duration >= 1.9:
        char_code = "\uE4E4"
        rest_type = "half"
    elif duration >= 0.9:
        char_code = "\uE4E5"
        rest_type = "quarter"
    elif duration >= 0.45:
        char_code = "\uE4E6"
        rest_type = "eighth"
    elif duration >= 0.225:
        char_code = "\uE4E7"
        rest_type = "16th"
    else:
        char_code = "\uE4E8"
        rest_type = "other"

    glyph_img, bearing_y = render_glyph_to_image(musicFontPath, char_code, font_size=50)
    return rest_type, glyph_img, bearing_y


def get_note_shape(duration):
    if duration >= 3.9:
        note_type = "full"
        char_code = "\uE1D2"
    elif duration >= 1.9:
        note_type = "half"
        char_code = "\uE1D3"
    elif duration >= 0.9:
        note_type = "quarter"
        char_code = "\uE1D5"
    elif duration >= 0.45:
        note_type = "eighth"
        char_code = "\uE1D7"
    elif duration >= 0.225:
        note_type = "16th"
        char_code = "\uE1D9"
    else:
        note_type = "other"
        char_code = "\uE1D5"
    glyph_img, bearing_y = render_glyph_to_image(musicFontPath, char_code, font_size=36)
    return note_type, glyph_img, bearing_y


# --------------------------------- 谱表配置 ---------------------------------

class StaffConfig:
    def __init__(self, base_midi, name):
        self.base_midi = base_midi  # 第一线（最下线）的 MIDI 编号
        self.name = name


# 高音谱：第一线 = C4 (60)
TREBLE = StaffConfig(60, "高音")
# 低音谱：第一线 = C3 (48)
BASS = StaffConfig(48, "低音")


# --------------------------------- 全局布局 ---------------------------------

LINE_SPACING = 12
NOTE_HEAD_R = 6
PIXELS_PER_BEAT = 80

STAFF_TOP_Y = 300
STAFF_GAP = 200
BASS_TOP_Y = STAFF_TOP_Y + STAFF_GAP


# 【修复】用音名+八度计算线位偏移，取代原来的 MIDI 半音遍历法
# 原方法的缺陷：MIDI 编号无法区分同音异名（如 G#3 和 Ab3 都是 MIDI 56），
# 从 C 向下遍历消耗半音时会停在相邻的自然音级上，导致带升降号的音符定位到错误的线。
def get_line_offset_from_pitch(note_step, note_octave, base_midi) -> int:
    """
    根据音名字母和八度计算线位偏移。

    Args:
        note_step: 音名字母 'C', 'D', 'E', 'F', 'G', 'A', 'B'
        note_octave: 八度数（整数），如 C4 的 octave=4
        base_midi: 谱表第一线（最下线）对应的 MIDI 编号

    Returns:
        line_offset: 整数。0 = 第一线（do），正数 = 向上，负数 = 向下加线。
    """
    NOTE_TO_LINE = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}
    base_octave = (base_midi // 12) - 1  # MIDI 60 → C4 (octave 4)
    return NOTE_TO_LINE[note_step] + (note_octave - base_octave) * 7


# --------------------------------- 绘制函数 ---------------------------------

def draw_staff(
    draw,
    config: StaffConfig,
    staff_y,
    notes_and_rests,
    key_timeline,
    start_x,
    canvas_width,
    font,
    music_font,
    当前谱表的小节,
    offset_map,
    canvas,
):
    base_midi = config.base_midi

    # 七条线的 Y 坐标 (线1=最下)
    line_y = []
    for i in range(7):
        y = staff_y - i * LINE_SPACING
        line_y.append(y)

    # 画七条线
    for i, y in enumerate(line_y):
        if i == 0:
            text = "do"
        elif i == 1:
            text = "re"
        elif i == 2:
            text = "mi"
        elif i == 3:
            text = "fa"
        elif i == 4:
            text = "so"
        elif i == 5:
            text = "la"
        elif i == 6:
            text = "si"
        draw.text((40 - 6, y), text, fill="black")
        draw.line((40, y, canvas_width - 40, y), fill="black", width=1)

    # 画拍号
    time_num_y = (line_y[3] + line_y[6]) / 2
    time_den_y = (line_y[0] + line_y[2]) / 2

    if config.name == "高音":
        time_events = get_time_sorted_events(score, music21.meter.TimeSignature)
        for ts in time_events:
            x = start_x
            draw.text(
                (x - 20, time_num_y - 10), str(ts.numerator), fill="black", font=font
            )
            draw.text(
                (x - 20, time_den_y - 10), str(ts.denominator), fill="black", font=font
            )

    # 画调号标记
    prev_key = None
    for offset, tonic_name, mode in key_timeline:
        if (tonic_name, mode) != prev_key:
            label = f"Key: {tonic_name}" + ("m" if mode == "minor" else "")
            x = start_x + offset * PIXELS_PER_BEAT
            draw.text((x - 30, line_y[6] - 18), label, fill="darkblue", font=font)
            prev_key = (tonic_name, mode)

    # 画小节线
    for m in 当前谱表的小节:
        x = start_x + m.offset * PIXELS_PER_BEAT
        top_y = line_y[6]
        bottom_y = line_y[0]
        draw.line((x, top_y, x, bottom_y), fill="black", width=1)

    # 处理音符/休止符
    for el in notes_and_rests:
        offset = el.offset
        x = start_x + offset * PIXELS_PER_BEAT

        if el.isRest:
            duration, img, bearing_y = get_rest_shape(el.quarterLength)

            line3_y = line_y[2]
            if duration == "full":
                y = line3_y - LINE_SPACING
            elif duration == "half":
                y = line3_y + LINE_SPACING
            else:
                y = line3_y

            pasete_y = y - bearing_y
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            canvas.paste(img, (int(x), int(pasete_y)), img)
            continue

        elif el.isNote:
            # 【修复】使用音名+八度计算线位，取代 MIDI 编号遍历
            line_offset = get_line_offset_from_pitch(
                el.pitch.step, el.pitch.octave, base_midi
            )

            # 计算符头 Y（线位对应的 Y 坐标）
            note_y = staff_y - line_offset * LINE_SPACING

            # 绘制加线
            if line_offset < 0 or line_offset > 6:
                draw.line(
                    (x - 3, note_y, x + 3, note_y),
                    fill="black",
                    width=1,
                )

            # -------- 符头 --------
            duration, img, bearing_y = get_note_shape(el.quarterLength)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # bearing_y = bitmap_top，即从基线（音符中心）到字形位图顶部的像素距离
            # paste_y = note_y - bearing_y  →  基线对齐到 note_y
            pasete_y = note_y - bearing_y
            canvas.paste(img, (int(x), int(pasete_y)), img)

            draw.text((x, note_y + 24), str(el.pitch), fill="black", font=smallFont)

            # -------- 临时变音记号 --------
            acc = el.pitch.accidental
            if acc is not None and acc.alter != 0:
                if acc.alter == 1:
                    symbol, acc_bearing_y = render_glyph_to_image(
                        musicFontPath, "\uE262", font_size=36
                    )
                elif acc.alter == -1:
                    symbol, acc_bearing_y = render_glyph_to_image(
                        musicFontPath, "\uE260", font_size=36
                    )
                if symbol.mode != 'RGBA':
                    symbol = symbol.convert('RGBA')
                # 【修复】变音记号也需要用 bearing_y 垂直居中对齐到 note_y
                acc_paste_y = note_y - acc_bearing_y
                canvas.paste(
                    symbol, (int(x - symbol.width - 2), int(acc_paste_y)), symbol
                )

            # 还原记号
            elif acc is not None and acc.name == "natural":
                symbol, acc_bearing_y = render_glyph_to_image(
                    musicFontPath, "\uE261", font_size=36
                )
                if symbol.mode != 'RGBA':
                    symbol = symbol.convert('RGBA')
                acc_paste_y = note_y - acc_bearing_y
                canvas.paste(
                    symbol, (int(x - symbol.width - 2), int(acc_paste_y)), symbol
                )

        elif el.isChord:
            pass


# --------------------------------- 主入口 ---------------------------------

def draw_seven_staff(score: music21.stream.Score, output_path: str):
    global score_ref
    score_ref = score

    parts = list(score.parts)
    if len(parts) == 1:
        treble_part = parts[0]
        bass_part = None
    else:
        treble_part = parts[0]
        bass_part = parts[1]

    treble_notes = list(treble_part.flat.notesAndRests) if treble_part else []
    bass_notes = list(bass_part.flat.notesAndRests) if bass_part else []

    treble_measures = treble_part.getElementsByClass(music21.stream.Measure)
    bass_measures = bass_part.getElementsByClass(music21.stream.Measure)

    all_notes = treble_notes + bass_notes
    max_time = max((el.offset + el.quarterLength for el in all_notes), default=4)

    canvas_width = int(max(1000, 80 + max_time * PIXELS_PER_BEAT + 100))
    canvas_height = int(BASS_TOP_Y + 7 * LINE_SPACING + 80)

    img = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(img)

    title = score.metadata.title or "Untitled"
    draw.text((0, 0), title, font=chineseFont, fill="black")

    key_events = get_time_sorted_events(score, music21.key.KeySignature)
    key_timeline = []
    for k in key_events:
        kobj = k.asKey()
        tonic = kobj.tonic.name
        mode = kobj.mode
        key_timeline.append((k.offset, tonic, mode))
    if not key_timeline or key_timeline[0][0] > 0:
        key_timeline.insert(0, (0.0, "C", "major"))

    draw_staff(
        draw, TREBLE, STAFF_TOP_Y, treble_notes, key_timeline,
        80, canvas_width, chineseFont, music_font, treble_measures, None, img
    )

    if bass_part:
        draw_staff(
            draw, BASS, BASS_TOP_Y, bass_notes, key_timeline,
            80, canvas_width, chineseFont, music_font, bass_measures, None, img
        )

    img.save(output_path)
    img.show()
    print(f"✅ 七线谱已保存到: {output_path}")


# --------------------------------- 文件解析 ---------------------------------

def parse(filePath: str):
    if (
        filePath.endswith(".abc")
        or filePath.endswith(".musicxml")
        or filePath.endswith(".mxl")
    ):
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
    if features.check("raqm"):
        print("✅ 系统支持 RAQM 布局引擎，将启用高级字体特性。")
        LAYOUT_ENGINE = ImageFont.Layout.RAQM
    else:
        print("⚠️ 系统不支持 RAQM。将使用基础布局。")
        LAYOUT_ENGINE = None

    try:
        chineseFont = ImageFont.truetype("assets/puhuiti.otf", 16)
        smallFont = ImageFont.truetype("assets/puhuiti.otf", 10)
        music_font = ImageFont.truetype(
            "assets/bravura-bravura-1.392/redist/otf/BravuraText.otf", 20
        )
    except Exception as e:
        print("⚠️ 找不到字体文件，将使用默认字体。")
    musicFontPath = "assets/bravura-bravura-1.392/redist/otf/BravuraText.otf"

    draw_seven_staff(score, args.output)
