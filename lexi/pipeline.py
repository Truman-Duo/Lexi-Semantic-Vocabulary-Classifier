import json
import sys
import os
from collections import defaultdict
from typing import Dict, List, Optional, Callable

from .cleaner import clean_text_stream
from .lemmatizer import lemmatize_words
from .classifier import Classifier
from .sorter import sort_by_frequency, zipf_to_cefr, get_zipf
from .models import WordInfo, ClassificationResult, CategoryMap


def run_pipeline(
    input_file: str,
    categories_json: str = "data/categories.json",
    stopwords_txt: str = "data/stopwords.txt",
    output_md: str = "output.md",
    output_json: str = "output.json",
    output_csv: Optional[str] = None,
    output_html: Optional[str] = None,
    output_anki: Optional[str] = None,
    overrides_json: Optional[str] = None,
    progress_callback: Optional[Callable] = None,
    status_callback: Optional[Callable] = None,
):
    _status = status_callback or (lambda msg: print(msg))
    _progress = progress_callback or (lambda pct: None)

    # Step 1
    _status("Step 1: 流式清洗文本...")
    raw_words = list(clean_text_stream(input_file))
    _status(f"  提取原始单词数: {len(raw_words)}")
    _progress(0.15)

    # Step 2
    _status("Step 2: 词形还原...")
    lemmatized = lemmatize_words(raw_words)
    _status(f"  还原后唯一词数: {len(lemmatized)}")
    _progress(0.25)

    # Step 3
    _status("Step 3: 加载分类器...")
    classifier = Classifier(categories_json, stopwords_txt, overrides_json)
    _progress(0.30)

    # Step 4
    _status("Step 4: 分类...")
    word_infos: Dict[str, WordInfo] = {}
    total = len(lemmatized)
    for i, word in enumerate(lemmatized):
        categories = classifier.classify(word)
        if categories:
            zipf = get_zipf(word)
            word_infos[word] = WordInfo(
                word=word,
                classifications=categories,
                zipf_frequency=zipf,
                cefr_level=zipf_to_cefr(zipf),
            )
        if i % 500 == 0 and total > 1000:
            _progress(0.30 + 0.35 * (i / total))
    _progress(0.65)

    # Build category map
    classified = _build_category_map(word_infos)

    # Step 5
    _status("Step 5: 词频排序...")
    for main_cat in list(classified.keys()):
        for sub_cat in list(classified[main_cat].keys()):
            word_list = classified[main_cat][sub_cat]
            word_list.sort(key=lambda wi: wi.zipf_frequency, reverse=True)
            if not word_list:
                del classified[main_cat][sub_cat]
        if not classified[main_cat]:
            del classified[main_cat]
    _progress(0.80)

    # Step 6
    _status("Step 6: 生成输出文件...")
    if output_md:
        _generate_markdown(classified, output_md)
    if output_json:
        _generate_json(classified, output_json, word_infos)

    if output_csv:
        _generate_csv(classified, word_infos, output_csv)
    if output_html:
        _generate_html(classified, word_infos, output_html)
    if output_anki:
        _generate_anki(classified, word_infos, output_anki)

    _progress(1.0)
    _status(f"完成！Markdown: {output_md}")


def _build_category_map(word_infos: Dict[str, WordInfo]) -> CategoryMap:
    classified: CategoryMap = defaultdict(lambda: defaultdict(list))
    for word, info in word_infos.items():
        for cl in info.classifications:
            classified[cl.main_category][cl.sub_category].append(info)
    return classified


