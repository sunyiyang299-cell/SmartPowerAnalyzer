"""Render the actual Markdown manual and real screenshots into a Chinese PDF."""
from html import escape
from pathlib import Path
import re
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, KeepTogether, LongTable, TableStyle


def render(source, target):
    source,target=Path(source).resolve(),Path(target).resolve()
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    body=ParagraphStyle('body',fontName='STSong-Light',fontSize=10.3,leading=17,spaceAfter=9,wordWrap='CJK')
    heading=ParagraphStyle('heading',parent=body,fontSize=15,leading=23,spaceBefore=16,spaceAfter=10,keepWithNext=True,textColor=colors.HexColor('#183153'))
    title=ParagraphStyle('title',parent=heading,fontSize=21,leading=31,spaceAfter=20)
    caption=ParagraphStyle('caption',parent=body,fontSize=9,leading=14,textColor=colors.HexColor('#53657e'))
    def para(text,style=body):return Paragraph(escape(text.replace('`','').replace('**','')),style)
    story=[];paragraph=[];table=[]
    def flush():
        if paragraph:story.append(para(' '.join(paragraph)));paragraph.clear()
        if table:
            result=LongTable([[para(value,caption) for value in row] for row in table],colWidths=[505/len(table[0])]*len(table[0]),repeatRows=1)
            result.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9f0fa')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#d4dfed')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            story.extend([result,Spacer(1,12)]);table.clear()
    for line in source.read_text(encoding='utf-8-sig').splitlines():
        match=re.match(r'!\[(.*?)\]\((.*?)\)',line)
        if match:
            flush();image=Image(str(source.parent/match.group(2)))
            scale=min(505/image.imageWidth,400/image.imageHeight)
            image.drawWidth=image.imageWidth*scale;image.drawHeight=image.imageHeight*scale
            story.extend([KeepTogether([image,Spacer(1,5),para(match.group(1)+'（真实运行截图，模拟数据，路径已遮蔽）',caption)]),Spacer(1,12)])
        elif line.startswith('# '):flush();story.append(para(line[2:],title));story.append(para('标准中文字体引用模式；接收方阅读器须支持中文。当前为审核候选材料。',caption))
        elif line.startswith('## '):flush();story.append(para(line[3:],heading))
        elif line.startswith('|'):
            if paragraph:flush()
            values=[value.strip() for value in line.strip('|').split('|')]
            if not all(re.fullmatch(r'[-: ]+',value) for value in values):table.append(values)
        elif not line.strip():flush()
        elif line.startswith('- '):flush();story.append(para('· '+line[2:]))
        else:paragraph.append(line.strip())
    flush()
    def page(canvas,document):
        canvas.saveState();canvas.setFont('STSong-Light',8);canvas.setFillColor(colors.HexColor('#53657e'))
        canvas.drawString(45,818,'智电析 · 用户操作手册 · 1.0.0 · 发行候选材料')
        canvas.drawRightString(A4[0]-45,28,f'第 {document.page} 页');canvas.restoreState()
    target.parent.mkdir(parents=True,exist_ok=True)
    doc=SimpleDocTemplate(str(target),pagesize=A4,leftMargin=45,rightMargin=45,topMargin=49,bottomMargin=45,title='智电析V1.0用户操作手册',author='SmartPowerAnalyzer documentation')
    doc.build(story,onFirstPage=page,onLaterPages=page)
    print(str(target))


if __name__=='__main__':render(sys.argv[1],sys.argv[2])
