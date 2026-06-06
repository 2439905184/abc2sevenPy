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

    # 设置字符大小（单位：1/64 点，*64 是 FreeType 惯例）

    face.set_char_size(font_size * 64)


    # 加载字形，使用 FT_LOAD_RENDER 直接渲染到位图

    # 第二个参数可以是 0 或 freetype.FT_LOAD_RENDER

    face.load_char(char_code, freetype.FT_LOAD_RENDER)

    glyph = face.glyph

    bitmap = glyph.bitmap


    # 获取位图数据（bytes 对象）

    width = bitmap.width

    height = bitmap.rows

    # 位图每行像素数（可能有 padding）

    pitch = bitmap.pitch


    # 将 FreeType 的灰度缓冲区（每个字节一个像素）转换为 Pillow Image

    # 注意：FreeType 的位图模式是 FT_PIXEL_MODE_GRAY，每个像素 1 字节

    mode = 'L'  # 8 位灰度，黑色为 0，白色为 255？

    # 实际上 FreeType 渲染的是黑色字符在透明背景上，但位图是反色？测试一下

    # 通常 bitmap.buffer 中是 [0,0,0,...] 表示背景，字符处 >0

    # 转换为 PIL 能用的 'L' 模式（0=黑，255=白）

    # 直接复制 buffer

    buffer_data = bitmap.buffer

    if isinstance(buffer_data, list):

        buffer_data = bytes(buffer_data)

    # 1. 创建 Alpha 通道：FreeType 的 buffer 直接就是 Alpha 掩码
    # 0=透明, 255=不透明
    alpha = Image.frombytes('L', (width, height), buffer_data)
    
    # 2. 创建颜色通道：我们要黑色的字，所以创建一个全黑的图像
    # 模式 'L'，全部填充 0 (黑色)
    black_layer = Image.new('L', (width, height), 0)
    
    # 3. 合并：将黑色层作为颜色，alpha 层作为透明度
    # 结果：字符部分是黑色且有不透明度，背景是完全透明
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

    glyph_img, bearing_y = render_glyph_to_image(musicFontPath, char_code, font_size=80)

    return rest_type, glyph_img, bearing_y

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

NOTE_HEAD_R =  6 #6 #符头半径

PIXELS_PER_BEAT = 80 # 38 normal


# 谱表垂直间距

STAFF_TOP_Y = 300  # 高音谱第一条线 Y

STAFF_GAP = 80  # 两谱表第一条线之间的距离（高音第一条线到低音第一条线）

BASS_TOP_Y = STAFF_TOP_Y + STAFF_GAP



# 返回: line_offset (整数)。0 表示基准线，1 表示高一条线，-1 表示低一条线。

# 你的思路非常清晰且正确：先算半音差，再根据自然音阶的“全全半全全全半”规律，将其转换为线位索引。