def _generate_markdown(classified: CategoryMap, output_md: str):
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write("# 词汇分类笔记\n\n")
        for main_cat, sub_cats in classified.items():
            f.write(f"# {main_cat}\n\n")
            for sub_cat, words in sub_cats.items():
                f.write(f"## {sub_cat}\n")
                for idx, winfo in enumerate(words, 1):
                    cefr = f" [{winfo.cefr_level}]" if winfo.cefr_level else ""
                    f.write(f"{idx}. {winfo.word}{cefr}\n")
                f.write("\n")

        # Summary
        all_words = list(set(wi.word for sub in classified.values()
                            for words in sub.values() for wi in words))
        f.write("---\n## 统计摘要\n\n")
        f.write(f"- **单词总数**: {len(all_words)}\n")
        f.write("- **分类方法分布**:\n")
        source_counts = defaultdict(int)
        seen_src = set()
        for words in (wl for sub in classified.values()
                     for wl in sub.values()):
            for wi in words:
                for cl in wi.classifications:
                    key = (wi.word, cl.source)
                    if key not in seen_src:
                        seen_src.add(key)
                        source_counts[cl.source] += 1
        total_cls = sum(source_counts.values()) or 1
        for src, cnt in sorted(source_counts.items(), key=lambda x: -x[1]):
            f.write(f"  - {src}: {cnt} ({100*cnt/total_cls:.1f}%)\n")
        f.write("\n")
        for main_cat, sub_cats in classified.items():
            cat_total = sum(len(words) for words in sub_cats.values())
            all_total = sum(len(words) for sub in classified.values()
                          for words in sub.values()) or 1
            f.write(f"- **{main_cat}**: {cat_total} 词 ({100*cat_total/all_total:.1f}%)\n")


def _generate_json(classified: CategoryMap, output_json: str,
                   word_infos: Dict[str, WordInfo]):
    all_unique_words = set()
    for sub_cats in classified.values():
        for words in sub_cats.values():
            all_unique_words.update(wi.word for wi in words)

    out = {
        "total_words": len(all_unique_words),
        "categories": {
            main: {
                sub: [
                    {
                        "word": wi.word,
                        "zipf": round(wi.zipf_frequency, 2),
                        "cefr": wi.cefr_level,
                        "confidence": next(
                            (c.confidence for c in wi.classifications
                             if c.main_category == main and c.sub_category == sub),
                            1.0
                        ),
                        "source": next(
                            (c.source for c in wi.classifications
                             if c.main_category == main and c.sub_category == sub),
                            "unknown"
                        ),
                    }
                    for wi in words
                ]
                for sub, words in sub_cats.items()
            }
            for main, sub_cats in classified.items()
        }
    }
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


def _generate_csv(classified: CategoryMap, word_infos: Dict[str, WordInfo],
                  output_csv: str):
    import csv
    rows = []
    for main_cat, sub_cats in classified.items():
        for sub_cat, words in sub_cats.items():
            for wi in words:
                cl = next((c for c in wi.classifications
                          if c.main_category == main_cat
                          and c.sub_category == sub_cat), None)
                rows.append({
                    "word": wi.word,
                    "main_category": main_cat,
                    "sub_category": sub_cat,
                    "zipf_frequency": round(wi.zipf_frequency, 2),
                    "cefr_level": wi.cefr_level,
                    "confidence": cl.confidence if cl else "",
                    "source": cl.source if cl else "",
                })

    seen = set()
    unique_rows = []
    for r in rows:
        key = (r["word"], r["main_category"], r["sub_category"])
        if key not in seen:
            seen.add(key)
            unique_rows.append(r)

    if not unique_rows:
        return

    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "word", "main_category", "sub_category",
            "zipf_frequency", "cefr_level", "confidence", "source"])
        writer.writeheader()
        writer.writerows(unique_rows)


