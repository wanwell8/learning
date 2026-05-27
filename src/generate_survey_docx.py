"""Generate 4-paper survey Word document (single-column, 电力系统自动化 style)."""
import os, zipfile

OUT = '/home/user/learning/paper/voltage_survey.docx'
os.makedirs('/home/user/learning/paper', exist_ok=True)

def rpr(bold=False, italic=False, sz=None, color=None, cn='宋体', en='Times New Roman',
        sup=False, sub_v=False):
    parts = []
    if bold:    parts.append('<w:b/><w:bCs/>')
    if italic:  parts.append('<w:i/><w:iCs/>')
    if sup:     parts.append('<w:vertAlign w:val="superscript"/>')
    if sub_v:   parts.append('<w:vertAlign w:val="subscript"/>')
    if sz:      parts.append(f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>')
    if color:   parts.append(f'<w:color w:val="{color}"/>')
    parts.append(f'<w:rFonts w:hint="eastAsia" w:eastAsia="{cn}" w:ascii="{en}" w:hAnsi="{en}"/>')
    return '<w:rPr>' + ''.join(parts) + '</w:rPr>'

def run(text, bold=False, italic=False, sz=None, color=None, cn='宋体',
        en='Times New Roman', sup=False, sub_v=False):
    rp = rpr(bold, italic, sz, color, cn, en, sup, sub_v)
    t = (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace('"', '&quot;'))
    return f'<w:r>{rp}<w:t xml:space="preserve">{t}</w:t></w:r>'

def para(*runs_xml, align='both', il=0, fi=0, before=0, after=60):
    sp = f'<w:spacing w:before="{before}" w:after="{after}"/>'
    ind = f'<w:ind w:left="{il}" w:firstLine="{fi}"/>' if il or fi else ''
    jc = f'<w:jc w:val="{align}"/>'
    return f'<w:p><w:pPr>{jc}{sp}{ind}</w:pPr>{"".join(runs_xml)}</w:p>'

def blank():
    return para(before=0, after=60)

def heading(text, lv=1, before=200, after=80):
    colors = {1: '1F3864', 2: '2E75B6', 3: '244D70'}
    sizes  = {1: 30, 2: 26, 3: 24}
    return para(run(text, bold=(lv<=2), sz=sizes.get(lv,24), color=colors.get(lv,'000000')),
                align='left', before=before, after=after)

def bp(text, fi=420, after=60, before=0, align='both'):
    return para(run(text, sz=20), align=align, fi=fi, before=before, after=after)

def hr():
    return ('<w:p><w:pPr><w:pBdr>'
            '<w:bottom w:val="single" w:sz="6" w:space="1" w:color="2E75B6"/>'
            '</w:pBdr><w:spacing w:before="120" w:after="120"/></w:pPr></w:p>')

def mr(text):
    t = text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    return f'<m:r><m:t>{t}</m:t></m:r>'

def msub(base, sub):
    return f'<m:sSub><m:sSubPr/><m:e>{base}</m:e><m:sub>{sub}</m:sub></m:sSub>'

def msup(base, sup):
    return f'<m:sSup><m:sSupPr/><m:e>{base}</m:e><m:sup>{sup}</m:sup></m:sSup>'

def mfrac(n, d):
    return f'<m:f><m:fPr/><m:num>{n}</m:num><m:den>{d}</m:den></m:f>'

def eq_tbl(math_inner, label=''):
    tbl_w, fml_w = 9072, 7439
    lbl_w = tbl_w - fml_w
    bdr = ('<w:tcBorders><w:top w:val="none"/><w:bottom w:val="none"/>'
           '<w:left w:val="none"/><w:right w:val="none"/></w:tcBorders>')
    c1 = (f'<w:tc><w:tcPr><w:tcW w:w="{fml_w}" w:type="dxa"/>{bdr}</w:tcPr>'
          f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
          f'<m:oMath>{math_inner}</m:oMath></w:p></w:tc>')
    c2 = (f'<w:tc><w:tcPr><w:tcW w:w="{lbl_w}" w:type="dxa"/>{bdr}</w:tcPr>'
          f'<w:p><w:pPr><w:jc w:val="right"/></w:pPr>'
          f'{run(label, sz=20)}</w:p></w:tc>')
    bdr2 = ('<w:tblBorders><w:top w:val="none"/><w:left w:val="none"/>'
            '<w:bottom w:val="none"/><w:right w:val="none"/>'
            '<w:insideH w:val="none"/><w:insideV w:val="none"/></w:tblBorders>')
    return (f'<w:tbl><w:tblPr><w:tblStyle w:val="TableNormal"/>'
            f'<w:tblW w:w="{tbl_w}" w:type="dxa"/>{bdr2}</w:tblPr>'
            f'<w:tr>{c1}{c2}</w:tr></w:tbl>')

def comp_table(rows):
    col_w = [1500, 1850, 1850, 1850, 1850]
    total = sum(col_w)
    bdr = 'w:val="single" w:sz="4" w:space="0" w:color="2E75B6"'
    xml_rows = []
    for ri, row in enumerate(rows):
        cells = ''
        for ci, cell in enumerate(row):
            is_hdr = ri == 0
            fill = 'D9E1F2' if is_hdr else ('EBF3FA' if ci == 0 else 'FFFFFF')
            cw = col_w[ci] if ci < len(col_w) else 1850
            t = cell.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            rp = rpr(bold=(is_hdr or ci == 0), sz=18)
            cells += (f'<w:tc><w:tcPr><w:tcW w:w="{cw}" w:type="dxa"/>'
                      f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/></w:tcPr>'
                      f'<w:p><w:pPr><w:jc w:val="center"/>'
                      f'<w:spacing w:before="40" w:after="40"/></w:pPr>'
                      f'<w:r>{rp}<w:t xml:space="preserve">{t}</w:t></w:r></w:p></w:tc>')
        xml_rows.append(f'<w:tr>{cells}</w:tr>')
    return (f'<w:tbl><w:tblPr><w:tblStyle w:val="TableNormal"/>'
            f'<w:tblW w:w="{total}" w:type="dxa"/>'
            f'<w:tblBorders>'
            f'<w:top {bdr}/><w:left {bdr}/><w:bottom {bdr}/><w:right {bdr}/>'
            f'<w:insideH {bdr}/><w:insideV {bdr}/></w:tblBorders></w:tblPr>'
            + ''.join(xml_rows) + '</w:tbl>')

parts = []

def add(*items):
    for x in items:
        parts.append(x)

# Cover
add(
    para(run('配电网电压控制文献综述', bold=True, sz=36, color='1F3864'),
         align='center', before=300, after=80),
    para(run('Survey of Voltage Control Methods in Distribution Networks',
             italic=True, sz=24, color='555555'),
         align='center', before=0, after=60),
    para(run('基于强化学习与数据驱动方法的系统综述', sz=22, color='666666'),
         align='center', before=0, after=60),
    para(run('本文档依据电力系统自动化期刊格式（单栏）整理，逐篇详细梳理框架、公式及说明',
             sz=20, color='333333'),
         align='center', before=0, after=300),
)

# ===== PAPER 1 =====
add(
    heading('文献1  安全离策略深度强化学习算法用于配电系统无功电压控制', lv=1),
    para(run('Safe Off-Policy Deep Reinforcement Learning Algorithm for Volt-VAR Control in Power Distribution Systems',
             italic=True, sz=20, color='555555'), align='left', after=40),
    para(run('Wei Wang, Nanpeng Yu, Yuanqi Gao, Jie Shi  |  IEEE Trans. Smart Grid, Vol.11, No.4, Jul. 2020',
             sz=18, color='777777'), align='left', after=120),
    heading('1.1  研究背景与动机', lv=2),
    bp('随着大规模光伏（PV）接入配电网，电压越限问题日益突出。传统无功电压控制（VVC）依赖精确的网络拓扑和参数，在实际中难以获取。现有强化学习（RL）方法将VVC建模为马尔可夫决策过程（MDP），采用Q学习或深度Q网络（DQN），但存在三大缺陷：①动作数量随控制设备数指数增长（可扩展性差）；②无法显式处理物理约束（电压越限不可避免）；③样本效率低（需大量在线交互）。本文提出约束软演员-评论家（CSAC）算法，将VVC建模为约束马尔可夫决策过程（CMDP），同时保证样本效率、可扩展性和约束满足三项目标。'),
    heading('1.2  问题建模：约束MDP（CMDP）', lv=2),
    bp('VVC问题定义为五元组 CMDP = (S, A, R, Rc, P)，具体如下：'),
    bp('状态空间 S：节点有功注入 P、无功注入 Q 及当前档位向量 Tap，即 s = [P, Q, Tap]；'),
    bp('动作空间 A：调整各可控设备档位，离散动作，设备i有Ai个档位，总动作数|A|=prod(Ai)，随设备数指数增长；'),
    bp('奖励函数——最小化运行成本（含网损和换挡成本）：'),
)
R_eq = (mr('R(s,a) = -C') + msub(mr('e'), mr('')) + mr(' * P') + msub(mr('loss'), mr('')) +
        mr(' - ') + msub(mr('SUM'), mr('j')) + mr('C') + msub(mr('T,j'), mr('')) +
        mr(' * |Delta tap') + msub(mr('j'), mr('')) + mr('|'))
add(
    eq_tbl(R_eq, '(1)'),
    bp('式中：Ce 为电价（$/MWh）；CT,j 为设备j每次档位调节成本；Ploss 为全网有功损耗；Delta tapj 为档位变化量。'),
    bp('代价函数——电压越限计数（物理约束的显式表达）：'),
)
Rc_eq = (mr('R^c(s,a) = ') + msub(mr('SUM'), mr('i')) +
         mr(' 1{V') + msub(mr('i'), mr('')) + mr(' not in [V_min, V_max]}'))
add(
    eq_tbl(Rc_eq, '(2)'),
    bp('式中：Vi 为节点i电压幅值；V_min=0.95 p.u.、V_max=1.05 p.u.。'),
    bp('CMDP最优化目标：'),
)
obj_eq = (mr('max_pi J(pi)   s.t.   J^c(pi) <= R^c'))
add(
    eq_tbl(obj_eq, '(3)'),
    bp('其中回报 J(pi)=E[SUM_t gamma^t * R(st,at)]，约束回报 Jc(pi)=E[SUM_t gamma^t * Rc(st,at)]。'),
    heading('1.3  核心算法：约束软演员-评论家（CSAC）', lv=2),
    bp('CSAC 在最大熵软演员-评论家（SAC）基础上引入拉格朗日乘子处理约束。'),
    heading('1.3.1  软演员-评论家（SAC）基础', lv=3),
    bp('SAC最大化包含熵正则化的累积回报：'),
)
sac_eq = (mr('max_pi E [ SUM_t gamma^t (R_t + alpha * H(pi(.|s_t))) ]'))
add(
    eq_tbl(sac_eq, '(4)'),
    bp('熵正则化项 H(pi(.|s))= -SUM_a pi(a|s)*log pi(a|s) 鼓励策略探索，避免过早收敛；温度系数 alpha 权衡奖励与熵探索。'),
    bp('Q函数Bellman目标（含熵）：'),
)
Qbell = (mr('Q(s_t, a_t) = R_t + gamma * E[ V^h(s_{t+1}) ]'))
add(
    eq_tbl(Qbell, '(5)'),
    bp('状态价值函数闭式解：V^h(s)=alpha*log SUM_a exp(Q^h(s,a)/alpha)，使离策略更新变为可行。'),
    heading('1.3.2  拉格朗日对偶与CSAC', lv=3),
    bp('引入非负拉格朗日乘子 lambda >= 0，将约束优化转化为无约束拉格朗日形式：'),
)
lagr_eq = (mr('L(pi, lambda) = E[V^h(s)] - lambda*(E[V^c(s)] - R^c)'))
add(
    eq_tbl(lagr_eq, '(6)'),
    bp('交替优化：固定lambda时最大化L对pi（标准SAC问题）；固定pi时按梯度上升更新lambda：'),
)
lam_eq = (mr('lambda <- max(0,  lambda + alpha_lambda*(E[V^c(s)] - R^c))'))
add(
    eq_tbl(lam_eq, '(7)'),
    bp('当 Jc(pi)>Rc 时lambda增大（加强约束惩罚）；满足约束时lambda减小，自适应平衡性能与安全。'),
    heading('1.3.3  设备解耦策略网络与序数编码', lv=3),
    bp('对于离散控制动作（档位调节），策略网络采用设备解耦结构：各设备i共享状态输入，独立输出各档位概率。序数编码引入动作间顺序归纳偏置。设备i选择档位j的概率（softmax归一化）：'),
)
prob_eq = (mr('p_{ij} = ') +
           mfrac(mr('exp(l_{ij})'), msub(mr('SUM'), mr('k')) + mr('exp(l_{ik})')))
add(
    eq_tbl(prob_eq, '(8)'),
    bp('全局策略概率为所有设备概率之积：pi(a|s)=PROD_i p_{ij}(s)，策略网络参数量仅随设备数线性增长。'),
    heading('1.4  仿真验证', lv=2),
    bp('在IEEE 4/34/123节点配电系统测试，对比算法：DQN（惩罚法）、CPO（约束策略优化）、SAC（固定惩罚）、MICP、MPC-MICP。结论：①CSAC达最高平均周回报，电压约束满足率接近100%；②CSAC在4节点系统仅需约1万样本，而CPO需约50万样本；③DQN无法在123节点系统合理时间内求解（指数可扩展性瓶颈），CSAC线性增长；④电压越限幅度平均不超0.01 p.u.。'),
    blank(),
)

# ===== PAPER 2 =====
add(
    hr(),
    heading('文献2  快速光伏波动与非理想通信下的分布式在线电压控制', lv=1),
    para(run('Distributed Online Voltage Control With Fast PV Power Fluctuations and Imperfect Communication',
             italic=True, sz=20, color='555555'), align='left', after=40),
    para(run('Licheng Wang, Luochen Xie, Yu Yang, Youbing Zhang, Kai Wang  |  IEEE Trans. Smart Grid, Vol.14, No.5, Sep. 2023',
             sz=18, color='777777'), align='left', after=120),
    heading('2.1  研究背景', lv=2),
    bp('高渗透率光伏接入配电网导致持续性电压越限风险。分布式PV逆变器通过无功补偿参与电压调节，但快速光伏波动（秒级）对实时控制提出挑战。现有分布式协调算法（ADMM或静态共识）在获得收敛解后才执行控制命令，控制滞后于PV波动。本文提出基于动态共识算法的分布式在线电压控制方案：每次迭代步骤立即执行控制命令，对随机时延和丢包具有鲁棒性，并从理论上推导了算法跟踪误差的量化上界。'),
    heading('2.2  协调无功电压控制', lv=2),
    bp('本地过压检测触发无功补偿，节点i处逆变器无功出力增量：'),
)
vv_eq = (mr('Delta q_{PV,i}(t) = c * max(0, V_i(t) - V_max)'))
add(
    eq_tbl(vv_eq, '(9)'),
    bp('式中：c 为控制步长；Vi(t) 为节点i当前电压；V_max=1.05 p.u.。'),
    bp('协调控制目标（按装机容量比例公平分配无功补偿负担）：'),
)
tgt_eq = (mr('x^q_avg = (1/n) * SUM_i (q_{PV,i}(k) / c_{pv,i})'))
add(
    eq_tbl(tgt_eq, '(10)'),
    bp('式中：c_{pv,i} 为节点i逆变器装机容量；n 为含PV节点数；x_avg 为协调目标（平均归一化无功出力）。'),
    heading('2.3  动态共识算法', lv=2),
    bp('动态共识迭代规则（每个迭代步k立即执行并广播）：'),
)
dc1 = (mr('x_i(k+1) = SUM_{j in J_i} (1/D_j) * x_j(k) + y_i(k)'))
dc2 = (mr('y_i(k+1) = x_i(k+1) - x_i(k)'))
add(
    eq_tbl(dc1, '(11)'),
    eq_tbl(dc2, '(12)'),
    bp('式中：J_i 为节点i的邻居节点集；D_j 为节点j的出度；y_i(k) 为辅助变量，记录相邻步间状态变化量。初始值y_i(0)=初始无功出力，s_i(0)=装机容量。'),
    heading('2.4  非理想通信处理机制', lv=2),
    bp('（1）随机时延与异步迭代：智能体i在步k收到邻居消息立即更新；若连续m步未收到来自邻居j的消息，则仍触发更新（避免算法停滞），使用已缓存的最新值推进迭代。'),
    bp('（2）丢包补偿机制：发送方累积变量 Delta_i(k)=SUM(最近m步y_i或s_i增量)，广播给邻居；接收方通过时间戳检验有效性，舍弃过时包；丢失数据通过后续包中的累积增量补偿，不会产生永久性误差。'),
    heading('2.5  状态转移模型', lv=2),
    bp('引入虚拟节点（Type I模拟时延、Type II模拟丢包）建立n智能体系统随机状态转移矩阵M(k)：'),
)
mat_eq = mr('[Y(k+1); S(k+1)] = M(k) * [Y(k); S(k)] + Q(k)')
add(
    eq_tbl(mat_eq, '(13)'),
    bp('Y(k)、S(k) 包含各智能体和虚拟节点状态；Q(k) 为外部时变激励（PV功率变化量）；M(k) 为行随机矩阵（各行元素非负且行和为1），这是后续收敛分析的关键基础。'),
    heading('2.6  跟踪误差理论上界（核心理论贡献）', lv=2),
    bp('命题1（跟踪误差定量上界）：设系统n智能体强连通，最长路由长度l，最大时延mu，最大连续丢包次数m，任意逆变器无功出力变化量上界q_max，则任意智能体i的跟踪误差满足：'),
)
err_eq = (mr('|x_i(k) - x^q_avg(k)| <= e_initial + e_dynamic'))
add(eq_tbl(err_eq, '(14)'))
ei_eq = (mr('e_initial = C_1 * T^k -> 0  (k->inf, T<1)'))
add(eq_tbl(ei_eq, '(15)'))
ed_eq = (mr('e_dynamic <= (ml + mu + m) * q_max / (c_pv * n)'))
add(
    eq_tbl(ed_eq, '(16)'),
    bp('式中：T 为收缩因子（T<1，由通信拓扑决定）；初始误差随迭代渐近趋零；动态误差由PV波动幅度和通信质量（mu、m）决定，不可完全消除。提高通信质量（降低mu、m）或减慢PV变化速率（降低q_max）均可压缩该误差。'),
    heading('2.7  高渗透场景：结合PV限功', lv=2),
    bp('当逆变器无功出力接近饱和（x_i>x^q_max）时，启动有功限功控制，限功量同样通过动态共识在各逆变器间公平分配。控制层次：①优先使用无功补偿；②无功接近饱和时激活有功限功；③电压风险消除后，共识状态反向退出，避免不必要限功。'),
    heading('2.8  仿真验证', lv=2),
    bp('在IEEE 33节点系统（含PV逆变器和电动汽车）测试，丢包率10%。主要结论：①动态共识算法实现每步实时无功重分配，消除下游逆变器无功饱和引发的过压（静态共识需约150次迭代/30秒才能收敛）；②m=4时通信开销降至同步规则的69.3%，跟踪误差仍满足理论上界；③高渗透场景（最大PV 6MW）结合限功策略成功将全网电压控制在1.05 p.u.以内。'),
    blank(),
)

# ===== PAPER 3 =====
add(
    hr(),
    heading('文献3  物理知识引导的图神经网络深度强化学习用于鲁棒配电系统电压控制', lv=1),
    para(run('Physics-Informed Graphical Representation-Enabled Deep Reinforcement Learning for Robust Distribution System Voltage Control',
             italic=True, sz=20, color='555555'), align='left', after=40),
    para(run('Di Cao, Junbo Zhao, Qi Huang, Zhe Chen, Weihao Hu  |  IEEE Trans. Smart Grid, Vol.15, No.1, Jan. 2024',
             sz=18, color='777777'), align='left', after=120),
    heading('3.1  研究背景与挑战', lv=2),
    bp('基于DRL的配电网电压控制方法面临三大挑战：①全网状态可观测性假设（实际仅有部分量测可用）；②异常量测（通信丢包、仪表误差）导致控制性能退化；③对精确线路参数的依赖（配电网R/X比高，Jacobian矩阵病态）。现有GNN方法虽能处理拓扑变化，但仍依赖全局观测和精确线路参数。本文提出物理知识引导的全局图注意力网络（GGAT）+深度自编码器（DAE）表征网络，与SAC控制策略集成，实现对异常量测的鲁棒性，同时降低对精确物理模型的依赖。'),
    heading('3.2  问题建模', lv=2),
    bp('配电网N个节点，含PV逆变器、静止无功补偿器（SVC）和储能（ESS）。节点i复功率注入分解：'),
)
pi_eq = (mr('p_i(t) = p_{g,i}(t) + p_{e,i}(t) - p_{c,i}(t)'))
add(
    eq_tbl(pi_eq, '(18)'),
    bp('式中：p_g 为PV发电，p_e 为ESS出力（正为放电），p_c 为负荷。非线性交流潮流方程：'),
)
pf_eq = (mr('p_i = v_i * SUM_{j in N} v_j*(G_ij*cos(theta_ij) + B_ij*sin(theta_ij))'))
add(
    eq_tbl(pf_eq, '(19)'),
    bp('电压安全约束：V_min <= v_i(t) <= V_max（V_min=0.95, V_max=1.05 p.u.）。'),
    bp('目标函数1（最小化电压偏差）：'),
)
obj1_eq = (mr('min F = SUM_{i in N} (v_i - v_ref)^2 + rho * 1{v_i not in [V_min,V_max]}'))
add(
    eq_tbl(obj1_eq, '(20)'),
    bp('目标函数2（最小化网络损耗，含ESS场景）：'),
)
obj2_eq = (mr('min F = SUM_{(i,j) in L} G_ij*[(v_{e,i}-v_{e,j})^2+(v_{f,i}-v_{f,j})^2]'))
add(
    eq_tbl(obj2_eq, '(21)'),
    heading('3.3  MDP建模', lv=2),
    bp('状态 s_t=m(t)：部分支路有功/无功功率量测（实时量测）+ 所有节点有功/无功注入预测（伪量测）+ 邻接矩阵T；'),
    bp('动作 a_t=[q_{s,i}(t), phi_{g,i}(t)]：SVC无功补偿量和PV逆变器无功出力；'),
    bp('奖励（电压偏差目标）：'),
)
rew_eq = (mr('r_t = -SUM_i (v_i - v_ref)^2 - rho*1{v_i not in [V_min,V_max]}'))
add(
    eq_tbl(rew_eq, '(22)'),
    heading('3.4  GGAT代理模型（核心创新）', lv=2),
    bp('代理模型核心作用：①模拟潮流计算，根据量测估算节点电压；②在离线训练中为DRL提供奖励信号，降低对精确线路参数的依赖。GGAT图注意力特征聚合（利用电网拓扑结构作为图结构先验）：'),
)
ggat_eq = (mr('h_i = SUM_{j in N(i)} alpha_{ij} * W * x_j'))
add(
    eq_tbl(ggat_eq, '(23)'),
    bp('注意力系数alpha_{ij}由节点i与j的特征相似度通过softmax归一化得到；邻接矩阵T确定邻域范围，实现结构知识嵌入，使网络能利用相邻节点信息填补缺失量测、平滑噪声量测。'),
    bp('代理模型监督训练损失（使用历史潮流数据，1000个训练样本）：'),
)
surr_eq = (mr('L_s = (1/|B|) * SUM_{i in B} ||v_i - v_hat_i||^2'))
add(
    eq_tbl(surr_eq, '(24)'),
    heading('3.5  深度自编码器（DAE）降维与鲁棒表征', lv=2),
    bp('GGAT输出高维量测表征 h_g，DAE对其进行维度压缩以提升DRL训练稳定性。'),
    bp('编码过程（降维到信息瓶颈）：'),
)
enc_eq = (mr('h_e = f_enc(h_g) = sigma(W_enc * h_g + b_enc)'))
add(
    eq_tbl(enc_eq, '(25)'),
    bp('解码过程（仅训练时使用，强迫编码器学习鲁棒低维表征）：'),
)
dec_eq = (mr('h_g_tilde = f_dec(h_e) = sigma(W_dec * h_e + b_dec)'))
add(
    eq_tbl(dec_eq, '(26)'),
    bp('DAE无监督训练损失（最小化重构误差）：'),
)
dae_eq = (mr('L_dae = ||h_g - h_g_tilde||^2'))
add(
    eq_tbl(dae_eq, '(27)'),
    bp('GGAT注意力机制融合相邻节点信息可填补缺失量测、平滑噪声量测；DAE进一步从高维GGAT特征中提取最精炼的鲁棒编码，供SAC策略使用。'),
    heading('3.6  SAC电压控制策略', lv=2),
    bp('SAC最大化带熵正则化的累积折扣奖励：'),
)
sac2_eq = (mr('argmax_pi E[ SUM_t gamma^t (r_t + alpha*H(pi(.|s_t))) ]'))
add(
    eq_tbl(sac2_eq, '(28)'),
    bp('评论家网络更新（最小化TD误差）：'),
)
crit_eq = (mr('L_q = E[ (Q(s,a) - r - gamma*Q_target(s_prime) + gamma*alpha*log(pi(a_prime|s_prime)))^2 ]'))
add(
    eq_tbl(crit_eq, '(29)'),
    bp('演员网络更新（最大化带熵Q值）：'),
)
act_eq = mr('L_a = E[ -Q(s, pi(s)) + alpha * log(pi(a|s)) ]')
add(
    eq_tbl(act_eq, '(30)'),
    bp('目标网络软更新：theta_targ <- tau*theta + (1-tau)*theta_targ（tau=0.005）稳定训练。'),
    heading('3.7  三阶段训练与实时控制', lv=2),
    bp('(1)离线训练阶段1：利用历史潮流数据监督训练GGAT代理模型，再无监督训练DAE，提取鲁棒量测表征；'),
    bp('(2)离线训练阶段2：固定GGAT+DAE参数，使用代理模型提供奖励信号，训练SAC智能体3000 episodes（每个episode对应一个运行日，24时步）；'),
    bp('(3)在线实时控制：载入离线训练参数，每时步由表征网络提取特征h_e，演员网络在毫秒级给出控制动作a_t。'),
    heading('3.8  仿真验证', lv=2),
    bp('在IEEE 33节点和119节点系统测试，设计6种量测配置场景（正常到多处缺失+50%高斯噪声）。主要结论：①提出方法在全部6个场景下平均电压偏差最小，较GCN-SAC在Case 1~6分别提升0%/7%/9%/18%/18%/27%/29%；②快速PV波动（1秒决策周期）场景下，相比随机规划（SP）预设策略保持电压在限值内；③消融分析：仅GGAT时鲁棒性主要来源于结构知识嵌入，加入DAE后进一步提升5~11%；④代理模型电压估算误差最大不超0.002 p.u.。'),
    blank(),
)

# ===== PAPER 4 =====
add(
    hr(),
    heading('文献4  基于自适应电压灵敏度估计与机会约束规划的在线无模型DER调度', lv=1),
    para(run('Online Model-Free DER Dispatch via Adaptive Voltage Sensitivity Estimation and Chance Constrained Programming',
             italic=True, sz=20, color='555555'), align='left', after=40),
    para(run('Haoyi Wang, Yingqi Liang, Yiyun Yao, Junbo Zhao, Fei Ding  |  IEEE Trans. Power Systems, Vol.39, No.6, Nov. 2024',
             sz=18, color='777777'), align='left', after=120),
    heading('4.1  研究背景', lv=2),
    bp('配电系统DER高渗透接入带来电压越限风险。现有方法面临：①LinDistFlow线性化需精确拓扑和全网负荷参数（实际难以获取）；②DRL方法需大量历史训练数据；③量测不确定性导致控制偏差。本文核心创新：①递推最小二乘（RLS）自适应估计局部灵敏度因子（LSF）消除模型依赖；②Tukey双权函数实现对异常量测的鲁棒估计；③情景机会约束规划量化量测不确定性对电压控制的影响。在真实759节点系统验证有效性。'),
    heading('4.2  OPF问题建模', lv=2),
    bp('控制目标为最小化PV实功削减量和无功消耗：'),
)
opf_eq = (mr('min SUM_{i in H} (c_{P,i}*|DeltaP_i| + c_{Q,i}*|DeltaQ_i|)'))
add(
    eq_tbl(opf_eq, '(31)'),
    bp('约束一：PV逆变器功率能力约束（分段线性化8个约束近似圆形功率约束区域，逆变器容量为Si）：'),
)
pv_eq = (mr('|P_i| <= P_{i,max},  P_i+Q_i <= sqrt(2)*S_i,  P_i-Q_i <= sqrt(2)*S_i, ...'))
add(
    eq_tbl(pv_eq, '(32)'),
    bp('约束二：电压幅值约束（全部量测节点）：V_min <= V_i <= V_max（0.95/1.05 p.u.）。'),
    heading('4.3  LSF线性化重构', lv=2),
    bp('局部灵敏度因子（LSF）描述电压幅值对功率注入的响应关系。对量测节点k，电压幅值线性近似（以实时量测值为展开点）：'),
)
lsf_eq = (mr('V_k approx V^meas_k + SUM_{i in H} (dV_k/dP_i * DeltaP_i + dV_k/dQ_i * DeltaQ_i)'))
add(
    eq_tbl(lsf_eq, '(33)'),
    bp('式中：dV_k/dP_i 和 dV_k/dQ_i 为节点k电压对节点i有功/无功注入的LSF，构成灵敏度矩阵 S in R^(M x 2n)（M为量测节点数，n为PV节点数）。LSF线性化将非线性OPF转化为LP问题，可在线快速求解（毫秒级），同时避免对全网拓扑和节点负荷的依赖。'),
    bp('LSF存在两大问题：①时变性（运行工况变化导致LSF随时间变化）；②量测不确定性（实际量测含噪声，导致LSF估计偏差）。本文分别通过自适应RLS和机会约束解决。'),
    heading('4.4  LSF自适应递推估计（核心算法）', lv=2),
    bp('利用N个历史量测样本 {(x_t, y_t)}，x_t=[Delta p_t; Delta q_t]（功率注入变化量），y_t=Delta v_t（电压变化量），建立稀疏回归：'),
)
reg_eq = (mr('y_t = X_t * u + e,   u = s_i (目标灵敏度向量)'))
add(
    eq_tbl(reg_eq, '(34)'),
    bp('式中：u=s_i 为目标灵敏度向量；e 为量测噪声（分布未知，可能含异常值）；X_t 为滑动窗口预测矩阵。'),
    bp('目标函数融合鲁棒损失、自适应加权L1正则和L2正则：'),
)
rob_eq = (mr('min_u G = G_1(u) + G_2(u) + G_3(u)'))
add(
    eq_tbl(rob_eq, '(35)'),
    bp('鲁棒损失函数（Tukey双权函数，c=4.685，对异常值自动降权）：'),
)
g1_eq = (mr('G_1 = SUM_j lambda_j * rho_Tukey(r_j / sigma_hat)'))
add(
    eq_tbl(g1_eq, '(36)'),
    bp('Tukey双权函数定义（对异常值降权，无异常时退化为最小二乘）：'),
)
tukey_eq = mr('rho_Tukey(r) = { c^2/6 * [1-(1-(r/c)^2)^3],  |r|<=c;   c^2/6,  |r|>c }')
add(
    eq_tbl(tukey_eq, '(37)'),
    bp('式中：r 为标准化残差 r=(y-Xu)/sigma_hat；sigma_hat 为在线噪声尺度估计量（无需假设已知噪声分布）。'),
    bp('自适应加权L1正则（促进稀疏性，保留主导灵敏度元素）：'),
)
g2_eq = (mr('G_2 = lambda_1 * SUM_i w_i * |u_i|   (w_i = 1/(|u_hat_i|+eps))'))
add(
    eq_tbl(g2_eq, '(38)'),
    bp('自适应权重 w_i=1/(|u_hat_i|+eps) 与当前估计值倒数成比例：主导元素权重小（保留），非主导元素权重大（压缩至零），实现自适应稀疏化。'),
    bp('遗忘因子自适应更新（追踪时变灵敏度）：'),
)
ff_eq = (mr('lambda_j(k) = c_lambda * lambda_j(k-1)   (c_lambda approx 0.98)'))
add(
    eq_tbl(ff_eq, '(39)'),
    bp('遗忘因子使近期样本权重大、旧样本指数衰减，使估计器快速跟踪运行工况变化。递推求解（每步仅需O(n^2)运算）使该估计器适合在线实时应用。'),
    heading('4.5  情景机会约束规划', lv=2),
    bp('量测不确定性导致LSF估计存在偏差，进而影响电压约束满足率。采用情景法将概率约束转化为确定性约束：生成N_s个LSF估计误差情景{e_hat_k}，要求在所有情景下电压约束满足：'),
)
cc_eq = (mr('V_min <= V^meas_k + (S_hat_k + e_hat_k)*[DeltaP; DeltaQ] <= V_max,  forall k=1,...,N_s'))
add(
    eq_tbl(cc_eq, '(40)'),
    bp('式中：S_hat_k 为当前LSF估计值；e_hat_k 为第k个LSF误差情景样本（由历史残差采样生成）；N_s 为情景数（典型值50~100，平衡求解效率与约束满足概率）。'),
    bp('在线控制循环：(1)实时量测（PV功率、电压）-> (2)RLS自适应LSF更新 -> (3)生成情景约束 -> (4)求解情景LP -> (5)下发控制指令 -> 返回(1)。'),
    heading('4.6  仿真验证', lv=2),
    bp('在真实美国Colorado州759节点配电系统（三相不平衡）测试，含多处PV接入点，量测含5%~10%高斯噪声和10%异常量测。对比方法：LinDistFlow-OPF（需精确模型）、标准RLS（无鲁棒性）、仅机会约束（无自适应估计）。主要结论：①自适应LSF估计误差比标准RLS降低约40%；②在量测误差和异常场景下，电压越限率最低；③无需系统模型前提下控制性能接近LinDistFlow-OPF（损耗差异<3%）；④情景机会约束（N_s=50）相比鲁棒优化计算效率提升2个数量级；⑤759节点大系统每步求解约0.1 s，满足在线要求。'),
    blank(),
)

# ===== COMPARISON =====
add(hr(), heading('综合对比与总结', lv=1))
add(heading('5.1  四篇文献核心框架对比', lv=2))
tbl_data = [
    ['维度',        '文献1 (CSAC)',     '文献2 (动态共识)',  '文献3 (GGAT-DRL)', '文献4 (LSF-CCP)'],
    ['控制范式',    '集中式DRL',        '分布式共识',        '集中式DRL',        '数据驱动LP'],
    ['模型依赖',    '无需模型',         '无需模型',          '代理模型替代',     '无需模型(RLS)'],
    ['不确定性',    'CMDP约束',         '误差上界证明',      '异常量测鲁棒',     '机会约束+RLS'],
    ['控制变量',    '离散档位/无功',    'PV无功/限功',       'SVC/PV/ESS',       'PV有功/无功'],
    ['理论保证',    '局部最优收敛',     '跟踪误差上界',      '无(DRL经验性)',     '机会约束概率保证'],
    ['在线效率',    '离线训练+推理',    '每步代数运算',      '离线训练+推理',    '每步LP(~0.1s)'],
]
add(comp_table(tbl_data), blank())

add(
    heading('5.2  关键公式体系总结', lv=2),
    bp('【控制目标】VVC最小化网损+换挡成本（文献1式1）；最小化PV削减+无功消耗（文献4式31）；最小化电压偏差（文献3式20）。'),
    bp('【强化学习】CMDP目标（文献1式3）；SAC最大熵目标（文献1式4，文献3式28）；CSAC拉格朗日对偶（文献1式6）；lambda自适应更新（文献1式7）。'),
    bp('【分布式协调】Volt-Var控制触发（文献2式9）；协调目标（文献2式10）；动态共识迭代（文献2式11-12）；跟踪误差上界（文献2式14-16）。'),
    bp('【图神经网络】GGAT注意力聚合（文献3式23）；代理模型训练损失（文献3式24）；DAE编解码（文献3式25-27）；SAC评论家和演员更新（文献3式29-30）。'),
    bp('【灵敏度估计】LSF线性化（文献4式33）；稀疏回归模型（文献4式34）；Tukey双权鲁棒损失（文献4式36-37）；自适应L1正则（文献4式38）；遗忘因子更新（文献4式39）；情景机会约束（文献4式40）。'),
    heading('5.3  与三阶段分布鲁棒电压调节框架的关联', lv=2),
    bp('文献4的RLS自适应灵敏度估计（式33~39）直接对应三阶段框架中事中阶段的在线电压灵敏度矩阵 S(t) 递推更新，是事中快速响应的数学基础：S(k+1)=S(k)+gamma*[DeltaV(k)-S(k)*DeltaP(k)]*DeltaP(k)^T / (||DeltaP(k)||^2+eps)，与文献4的Tukey-RLS在形式上均通过在线量测增量迭代更新灵敏度。'),
    bp('文献1的CSAC/CMDP框架揭示了将VVC约束显式建模（而非惩罚项嵌入奖励）的优越性，印证三阶段框架采用LP对偶影子价格触发重规划（而非DRL梯度）的理由：LP最优顶点处影子价格梯度突变，DRL在该处梯度为零或不稳定（零梯度问题），从而对实时约束趋紧缺乏灵敏响应。'),
    bp('文献2的分布式通信模型揭示了配电网5~15%丢包率的量化影响（参数mu、m），为三阶段框架选取事件触发阈值eta的实际依据提供了理论支撑：通信质量越差、PV波动越快，则触发间隔应越短（eta更小），动态误差越大。'),
    bp('文献3的GGAT代理模型降低了对精确线路参数的依赖，与文献4的无模型LSF思路互补，均属数据驱动+物理约束的混合范式，是三阶段框架设计中重要的横向参比基准。'),
    blank(),
)



# ===== SECTION 6: FAULT EXTENSION =====
add(hr(), heading('6  故障情景下的电压调节扩展分析', lv=1))
add(
    heading('6.1  故障情景对三阶段框架的影响', lv=2),
    bp('三阶段框架基于LinDistFlow线性化模型，假设网络拓扑固定，电压灵敏度矩阵S(t)在整个调度周期内平滑演化。当配电网发生N-1故障（支路开断）时，拓扑结构产生离散跳变，对框架三个阶段均造成本质性冲击：（a）事前预规划阶段——正常拓扑T_0下的优化结果在故障拓扑T^(k)下可能严重越限，需补充N-1预想故障约束；（b）事中RLS更新阶段——平滑递推假设S(t)连续变化，拓扑突变导致灵敏度矩阵离散跳变，RLS追踪失效；（c）事件触发重规划阶段——当前触发指标g(t)仅感知约束趋紧度，无法直接感知故障，故障信号应作为独立触发条件补充。结合28篇文献中相关工作，本节从四个维度梳理故障场景扩展：拓扑切换（文献6）、FIDVR抑制与PV低穿（文献15、23）、预规划N-1安全约束（文献3、20）、灵敏度矩阵重辨识（文献22扩展）。'),
)
fault_impact_tbl = [
    ['框架阶段',   '正常工况',          '故障工况冲击',       '扩展方案',         '引用文献'],
    ['事前预规划', 'LP在T0下优化P_h',   '故障拓扑下约束失效', 'N-1安全约束(F9)', '文献3/20'],
    ['事中RLS更新','S(t)平滑递推',      '拓扑突变S(t)跳变',   '突变检测+重辨识',  '文献22'],
    ['事件触发',   'g(t)>=eta感知趋紧', '无法感知故障信号',   '新增故障触发条件', '文献6'],
    ['重规划',     'T0下水电再调度',    'T^(k)约束结构改变',  '基于T^(k)重建LP',  '文献15/23'],
]
add(comp_table(fault_impact_tbl), blank())

# --- 6.2 SOP ---
add(
    heading('6.2  拓扑切换软开关（SOP）辅助运行——文献6', lv=2),
    bp('软开关（Soft Open Point, SOP）是基于背靠背变流器的电力电子装置，能在不切断电路的前提下实现拓扑柔性切换，故障时将受影响区域无缝转接至健康馈线。文献6（Wang et al., Modern Power Systems 2024）提出SOP辅助ADN实时协同运行方法，在拓扑切换后维持全网电压合格。'),
    bp('SOP功率平衡约束（节点i与节点j间）：'),
)
sop_f1 = (msub(mr('P'), mr('SOP,ij')) + mr(' + ') +
           msub(mr('P'), mr('SOP,ji')) + mr(' + ') +
           msub(mr('P'), mr('loss,SOP')) + mr(' = 0'))
add(
    eq_tbl(sop_f1, '(F1)'),
    bp('式中：P_SOP,ij 和 P_SOP,ji 为SOP两侧注入节点i、j的有功功率；P_loss,SOP 为变流器内部损耗，通常建模为二次损耗 a*P_SOP,ij^2 + b。'),
    bp('SOP视在功率容量约束（功率圆约束）：'),
)
sop_f2 = (msup(msub(mr('P'), mr('SOP,ij')), mr('2')) + mr(' + ') +
           msup(msub(mr('Q'), mr('SOP,i')), mr('2')) + mr(' <= ') +
           msup(msub(mr('S'), mr('SOP,max')), mr('2')))
add(
    eq_tbl(sop_f2, '(F2)'),
    bp('SOP可独立控制两侧无功功率（Q_SOP,i 和 Q_SOP,j 各自独立调节），为故障后电压支撑提供额外自由度。故障k发生后新拓扑T^(k)下的电压灵敏度矩阵：'),
)
sop_f3 = (msup(mr('S'), mr('(k)')) + mr(' = LinDistFlow(T') +
           msup(mr(''), mr('(k)')) + mr(')'))
add(
    eq_tbl(sop_f3, '(F3)'),
    bp('在SOP柔性互联下，T^(k)是重构后的联通拓扑而非孤岛拓扑，可直接用LinDistFlow计算新S^(k)，为后续灵敏度重辨识（6.6节）提供解析初始值，实现故障后快速无缝切换。'),
    blank(),
)

# --- 6.3 FIDVR ---
add(
    heading('6.3  故障诱发延迟电压恢复（FIDVR）抑制——文献15', lv=2),
    bp('FIDVR（Fault-Induced Delayed Voltage Recovery，故障诱发延迟电压恢复）是配电网典型故障后电压失稳模式：大量感应电动机在低电压期间堵转，故障切除后吸收大量无功功率，导致电压长时间无法恢复至正常范围。文献15（Park et al., IEEE TPS 2021）利用储能系统（ESS）配合信号时序逻辑（STL）控制律进行FIDVR抑制。'),
    bp('FIDVR检测条件——联合电压幅值与变化率判断：'),
)
fidvr_f4 = (msub(mr('Phi'), mr('FIDVR')) + mr('(t) = 1{V(t) < ') +
             msub(mr('V'), mr('th')) + mr('} AND 1{dV/dt < 0}'))
add(
    eq_tbl(fidvr_f4, '(F4)'),
    bp('式中：V_th 为FIDVR检测阈值，一般取0.85~0.90 p.u.；当电压低于阈值且持续下降时触发FIDVR控制模式，即进入事中阶段储能紧急响应。'),
    bp('STL满足度（robustness metric）——连续可微的电压恢复质量指标：'),
)
stl_f5 = (msup(mr('rho'), mr('phi')) + mr('(t) = ') +
           msub(mr('min'), mr('s in [t, t+T_rec]')) +
           mr('(V(s) - ') + msub(mr('V'), mr('min')) + mr(')'))
add(
    eq_tbl(stl_f5, '(F5)'),
    bp('式中：T_rec 为规定的最大电压恢复时间（典型值2~5 s）；rho^phi(t)>0 表示STL约束满足，值越大恢复裕度越充足。相比硬约束，STL满足度提供连续可微的优化指标，便于与三阶段框架的LP目标函数集成。'),
    bp('ESS紧急控制律（最大化STL满足度，同时约束SOC偏差）：'),
)
ess_f6 = (msup(mr('P'), mr('*')) + msub(mr('ESS'), mr('')) +
           mr('(t) = argmin') + msub(mr(''), mr('P in [P_min,P_max]')) +
           mr('{-rho^phi(t) + lambda_E * (E(t) - ') +
           msub(mr('E'), mr('ref')) + mr(')^2}'))
add(
    eq_tbl(ess_f6, '(F6)'),
    bp('式中：lambda_E 为SOC偏差权重系数，平衡FIDVR抑制与储能能量管理；控制律保证在最大T_rec内将电压恢复至V_min以上，与三阶段框架事中阶段储能快速响应（文献4的LSF驱动调度）在执行层直接对接。'),
    blank(),
)

# --- 6.4 PV LVRT ---
add(
    heading('6.4  PV逆变器短时电压稳定控制——文献23', lv=2),
    bp('文献23（Lammert et al., IEEE TEC 2019）研究PV逆变器对故障后短时电压稳定的贡献机理及控制策略。故障期间PV须满足低电压穿越（LVRT, Low Voltage Ride-Through）要求，通过注入无功电流支撑电压恢复。'),
    bp('LVRT无功电流注入标准（德国VDE-AR-N 4120 / 中国GB/T 19964）：'),
)
lvrt_f7 = (msub(mr('I'), mr('Q,PV')) + mr('(t) = ') +
            msub(mr('k'), mr('LVRT')) + mr(' * max(0, 1 - V(t)/') +
            msub(mr('V'), mr('n')) + mr(') * ') + msub(mr('I'), mr('n')))
add(
    eq_tbl(lvrt_f7, '(F7)'),
    bp('式中：k_LVRT 为无功电流增益，标准要求k_LVRT >= 2（电压每跌落10%额定值，注入10%额定无功电流）；V_n 为额定电压（1 p.u.）；I_n 为PV额定电流。'),
    bp('LVRT控制的短时电压恢复目标：'),
)
lvrt_f8 = (mr('lim') + msub(mr(''), mr('t -> T_rec')) +
            mr(' V(t) >= ') + msub(mr('V'), mr('min')))
add(
    eq_tbl(lvrt_f8, '(F8)'),
    bp('文献23表明：适当增大k_LVRT（超出标准最低要求）能显著提升短时恢复速度，但过大时故障切除瞬间可能发生电压过冲，需与ESS紧急控制联合调优。与三阶段框架的关联：PV的LVRT行为改变故障期有功/无功注入特性，需在P-box不确定集中对故障工况单独建模，区别于正常运行的PV出力区间 [P_min(t), P_max(t)]。'),
    blank(),
)

# --- 6.5 N-1 LP ---
add(
    heading('6.5  N-1安全约束嵌入预规划LP——文献3与文献20', lv=2),
    bp('为使预规划阶段的优化结果在N-1故障下安全可行，需在LP中引入预想故障集约束。设K_N1为N-1预想故障集（各支路单独开断），|K_N1|=|E|（支路总数）。'),
    bp('故障拓扑k下的节点电压约束（确定性N-1约束）：'),
)
n1_f9 = (msub(mr('V'), mr('min')) + mr(' <= ') +
          msub(mr('V'), mr('0')) + mr(' + S') + msup(mr(''), mr('(k)')) +
          mr(' * (') + msub(mr('P'), mr('net')) + mr(' - ') +
          msub(mr('P'), mr('DER')) + mr(') <= ') + msub(mr('V'), mr('max')) +
          mr(',   for all k in K_{N1}'))
add(
    eq_tbl(n1_f9, '(F9)'),
    bp('式中：S^(k) 为故障拓扑T^(k)下的电压灵敏度矩阵（由LinDistFlow预计算离线存储）；P_net(t) 为节点净负荷；P_DER(t) 为DER有功出力。N-1约束将LP约束数量扩大为(|K_N1|+1)倍，可采用预先筛选最严苛预想故障（critical contingency screening）降低计算规模。'),
    bp('分布鲁棒机会约束形式（文献3，Rayati et al., IEEE TSG 2022）——处理故障概率分布不确定性：'),
)
dr_f10 = (mr('inf') + msub(mr(''), mr('P in B_eps(P_hat)')) +
           mr(' Pr(V') + msup(mr(''), mr('(k)')) + mr('_i in [') +
           msub(mr('V'), mr('min')) + mr(', ') + msub(mr('V'), mr('max')) +
           mr(']) >= 1 - alpha,   for all k in K_{N1}'))
add(
    eq_tbl(dr_f10, '(F10)'),
    bp('式中：B_eps(P̂) 为以经验分布P̂为中心、Wasserstein半径eps的概率模糊集；1-alpha 为约束置信水平（典型取0.95~0.99）。最坏概率分布下依然满足电压安全约束，避免过保守的确定性N-1约束带来的不必要削减。'),
    bp('多阶段时间耦合约束（文献20，Guo et al., IEEE TPS 2025）——保证整个调度时域内N-1安全：'),
)
ms_f11 = (mr('V') + msup(mr(''), mr('(k)')) + mr('(t) = V') +
           msup(mr(''), mr('(k)')) + mr('(t-1) + S') +
           msup(mr(''), mr('(k)')) + mr(' * DeltaP(t),') +
           mr('   for all k in K_{N1}, t = 1,...,T'))
add(
    eq_tbl(ms_f11, '(F11)'),
    bp('时间耦合约束确保整个调度时域内各预想故障拓扑均满足电压安全，而非仅当前时刻，这对于水电-储能协同调度（水库容量约束、SOC约束跨时刻耦合）尤为重要。结合Proposition 1的内生储备裕度rho_min(t)，N-1约束可等价为对rho_min(t)的加严要求。'),
    blank(),
)

# --- 6.6 S(t) Re-init ---
add(
    heading('6.6  故障后电压灵敏度矩阵重辨识——文献22扩展', lv=2),
    bp('文献22（Wang et al., IEEE TPS 2024）的在线自适应LSF估计在拓扑不变时具有最优追踪性能，但故障拓扑突变导致S(t)离散跳变，需检测到跳变后立即重辨识，再继续RLS递推。以下为三步重辨识流程。'),
    bp('步骤一：拓扑跳变检测（基于灵敏度矩阵相邻步变化量）：'),
)
jump_f12 = (msub(mr('delta_S'), mr('k')) + mr(' = ||S(k) - S(k-1)||') +
             msub(mr(''), mr('F')) + mr(' > ') + msub(mr('delta'), mr('th')) +
             mr('  =>  拓扑突变，触发重辨识'))
add(
    eq_tbl(jump_f12, '(F12)'),
    bp('式中：||·||_F 为Frobenius范数；delta_th 由正常运行期灵敏度波动方差sigma_S确定（建议delta_th = 3*sigma_S）；检测延迟不超过一个控制周期（1 s），及时触发重辨识，不影响在线调度。'),
    bp('步骤二：最近邻预想故障匹配，灵敏度矩阵重初始化：'),
)
reinit_f13 = (mr('S(t_f+) = ') + msup(msub(mr('S'), mr('0')), mr('(k*)')) +
               mr(',   k* = argmin') + msub(mr(''), mr('k in K_{N1}')) +
               mr(' ||T_meas - T') + msup(mr(''), mr('(k)')) + mr('||') +
               msub(mr(''), mr('F')))
add(
    eq_tbl(reinit_f13, '(F13)'),
    bp('式中：S^(k*)_0 为预想故障k*的LinDistFlow解析灵敏度（预计算离线存储）；T_meas 由量测电流向量估计当前拓扑特征，通过最近邻匹配快速定位开断支路，全过程无需停止在线调度，单步完成初始化。'),
    bp('步骤三：重初始化后继续Tukey鲁棒RLS递推（与文献4式39形式一致，在故障后量测异常期间抑制异常值污染）：'),
)
rls_f14 = (mr('S(t+1) = S(t) + gamma * [DeltaV(t) - S(t)*DeltaP(t)] * ') +
            mfrac(mr('DeltaP(t)^T'),
                  mr('||DeltaP(t)||^2 + eps')))
add(
    eq_tbl(rls_f14, '(F14)'),
    bp('采用Tukey双权鲁棒损失在故障后量测异常期间（电机振荡、保护动作引起测量突跳）抑制其对LSF估计的污染，通常约5~10个控制周期（每步1 s）内S(t)收敛至故障拓扑下的真实灵敏度值，为后续重规划提供准确的S^(k*)。'),
    blank(),
)

# --- 6.7 DR-MPC ---
add(
    heading('6.7  三阶段框架故障扩展综合方案——文献18与文献25', lv=2),
    bp('文献18（Zhang et al., IEEE TSTE 2022）的三阶段层级Volt-Var控制结构与本框架高度对应，且层级设计天然适配故障响应的时间尺度分解：①毫秒级——保护动作（不在本框架范围）；②秒级——储能快速响应（事中阶段，文献15的STL控制律，式F6）；③分钟级——水电重规划（事件触发重规划阶段，引入N-1约束，式F9）。这一时间尺度分解验证了将故障处理分层嵌入现有三阶段框架的合理性，无需重构框架结构。'),
    bp('文献25（Li et al., IEEE TSG 2024）的分布鲁棒MPC将故障视为动态不确定性事件（拓扑跳变随机发生），在预规划时域N内预留弹性裕度。DR-MPC优化目标：'),
)
drmpc_f15 = (mr('min') + msub(mr('_u'), mr('')) + mr('  max') +
              msub(mr(''), mr('P in B_W(P_hat)')) + mr('  E') +
              msub(mr('_P'), mr('')) + mr('[') +
              msub(mr('SUM'), mr('t=k,...,k+N-1')) +
              mr(' l(') + msub(mr('x'), mr('t')) + mr(', ') +
              msub(mr('u'), mr('t')) + mr(')]'))
add(
    eq_tbl(drmpc_f15, '(F15)'),
    bp('式中：B_W(P̂) 为Wasserstein距离球内的概率模糊集，覆盖正常运行不确定性（PV/负荷波动）和低概率故障场景；l(x_t, u_t) 为运行代价（网损+调节成本）。'),
    bp('故障条件下的电压安全概率约束（结合N-1预想故障集，式F10的DR-MPC扩展）：'),
)
fault_cst_f16 = (mr('Pr(') + msub(mr('V'), mr('t')) + mr(' in ') +
                  msub(mr('X'), mr('safe')) + mr(' | T') + msup(mr(''), mr('(k)')) +
                  mr(') >= 1 - ') + msub(mr('alpha'), mr('k')) +
                  mr(',   for all k in K_{N1}, t = 1,...,T'))
add(
    eq_tbl(fault_cst_f16, '(F16)'),
    bp('式中：X_safe = [V_min, V_max]^n 为节点电压安全集合；alpha_k 为第k个预想故障的约束违反容忍率，可按故障严重性分级设置（严重故障alpha_k更小，约束更紧）。DR-MPC通过在Wasserstein球内最大化期望代价，将弹性裕度内嵌至预规划，使三阶段框架在面对低概率故障时具备足够的鲁棒储备。'),
    blank(),
)

# --- 6.8 Comparison Table ---
add(heading('6.8  故障扩展相关文献综合对比', lv=2))
fault_comp_tbl = [
    ['文献（序号）',     '核心技术贡献',           '对应框架扩展环节',   '主要适用场景',      '优先级'],
    ['文献6（Wang）',    'SOP柔性拓扑切换',        '触发机制：故障触发', 'N-1支路开断+重构',  '★★★'],
    ['文献15（Park）',   'ESS+STL的FIDVR抑制',     '事中：储能紧急控制', '感应电机FIDVR',     '★★★'],
    ['文献23（Lammert）','PV逆变器LVRT电压恢复',   'P-box：故障期建模',  '高光伏ADN故障',     '★★★'],
    ['文献22（Wang）',   '自适应RLS灵敏度估计',    '事中：S(t)重辨识',   '拓扑突变失效场景',  '★★'],
    ['文献3（Rayati）',  'DR机会约束弹性优化',     '预规划：N-1概率约束','故障概率不确定',    '★★'],
    ['文献20（Guo）',    '多阶段鲁棒无功优化',     '预规划：N-1时间耦合','水电多时段N-1',     '★★'],
    ['文献18（Zhang）',  '三阶段层级Volt-Var控制', '框架时间尺度分解',   '层级协调故障响应',  '★★'],
    ['文献25（Li）',     'DR-MPC静/动态不确定性',  '预规划：故障动态建模','DR-MPC弹性裕度',   '★★'],
]
add(comp_table(fault_comp_tbl), blank())



# References (extended with fault scenario papers)
add(hr(), heading('参考文献', lv=1))
refs = [
    '[1]  Wang W, Yu N, Gao Y, et al. Safe off-policy deep reinforcement learning algorithm for Volt-VAR control in power distribution systems [J]. IEEE Transactions on Smart Grid, 2020, 11(4): 3008-3018. DOI: 10.1109/TSG.2019.2962625.',
    '[2]  Wang L, Xie L, Yang Y, et al. Distributed online voltage control with fast PV power fluctuations and imperfect communication [J]. IEEE Transactions on Smart Grid, 2023, 14(5): 3398-3411. DOI: 10.1109/TSG.2023.3236724.',
    '[3]  Cao D, Zhao J, Huang Q, et al. Physics-informed graphical representation-enabled deep reinforcement learning for robust distribution system voltage control [J]. IEEE Transactions on Smart Grid, 2024, 15(1): 948-961. DOI: 10.1109/TSG.2023.3267069.',
    '[4]  Wang H, Liang Y, Yao Y, et al. Online model-free DER dispatch via adaptive voltage sensitivity estimation and chance constrained programming [J]. IEEE Transactions on Power Systems, 2024, 39(6): 7317-7330. DOI: 10.1109/TPWRS.2024.3369632.',
    '[5]  Wang B, Yang T, Luo X, et al. Topology-switching soft open point assisted real-time cooperative operation of active distribution networks [J]. Modern Power Systems and Clean Energy, 2024.',
    '[6]  Park B, Yang L, Tompaidis D T, et al. Mitigation of motor stalling and FIDVR via energy storage systems with signal temporal logic [J]. IEEE Transactions on Power Systems, 2021, 36(6): 5241-5252.',
    '[7]  Lammert G, Ospina L F, Pourbeik P, et al. Control of photovoltaic systems for enhanced short-term voltage stability and recovery [J]. IEEE Transactions on Energy Conversion, 2019, 34(1): 243-254.',
    '[8]  Rayati M, Ranjbar A M, Chevalier S, et al. Distributionally robust chance constrained optimization for providing flexibility in an active distribution network [J]. IEEE Transactions on Smart Grid, 2022, 13(6): 4870-4884.',
    '[9]  Guo Z, Liu Z, Tang W, et al. Multi-stage robust reactive power optimization in active distribution networks with discrete intertemporal constraints [J]. IEEE Transactions on Power Systems, 2025, 40(1): 389-402.',
    '[10] Zhang C, Xu Y, Zhao J, et al. Three-stage hierarchically-coordinated voltage/Var control based on PV inverters considering distribution network reconfiguration [J]. IEEE Transactions on Sustainable Energy, 2022, 13(2): 868-881.',
    '[11] Li Q, Gao W, Zhang H, et al. A distributionally robust model predictive control for static and dynamic uncertainties in smart grids [J]. IEEE Transactions on Smart Grid, 2024, 15(3): 2858-2871.',
]
for ref in refs:
    add(para(run(ref, sz=18), align='both', il=360, fi=-360, before=0, after=60))
add(blank())

# Assemble XML
NS = (
    'xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:o="urn:schemas-microsoft-com:office:office" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
    'xmlns:v="urn:schemas-microsoft-com:vml" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:w10="urn:schemas-microsoft-com:office:word" '
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
    'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml"'
)
SECTPR = ('<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
          '<w:pgMar w:top="1701" w:right="1417" w:bottom="1701" w:left="1701"'
          ' w:header="851" w:footer="992" w:gutter="0"/></w:sectPr>')

body_xml = '\n'.join(parts) + SECTPR
doc_xml = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           f'<w:document {NS}><w:body>{body_xml}</w:body></w:document>')

styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults><w:rPrDefault><w:rPr>
    <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"
              w:eastAsia="&#23435;&#20307;" w:cs="Times New Roman"/>
    <w:sz w:val="21"/><w:szCs w:val="21"/>
    <w:lang w:val="en-US" w:eastAsia="zh-CN"/>
  </w:rPr></w:rPrDefault></w:docDefaults>
  <w:style w:type="paragraph" w:styleId="Normal" w:default="1">
    <w:name w:val="Normal"/></w:style>
  <w:style w:type="table" w:styleId="TableNormal">
    <w:name w:val="Normal Table"/>
    <w:tblPr><w:tblInd w:w="0" w:type="dxa"/></w:tblPr>
  </w:style>
</w:styles>'''

settings_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:compat><w:compatSetting w:name="compatibilityMode"'
                ' w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>'
                '</w:compat></w:settings>')

rels_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
            '</Relationships>')

pkg_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')

ct_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
          '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
          '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
          '</Types>')

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', ct_xml)
    z.writestr('_rels/.rels', pkg_rels)
    z.writestr('word/document.xml', doc_xml)
    z.writestr('word/styles.xml', styles_xml)
    z.writestr('word/settings.xml', settings_xml)
    z.writestr('word/_rels/document.xml.rels', rels_xml)

size = os.path.getsize(OUT)
print(f'Generated: {OUT}  ({size:,} bytes)')
print(f'Total parts: {len(parts)}')
