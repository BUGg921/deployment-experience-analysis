from pathlib import Path
from collections import Counter
import re,json,ast,hashlib
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'256卡19场景报告汇总_不含s021'
prior=json.loads((ROOT/'analysis/跨规模核对结果.json').read_text())
old={p['id']:p for p in prior['pairs']}
raw128={}
for line in (ROOT/'100场景_慢卡分布_熵_最优策略_部署经验汇总.md').read_text().splitlines():
 if line.startswith('| [s'):
  c=[v.strip() for v in line.strip('|').split('|')]; sid=re.search('s[0-9]{3}',c[0])[0]
  raw128[sid]={'nodes':list(map(int,c[3].split('-'))),'time':float(c[10].split()[0]),'strategy':c[8].strip('`')}
combined=(BASE/'256卡19场景最新报告合集_含部署经验.md').read_text()
scenes=[]
D_M='PP4_TP4_DP16_EP8_MB8';D_L='PP4_TP2_DP32_EP8_MB4';S='PP1_TP4_DP64_EP8_MB1'
for p in sorted(BASE.glob('s*_仿真报告.md')):
 sid=p.name[:4]; text=p.read_text()
 # Compare complete combined sections after the intentional heading level shift.
 segment=re.search(r'<a id="'+sid+r'"></a>\s*(.*?)(?=\n<a id="s|\Z)',combined,re.S)[1].strip()
 normalize=lambda s:re.sub(r'(?m)^#+ ', '',s).strip().removesuffix('---').strip()
 assert normalize(segment)==normalize(text),sid+' merged mismatch'
 nodes=ast.literal_eval(re.search(r'逐节点慢卡数：`([^`]+)`',text)[1])
 groups=ast.literal_eval(re.search(r'逐亲和组慢卡数：`([^`]+)`',text)[1])
 ranks=ast.literal_eval(re.search(r'慢卡 rank：`([^`]+)`',text)[1])
 slow=int(re.search(r'慢卡：(\d+)/256',text)[1])
 assert len(nodes)==16 and len(groups)==8 and all(0<=v<=16 for v in nodes) and all(0<=v<=32 for v in groups)
 assert len(ranks)==len(set(ranks))==slow==sum(nodes)==sum(groups)
 assert all(0<=r<256 for r in ranks)
 assert [sum(r//16==i for r in ranks) for i in range(16)]==nodes
 assert [sum(nodes[i:i+2]) for i in range(0,16,2)]==groups
 feats=[slow/256,sum(v>0 for v in nodes)/16,sum(v>0 for v in groups)/8,max(nodes)/16,max(abs(nodes[i]-nodes[i+1]) for i in range(0,16,2))/16,sum(abs(x-y) for i,x in enumerate(groups) for y in groups[i+1:])/32/28]
 summary=text.split('## 1. 结果摘要')[1].split('## 2. 场景配置')[0]
 metrics={c[0]:c[1] for line in summary.splitlines() if line.startswith('|') and len(c:=[v.strip() for v in line.strip('|').split('|')])==2}
 table=text.split('## 5. 仿真排名前十的部署策略')[1].split('## 6.')[0]
 candidates=[]
 for line in table.splitlines():
  if not re.match(r'\| \d+ \|',line): continue
  c=[v.strip() for v in line.strip('|').split('|')]
  rank=int(c[0]);name=c[1].strip('`');pp,tp,dp,mb,ep=map(int,c[2:7]);tm=float(c[7]);mem=float(c[9])
  assert pp*tp*dp==256 and 44%pp==0 and dp%ep==0 and 192%ep==0 and 128%(dp*mb)==0 and 192/ep<=24 and mem<=57.6
  assert name==f'PP{pp}_TP{tp}_DP{dp}_EP{ep}_MB{mb}'
  assert abs((tm/float(metrics['仿真最优耗时'].split()[0])-1)*100-float(c[8].strip('%')))<.006
  candidates.append({'rank':rank,'strategy':name,'time':tm,'memory_gib_reported':mem})
 assert len(candidates)==10 and [x['rank'] for x in candidates]==list(range(1,11))
 assert [x['time'] for x in candidates]==sorted(x['time'] for x in candidates)
 assert metrics['仿真最优']==metrics['评分摘要 top1']==candidates[0]['strategy']
 assert float(metrics['仿真最优耗时'].split()[0])==candidates[0]['time']
 times={c['strategy']:c['time'] for c in candidates};best=candidates[0]['time']
 score=re.search(r'def score\(ctx\):\n(.*?)\n```',text,re.S)[0].removesuffix('\n```')
 fields=sorted(set(re.findall(r'ctx\.(\w+)',score)))
 scenes.append({'id':sid,'source':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'batch':'2026-09-25' if sid in ['s009','s010','s049'] else '2026-09-22','nodes':nodes,'groups':groups,'slow_ranks':ranks,'features':feats,'nodes_repeat128':nodes==raw128[sid]['nodes']*2,'rank_half_repeats':sorted(r for r in ranks if r<128)==sorted(r-128 for r in ranks if r>=128),'metrics':metrics,'candidates':candidates,'score_fields':fields,'raw_experience':text.split('**部署经验：**')[1].split('## 1.')[0].strip(),'representative_times':{key:times.get(val) for key,val in [('D-M',D_M),('D-L',D_L),('S',S)]},'representative_regret_pct':{key:None if val not in times else (times[val]/best-1)*100 for key,val in [('D-M',D_M),('D-L',D_L),('S',S)]},'time128':raw128[sid]['time'],'ratio128to256':raw128[sid]['time']/best})
assert len(scenes)==19
result={'count':19,'combined_matches_individual':True,'all_nodes_repeat128':all(s['nodes_repeat128'] for s in scenes),'all_rank_half_repeats':all(s['rank_half_repeats'] for s in scenes),'representative_missing':{s['id']:[k for k,v in s['representative_times'].items() if v is None] for s in scenes},'strategy_counts':dict(Counter(s['metrics']['仿真最优'] for s in scenes)),'scenes':scenes}
(ROOT/'analysis/256原始报告核验.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='scenes'},ensure_ascii=False,indent=2))
for s in scenes: print(s['id'],s['representative_times'],{k:None if v is None else round(v,3) for k,v in s['representative_regret_pct'].items()},'128/256=',round(s['ratio128to256'],4))
