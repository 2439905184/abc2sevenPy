# 把abc、musicXML谱转换成七线谱的工具
自然音阶do re me fa so la si

## 开发
```
pip install music21
pip install pillow
```
## music21支持的转换器
```
<class 'music21.converter.subConverters.ConverterABC'>
<class 'music21.converter.subConverters.ConverterBraille'>
<class 'music21.converter.subConverters.ConverterCapella'>
<class 'music21.converter.subConverters.ConverterClercqTemperley'>
<class 'music21.converter.subConverters.ConverterHumdrum'>
<class 'music21.converter.subConverters.ConverterIPython'>
<class 'music21.converter.subConverters.ConverterLilypond'>
<class 'music21.converter.subConverters.ConverterMEI'>
<class 'music21.converter.subConverters.ConverterMidi'>
<class 'music21.converter.subConverters.ConverterMuseData'>
<class 'music21.converter.subConverters.ConverterMusicXML'>
<class 'music21.converter.subConverters.ConverterNoteworthy'>
<class 'music21.converter.subConverters.ConverterNoteworthyBinary'>
<class 'music21.converter.subConverters.ConverterRomanText'>
<class 'music21.converter.subConverters.ConverterScala'>
<class 'music21.converter.subConverters.ConverterText'>
<class 'music21.converter.subConverters.ConverterTextLine'>
<class 'music21.converter.subConverters.ConverterTinyNotation'>
<class 'music21.converter.subConverters.ConverterVexflow'>
<class 'music21.converter.subConverters.ConverterVolpiano'>
```
目前仅实现了`music21.converter.subConverters.ConverterABC`和`music21.converter.subConverters.ConverterMusicXML`的解析

## 使用与找谱子
1. 找abc谱子或者下musescore的谱子，转换成musicXML后可以被该程序读取就可以导出7线谱图片了

## 设计哲学
[七线谱定义和介绍v4版](%E4%B8%83%E7%BA%BF%E8%B0%B1%E5%AE%9A%E4%B9%89%E5%92%8C%E4%BB%8B%E7%BB%8Dv4%E7%89%88.txt)