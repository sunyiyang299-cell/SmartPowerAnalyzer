"""Export real application sources from an explicit committed Git snapshot."""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import subprocess
import sys


def export(commit, output):
    root=Path(__file__).resolve().parents[1]
    resolved=subprocess.check_output(['git','rev-parse',commit+'^{commit}'],cwd=root,text=True).strip()
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',resolved],cwd=root,text=True,encoding='utf-8').splitlines()
    names=[name for name in names if name=='main.py' or (name.startswith('smartpower/') and name.endswith('.py'))]
    assert names and 'main.py' in names
    directory=Path(output);directory.mkdir(parents=True,exist_ok=True)
    generated=datetime.now(timezone.utc).isoformat()
    excerpt=[f'软件：智电析电力系统运行数据分析与可视化软件 V1.0\n版本：1.0.0\n源码Git Commit：{resolved}\n材料生成UTC：{generated}\n仅为源程序交存候选汇编；生成日期不是软件完成/首次发表日期，不声明符合全部登记格式。\n仅包含项目main.py与smartpower/*.py，不含第三方库源码、字体或缓存。\n']
    manifest=['# V1.0 源程序材料来源清单\n',f'源码Git Commit：`{resolved}`。生成UTC：`{generated}`。\n',
              '以git show读取该真实提交中的原始内容，按路径汇编，保留全部上下文与空行；不虚构或重复代码凑页数。作者、权利人与完成/发表日期由申请人确认。本清单不代表登记审核结果。\n',
              '| 文件 | 原始行数 | SHA-256（提交中的原始字节） |\n|---|---:|---|']
    total=0
    for name in names:
        raw=subprocess.check_output(['git','show',resolved+':'+name],cwd=root)
        digest=hashlib.sha256(raw).hexdigest();text=raw.decode('utf-8-sig');lines=len(text.splitlines());total+=lines
        manifest.append(f'| {name} | {lines} | `{digest}` |')
        excerpt.append(f'\n===== 来源文件：{name}；原始行数：{lines}；SHA256：{digest} =====\n')
        excerpt.append(text)
        if not text.endswith('\n'):excerpt.append('\n')
    manifest.append(f'\n合计{len(names)}个项目Python源文件、{total}行（含原有空行）。未套用未经核对的固定页数/页行数。用户手册、设计和测试另见docs；构建/安装脚本不伪装为业务源程序。\n')
    (directory/'SOURCE_MANIFEST.md').write_text('\n'.join(manifest),encoding='utf-8',newline='\n')
    (directory/'SOURCE_EXCERPT_V1.0.txt').write_text(''.join(excerpt),encoding='utf-8',newline='\n')
    print(resolved,len(names),total)


if __name__=='__main__':export(sys.argv[1],sys.argv[2])
