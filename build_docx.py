# -*- coding: utf-8 -*-
"""Standalone .docx builder (stdlib only) for the chapter, formatted for
《电力系统自动化》-style manuscript: SimSun body 10.5pt, SimHei headings,
Times New Roman for Latin/numerals, numbered headings, equations, three-line tables.
"""
import zipfile, os

def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace('"', '&quot;'))

# ---- run / paragraph builders -------------------------------------------------
def run(text, *, bold=False, italic=False, sz=21, ea='宋体', ascii_='Times New Roman', color=None):
    """sz is in half-points (21 = 10.5pt)."""
    rpr = ['<w:rPr>']
    rpr.append(f'<w:rFonts w:ascii="{ascii_}" w:hAnsi="{ascii_}" w:eastAsia="{ea}" w:cs="{ascii_}"/>')
    if bold:
        rpr.append('<w:b/><w:bCs/>')
    if italic:
        rpr.append('<w:i/><w:iCs/>')
    if color:
        rpr.append(f'<w:color w:val="{color}"/>')
    rpr.append(f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>')
    rpr.append('</w:rPr>')
    return (f'<w:r>{"".join(rpr)}'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r>')

def para(runs_xml, *, align=None, indent_chars=0, line=360, before=0, after=0,
         tabs=None, keep=False):
    ppr = ['<w:pPr>']
    if keep:
        ppr.append('<w:keepNext/>')
    if tabs:
        ppr.append('<w:tabs>')
        for kind, pos in tabs:
            ppr.append(f'<w:tab w:val="{kind}" w:pos="{pos}"/>')
        ppr.append('</w:tabs>')
    if indent_chars:
        fl = int(indent_chars * 210)
        ppr.append(f'<w:ind w:firstLine="{fl}" w:firstLineChars="{indent_chars*100}"/>')
    ppr.append(f'<w:spacing w:line="{line}" w:lineRule="auto" w:before="{before}" w:after="{after}"/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    ppr.append('</w:pPr>')
    return f'<w:p>{"".join(ppr)}{runs_xml}</w:p>'

# Text-width tab stops (A4, 1440twip margins -> ~9026 twip text width)
CENTER_TAB = 4513
RIGHT_TAB = 9026

def P(text, indent=2):
    """Body paragraph, SimSun 10.5, first-line indent 2 chars."""
    return para(run(text), indent_chars=indent, align='both')

def TITLE(text):
    return para(run(text, bold=True, sz=36, ea='黑体', ascii_='SimHei'),
                align='center', after=120, line=300)

def AUTH(text):
    return para(run(text, sz=21, ea='宋体'), align='center', after=40, line=280)

def H1(num, text):
    r = run(num + ' ' + text, bold=True, sz=28, ea='黑体', ascii_='SimHei')
    return para(r, before=200, after=80, line=320, keep=True)

def H2(num, text):
    r = run(num + ' ' + text, bold=True, sz=24, ea='黑体', ascii_='SimHei')
    return para(r, before=140, after=60, line=300, keep=True)

def H3(num, text):
    r = run(num + ' ' + text, bold=True, sz=21, ea='黑体', ascii_='SimHei')
    return para(r, before=100, after=40, line=300, keep=True)

def EQ(eqtext, num):
    inner = '<w:r><w:tab/></w:r>' + run(eqtext, italic=False, sz=21) + \
            '<w:r><w:tab/></w:r>' + run('(' + num + ')', sz=21)
    return para(inner, tabs=[('center', CENTER_TAB), ('right', RIGHT_TAB)], line=320,
                before=40, after=40)

def CAP(text):
    return para(run(text, bold=True, sz=19, ea='黑体', ascii_='SimHei'),
                align='center', before=40, after=40, line=280)

def REFTITLE():
    return para(run('参 考 文 献', bold=True, sz=24, ea='黑体', ascii_='SimHei'),
                align='center', before=160, after=80, line=300)

def REF(text):
    return para(run(text, sz=18), indent_chars=0, align='both', line=280)

def three_line_table(headers, rows, widths):
    """widths in twips (sum ~ 9026)."""
    cols = ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    def cell(text, w, header=False, last_header=False):
        bottom = '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/>' if header else ''
        tcborders = f'<w:tcBorders>{bottom}</w:tcBorders>' if header else ''
        r = run(text, bold=header, sz=19, ea=('黑体' if header else '宋体'),
                ascii_=('SimHei' if header else 'Times New Roman'))
        ppr = ('<w:pPr><w:spacing w:line="260" w:lineRule="auto" w:before="20" w:after="20"/>'
               '<w:jc w:val="center"/></w:pPr>')
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{tcborders}'
                f'<w:vAlign w:val="center"/></w:tcPr><w:p>{ppr}{r}</w:p></w:tc>')
    out = ['<w:tbl>']
    out.append('<w:tblPr><w:tblW w:w="0" w:type="auto"/><w:jc w:val="center"/>'
               '<w:tblBorders>'
               '<w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
               '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
               '</w:tblBorders>'
               '<w:tblCellMar><w:left w:w="60" w:type="dxa"/><w:right w:w="60" w:type="dxa"/></w:tblCellMar>'
               '</w:tblPr>')
    out.append(f'<w:tblGrid>{cols}</w:tblGrid>')
    # header row
    hc = ''.join(cell(h, widths[i], header=True) for i, h in enumerate(headers))
    out.append(f'<w:tr>{hc}</w:tr>')
    for row in rows:
        rc = ''.join(cell(c, widths[i]) for i, c in enumerate(row))
        out.append(f'<w:tr>{rc}</w:tr>')
    out.append('</w:tbl>')
    # spacer paragraph after table
    out.append('<w:p><w:pPr><w:spacing w:line="120" w:lineRule="auto"/></w:pPr></w:p>')
    return ''.join(out)

# ---- assemble document body ---------------------------------------------------
def build(body_parts):
    body = ''.join(body_parts)
    sect = ('<w:sectPr>'
            '<w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
            'w:header="851" w:footer="992" w:gutter="0"/>'
            '<w:pgNumType w:fmt="decimal"/>'
            '</w:sectPr>')
    doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
           'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
           f'<w:body>{body}{sect}</w:body></w:document>')
    return doc

CONTENT_TYPES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
 '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
 '<Default Extension="xml" ContentType="application/xml"/>'
 '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
 '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
 '</Types>')

RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
 '</Relationships>')

DOC_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
 '</Relationships>')

STYLES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
 '<w:docDefaults><w:rPrDefault><w:rPr>'
 '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体" w:cs="Times New Roman"/>'
 '<w:sz w:val="21"/><w:szCs w:val="21"/><w:lang w:val="en-US" w:eastAsia="zh-CN"/>'
 '</w:rPr></w:rPrDefault></w:docDefaults>'
 '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/>'
 '<w:pPr><w:spacing w:line="360" w:lineRule="auto"/></w:pPr></w:style>'
 '</w:styles>')

def write_docx(path, parts):
    doc = build(parts)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', CONTENT_TYPES)
        z.writestr('_rels/.rels', RELS)
        z.writestr('word/_rels/document.xml.rels', DOC_RELS)
        z.writestr('word/styles.xml', STYLES)
        z.writestr('word/document.xml', doc)
    print('wrote', path, os.path.getsize(path), 'bytes')
