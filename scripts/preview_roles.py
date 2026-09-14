"""生成 12 类离线审阅页；仅展示目录与写作示例，不伪造测评分数。"""
from pathlib import Path
import base64
import html
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.role_match import ROLES


def build_preview(output: Path) -> Path:
    editorial = (ROOT / 'references/role-editorial.md').read_text()
    rows = [line.split('|')[1:-1] for line in editorial.splitlines() if line.startswith('| ')] [1:]
    notes = {row[0].strip(): [x.strip() for x in row[1:]] for row in rows}
    cards = []
    for role in ROLES:
        asset = ROOT / 'assets/characters' / role['asset']
        mime = 'image/png' if asset.suffix == '.png' else 'image/webp'
        uri = f'data:{mime};base64,' + base64.b64encode(asset.read_bytes()).decode()
        quote, action, audit = notes[role['name']]
        cards.append(f'''<article><header><span>{role['order']:02d}</span><b>{html.escape(role['name'])}</b></header>
        <p class="definition">{html.escape(role['definition'])}</p><img src="{uri}" alt="{html.escape(role['name'])}">
        <blockquote>{html.escape(quote)}</blockquote><p><strong>增强价值</strong><br>{html.escape(action)}</p>
        <details><summary>分类边界与形象核对</summary><p>{html.escape(role['description'])}</p><p>{html.escape(audit)}</p></details></article>''')
    logo = base64.b64encode((ROOT/'assets/brand/svg/MBAI_wordmark.svg').read_bytes()).decode()
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MBAI · 12 类完整预览</title><style>
    *{box-sizing:border-box}body{margin:0;background:#f4f4f0;color:#0d0d0d;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1260px;margin:auto;padding:24px}nav{background:#0d0d0d;color:#ebfb3b;padding:18px;display:flex;align-items:center;justify-content:space-between;gap:20px}nav img{width:140px}h1{font-size:42px;margin:30px 0 12px}main>p{max-width:820px;line-height:1.8}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px;margin-top:30px}article{background:#ebfb3b;border:3px solid #0d0d0d;padding:20px;box-shadow:6px 6px #0d0d0d}header{display:flex;align-items:center;gap:12px}header span{background:#ff4a00;padding:4px 7px;font-weight:900}header b{font-size:25px}.definition{min-height:52px;font-weight:700}article img{width:100%;aspect-ratio:1;object-fit:contain;background:white;border:2px solid black;border-radius:16px}blockquote{margin:18px 0;background:#0d0d0d;color:#ebfb3b;border-left:7px solid #ff4a00;padding:16px;font-size:22px;font-weight:800;min-height:110px}p{line-height:1.65}summary{cursor:pointer;font-weight:700}details{border-top:2px solid black;padding-top:12px}footer{margin-top:36px;background:#0d0d0d;color:#ebfb3b;padding:20px}footer b{background:#ff4a00;color:black;padding:4px 8px}@media(max-width:950px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){.grid{grid-template-columns:1fr}main{padding:16px}h1{font-size:32px}nav{flex-wrap:wrap}}
    </style><main><nav><img src="data:image/svg+xml;base64,LOGO" alt="MBAI"><span>我，在 AI 之上</span></nav><h1>十二种职场本事，你是哪一种？</h1><p>完整名称、形象与表达预览。下列句子是写作示例，实际测评必须依据你的任务重写。分类不绑定分数，也不表示稀有程度。</p><section class="grid">CARDS</section><footer>搜 <b>欧八同学</b> 生成自己的职业 AI 体检报告</footer></main><script>/* 预览页与报告共用资源就绪探针；此页没有测评 Canvas。 */ Promise.all([...document.images].map(image=>image.decode())).then(()=>{window.__CARD_READY__=true;}).catch(error=>{window.__CARD_ERROR__=String(error);});</script></html>'''.replace('LOGO',logo).replace('CARDS',''.join(cards))
    output.mkdir(parents=True,exist_ok=True)
    target=output/'index.html';target.write_text(page)
    return target

if __name__ == '__main__':
    print(build_preview(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'examples/output/roles-review'))
