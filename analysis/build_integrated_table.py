from pathlib import Path
from html import escape
root=Path(__file__).resolve().parent.parent
rows=[
('D-M','稀疏局部化','128：1；256：2','主要：亲和组覆盖率 C_A=0.25；节点覆盖率 C_N=0.125；辅助：256 慢卡率 ρ=3.91%–4.69%','PP 保持较深；保留 MB/PP≈2 时，TP≥2N/B；256 报告代表 PP4、TP4、MB8','128:s006；256:s005、s006','较大 MB 为深流水提供更多调度批次；固定 B 下需提高 TP 才能保留该 MB，仍需检查同步代价。128:s005 已隔离。'),
('D-M','半亲和组覆盖，深结构延续','128：2；256：2','主要：亲和组覆盖率 C_A=0.50；节点覆盖率 C_N=0.25–0.375；辅助：组内不均衡 D_intra=0.25–1','继承深 PP；128 代表 TP2、MB8；256 代表 TP4、MB8；TP 上界沿用场景原公式','两规模:s010、s026','保留较多微批次时，新增 GPU 通过 TP 承接；局部化只是经验关联，能否减少慢卡影响取决于放置。'),
('D-M','半亲和组覆盖，浅转深边界','128：2；256：2','主要：亲和组覆盖率 C_A=0.50；节点覆盖率 C_N=0.50；辅助：慢卡率 ρ≈42.19%–45.31%；组内不均衡 D_intra=0 或 0.375','128 保留原浅 PP 实例；256 增加深 PP、大 MB 分支；两结构并列验证，不强制按均衡程度选浅 PP','两规模:s043、s046','相近分布下结构发生变化；可行域变化提供解释线索，但不足以证明性能机制，应比较两种结构的耗时。'),
('D-L','强组内失衡，分支待辨','128：2；256：2','主要：亲和组覆盖率 C_A=0.50；单节点最大慢卡比例 R_max=1；组内不均衡 D_intra=0.6875–1；辅助：慢卡率 ρ≈24.22%–41.41%','保留 PP4、TP2 时，MB≤B×PP×TP/N；128 代表 MB8；256 代表 MB4；s025 的 MB≥PP 只作弱偏好','两规模:s025、s042；反例256:s026','较小 TP 限制同步组大小；DP 随规模增加使可用 MB 上界降低。不能用强失衡单独识别本分支。'),
('S','全组覆盖，低至中等负担','128：5；256：5','主要：亲和组覆盖率 C_A=1；辅助：慢卡率 ρ≈3.13%–48.44%；组内不均衡 D_intra=0.0625–0.375','PP 取最浅可行值，当前代表 1；TP≈4；MB≈1；DP 按满卡关系从 32 增至 64','两规模:s004、s009、s031、s037、s049','浅 PP 减少阶段依赖，小 MB 与浅结构对应；DP 增加仅表示副本数增加，吞吐收益需验证。'),
('S','全组覆盖，单节点集中边界','128：1；256：1','主要：亲和组覆盖率 C_A=1；节点覆盖率 C_N=0.50；组内不均衡 D_intra=1；辅助：慢卡率 ρ≈44.53%','保留 PP1、TP≤4；256 原规则 DP×MB≤2B/3；代表 MB1；单样本不生成新阈值','两规模:s045','全组覆盖与极端局部失衡同时存在，但报告仍采用浅结构，说明最大失衡并非深 PP 的充分条件。'),
('S','多数亲和组覆盖，保留正常组','128：2；256：2','主要：亲和组覆盖率 C_A=0.75；单节点最大慢卡比例 R_max=1；辅助：慢卡率 ρ≈51.56%–72.66%；组内不均衡 D_intra=0.0625–0.125','继承浅 PP、小 MB；256:s052 保留 DP≥64 和 0.65≤MB/PP≤1.35；s073 保留 MB1、2.6≤TP/PP≤5.4、PP×TP²≤N/10','两规模:s052、s073','保留正常组并不自动意味着适合深 PP；两规模现有经验均支持浅结构，具体补充规则分别保留。'),
('S','全节点近饱和','128：3；256：3','主要：亲和组覆盖率 C_A=1；节点覆盖率 C_N=1；慢卡率 ρ≈89.84%–92.97%；辅助：组内不均衡 D_intra=0.0625–0.625','PP≈1；TP 维持中等，原上界分别保留；MB≈1；DP 派生；不外推至无证据的其他负担区间','两规模:s090、s092、s093','报告经验在此范围保持浅结构；广泛慢卡暴露下减少阶段依赖是解释假设，不能据此声称深 PP 必然更慢。')]
families={
'D-M':(3,'D / D-M：深流水线的大 MB 分支','PP 较深；MB/PP 偏大；TP 由 batch 必要下界与场景上界联合约束','主要为局部化覆盖：亲和组覆盖率 C_A=0.25–0.50；节点覆盖率 C_N≤0.50'),
'D-L':(1,'D / D-L：深流水线的低 TP 分支','PP 较深；TP 偏小；MB/PP≤(B/N)TP，按上界限制大 MB 偏好','当前两个 256 样本均覆盖半数亲和组，存在全慢节点及明显组内失衡；非充分判据'),
'S':(4,'S：浅流水线','PP 取最浅可行值；TP 中等；MB 较小；保留原公式具体条件','当前配对样本主要广覆盖：亲和组覆盖率 C_A=0.75–1；节点覆盖率 C_N≥0.50')}
heads=['Experience Family / 经验族','Family Characteristics / 经验族部署特征','Family-level Scenario Profile / 经验族场景总体特征','Scenario Motif / 场景模式','Scenario Count / 场景数量','Slow-GPU Distribution Features / 慢卡分布特征','Scenario-specific Deployment Experience / 场景级部署经验','Representative Scenarios / 代表场景','Deployment Rationale / 部署经验解释']
fmt=lambda s:escape(s).replace('；','；<br>')
out=['<table>','<colgroup>'+''.join(f'<col style="width:{w}%">' for w in [6,12,11,9,6,15,15,8,18])+'</colgroup>','<thead><tr>'+''.join('<th>'+h+'</th>' for h in heads)+'</tr></thead>','<tbody>']; seen=set()
for family,*cells in rows:
    out.append('<tr>')
    if family not in seen:
        span,*common=families[family]
        out.extend(f'<td rowspan="{span}">{fmt(c)}</td>' for c in common); seen.add(family)
    out.extend('<td>'+fmt(c)+'</td>' for c in cells); out.append('</tr>')
out.extend(['</tbody>','</table>'])
table='\n'.join(out)
p=root/'256GPU与128GPU_差异分析及策略细化.md'
s=p.read_text()
if '<!-- INTEGRATED_TABLE -->' in s:
    s=s.replace('<!-- INTEGRATED_TABLE -->',table)
else:
    start=s.index('<table>'); end=s.index('</table>',start)+len('</table>')
    s=s[:start]+table+s[end:]
if '<!-- PAIR_TABLE -->' in s:
    s=s.replace('<!-- PAIR_TABLE -->',(root/'analysis/同编号19场景对照.md').read_text())
else:
    start=s.index('| 场景 | 128 卡模式 |'); end=s.index('## 附录 B：',start)
    s=s[:start]+(root/'analysis/同编号19场景对照.md').read_text()+'\n'+s[end:]
p.write_text(s)
print('已写入8条融合场景模式与19行配对表')
