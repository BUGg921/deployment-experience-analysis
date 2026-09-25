"""重建报告的离散可行域与评分；不运行 DAG 仿真。"""
from pathlib import Path
from types import SimpleNamespace
from itertools import product
import ast,re,json,hashlib
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'256卡19场景报告汇总_不含s021'
audit=json.loads((ROOT/'analysis/256原始报告核验.json').read_text())
manifest=json.loads((BASE/'来源清单.json').read_text())
assert all(hashlib.sha256((BASE/m['file']).read_bytes()).hexdigest()==m['sha256'] for m in manifest)
def memory(pp,tp,dp,ep,mb):
 dense=3746457600; expert=32463912960;b=128/(dp*mb)
 local=(dense+expert/ep)/(pp*tp)
 states=(dense/dp+expert/dp)/(pp*tp)*16
 activations=b*4096*2560*2*24*44/pp/tp*min(mb,pp)
 return (states+local*2+activations)/2**30+4

def scope(pp,tp,dp,axis):
 rank=lambda s,d,t:(s*dp+d)*tp+t
 groups=([[rank(s,d,t) for t in range(tp)] for s in range(pp) for d in range(dp)] if axis=='tp' else [[rank(s,d,t) for d in range(dp)] for s in range(pp) for t in range(tp)])
 def group_mean(g):
  if len(g)==1:return 0
  return sum(0 if x//16==y//16 else .5 if x//32==y//32 else 1 for x,y in zip(g,g[1:]+g[:1]))/len(g)
 return sum(map(group_mean,groups))/len(groups)
candidates={}
for pp,tp,ep,mb in product([1,2,4],[1,2,4,8,16,32],[1,2,4,8,16,32],[1,2,4,8,16,32]):
 if 256%(pp*tp):continue
 dp=256//pp//tp
 if 44%pp or dp%ep or 192%ep or 128%(dp*mb) or 192/ep>24:continue
 mem=memory(pp,tp,dp,ep,mb)
 if mem>57.6:continue
 name=f'PP{pp}_TP{tp}_DP{dp}_EP{ep}_MB{mb}'
 candidates[name]=SimpleNamespace(pp_degree=pp,tp_degree=tp,dp_degree=dp,expert_capacity_pressure=8/ep,microbatch_count=mb,microbatch_pp_ratio=mb/pp,tp_pp_ratio=tp/pp,tp_dp_ratio=tp/dp,pipeline_bubble=(pp-1)/(mb+pp-1),microbatch_pressure=1/(1+128/(dp*mb)),memory_pressure=mem/57.6,tp_scope_exposure=scope(pp,tp,dp,'tp'),dp_scope_exposure=scope(pp,tp,dp,'dp'))
assert len(candidates)==90,len(candidates)
results=[]
helpers={'hinge_above':lambda x,a:max(0,x-a),'hinge_below':lambda x,a:max(0,a-x),'distance_to':lambda x,a:abs(x-a)}
for scene in audit['scenes']:
 text=(ROOT/scene['source']).read_text()
 src=re.search(r'def score\(ctx\):\n(.*?)\n```',text,re.S)[0].removesuffix('\n```')
 tree=ast.parse(src)
 allowed=(ast.Module,ast.FunctionDef,ast.arguments,ast.arg,ast.Assign,ast.AugAssign,ast.If,ast.Return,ast.Name,ast.Load,ast.Store,ast.Constant,ast.Attribute,ast.Compare,ast.BinOp,ast.UnaryOp,ast.BoolOp,ast.Call,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.USub,ast.And,ast.Or,ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Eq,ast.NotEq)
 for node in ast.walk(tree):
  assert isinstance(node,allowed),type(node)
  if isinstance(node,ast.Call):assert isinstance(node.func,ast.Name) and node.func.id in helpers
  if isinstance(node,ast.Attribute):assert isinstance(node.value,ast.Name) and node.value.id=='ctx' and not node.attr.startswith('_')
 env={'__builtins__':{},**helpers};exec(compile(tree,scene['id'],'exec'),env)
 scores={name:env['score'](ctx) for name,ctx in candidates.items()};top=max(scores.values())
 winners=[n for n,v in scores.items() if abs(v-top)<1e-10]
 assert winners==[scene['metrics']['评分摘要 top1']],(scene['id'],winners)
 for cand in scene['candidates']:
  assert cand['strategy'] in candidates
  assert abs(candidates[cand['strategy']].memory_pressure*57.6-cand['memory_gib_reported'])<=.000501
 results.append({'id':scene['id'],'score_top1':winners[0],'highest_score':top,'tie_count':len(winners),'representative_scores':{name:scores[name] for name in ['PP4_TP4_DP16_EP8_MB8','PP4_TP2_DP32_EP8_MB4','PP1_TP4_DP64_EP8_MB1']}})
out={'manifest_hashes_match':True,'feasible_candidates':90,'all_19_unique_top1_match':True,'all_190_memory_match':True,'score_results':results,'representative_scopes':{n:{'tp_scope':candidates[n].tp_scope_exposure,'dp_scope':candidates[n].dp_scope_exposure} for n in ['PP4_TP4_DP16_EP8_MB8','PP4_TP2_DP32_EP8_MB4','PP1_TP4_DP64_EP8_MB1']}}
(ROOT/'analysis/评分重算核验.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in out.items() if k!='score_results'},ensure_ascii=False,indent=2))
