"""Mevcut rapordaki biçimleri kopyalayarak yeni bölüm ekleme yardımcıları."""
import copy, docx
from docx.shared import Cm
class Writer:
    def __init__(s, doc, anchor):
        s.d = doc; P = doc.paragraphs; s.anchor = anchor
        find = lambda style, start=0: next(p for p in P[start:] if p.style is not None and p.style.name == style)
        s.T = {"h1": find("Heading 1"), "h2": find("Heading 2"), "body": P[188], "bullet": P[200], "num": P[211], "cap": P[194], "img": P[193]}
        s.tbl = doc.tables[-4]
    def _clone(s, key, text):
        el = copy.deepcopy(s.T[key]._p); s.anchor._p.addprevious(el)
        p = docx.text.paragraph.Paragraph(el, s.anchor._parent)
        runs = p.runs
        for r in runs[1:]: r._r.getparent().remove(r._r)
        for h in el.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hyperlink"): el.remove(h)
        if runs: runs[0].text = text; runs[0].bold = None if key not in ("h1", "h2") else runs[0].bold
        else: p.add_run(text)
        return p
    def h1(s, t): return s._clone("h1", t)
    def h2(s, t): return s._clone("h2", t)
    def p(s, t): return s._clone("body", t)
    def bullet(s, t): return s._clone("bullet", t)
    def num(s, t): return s._clone("num", t)
    def cap(s, t): return s._clone("cap", t)
    def bold_lead(s, lead, rest, key="bullet"):
        p = s._clone(key, lead); p.runs[0].bold = True; r = p.add_run(rest); r.bold = False; return p
    def img(s, path, width_cm=16):
        p = s._clone("img", "")
        for r in list(p.runs): r._r.getparent().remove(r._r)
        for el in p._p.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing"): el.getparent().remove(el)
        p.add_run().add_picture(path, width=Cm(width_cm)); return p
    def table(s, rows, widths=None):
        t = copy.deepcopy(s.tbl._tbl); s.anchor._p.addprevious(t)
        T = docx.table.Table(t, s.anchor._parent)
        hdr, body = copy.deepcopy(T.rows[0]._tr), copy.deepcopy(T.rows[1]._tr)
        for r in list(T.rows): t.remove(r._tr)
        ncol = len(rows[0]); W = widths or [9638 // ncol] * ncol
        grid = t.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblGrid")
        for g in list(grid): grid.remove(g)
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        for w in W:
            g = OxmlElement("w:gridCol"); g.set(qn("w:w"), str(w)); grid.append(g)
        for i, row in enumerate(rows):
            tr = copy.deepcopy(hdr if i == 0 else body); t.append(tr)
            tcs = tr.findall(qn("w:tc"))
            while len(tcs) < ncol: tr.append(copy.deepcopy(tcs[-1])); tcs = tr.findall(qn("w:tc"))
            for extra in tcs[ncol:]: tr.remove(extra)
            tcs = tr.findall(qn("w:tc"))
            for j, (tc, val) in enumerate(zip(tcs, row)):
                tc.find(qn("w:tcPr")).find(qn("w:tcW")).set(qn("w:w"), str(W[j]))
                ps = tc.findall(qn("w:p"))
                for extra in ps[1:]: tc.remove(extra)
                cp = docx.text.paragraph.Paragraph(ps[0], None)
                for r in cp.runs[1:]: r._r.getparent().remove(r._r)
                if cp.runs: cp.runs[0].text = str(val)
                else: cp.add_run(str(val))
        return T
