from pathlib import Path
import re, json
from collections import Counter
ROOT=Path(__file__).resolve().parent.parent
raw=(ROOT/'100场景_慢卡分布_熵_最优策略_部署经验汇总.md').read_text()
r128=(ROOT/'128GPU_100场景_部署经验与场景关系分析报告.md').read_text()
r256=(ROOT/'256GPU_19场景_部署经验与场景关系分析报告.md').read_text()
mapping={}
for motif, members in re.findall(r'### ([AB][123])（\d+ 个）\s*\n\s*(s\d{3}(?:, s\d{3})*)',r128):
    for sid in members.split(', '): mapping[sid]=motif
rows={}; anomalies=[]
for line in raw.splitlines():
    if not line.startswith('| [s'): continue
    c=[v.strip() for v in line.strip('|').split('|')]
    sid=re.search(r's\d{3}',c[0])[0]; n=list(map(int,c[3].split('-'))); a=list(map(int,c[4].split('-')))
    slow=int(c[2].split('/')[0])
    if sum(n)!=slow or sum(a)!=slow or [sum(n[i:i+2]) for i in range(0,8,2)]!=a: anomalies.append(sid)
    aff=sum(abs(x-y) for i,x in enumerate(a) for y in a[i+1:])/32/6
    rows[sid]={'id':sid,'motif128':mapping.get(sid,'异常隔离'),'features128':[slow/128,sum(x>0 for x in n)/8,sum(x>0 for x in a)/4,max(n)/16,max(abs(n[i]-n[i+1]) for i in range(0,8,2))/16,aff], 'strategy128':c[8], 'formula128':c[11]}
pairs=[]
for line in r256.split('## 附录 A：')[1].splitlines():
    if not re.match(r'\| s\d{3} ',line): continue
    c=[v.strip() for v in line.strip('|').split('|')]; d=rows[c[0]].copy()
    d.update(family256=c[1],features256_reported=[float(c[2].strip('%'))/100]+[float(v) for v in c[3:]])
    # Source appendix is rounded: 0.01 percentage point for rho; 0.001 for other columns.
    d['first_five_match_rounding']=all(abs(x-y)<=tol+1e-10 for x,y,tol in zip(d['features128'][:5],d['features256_reported'][:5],[.000051,.000501,.000501,.000501,.000501]))
    d['aff_matches_replication_factor']=abs(d['features256_reported'][5]-d['features128'][5]*6/7)<=.000501
    pairs.append(d)
assert len(rows)==100 and len(pairs)==19 and len(mapping)==99 and not anomalies
result={'count128':len(rows),'count256':len(pairs),'count_valid_overlap':sum(p['motif128']!='异常隔离' for p in pairs),'transitions':dict(Counter(p['motif128'][0]+' → '+p['family256'] for p in pairs if p['motif128']!='异常隔离')),'first_five_matching':sum(p['first_five_match_rounding'] for p in pairs),'aff_factor_matching':sum(p['aff_matches_replication_factor'] for p in pairs),'pairs':pairs}
(ROOT/'analysis/跨规模核对结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
lines=['| 场景 | 128 卡模式 | 256 卡经验族 | 慢卡率（128 卡精确值） | 节点覆盖率 | 亲和组覆盖率 | 组内不均衡 | 128 卡组间不均衡 | 256 卡组间不均衡（报告值） | 对照结论 |','|---|---|---|---:|---:|---:|---:|---:|---:|---|']
for p in pairs:
    f=p['features128']; transition='异常隔离，暂不评价迁移' if p['motif128']=='异常隔离' else ('浅→深，重点复核' if p['motif128'].startswith('B') and p['family256']=='A' else ('深→深，低 TP 分支' if p['family256']=='B' else ('深→深，大 MB 分支' if p['family256']=='A' else '浅→浅')))
    lines.append(f"| {p['id']} | {p['motif128']} | {p['family256']} | {f[0]:.4%} | {f[1]:.4f} | {f[2]:.4f} | {f[4]:.4f} | {f[5]:.5f} | {p['features256_reported'][5]:.3f} | {transition} |")
(ROOT/'analysis/同编号19场景对照.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='pairs'},ensure_ascii=False,indent=2))