def _generate_html(classified: CategoryMap, word_infos: Dict[str, WordInfo],
                   output_html: str):
    cats_data = {}
    for main_cat, sub_cats in classified.items():
        cats_data[main_cat] = {}
        for sub_cat, words in sub_cats.items():
            cats_data[main_cat][sub_cat] = [
                {
                    "word": wi.word,
                    "zipf": round(wi.zipf_frequency, 2),
                    "cefr": wi.cefr_level,
                    "sources": list(set(
                        c.source for c in wi.classifications
                        if c.main_category == main_cat
                        and c.sub_category == sub_cat
                    )),
                }
                for wi in words
            ]

    import json as _json
    json_str = _json.dumps(cats_data, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lexi 词汇分类浏览器</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system,'Segoe UI',sans-serif; background:#f5f5f5; color:#333; }}
  .header {{ background:#2c3e50; color:#fff; padding:20px; position:sticky; top:0; z-index:100; }}
  .header h1 {{ font-size:20px; }}
  .controls {{ display:flex; gap:12px; margin-top:12px; flex-wrap:wrap; }}
  .controls input,.controls select {{ padding:6px 10px; border:1px solid #ccc; border-radius:4px; font-size:14px; }}
  .controls input {{ flex:1; min-width:150px; }}
  .container {{ display:flex; max-width:1200px; margin:0 auto; padding:16px; gap:16px; }}
  .sidebar {{ width:260px; flex-shrink:0; }}
  .cat-btn {{ display:block; width:100%; text-align:left; padding:10px 14px; border:none; background:#fff; border-radius:6px; margin-bottom:4px; cursor:pointer; font-size:14px; box-shadow:0 1px 3px rgba(0,0,0,0.08); }}
  .cat-btn:hover {{ background:#e8f4f8; }}
  .cat-btn.active {{ background:#3498db; color:#fff; }}
  .cat-btn .badge {{ float:right; color:#999; font-size:12px; }}
  .cat-btn.active .badge {{ color:#ddd; }}
  .sub-btn {{ display:block; width:100%; text-align:left; padding:6px 14px 6px 28px; border:none; background:none; cursor:pointer; font-size:13px; color:#555; }}
  .sub-btn:hover {{ color:#2980b9; }}
  .sub-btn.active {{ color:#e74c3c; font-weight:bold; }}
  .panel {{ flex:1; background:#fff; border-radius:8px; padding:20px; box-shadow:0 1px 4px rgba(0,0,0,0.08); }}
  .panel h2 {{ font-size:18px; margin-bottom:16px; color:#2c3e50; }}
  .list {{ columns:3 200px; column-gap:24px; }}
  .item {{ break-inside:avoid; padding:4px 0; font-size:14px; border-bottom:1px solid #f0f0f0; }}
  .item .w {{ font-weight:500; }}
  .item .m {{ color:#999; font-size:11px; margin-left:6px; }}
  .tag {{ display:inline-block; font-size:10px; padding:1px 5px; border-radius:3px; margin-left:4px; }}
  .a1 {{ background:#27ae60; color:#fff; }} .a2 {{ background:#2ecc71; color:#fff; }}
  .b1 {{ background:#f39c12; color:#fff; }} .b2 {{ background:#e67e22; color:#fff; }}
  .c1 {{ background:#e74c3c; color:#fff; }} .c2 {{ background:#c0392b; color:#fff; }}
  .empty {{ color:#999; text-align:center; padding:40px; }}
  @media(max-width:700px){{ .container{{flex-direction:column;}} .sidebar{{width:100%;}} .list{{columns:2 150px;}} }}
</style>
</head>
<body>
<div class="header">
  <h1>Lexi 词汇分类浏览器</h1>
  <div class="controls">
    <input type="text" id="q" placeholder="搜索单词..." oninput="render()">
    <select id="srt" onchange="render()">
      <option value="zipf">按词频</option>
      <option value="alpha">按字母</option>
    </select>
    <select id="cefr" onchange="render()">
      <option value="">全部等级</option>
      <option value="A1">A1</option><option value="A2">A2</option>
      <option value="B1">B1</option><option value="B2">B2</option>
      <option value="C1">C1</option><option value="C2">C2</option>
    </select>
    <span id="cnt" style="color:#ccc;font-size:13px;line-height:32px;"></span>
  </div>
</div>
<div class="container">
  <div class="sidebar" id="sb"></div>
  <div class="panel" id="panel"><div class="empty">选择一个分类</div></div>
</div>
<script>
const D = {json_str};
const L = {{'A1':'a1','A2':'a2','B1':'b1','B2':'b2','C1':'c1','C2':'c2'}};
let m=null, s=null;

function sb() {{
  const e=document.getElementById('sb'); e.innerHTML='';
  Object.keys(D).forEach(k => {{
    const o=D[k]; let t=0; Object.values(o).forEach(a=>t+=a.length);
    const b=document.createElement('button');
    b.className='cat-btn'+(k==m?' active':'');
    b.innerHTML=k+' <span class="badge">'+t+'</span>';
    b.onclick=()=>{{ if(m==k){{m=null;s=null;}}else{{m=k;s=Object.keys(D[k])[0]||null;}}sb();render();}};
    e.appendChild(b);
    if(k==m) Object.keys(o).forEach(x=>{{
      const z=document.createElement('button');
      z.className='sub-btn'+(x==s?' active':'');
      z.textContent=x+' ('+o[x].length+')';
      z.onclick=()=>{{s=x;sb();render();}};
      e.appendChild(z);
    }});
  }});
}}

function render() {{
  const p=document.getElementById('panel');
  if(!m||!s){{p.innerHTML='<div class="empty">选择一个分类</div>';document.getElementById('cnt').textContent='';return;}}
  let w=(D[m]&&D[m][s])||[];
  const q=document.getElementById('q').value.toLowerCase().trim();
  const c=document.getElementById('cefr').value;
  if(q) w=w.filter(x=>x.word.includes(q));
  if(c) w=w.filter(x=>x.cefr===c);
  const o=document.getElementById('srt').value;
  if(o==='alpha') w=[...w].sort((a,b)=>a.word.localeCompare(b.word));
  document.getElementById('cnt').textContent=m+' › '+s+' — '+w.length+' 词';
  if(!w.length){{p.innerHTML='<div class="empty">无匹配</div>';return;}}
  let h='<h2>'+m+' › '+s+' <span style="font-size:13px;color:#999;">('+w.length+' 词)</span></h2><div class="list">';
  w.forEach(x=>{{
    const t=x.cefr?'<span class="tag '+L[x.cefr]+'">'+x.cefr+'</span>':'';
    const r='<span class="m">['+(x.sources?x.sources.join(','):'')+']</span>';
    h+='<div class="item"><span class="w">'+x.word+'</span>'+t+r+'</div>';
  }});
  h+='</div>'; p.innerHTML=h;
}}

sb();
if(Object.keys(D).length){{m=Object.keys(D)[0];s=Object.keys(D[m])[0]||null;sb();render();}}
</script>
</body>
</html>"""
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html)


def _generate_anki(classified: CategoryMap, word_infos: Dict[str, WordInfo],
                   output_anki: str):
    try:
        import genanki
    except ImportError:
        print("  [警告] 需要安装 genanki 来导出 Anki 牌组: pip install genanki",
              file=sys.stderr)
        return

    model = genanki.Model(
        1607392319,
        'Lexi Word Model',
        fields=[
            {'name': 'Word'},
            {'name': 'Category'},
            {'name': 'SubCategory'},
            {'name': 'CEFR'},
            {'name': 'ZipfFrequency'},
        ],
        templates=[{
            'name': 'Lexi Card',
            'qfmt': '{{Word}}',
            'afmt': (
                '{{FrontSide}}<hr id="answer">'
                '<b>分类:</b> {{Category}} › {{SubCategory}}<br>'
                '<b>CEFR:</b> {{CEFR}}<br>'
                '<b>词频:</b> {{ZipfFrequency}}'
            ),
        }])

    words_added = set()
    deck = genanki.Deck(2059400110, 'Lexi Vocabulary')

    for main_cat, sub_cats in classified.items():
        for sub_cat, words in sub_cats.items():
            for wi in words:
                if wi.word in words_added:
                    continue
                words_added.add(wi.word)
                note = genanki.Note(
                    model=model,
                    fields=[
                        wi.word,
                        main_cat,
                        sub_cat,
                        wi.cefr_level,
                        str(round(wi.zipf_frequency, 2)),
                    ])
                deck.add_note(note)

    genanki.Package(deck).write_to_file(output_anki)
    print(f"  Anki 牌组已导出: {output_anki} ({len(words_added)} 张卡片)")