def get_line_offset_from_midi_treble(midi_note, base_midi_c) -> int:

    # 计算 MIDI 音符相对于基准 C (base_midi_c) 的线索引偏移量。

    """计算半音差：diff_semitones = midi_note - base_midi。

定义自然音阶步长：

C -> D: +2 半音 (全音)

D -> E: +2 半音 (全音)

E -> F: +1 半音 (半音)

F -> G: +2 半音 (全音)

G -> A: +2 半音 (全音)

A -> B: +2 半音 (全音)

B -> C: +1 半音 (半音)

循环累加：从基准线（Line 0）开始，不断减去上述步长，直到剩余的半音数不足以支撑下一个自然音级。减去的次数就是线位的偏移量。
"""

    半音差 = midi_note - base_midi_c

    自然音阶半音关系表 = [2, 2, 1, 2, 2, 2, 1] # 这里表示midi数字编号的差，1就是半音，2就是全音

    line_offset = 0

    remaining_semitones = 半音差
    

    # 如果音符比基准音低，我们需要反向计算

    if remaining_semitones < 0:

        # 反向步长: C<-B(1), B<-A(2), A<-G(2), G<-F(1), F<-E(2), E<-D(2), D<-C(2)

        reverse_steps = [1, 2, 2, 1, 2, 2, 2] 

        idx = 0 # 从 C 往 B 方向走

        while remaining_semitones < 0:

            # 取出当前方向的步长

            step = reverse_steps[idx % 7]

            if remaining_semitones + step <= 0:

                remaining_semitones += step

                line_offset -= 1

            else:

                break

            idx += 1

    else:

        # 如果音符比基准音高，正向计算

        idx = 0

        while remaining_semitones > 0:

            step = 自然音阶半音关系表[idx % 7]

            if remaining_semitones - step >= 0:

                remaining_semitones -= step

                line_offset += 1

            else:

                break

            idx += 1

    return line_offset

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
    """

    在指定 Y 位置绘制一个谱表（七条线+音符/休止符/加线/临时记号/调号标记/拍号）。

    offset_map 用于将 music21 的 offset 换算为 X 坐标。
    """

    base_midi = config.base_midi

    # 七条线的 Y 坐标 (线1=最下)

    # line_y = [staff_y - i * LINE_SPACING for i in range(7)]

    line_y = []

    for i in range(7):

        y = staff_y - i * LINE_SPACING

        line_y.append(y)


    # 画七条线

    for i, y in enumerate(line_y):

        draw.line((40, y, canvas_width - 40, y), fill="black", width=1)


    # 画拍号（只在该谱表的小节开始处画）

    time_num_y = (line_y[3] + line_y[6]) / 2

    time_den_y = (line_y[0] + line_y[2]) / 2

    # 提取拍号变化点（可以从 measures 或 time_events 获取）

    # 这里简单从整个 score 的拍号事件处理，但为避免重复绘制，只在高音谱画拍号

    # 这里的for循环有问题，循环了两次，二次绘制拍号的位置不对

    if config.name == "高音":

        time_events = get_time_sorted_events(score, music21.meter.TimeSignature)

        for ts in time_events:

            x = start_x  # + ts.offset * PIXELS_PER_BEAT

            draw.text(

                (x - 20, time_num_y - 10), str(ts.numerator), fill="black", font=font
            )

            draw.text(

                (x - 20, time_den_y - 10), str(ts.denominator), fill="black", font=font
            )


    # 画调号标记（只在调性变化处上方标注）

    # 取 key_timeline 去重

    prev_key = None

    for offset, tonic_name, mode in key_timeline:

        if (tonic_name, mode) != prev_key:

            label = f"Key: {tonic_name}" + ("m" if mode == "minor" else "")

            x = start_x + offset * PIXELS_PER_BEAT

            draw.text((x - 30, line_y[6] - 18), label, fill="darkblue", font=font)

            prev_key = (tonic_name, mode)


    # 画小节线（每个谱表独立）

    for m in 当前谱表的小节:

        x = start_x + m.offset * PIXELS_PER_BEAT

        top_y = line_y[6]# - 5

        bottom_y = line_y[0] #+ 5

        draw.line((x, top_y, x, bottom_y), fill="black", width=1)

        #print("小节线:", m.offset, x)


    # 处理音符/休止符

    for el in notes_and_rests:

        offset = el.offset

        x = start_x + offset * PIXELS_PER_BEAT


        if el.isRest:

            duration, img, bearing_y = get_rest_shape(el.quarterLength)

            line3_y = line_y[2]  # 第三条线

            if duration == "full":

                y = line3_y - LINE_SPACING

            elif duration == "half":

                y = line3_y + LINE_SPACING

            else:

                y = line3_y

            pasete_y = y - bearing_y
            # 【修改点】：如果 img 是 RGBA 模式，直接 paste，不需要 mask 参数
            # 确保 img 是 RGBA 模式
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            canvas.paste(img, (int(x), int(pasete_y)), img)
            #draw.text((x - 4, y - 2), symbol, fill="black", font=font)

            continue

        

        elif el.isNote:

            midi = el.pitch.midi

            line_offset = get_line_offset_from_midi_treble(midi, base_midi)


            # 计算符头 Y

            note_y = staff_y - line_offset * LINE_SPACING


            # 绘制加线

            if line_offset < 0 or line_offset > 6:

                draw.line(

                    (x - NOTE_HEAD_R - 3, note_y, x + NOTE_HEAD_R + 3, note_y),

                    fill="black",

                    width=1,
                )

            # -------- 符头 --------

            # draw.ellipse(

            #     [

            #         x - NOTE_HEAD_R,

            #         note_y - NOTE_HEAD_R,

            #         x + NOTE_HEAD_R,

            #         note_y + NOTE_HEAD_R,

            #     ],

            #     fill="black",

            # )

            draw.circle([x,note_y], NOTE_HEAD_R, fill="black")

            draw.text((x-NOTE_HEAD_R,note_y),str(el.pitch),fill="black",font=font)


            # -------- 临时变音记号 --------

            acc = el.pitch.accidental

            if acc is not None and acc.alter != 0:

                symbol = "♯" if acc.alter == 1 else "♭" if acc.alter == -1 else ""

                if symbol:

                    draw.text(

                        (x + NOTE_HEAD_R + 2, note_y - NOTE_HEAD_R),

                        symbol,
                        fill="red",
                        font=font,
                    )

            # 还原记号（显式 natural）

            elif acc is not None and acc.name == "natural":

                draw.text(

                    (x + NOTE_HEAD_R + 2, note_y - NOTE_HEAD_R), "♮", fill="red", font=font
                )
                pass

        elif el.isChord:

            pass



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


    # 获取小节 这里获取不到小节信息，需要查询API，或者使用Score.measures，但是这是总表的，不是每个声部的蒋小姐

    treble_measures = treble_part.getElementsByClass(music21.stream.Measure)

    bass_measures = bass_part.getElementsByClass(music21.stream.Measure)

    #print(treble_measures)
    

    # 计算最大时间

    all_notes = treble_notes + bass_notes

    max_time = max((el.offset + el.quarterLength for el in all_notes), default=4)

    canvas_width = int(max(1000, 80 + max_time * PIXELS_PER_BEAT + 100))

    canvas_height = int(BASS_TOP_Y + 7 * LINE_SPACING + 80)

    img = Image.new("RGB", (canvas_width, canvas_height), "white")

    draw = ImageDraw.Draw(img)

    

    # 标题

    title = score.metadata.title or "Untitled"

    draw.text(

        (0, 0),
        title,

        font=chineseFont,

        fill="black",
    )

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

        key_timeline.insert(0, (0.0, "C", "major"))


    # 绘制高音谱

    draw_staff(

        draw,

        TREBLE,

        STAFF_TOP_Y,

        treble_notes,

        key_timeline,

        80,

        canvas_width,

        chineseFont,

        music_font,

        treble_measures,

        None,

        img
    )


    # 绘制低音谱（如果有）

    if bass_part:

        #draw_staff(draw, BASS, BASS_TOP_Y, bass_notes, key_timeline,

        #           80, canvas_width, chineseFont, music_font, bass_measures, None)
        pass


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

        print("   (如需启用，在 Ubuntu/Debian 可执行: sudo apt-get install libraqm-dev)")

        LAYOUT_ENGINE = None

    chineseFont = ImageFont.truetype("assets/puhuiti.otf", 16)

    try:

        music_font = ImageFont.truetype("assets/bravura-bravura-1.392/redist/otf/BravuraText.otf", 20)

    except Exception as e:

        print("⚠️ 找不到字体文件，将使用默认字体。")

        # music_font = ImageFont.truetype("assets/NotoSansCJK-Regular.otf", 20)

    musicFontPath = "assets/bravura-bravura-1.392/redist/otf/BravuraText.otf"

    draw_seven_staff(score, args.output)