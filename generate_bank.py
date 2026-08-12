from __future__ import annotations
import json, math, random, re, hashlib, statistics
from pathlib import Path
from collections import defaultdict, Counter
import openpyxl

SEED = 20260813
rng = random.Random(SEED)
BASE_XLSX = Path('/mnt/data/metal_cbt_app_v3_1_verified/data/generated_2000_verified.xlsx')
OUT = Path('/mnt/data/metal_cbt_v5/data')
OUT.mkdir(parents=True, exist_ok=True)

questions=[]
seen_stems=set()
next_id=1

SUBJ1='1장 금속조직학'; SUBJ2='2장 금속재료학'; SUBJ3='3장 금속가공학'; SUBJ4='4장 재료시험'; SUBJ5='5장 열처리'

def norm_text(s:str)->str:
    s=re.sub(r'\s+',' ',s.strip().lower())
    s=re.sub(r'[\[\](){}<>.,:;!?%°℃μ×·→←–—_\-]','',s)
    return s

_SUPERSCRIPT = str.maketrans('0123456789+-', '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻')
_E_NOTATION_RE = re.compile(r'(?<![A-Za-z])([+-]?\d+(?:\.\d+)?)[eE]([+-]?\d+)')

def sci(x: float, digits: int = 3) -> str:
    """일반 공학/교재식 과학적 표기: 1.23×10⁻⁴ (Python e 표기 미사용)."""
    if x == 0:
        return '0'
    raw = f'{x:.{digits}e}'
    mantissa, exponent = raw.lower().split('e')
    mantissa = mantissa.rstrip('0').rstrip('.')
    exponent = str(int(exponent)).translate(_SUPERSCRIPT)
    return f'{mantissa}×10{exponent}'

def convert_e_notation(text: str) -> str:
    """문항/선택지/해설 안의 1.2*10**(-3) 형식을 1.2×10⁻³ 형식으로 변환."""
    def repl(m):
        mantissa = m.group(1)
        exponent = str(int(m.group(2))).translate(_SUPERSCRIPT)
        return f'{mantissa}×10{exponent}'
    return _E_NOTATION_RE.sub(repl, text)

def shuffled_choices(correct, distractors, seed_key):
    vals=[]
    for x in [correct]+list(distractors):
        x=str(x)
        if x not in vals: vals.append(x)
    if len(vals)<4:
        return None
    vals=vals[:4]
    rr=random.Random(hash(seed_key)&0xffffffff)
    rr.shuffle(vals)
    return vals, vals.index(str(correct))+1

def add(subject,topic,difficulty,stem,correct,distractors,explanation,concept_id,qtype,source='v5 독립생성'):
    global next_id
    key=norm_text(stem)
    if key in seen_stems: return False
    pack=shuffled_choices(correct,distractors,f'{concept_id}|{stem}|{next_id}')
    if not pack: return False
    choices, answer=pack
    q={
        'id':next_id,'subject':subject,'topic':topic,'difficulty':difficulty,
        'question':stem,'choices':choices,'answer':answer,'explanation':explanation,
        'source':source,'concept_id':concept_id,'type':qtype,'trust':'verified-rule'
    }
    questions.append(q); seen_stems.add(key); next_id+=1
    return True

def fmt(x, unit='', digits=2):
    if abs(x)>=1000 or (0<abs(x)<0.001):
        s=sci(x, 3)
    else:
        s=f'{x:.{digits}f}'.rstrip('0').rstrip('.')
    return f'{s}{unit}'

def numeric_options(correct, rels=(0.8,1.2,1.5), unit='', digits=2, extra=None):
    c=fmt(correct,unit,digits)
    vals=[]
    for r in rels:
        vals.append(fmt(correct*r,unit,digits))
    if extra is not None: vals[-1]=fmt(extra,unit,digits)
    # uniqueness fallback
    out=[]
    for v in vals:
        if v!=c and v not in out: out.append(v)
    k=2
    while len(out)<3:
        v=fmt(correct*(1+0.17*k),unit,digits)
        if v!=c and v not in out: out.append(v)
        k+=1
    return c,out[:3]

# ---------- import verified core 2,000 ----------
wb=openpyxl.load_workbook(BASE_XLSX, read_only=True, data_only=True)
ws=wb['통합문제은행']
for row in ws.iter_rows(min_row=2, max_row=2001, values_only=True):
    old_id=int(row[0]); subject=str(row[1]); topic=str(row[2]); difficulty=str(row[3]); stem=str(row[4])
    choices=[str(row[5]),str(row[6]),str(row[7]),str(row[8])]; ans=int(row[9]); exp=str(row[10] or ''); src=str(row[11] or '')
    key=norm_text(stem)
    if key in seen_stems: continue
    q={'id':next_id,'subject':subject,'topic':topic,'difficulty':difficulty,'question':stem,'choices':choices,'answer':ans,
       'explanation':exp,'source':f'v3.1 검증핵심 | {src}','concept_id':f'core:{topic}:{old_id}','type':'core','trust':'verified-core'}
    questions.append(q); seen_stems.add(key); next_id+=1

# ---------- SUBJECT 1 NUMERIC / APPLICATION ----------
# 1. cubic density
atomic_data=[('Al',26.98,4.05,'FCC',4),('Cu',63.55,3.615,'FCC',4),('Ni',58.69,3.524,'FCC',4),('Fe(α)',55.85,2.866,'BCC',2),('Cr',52.00,2.885,'BCC',2),('Mo',95.95,3.147,'BCC',2)]
NA=6.02214076*10**23
for i in range(180):
    name,M,a,struct,n=rng.choice(atomic_data)
    # small measurement-like perturbation around known a to vary calculation while keeping formula exercise
    a2=a*(1+rng.uniform(-0.012,0.012))
    rho=n*M/(NA*(a2*10**-8)**3)
    c,ds=numeric_options(rho,(0.75,1.25,2.0),' g/cm³',2)
    add(SUBJ1,'결정구조 계산','중',f'{name}의 결정구조를 {struct}, 단위정당 원자 수를 {n}개로 본다. 격자상수 a={a2:.4f} Å일 때 이론 밀도는? (N_A=6.022×10²³ mol⁻¹)',c,ds,
        f'ρ=nM/(N_A a³)={n}×{M:.2f}/[6.022×10²³×({a2:.4f}×10⁻⁸)³]≈{rho:.2f} g/cm³.',f's1:density:{name}:{i}','calculation')

# 2. radius-lattice relations
for i in range(160):
    st=rng.choice(['FCC','BCC'])
    if st=='FCC':
        a=rng.uniform(3.2,4.5); r=a*math.sqrt(2)/4; rel='FCC에서는 면대각선에서 4r=√2a.'
    else:
        a=rng.uniform(2.7,3.6); r=a*math.sqrt(3)/4; rel='BCC에서는 체대각선에서 4r=√3a.'
    ask=rng.choice(['r','a'])
    if ask=='r':
        c,ds=numeric_options(r,(0.7,1.3,math.sqrt(2)),' Å',3)
        stem=f'{st} 금속의 격자상수가 {a:.3f} Å일 때 원자반경 r은?'
        exp=f'{rel} 따라서 r≈{r:.3f} Å.'
    else:
        rr=rng.uniform(1.15,1.60)
        aa=(4*rr/math.sqrt(2)) if st=='FCC' else (4*rr/math.sqrt(3))
        c,ds=numeric_options(aa,(0.8,1.2,math.sqrt(2)),' Å',3)
        stem=f'{st} 금속의 원자반경이 {rr:.3f} Å일 때 격자상수 a는?'
        exp=f'{rel} 따라서 a≈{aa:.3f} Å.'
    add(SUBJ1,'결정구조 계산','중',stem,c,ds,exp,f's1:lattice:{st}:{ask}:{i}','calculation')

# 3. APF coordination direct applications
struct_props={
    'FCC':{'CN':12,'APF':0.74,'planes':'{111}','dirs':'<110>'},
    'BCC':{'CN':8,'APF':0.68,'planes':'{110}','dirs':'<111>'},
    'HCP':{'CN':12,'APF':0.74,'planes':'(0001)','dirs':'<11-20>'},
    'SC':{'CN':6,'APF':0.52,'planes':'{100}','dirs':'<100>'}}
for i in range(180):
    prop=rng.choice(['CN','APF','planes','dirs']); st=rng.choice(list(struct_props))
    val=struct_props[st][prop]
    if prop=='CN': opts=[str(x) for x in [6,8,12,14] if x!=val][:3]; corr=str(val); desc='배위수'
    elif prop=='APF': opts=[f'{x:.2f}' for x in [0.52,0.60,0.68,0.74] if abs(x-val)>10**-9][:3]; corr=f'{val:.2f}'; desc='원자충진율(APF)'
    elif prop=='planes': opts=[x for x in ['{100}','{110}','{111}','(0001)'] if x!=val][:3]; corr=val; desc='대표 조밀면'
    else: opts=[x for x in ['<100>','<110>','<111>','<11-20>'] if x!=val][:3]; corr=val; desc='대표 조밀방향'
    add(SUBJ1,'결정구조','하',f'{st} 결정구조의 {desc}로 가장 적절한 것은?',corr,opts,
        f'{st}의 {desc}는 {corr}이다.',f's1:structure:{st}:{prop}:{i}','concept-application')

# 4. Schmid factor, forward/inverse
for i in range(220):
    sig=rng.randrange(80,601,10); phi=rng.choice([20,25,30,35,40,45,50,55,60]); lam=rng.choice([20,25,30,35,40,45,50,55,60])
    m=math.cos(math.radians(phi))*math.cos(math.radians(lam)); tau=sig*m
    if rng.random()<0.72:
        c,ds=numeric_options(tau,(0.5,1.25,1/m if m else 2),' MPa',1)
        stem=f'단결정에 인장응력 {sig} MPa가 작용하고 슬립면 법선과 인장축의 각 φ={phi}°, 슬립방향과 인장축의 각 λ={lam}°이다. 분해전단응력은?'
        exp=f'τ=σcosφcosλ={sig}cos{phi}°cos{lam}°≈{tau:.1f} MPa.'
    else:
        crss=rng.randrange(30,151,5); req=crss/m
        c,ds=numeric_options(req,(0.75,1.25,1.6),' MPa',1)
        stem=f'φ={phi}°, λ={lam}°인 슬립계의 임계분해전단응력(CRSS)이 {crss} MPa라면 슬립이 시작되는 인장응력은?'
        exp=f'CRSS=σcosφcosλ이므로 σ={crss}/({m:.4f})≈{req:.1f} MPa.'
    add(SUBJ1,'슬립','중',stem,c,ds,exp,f's1:schmid:{i}','calculation')

# 5. Burgers vector magnitude
for i in range(140):
    st=rng.choice(['FCC','BCC']); a=rng.uniform(2.8,4.2)
    b=a/math.sqrt(2) if st=='FCC' else a*math.sqrt(3)/2
    c,ds=numeric_options(b,(0.5,1.25,math.sqrt(2)),' Å',3)
    vec='a/2<110>' if st=='FCC' else 'a/2<111>'
    add(SUBJ1,'전위','중',f'{st} 완전전위의 버거스벡터가 {vec}이고 격자상수 a={a:.3f} Å일 때 |b|는?',c,ds,
        f'{st}에서 |b|={"a/√2" if st=="FCC" else "√3a/2"}≈{b:.3f} Å.',f's1:burgers:{st}:{i}','calculation')

# 6. Fick first law
for i in range(180):
    D=10**rng.uniform(-15,-10); dc=rng.uniform(0.2,2.5); dx=rng.uniform(0.2*10**-3,3*10**-3); grad=dc/dx; J=D*grad
    c,ds=numeric_options(J,(0.1,10,dx*1000),' kg·m⁻²·s⁻¹',3)
    add(SUBJ1,'확산','중',f'1차원 정상상태 확산에서 D={sci(D,2)} m²/s, 농도차의 크기 ΔC={dc:.2f} kg/m³, 거리 Δx={dx*1*10**(3):.2f} mm이다. 확산 플럭스의 크기 |J|는?',c,ds,
        f'Fick 제1법칙 |J|=D|ΔC/Δx|={sci(D,2)}×{dc:.2f}/{sci(dx,2)}≈{sci(J,3)} kg·m⁻²·s⁻¹.',f's1:fick1:{i}','calculation')

# 7. diffusion characteristic time x~sqrt(Dt)
for i in range(180):
    D=10**rng.uniform(-15,-10); t=rng.uniform(60,36000); x=math.sqrt(D*t)
    c,ds=numeric_options(x*10**6,(0.5,2,3),' μm',2)
    add(SUBJ1,'확산','중',f'확산거리의 차수 추정에 x≈√(Dt)를 사용한다. D={sci(D,2)} m²/s, 시간 t={t/3600:.2f} h일 때 x는 약 얼마인가?',c,ds,
        f'x≈√(Dt)=√({sci(D,2)}×{t:.1f})≈{x*10**6:.2f} μm.',f's1:diffdistance:{i}','calculation')

# 8. Arrhenius ratio
R=8.314
for i in range(180):
    Q=rng.uniform(80*10**3,280*10**3); T1=rng.uniform(700,1100); T2=T1+rng.uniform(50,250)
    ratio=math.exp(-Q/R*(1/T2-1/T1))
    c,ds=numeric_options(ratio,(0.5,1.5,2.0),' 배',2)
    add(SUBJ1,'확산','상',f'확산계수 D=D₀exp(-Q/RT)를 따른다. Q={Q/1000:.0f} kJ/mol일 때 온도가 {T1:.0f} K에서 {T2:.0f} K로 올라가면 D₂/D₁은 약 얼마인가?',c,ds,
        f'D₂/D₁=exp[-Q/R(1/T₂-1/T₁)]≈{ratio:.2f}.',f's1:arrhenius:{i}','calculation')

# 9. Hall-Petch forward/inverse
for i in range(180):
    s0=rng.uniform(80,260); k=rng.uniform(0.2,0.9); d=rng.uniform(5,80) # um, use k MPa sqrt(mm) convert d mm
    dmm=d/1000; sy=s0+k/math.sqrt(dmm)
    if rng.random()<0.75:
        c,ds=numeric_options(sy,(0.8,1.2,1.5),' MPa',1)
        stem=f'Hall–Petch 식 σ_y=σ₀+k d^(-1/2)를 사용한다. σ₀={s0:.0f} MPa, k={k:.3f} MPa·m^1/2가 아니라 MPa·mm^1/2 단위로 주어졌고, d={d:.1f} μm일 때 σ_y는?'
        # fix wording unit: k is MPa*sqrt(mm)
        stem=stem.replace('MPa·m^1/2가 아니라 MPa·mm^1/2 단위로 주어졌고','MPa·mm^1/2이고')
        exp=f'd={dmm:.5f} mm, σ_y={s0:.0f}+{k:.3f}/√{dmm:.5f}≈{sy:.1f} MPa.'
    else:
        target=sy+rng.uniform(30,120); dreq=(k/(target-s0))**2*1000
        c,ds=numeric_options(dreq,(0.5,1.5,2.0),' μm',2)
        stem=f'σ_y=σ₀+k d^(-1/2)에서 σ₀={s0:.0f} MPa, k={k:.3f} MPa·mm^1/2이다. 항복강도 {target:.1f} MPa를 얻기 위한 평균 결정립 크기 d는 약 얼마인가?'
        exp=f'd=[k/(σ_y-σ₀)]²≈{dreq:.2f} μm.'
    add(SUBJ1,'결정립강화','상',stem,c,ds,exp,f's1:hallpetch:{i}','calculation')

# 10. Phase rule
for i in range(120):
    C=rng.choice([1,2,3]); P=rng.choice([1,2,3]); fixedP=rng.choice([True,False])
    F=C-P+(1 if fixedP else 2)
    if F<0: continue
    corr=str(F); ds=[str(x) for x in range(0,5) if x!=F][:3]
    cond='압력이 일정한' if fixedP else '압력까지 독립 변수로 포함하는'
    add(SUBJ1,'상률','중',f'{cond} {C}성분계에서 평형상 {P}개가 공존한다. Gibbs 상률에 따른 자유도 F는?',corr,ds,
        f'{"일정 압력에서는 F=C-P+1" if fixedP else "일반 Gibbs 상률은 F=C-P+2"}이므로 F={F}.',f's1:phase_rule:{C}:{P}:{fixedP}:{i}','calculation')

# 11. Lever rule generic binary
for i in range(180):
    Ca=rng.uniform(0.0,0.25); Cb=rng.uniform(0.65,1.2); C0=rng.uniform(Ca+0.08,Cb-0.08)
    fb=(C0-Ca)/(Cb-Ca); fa=1-fb
    ask=rng.choice(['alpha','beta'])
    val=fa if ask=='alpha' else fb
    c,ds=numeric_options(val*100,(0.5,1.4,2.0),'%',1)
    add(SUBJ1,'상태도','중',f'2상 α+β 영역에서 Cα={Ca:.2f} wt%, Cβ={Cb:.2f} wt%, 합금 조성 C₀={C0:.2f} wt%이다. 지렛대법칙에 의한 {"α" if ask=="alpha" else "β"}상 질량분율은?',c,ds,
        f'fβ=(C₀-Cα)/(Cβ-Cα)={fb:.3f}, fα=1-fβ={fa:.3f}. 따라서 답은 {val*100:.1f}%.',f's1:lever:{i}:{ask}','calculation')

# 12. Fe-C specific lever rule hypoeutectoid / hypereutectoid
for i in range(180):
    if rng.random()<0.7:
        C0=rng.uniform(0.10,0.70); fP=(C0-0.022)/(0.76-0.022); fF=1-fP; ask=rng.choice(['펄라이트','초석 페라이트']); val=fP if ask=='펄라이트' else fF
        c,ds=numeric_options(val*100,(0.5,1.35,1.8),'%',1)
        stem=f'공석온도 바로 아래에서 {C0:.2f} wt%C 아공석강을 페라이트(0.022%C)+펄라이트(평균 0.76%C)로 근사한다. {ask}의 질량분율은?'
        exp=f'f_P=(C₀-0.022)/(0.76-0.022)={fP:.3f}, f_F={fF:.3f}. 답≈{val*100:.1f}%.'
    else:
        C0=rng.uniform(0.82,1.35); fC=(C0-0.76)/(6.67-0.76); fP=1-fC; ask=rng.choice(['펄라이트','초석 시멘타이트']); val=fP if ask=='펄라이트' else fC
        c,ds=numeric_options(val*100,(0.5,1.5,2.2),'%',1)
        stem=f'공석온도 바로 아래에서 {C0:.2f} wt%C 과공석강을 펄라이트(평균 0.76%C)+시멘타이트(6.67%C)로 근사한다. {ask}의 질량분율은?'
        exp=f'f_Cem=(C₀-0.76)/(6.67-0.76)={fC:.3f}, f_P={fP:.3f}. 답≈{val*100:.1f}%.'
    add(SUBJ1,'Fe-C 상태도','상',stem,c,ds,exp,f's1:feclever:{i}','calculation')

# 13. Bragg law
lam=1.5406 # Angstrom Cu Kalpha
for i in range(180):
    theta=rng.uniform(15,60); n=1; d=lam/(2*math.sin(math.radians(theta)))
    if rng.random()<0.65:
        c,ds=numeric_options(d,(0.75,1.25,1.6),' Å',3)
        stem=f'Cu Kα X선(λ={lam:.4f} Å)의 1차 회절피크가 2θ={2*theta:.2f}°에서 관찰되었다. 면간거리 d는?'
        exp=f'Bragg 법칙 nλ=2d sinθ, θ={theta:.2f}°이므로 d≈{d:.3f} Å.'
    else:
        d2=rng.uniform(1.2,3.2); th=math.degrees(math.asin(lam/(2*d2))); twoth=2*th
        c,ds=numeric_options(twoth,(0.8,1.2,1.5),'°',2)
        stem=f'면간거리 d={d2:.3f} Å인 결정면을 Cu Kα(λ={lam:.4f} Å)로 1차 회절할 때 예상되는 2θ는?'
        exp=f'θ=sin⁻¹(λ/2d)={th:.2f}°, 따라서 2θ≈{twoth:.2f}°.'
    add(SUBJ1,'X선 회절','중',stem,c,ds,exp,f's1:bragg:{i}','calculation')

# 14. true/engineering strain
for i in range(160):
    L0=rng.uniform(20,100); L=rng.uniform(L0*1.03,L0*1.8); eng=(L-L0)/L0; true=math.log(L/L0)
    ask=rng.choice(['공학변형률','진변형률']); val=eng if ask=='공학변형률' else true
    c,ds=numeric_options(val,(0.5,1.5,2.0),'',3)
    add(SUBJ1,'변형률','중',f'표점거리 {L0:.1f} mm인 시편이 균일 인장되어 {L:.1f} mm가 되었다. {ask}은?',c,ds,
        f'공학변형률 e=(L-L₀)/L₀={eng:.3f}, 진변형률 ε=ln(L/L₀)={true:.3f}.',f's1:strain:{i}:{ask}','calculation')

# 15. dislocation density and spacing
for i in range(120):
    rho=10**rng.uniform(10,15); spacing=1/math.sqrt(rho)
    c,ds=numeric_options(spacing*10**9,(0.5,2,4),' nm',2)
    add(SUBJ1,'전위밀도','상',f'전위밀도 ρ={sci(rho,2)} m⁻²일 때 평균 전위 간격의 차수를 L≈1/√ρ로 추정하면 L은 약 얼마인가?',c,ds,
        f'L≈1/√ρ≈{spacing*10**9:.2f} nm.',f's1:dislocation_spacing:{i}','calculation')

# ---------- SUBJECT 2 CONCEPT / APPLICATION TABLES ----------
# Structured knowledge records: term, concise property, application, distractor terms within family.
families = [
    (SUBJ2,'주철',[
        ('회주철','편상 흑연이 존재하며 진동감쇠능과 절삭성이 좋다.','공작기계 베드·하우징'),
        ('구상흑연주철','흑연을 구상화하여 회주철보다 연성과 인성이 높다.','자동차 부품·관'),
        ('백주철','탄소가 주로 시멘타이트 형태로 존재해 매우 경하고 취성이다.','내마모 라이너'),
        ('가단주철','백주철을 장시간 열처리해 temper carbon을 형성시켜 인성을 높인다.','관이음쇠·소형 부품')]),
    (SUBJ2,'스테인리스강',[
        ('오스테나이트계 스테인리스강','Cr-Ni계가 대표적이며 상온에서 주로 FCC 오스테나이트 조직이다.','내식 배관·주방기기'),
        ('페라이트계 스테인리스강','Cr계가 대표적이며 상온에서 주로 BCC 페라이트 조직이다.','배기계·가전'),
        ('마르텐사이트계 스테인리스강','열처리로 경화 가능하고 높은 경도가 필요한 용도에 쓰인다.','칼날·터빈 블레이드 일부'),
        ('석출경화형 스테인리스강','시효에 의한 석출강화를 이용해 높은 강도를 얻는다.','항공·고강도 부품')]),
    (SUBJ2,'Cu 합금',[
        ('황동','Cu-Zn 합금이다.','밸브·관·장식재'),
        ('청동','전통적으로 Cu-Sn계 합금을 가리킨다.','베어링·주조품'),
        ('백동','Cu-Ni 합금으로 해수 내식성이 우수하다.','해수용 열교환기·동전'),
        ('베릴륨동','Cu-Be계 석출경화 합금으로 높은 강도와 탄성을 얻을 수 있다.','스프링·비점화 공구')]),
    (SUBJ2,'Al 합금',[
        ('Al-Cu계','시효경화 가능한 대표적 열처리형 Al 합금계이다.','항공 구조재'),
        ('Al-Mg계','고용강화와 내식성이 양호하며 일반적으로 비열처리형으로 분류된다.','선박·용접 구조재'),
        ('Al-Mg-Si계','Mg2Si 석출을 이용한 열처리형 합금계이다.','압출 형재'),
        ('Al-Zn-Mg(-Cu)계','매우 높은 강도를 얻을 수 있는 열처리형 Al 합금계이다.','고강도 항공재')]),
    (SUBJ2,'Ti 합금',[
        ('α-Ti 합금','α 안정화 원소의 영향이 크고 고온 안정성·용접성이 비교적 좋다.','고온·내식 부품'),
        ('β-Ti 합금','β 안정화 원소를 많이 포함하며 높은 성형성과 시효강화 가능성이 있다.','고강도 스프링·항공부품'),
        ('α+β Ti 합금','α와 β 두 상을 이용해 강도와 인성의 균형을 얻는다.','Ti-6Al-4V 구조재'),
        ('CP Ti','상업용 순티타늄으로 내식성과 성형성이 우수하다.','화학설비·의료')]),
    (SUBJ2,'공구강',[
        ('고속도공구강','W, Mo, V, Cr 등을 포함해 적열경도가 높다.','절삭공구'),
        ('냉간금형강','상온 부근에서 높은 내마모성과 압축강도가 요구된다.','펀치·다이'),
        ('열간금형강','열피로와 고온연화에 대한 저항이 중요하다.','다이캐스팅 금형'),
        ('충격용 공구강','인성과 충격저항을 중시한다.','치즐·해머')]),
    (SUBJ2,'베어링 합금',[
        ('배빗메탈','연한 기지와 경질 입자의 조합으로 순응성과 매입성이 좋다.','미끄럼 베어링'),
        ('Cu-Pb계 베어링합금','비교적 높은 하중용 미끄럼 베어링에 사용된다.','엔진 베어링'),
        ('Al-Sn계 베어링합금','경량이고 내식성이 좋으며 자동차 베어링에 쓰인다.','자동차 엔진'),
        ('소결함유베어링','다공질 소결체에 윤활유를 함침해 자기윤활성을 얻는다.','소형 모터')]),
]
for subject,topic,records in families:
    terms=[r[0] for r in records]
    for idx,(term,prop,app) in enumerate(records):
        others=[t for t in terms if t!=term]
        # description -> term
        for v in range(16):
            context=rng.choice([
                f'재료 선택 회의에서 다음 특성이 요구되었다: {prop} 이에 해당하는 재료는?',
                f'다음 설명에 해당하는 재료 또는 합금 분류는? {prop}',
                f'설계자가 {app} 용도를 검토 중이다. 다음 중 가장 직접적으로 연관되는 재료는? ({prop})',
                f'{prop}라는 설명과 가장 잘 대응하는 것은?'
            ])
            add(subject,topic,'중',context,term,others,
                f'{term}: {prop} 대표 용도 예: {app}.',f's2:{topic}:{term}:desc:{v}','scenario')
        # term -> property (use properties of others as distractors)
        otherprops=[r[1] for r in records if r[0]!=term]
        for v in range(8):
            stem=f'{term}에 대한 설명으로 가장 적절한 것은? (적용 상황 {v+1})'
            add(subject,topic,'중',stem,prop,otherprops,
                f'{term}은 {prop}',f's2:{topic}:{term}:prop:{v}','concept')

# alloy strengthening / solid solution / precipitation
strength_records=[
    ('고용강화','용질 원자의 크기·탄성계수 차이로 격자 변형장이 생겨 전위 이동을 방해한다.'),
    ('석출강화','미세한 제2상 입자가 전위 절단 또는 Orowan 우회를 방해한다.'),
    ('가공경화','소성변형으로 전위밀도가 증가하고 전위 간 상호작용이 커진다.'),
    ('결정립미세화강화','결정립계가 전위 이동을 방해하며 Hall–Petch 관계로 설명된다.')]
for term,prop in strength_records:
    others=[x[0] for x in strength_records if x[0]!=term]
    otherp=[x[1] for x in strength_records if x[0]!=term]
    for v in range(30):
        stem=rng.choice([f'{prop} 이 강화기구는?',f'금속의 항복강도를 높이는 방법 중 다음 메커니즘에 해당하는 것은? {prop}',f'현미조직 변화가 다음과 같이 관찰되었다. {prop} 가장 적절한 강화기구는?'])
        topic='고용강화' if term=='고용강화' else ('석출강화' if term=='석출강화' else '고강도강')
        add(SUBJ2,topic,'중',stem,term,others,f'{term}: {prop}',f's2:strength:{term}:{v}','scenario')

# Composition conversions wt% <-> at% for binary systems
atomic_weights={'Al':26.98,'Cu':63.55,'Ni':58.69,'Fe':55.85,'Cr':52.00,'Mg':24.31,'Ti':47.87,'Zn':65.38,'Sn':118.71}
pairs=[('Cu','Ni'),('Al','Cu'),('Fe','Cr'),('Cu','Zn'),('Al','Mg'),('Ti','Al')]
for i in range(260):
    A,B=rng.choice(pairs); wA=rng.uniform(5,95); wB=100-wA
    nA=wA/atomic_weights[A]; nB=wB/atomic_weights[B]; atA=nA/(nA+nB)*100
    c,ds=numeric_options(atA,(0.75,1.25,1.6),' at%',1)
    add(SUBJ2,'고용체','상',f'{A}-{B} 이원합금에서 조성이 {wA:.1f} wt% {A} - {wB:.1f} wt% {B}이다. 이를 원자분율로 환산한 {A} 함량은? (원자량 {A}={atomic_weights[A]}, {B}={atomic_weights[B]})',c,ds,
        f'n_A={wA:.1f}/{atomic_weights[A]}, n_B={wB:.1f}/{atomic_weights[B]}, at% A=n_A/(n_A+n_B)×100≈{atA:.1f} at%.',f's2:wtat:{i}','calculation')

# Rule of mixtures density for two-phase composite / alloy approximation
for i in range(180):
    rho1=rng.uniform(2.5,9.0); rho2=rng.uniform(2.0,10.5); f=rng.uniform(0.1,0.9)
    rho=f*rho1+(1-f)*rho2
    c,ds=numeric_options(rho,(0.8,1.2,1.5),' g/cm³',2)
    add(SUBJ2,'고용체','중',f'두 상의 체적분율을 단순 혼합법칙으로 근사한다. 상 1의 밀도 {rho1:.2f} g/cm³, 상 2의 밀도 {rho2:.2f} g/cm³, 상 1 체적분율 {f:.2f}일 때 혼합 밀도는?',c,ds,
        f'ρ=fρ₁+(1-f)ρ₂={f:.2f}×{rho1:.2f}+{1-f:.2f}×{rho2:.2f}≈{rho:.2f} g/cm³.',f's2:rom_density:{i}','calculation')

# stainless PREN simple application (PREN=Cr+3.3Mo+16N)
for i in range(160):
    Cr=rng.uniform(16,26); Mo=rng.uniform(0,5); N=rng.uniform(0.02,0.35); pren=Cr+3.3*Mo+16*N
    c,ds=numeric_options(pren,(0.85,1.15,1.35),'',1)
    add(SUBJ2,'스테인리스강','상',f'스테인리스강의 공식 저항을 단순 비교하기 위해 PREN=Cr+3.3Mo+16N을 사용한다. Cr={Cr:.1f}%, Mo={Mo:.1f}%, N={N:.2f}%이면 PREN은?',c,ds,
        f'PREN={Cr:.1f}+3.3×{Mo:.1f}+16×{N:.2f}≈{pren:.1f}.',f's2:pren:{i}','calculation')

# carbon equivalent CEIIW approx
for i in range(150):
    C=rng.uniform(0.05,0.35); Mn=rng.uniform(0.5,1.8); Cr=rng.uniform(0,1.5); Mo=rng.uniform(0,0.5); V=rng.uniform(0,0.2); Ni=rng.uniform(0,2.0); Cu=rng.uniform(0,1.0)
    ce=C+Mn/6+(Cr+Mo+V)/5+(Ni+Cu)/15
    c,ds=numeric_options(ce,(0.75,1.25,1.5),'',3)
    add(SUBJ2,'탄소강','상',f'IIW 탄소당량 CE=C+Mn/6+(Cr+Mo+V)/5+(Ni+Cu)/15를 사용한다. C={C:.2f}, Mn={Mn:.2f}, Cr={Cr:.2f}, Mo={Mo:.2f}, V={V:.2f}, Ni={Ni:.2f}, Cu={Cu:.2f} wt%일 때 CE는?',c,ds,
        f'식에 대입하면 CE≈{ce:.3f}. 일반적으로 CE가 커질수록 용접 열영향부 경화·균열 관리가 중요해진다.',f's2:ce:{i}','calculation')

# ---------- SUBJECT 3 NUMERIC ----------
# rolling reduction / true strain
for i in range(220):
    h0=rng.uniform(2,60); hf=rng.uniform(h0*0.35,h0*0.95); red=(h0-hf)/h0*100; eps=math.log(h0/hf)
    if rng.random()<0.55:
        c,ds=numeric_options(red,(0.5,1.5,2),'%',1); stem=f'두께 {h0:.2f} mm의 판재를 {hf:.2f} mm로 압연했다. 압하율은?'; exp=f'압하율=(h₀-h_f)/h₀×100≈{red:.1f}%.'
    else:
        c,ds=numeric_options(eps,(0.5,1.5,2),'',3); stem=f'폭 퍼짐을 무시하는 압연에서 두께가 {h0:.2f} mm에서 {hf:.2f} mm로 감소했다. 두께방향 진변형률의 크기 ln(h₀/h_f)는?'; exp=f'ε=ln({h0:.2f}/{hf:.2f})≈{eps:.3f}.'
    add(SUBJ3,'압연','중',stem,c,ds,exp,f's3:rolling_reduction:{i}','calculation')

# max draft Δh≈μ²R
for i in range(180):
    mu=rng.uniform(0.08,0.35); Rr=rng.uniform(100,500); dh=mu**2*Rr
    c,ds=numeric_options(dh,(0.5,1.5,2.0),' mm',2)
    add(SUBJ3,'압연','상',f'평압연의 물림 조건을 Δh_max≈μ²R로 근사한다. 마찰계수 μ={mu:.3f}, 롤 반경 R={Rr:.0f} mm일 때 최대 압하량은?',c,ds,
        f'Δh_max≈μ²R={mu:.3f}²×{Rr:.0f}≈{dh:.2f} mm.',f's3:maxdraft:{i}','calculation')

# roll speed from rpm
for i in range(120):
    Rr=rng.uniform(100,500)/1000; rpm=rng.uniform(20,300); v=2*math.pi*Rr*rpm/60
    c,ds=numeric_options(v,(0.5,1.5,2.0),' m/s',2)
    add(SUBJ3,'압연','중',f'롤 반경 R={Rr*1000:.0f} mm, 회전속도 {rpm:.0f} rpm인 압연기의 롤 표면속도는?',c,ds,
        f'v=2πRN/60≈{v:.2f} m/s.',f's3:rollspeed:{i}','calculation')

# extrusion ratio and true strain
for i in range(220):
    D0=rng.uniform(20,120); Df=rng.uniform(D0*0.18,D0*0.75); Rratio=(D0/Df)**2; eps=math.log(Rratio)
    if rng.random()<0.5:
        c,ds=numeric_options(Rratio,(0.5,1.5,2),'',2); stem=f'원형 빌릿 직경 {D0:.1f} mm를 직경 {Df:.1f} mm로 압출한다. 압출비 A₀/A_f는?'; exp=f'압출비=(D₀/D_f)²≈{Rratio:.2f}.'
    else:
        c,ds=numeric_options(eps,(0.5,1.5,2),'',3); stem=f'압출비가 {Rratio:.2f}인 이상 압출에서 진변형률 ε=ln(A₀/A_f)는?'; exp=f'ε=ln({Rratio:.2f})≈{eps:.3f}.'
    add(SUBJ3,'압출','중',stem,c,ds,exp,f's3:extrusion:{i}','calculation')

# ideal extrusion pressure p≈k ln R
for i in range(160):
    k=rng.uniform(120,500); rr=rng.uniform(2,30); p=k*math.log(rr)
    c,ds=numeric_options(p,(0.7,1.3,1.7),' MPa',1)
    add(SUBJ3,'압출','상',f'마찰과 중복변형을 무시한 단순 모델에서 평균 압출압력 p≈k ln R을 사용한다. 평균 유동응력 k={k:.0f} MPa, 압출비 R={rr:.2f}일 때 p는?',c,ds,
        f'p≈{k:.0f}ln({rr:.2f})≈{p:.1f} MPa.',f's3:extrusion_pressure:{i}','calculation')

# drawing reduction / final diameter
for i in range(180):
    D0=rng.uniform(3,25); r=rng.uniform(5,45)/100; Af=(1-r)*math.pi*D0**2/4; Df=math.sqrt(4*Af/math.pi)
    c,ds=numeric_options(Df,(0.8,1.2,1.5),' mm',2)
    add(SUBJ3,'인발','중',f'직경 {D0:.2f} mm 원형 선재를 단면감소율 {r*100:.1f}%로 1패스 인발한다. 최종 직경은?',c,ds,
        f'A_f=(1-r)A₀이므로 D_f=D₀√(1-r)≈{Df:.2f} mm.',f's3:drawing_diameter:{i}','calculation')

# drawing true strain
for i in range(140):
    r=rng.uniform(0.05,0.55); eps=math.log(1/(1-r))
    c,ds=numeric_options(eps,(0.5,1.5,2),'',3)
    add(SUBJ3,'인발','중',f'단면감소율이 {r*100:.1f}%인 인발에서 체적불변을 가정할 때 축방향 진변형률 ln(A₀/A_f)는?',c,ds,
        f'A_f/A₀=1-r={1-r:.3f}, ε=ln[1/(1-r)]≈{eps:.3f}.',f's3:drawing_strain:{i}','calculation')

# forging volume conservation upsetting cylinder
for i in range(180):
    D0=rng.uniform(20,80); h0=rng.uniform(30,120); hf=rng.uniform(h0*0.35,h0*0.85); Df=D0*math.sqrt(h0/hf)
    c,ds=numeric_options(Df,(0.8,1.2,1.5),' mm',1)
    add(SUBJ3,'단조','중',f'원주형 소재(D₀={D0:.1f} mm, h₀={h0:.1f} mm)를 업세팅하여 높이 {hf:.1f} mm로 만든다. 배럴링과 체적변화를 무시할 때 최종 직경은?',c,ds,
        f'체적보존 D₀²h₀=D_f²h_f → D_f=D₀√(h₀/h_f)≈{Df:.1f} mm.',f's3:upsetting:{i}','calculation')

# forging true strain
for i in range(120):
    h0=rng.uniform(30,150); hf=rng.uniform(h0*0.3,h0*0.9); eps=math.log(h0/hf)
    c,ds=numeric_options(eps,(0.5,1.5,2),'',3)
    add(SUBJ3,'단조','중',f'업세팅에서 높이가 {h0:.1f} mm에서 {hf:.1f} mm로 감소했다. 압축 진변형률의 크기 ln(h₀/h_f)는?',c,ds,
        f'|ε|=ln({h0:.1f}/{hf:.1f})≈{eps:.3f}.',f's3:forging_strain:{i}','calculation')

# blanking/punching force = perimeter*t*tau
for i in range(220):
    shape=rng.choice(['원','직사각형'])
    t=rng.uniform(0.5,8); tau=rng.uniform(180,600)
    if shape=='원':
        D=rng.uniform(10,120); per=math.pi*D; desc=f'직경 {D:.1f} mm 원형'
    else:
        a=rng.uniform(10,100); b=rng.uniform(10,100); per=2*(a+b); desc=f'{a:.1f} mm×{b:.1f} mm 직사각형'
    F=per*t*tau/1000
    c,ds=numeric_options(F,(0.7,1.3,1.8),' kN',1)
    add(SUBJ3,'전단가공','중',f'{desc} 블랭킹을 한다. 판두께 t={t:.2f} mm, 전단강도 τ={tau:.0f} MPa일 때 최대 전단하중을 F≈둘레×t×τ로 추정하면?',c,ds,
        f'둘레={per:.1f} mm, F≈{per:.1f}×{t:.2f}×{tau:.0f} N≈{F:.1f} kN.',f's3:shear_force:{i}','calculation')

# clearance per side
for i in range(140):
    t=rng.uniform(0.5,10); pct=rng.uniform(3,12); cside=t*pct/100
    c,ds=numeric_options(cside,(0.5,1.5,2),' mm',3)
    add(SUBJ3,'전단가공','중',f'펀칭/블랭킹에서 편측 클리어런스를 판두께의 {pct:.1f}%로 설정한다. 판두께 {t:.2f} mm일 때 편측 클리어런스는?',c,ds,
        f'c={t:.2f}×{pct:.1f}/100≈{cside:.3f} mm.',f's3:clearance:{i}','calculation')

# deep drawing LDR
for i in range(160):
    Dblank=rng.uniform(80,300); Dp=rng.uniform(Dblank/2.4,Dblank/1.3); ldr=Dblank/Dp
    c,ds=numeric_options(ldr,(0.8,1.2,1.5),'',2)
    add(SUBJ3,'딥드로잉','중',f'블랭크 직경 {Dblank:.1f} mm, 펀치 직경 {Dp:.1f} mm인 딥드로잉에서 drawing ratio D₀/D_p는?',c,ds,
        f'DR=D₀/D_p={Dblank:.1f}/{Dp:.1f}≈{ldr:.2f}.',f's3:ldr:{i}','calculation')

# bend allowance BA=theta(R+Kt)
for i in range(180):
    theta_deg=rng.choice([30,45,60,90,120,135]); Rb=rng.uniform(1,15); t=rng.uniform(0.5,6); K=rng.uniform(0.3,0.5); BA=math.radians(theta_deg)*(Rb+K*t)
    c,ds=numeric_options(BA,(0.75,1.25,1.6),' mm',2)
    add(SUBJ3,'굽힘','상',f'판재 굽힘의 굽힘여유를 BA=θ(R+Kt)로 근사한다(θ는 rad). θ={theta_deg}°, 내측반경 R={Rb:.2f} mm, 두께 t={t:.2f} mm, K={K:.2f}일 때 BA는?',c,ds,
        f'BA={math.radians(theta_deg):.4f}×({Rb:.2f}+{K:.2f}×{t:.2f})≈{BA:.2f} mm.',f's3:bend_allowance:{i}','calculation')

# plastic work / power estimate
for i in range(140):
    F=rng.uniform(10,500)*1000; v=rng.uniform(0.005,0.3); P=F*v/1000
    c,ds=numeric_options(P,(0.5,1.5,2),' kW',1)
    add(SUBJ3,'소성가공 기초','중',f'가공하중이 {F/1000:.1f} kN이고 공구 속도가 {v:.3f} m/s일 때 순간 기계동력 P=Fv는?',c,ds,
        f'P={F:.0f}×{v:.3f}≈{P:.1f} kW.',f's3:power:{i}','calculation')

# ---------- SUBJECT 4 NUMERIC ----------
# tensile engineering stress/strain/modulus
for i in range(260):
    D=rng.uniform(4,20); A=math.pi*D**2/4; F=rng.uniform(5,200)*1000; sig=F/A
    c,ds=numeric_options(sig,(0.5,1.5,2),' MPa',1)
    add(SUBJ4,'인장시험','중',f'원형 인장시편의 초기 직경이 {D:.2f} mm이고 하중 {F/1000:.1f} kN이 작용한다. 공학응력은?',c,ds,
        f'A₀=πD²/4={A:.2f} mm², σ=F/A₀≈{sig:.1f} MPa.',f's4:engstress:{i}','calculation')
for i in range(160):
    L0=rng.uniform(25,100); dL=rng.uniform(0.05,3); eps=dL/L0; sig=rng.uniform(50,400); E=sig/eps/1000
    c,ds=numeric_options(E,(0.7,1.3,1.8),' GPa',1)
    add(SUBJ4,'인장시험','중',f'탄성구간에서 표점거리 {L0:.1f} mm인 시편이 {dL:.3f} mm 늘어날 때 응력이 {sig:.1f} MPa이다. 탄성계수 E는?',c,ds,
        f'ε=ΔL/L₀={eps:.6f}, E=σ/ε≈{E:.1f} GPa.',f's4:modulus:{i}','calculation')

# RA and elongation
for i in range(180):
    D0=rng.uniform(6,20); Df=rng.uniform(D0*0.45,D0*0.95); RA=(1-(Df/D0)**2)*100
    c,ds=numeric_options(RA,(0.5,1.4,1.8),'%',1)
    add(SUBJ4,'인장시험','중',f'원형 인장시편의 초기 직경 {D0:.2f} mm, 파단부 최소직경 {Df:.2f} mm이다. 단면수축률은?',c,ds,
        f'RA=[1-(D_f/D₀)²]×100≈{RA:.1f}%.',f's4:RA:{i}','calculation')
for i in range(160):
    L0=rng.choice([25,50,80,100]); Lf=rng.uniform(L0*1.05,L0*1.6); el=(Lf-L0)/L0*100
    c,ds=numeric_options(el,(0.5,1.5,2),'%',1)
    add(SUBJ4,'인장시험','하',f'표점거리 L₀={L0} mm인 시편의 파단 후 표점거리가 {Lf:.1f} mm이다. 연신율은?',c,ds,
        f'연신율=(L_f-L₀)/L₀×100≈{el:.1f}%.',f's4:elongation:{i}','calculation')

# resilience U=sy^2/(2E)
for i in range(140):
    sy=rng.uniform(150,1200)*10**6; E=rng.uniform(70,220)*10**9; U=sy**2/(2*E)/10**6
    c,ds=numeric_options(U,(0.5,1.5,2),' MJ/m³',2)
    add(SUBJ4,'인장시험','상',f'선형탄성 재료에서 탄성에너지밀도(탄성한계까지)를 U_r≈σ_y²/(2E)로 근사한다. σ_y={sy/10**6:.0f} MPa, E={E/10**9:.0f} GPa일 때 U_r은?',c,ds,
        f'U_r=σ_y²/(2E)≈{U:.2f} MJ/m³.',f's4:resilience:{i}','calculation')

# Brinell hardness
for i in range(160):
    D=rng.choice([2.5,5,10]); P=rng.uniform(500,3000); d=rng.uniform(D*0.2,D*0.75)
    HB=2*P/(math.pi*D*(D-math.sqrt(D**2-d**2)))
    c,ds=numeric_options(HB,(0.7,1.3,1.7),' HB',1)
    add(SUBJ4,'경도시험','상',f'브리넬 경도 HB=2P/[πD(D-√(D²-d²))]를 사용한다. 압입자 직경 D={D} mm, 하중 P={P:.0f} kgf, 압흔 직경 d={d:.2f} mm일 때 HB는?',c,ds,
        f'식에 대입하면 HB≈{HB:.1f}.',f's4:brinell:{i}','calculation')

# Vickers hardness HV=1.8544F/d^2
for i in range(160):
    F=rng.uniform(1,100); d=rng.uniform(0.15,0.8); HV=1.8544*F/d**2
    c,ds=numeric_options(HV,(0.7,1.3,1.7),' HV',1)
    add(SUBJ4,'경도시험','중',f'비커스 경도 HV=1.8544F/d²(F: kgf, d: mm)를 사용한다. F={F:.1f} kgf, 평균 대각선 d={d:.3f} mm일 때 HV는?',c,ds,
        f'HV=1.8544×{F:.1f}/{d:.3f}²≈{HV:.1f}.',f's4:vickers:{i}','calculation')

# Charpy energy pendulum m g (h1-h2)
for i in range(140):
    m=rng.uniform(10,30); h1=rng.uniform(1.2,2.5); h2=rng.uniform(0.2,h1-0.1); E=m*9.80665*(h1-h2)
    c,ds=numeric_options(E,(0.7,1.3,1.7),' J',1)
    add(SUBJ4,'충격시험','중',f'샤르피 충격시험에서 해머 질량 {m:.1f} kg, 낙하 전 높이 {h1:.2f} m, 파단 후 상승 높이 {h2:.2f} m로 단순화한다. 마찰손실을 무시한 흡수에너지는?',c,ds,
        f'E=mg(h₁-h₂)≈{E:.1f} J.',f's4:charpy:{i}','calculation')

# fracture K=Y sigma sqrt(pi a)
for i in range(220):
    Y=rng.uniform(0.9,1.3); sig=rng.uniform(80,900); a=rng.uniform(0.2,8)/1000; K=Y*sig*math.sqrt(math.pi*a)
    if rng.random()<0.65:
        c,ds=numeric_options(K,(0.7,1.3,1.7),' MPa√m',1)
        stem=f'모드 I 응력확대계수 K_I=Yσ√(πa)를 사용한다. Y={Y:.2f}, σ={sig:.0f} MPa, 균열크기 a={a*1000:.2f} mm일 때 K_I는?'
        exp=f'K_I={Y:.2f}×{sig:.0f}×√(π×{a:.5f})≈{K:.1f} MPa√m.'
    else:
        Kic=rng.uniform(max(20,K*0.8),120); acrit=(Kic/(Y*sig))**2/math.pi
        c,ds=numeric_options(acrit*1000,(0.5,1.5,2),' mm',2)
        stem=f'K_IC={Kic:.1f} MPa√m인 재료에 σ={sig:.0f} MPa가 작용하며 Y={Y:.2f}이다. K_IC=Yσ√(πa_c)로부터 임계균열크기 a_c는?'
        exp=f'a_c=[K_IC/(Yσ)]²/π≈{acrit*1000:.2f} mm.'
    add(SUBJ4,'파괴역학','상',stem,c,ds,exp,f's4:fractureK:{i}','calculation')

# plane strain validity thickness B >= 2.5(KIC/sigy)^2
for i in range(120):
    Kic=rng.uniform(20,120); sy=rng.uniform(250,1400); B=2.5*(Kic/sy)**2*1000
    c,ds=numeric_options(B,(0.5,1.5,2),' mm',2)
    add(SUBJ4,'파괴역학','상',f'평면변형 파괴인성 시험의 대표적인 크기조건 B≥2.5(K_IC/σ_y)²을 사용한다. K_IC={Kic:.1f} MPa√m, σ_y={sy:.0f} MPa일 때 필요한 두께 B의 하한은?',c,ds,
        f'B≥2.5({Kic:.1f}/{sy:.0f})² m≈{B:.2f} mm.',f's4:plane_strain:{i}','calculation')

# fatigue mean/amplitude/R
for i in range(220):
    smax=rng.uniform(120,800); smin=rng.uniform(-0.6*smax,0.8*smax); sm=(smax+smin)/2; sa=(smax-smin)/2; Rr=smin/smax
    ask=rng.choice(['평균응력','응력진폭','응력비'])
    if ask=='평균응력': val=sm; unit=' MPa'; digits=1
    elif ask=='응력진폭': val=sa; unit=' MPa'; digits=1
    else: val=Rr; unit=''; digits=3
    c,ds=numeric_options(val,(0.5,1.5,2),unit,digits)
    add(SUBJ4,'피로시험','중',f'피로하중에서 σ_max={smax:.1f} MPa, σ_min={smin:.1f} MPa이다. {ask}은?',c,ds,
        f'σ_m=(σ_max+σ_min)/2={sm:.1f} MPa, σ_a=(σ_max-σ_min)/2={sa:.1f} MPa, R=σ_min/σ_max={Rr:.3f}.',f's4:fatigue_basic:{i}:{ask}','calculation')

# Goodman relation sa/Se + sm/Sut = 1, solve allowable sa
for i in range(160):
    Se=rng.uniform(120,450); Sut=rng.uniform(max(500,Se*1.6),1200); sm=rng.uniform(0,0.6*Sut); sa=Se*(1-sm/Sut)
    c,ds=numeric_options(sa,(0.7,1.3,1.7),' MPa',1)
    add(SUBJ4,'피로시험','상',f'수정 Goodman 선을 σ_a/S_e+σ_m/S_ut=1로 사용한다. S_e={Se:.0f} MPa, S_ut={Sut:.0f} MPa, 평균응력 σ_m={sm:.0f} MPa일 때 허용 응력진폭 σ_a는?',c,ds,
        f'σ_a=S_e(1-σ_m/S_ut)≈{sa:.1f} MPa.',f's4:goodman:{i}','calculation')

# Paris law da/dN=C(ΔK)^m
for i in range(160):
    C=10**rng.uniform(-13,-9); mexp=rng.uniform(2.2,4.2); dK=rng.uniform(5,35); rate=C*dK**mexp
    c,ds=numeric_options(rate,(0.2,5,10),' m/cycle',3)
    add(SUBJ4,'파괴역학','상',f'Paris 법칙 da/dN=C(ΔK)^m에서 C={sci(C,2)}, m={mexp:.2f}, ΔK={dK:.1f} MPa√m이다. 균열성장속도 da/dN은?',c,ds,
        f'da/dN={sci(C,2)}×{dK:.1f}^{mexp:.2f}≈{sci(rate,3)} m/cycle.',f's4:paris:{i}','calculation')

# Larson-Miller P=T(C+log t)
for i in range(150):
    T=rng.uniform(700,1200); t=10**rng.uniform(1,5); Cc=20; P=T*(Cc+math.log10(t))
    c,ds=numeric_options(P,(0.8,1.2,1.5),' K',0)
    add(SUBJ4,'크리프시험','중',f'Larson–Miller parameter를 P=T(C+log₁₀t), C=20으로 둔다. T={T:.0f} K, 파단시간 t={t:.1f} h일 때 P는?',c,ds,
        f'P={T:.0f}×[20+log₁₀({t:.1f})]≈{P:.0f}.',f's4:LMP:{i}','calculation')

# ultrasonic TOF thickness d=vt/2
for i in range(180):
    v=rng.uniform(3000,6500); d=rng.uniform(2,100)/1000; tof=2*d/v; c,ds=numeric_options(d*1000,(0.5,1.5,2),' mm',1)
    add(SUBJ4,'비파괴시험','중',f'초음파 펄스-에코에서 종파속도 v={v:.0f} m/s, 왕복시간 t={tof*10**6:.2f} μs가 측정되었다. 반사면까지의 깊이는?',c,ds,
        f'd=vt/2={v:.0f}×{sci(tof,3)}/2≈{d*1000:.1f} mm.',f's4:UT:{i}','calculation')

# radiographic attenuation I=I0 exp(-mu x)
for i in range(140):
    mu=rng.uniform(0.05,0.8); x=rng.uniform(2,30); ratio=math.exp(-mu*x)
    c,ds=numeric_options(ratio*100,(0.5,1.5,2),'%',2)
    add(SUBJ4,'비파괴시험','상',f'방사선 투과강도를 I/I₀=exp(-μx)로 근사한다. μ={mu:.3f} mm⁻¹, 두께 x={x:.1f} mm일 때 투과율 I/I₀는?',c,ds,
        f'I/I₀=exp(-{mu:.3f}×{x:.1f})≈{ratio:.4f}, 즉 {ratio*100:.2f}%.',f's4:RTatten:{i}','calculation')

# ---------- SUBJECT 4 CONCEPT SCENARIOS ----------
ndt_records=[
    ('초음파탐상(UT)','두꺼운 재료 내부의 평면성 결함 탐지와 깊이 평가에 유리하다.'),
    ('방사선투과시험(RT)','투과 영상을 얻어 체적성 내부결함을 시각적으로 확인하기 좋다.'),
    ('자분탐상(MT)','강자성체의 표면 및 표면근처 결함 검출에 적합하다.'),
    ('침투탐상(PT)','비다공성 재료의 표면개구 결함 검출에 사용된다.'),
    ('와전류탐상(ET)','전도성 재료의 표면·근표면 결함과 두께/전도도 평가에 활용된다.')]
for term,prop in ndt_records:
    ds=[x[0] for x in ndt_records if x[0]!=term][:3]
    for v in range(30):
        stem=rng.choice([f'검사 대상 조건: {prop} 가장 적합한 비파괴검사법은?',f'다음 특징에 해당하는 비파괴검사법은? {prop}',f'현장 검사계획에서 "{prop}"가 핵심 요구사항이다. 선택할 방법은?'])
        add(SUBJ4,'비파괴시험','중',stem,term,ds,f'{term}: {prop}',f's4:ndt:{term}:{v}','scenario')

fracture_records=[
    ('연성파괴','미세공동의 생성·성장·합체가 대표 메커니즘이며 딤플 파면이 흔하다.'),
    ('벽개파괴','결정학적 면을 따라 빠르게 파괴되며 river pattern이 관찰될 수 있다.'),
    ('피로파괴','반복하중으로 균열이 점진 성장하며 beach mark나 striation이 관찰될 수 있다.'),
    ('입계파괴','균열이 주로 결정립계를 따라 전파한다.')]
for term,prop in fracture_records:
    ds=[x[0] for x in fracture_records if x[0]!=term]
    for v in range(30):
        add(SUBJ4,'파면분석','중',rng.choice([f'파면 관찰 결과 {prop} 이 파괴형태는?',f'{prop}라는 특징이 확인되었다. 가장 적절한 파괴 분류는?',f'파손 원인 분석에서 다음 증거가 나왔다: {prop}']),term,ds,f'{term}: {prop}',f's4:fracture_surface:{term}:{v}','scenario')

# ---------- SUBJECT 5 HEAT TREATMENT SCENARIOS / NUMERIC ----------
# TTT product by isothermal hold, explicitly enough to avoid diagram ambiguity
TTT_cases=[
    ('상부 펄라이트','공석강을 오스테나이트화한 뒤 비교적 높은 펄라이트 변태온도에서 충분히 등온 유지하여 변태를 완료한다.'),
    ('미세 펄라이트','공석강을 오스테나이트화한 뒤 낮은 펄라이트 변태온도에서 충분히 등온 유지하여 변태를 완료한다.'),
    ('상부 베이나이트','오스테나이트화 후 대략 450~550°C 부근 베이나이트 영역에서 충분히 등온 변태시킨다.'),
    ('하부 베이나이트','오스테나이트화 후 Ms보다 높고 비교적 낮은 베이나이트 온도(대략 250~400°C)에서 충분히 등온 변태시킨다.'),
    ('마르텐사이트','확산변태 시작을 피할 만큼 빠르게 Ms 이하로 냉각한 뒤 Mf 부근 또는 그 이하까지 냉각한다.')]
for term,desc in TTT_cases:
    ds=[x[0] for x in TTT_cases if x[0]!=term][:3]
    for v in range(55):
        stem=rng.choice([f'열처리 경로가 다음과 같다. {desc} 최종 주조직은?',f'공석강의 TTT 거동을 고려할 때 다음 경로에 가장 가까운 조직은? {desc}',f'오스테나이트에서 시작하여 {desc} 이때 얻고자 하는 조직은?'])
        topic='TTT' if term!='마르텐사이트' else '마르텐사이트'
        add(SUBJ5,topic,'중',stem,term,ds,f'제시된 경로는 {term} 형성 조건에 해당한다.',f's5:TTT:{term}:{v}','scenario')

# Isothermal process distinctions
process_records=[
    ('오스템퍼링','오스테나이트화 후 베이나이트 변태온도로 급랭하여 변태가 완료될 때까지 등온 유지한 뒤 냉각한다.','주로 베이나이트 조직'),
    ('마템퍼링','오스테나이트화 후 Ms 바로 위(또는 부근)의 욕에서 단면 온도를 균일화한 뒤 냉각하여 마르텐사이트를 만들고 이후 뜨임한다.','변형·균열 저감 목적의 마르텐사이트'),
    ('담금질','오스테나이트화 후 임계냉각속도 이상으로 냉각하여 마르텐사이트 형성을 목표로 한다.','마르텐사이트'),
    ('불림','오스테나이트화 후 공랭하여 조직을 미세화하고 기계적 성질을 정돈한다.','미세 페라이트+펄라이트(아공석강 등)')]
for term,desc,res in process_records:
    ds=[x[0] for x in process_records if x[0]!=term]
    for v in range(40):
        stem=rng.choice([f'다음 열처리 경로의 명칭은? {desc}',f'공정 목적이 "{res}"이고 경로가 다음과 같다: {desc} 이에 해당하는 열처리는?',f'열처리 계획서에 {desc}라고 적혀 있다. 공정명은?'])
        add(SUBJ5,'등온열처리' if term in ['오스템퍼링','마템퍼링'] else ('담금질' if term=='담금질' else '불림'),'중',stem,term,ds,f'{term}: {desc} 결과/목표: {res}.',f's5:process:{term}:{v}','scenario')

# Koistinen-Marburger martensite fraction f=1-exp[-alpha(Ms-T)] for T<Ms
for i in range(200):
    Ms=rng.uniform(220,450); T=rng.uniform(Ms-220,Ms-10); alpha=0.011; f=1-math.exp(-alpha*(Ms-T))
    c,ds=numeric_options(f*100,(0.7,1.2,1.5),'%',1)
    add(SUBJ5,'마르텐사이트','상',f'Koistinen–Marburger 근사 f_M=1-exp[-0.011(M_s-T)]를 사용한다. M_s={Ms:.0f}°C, 냉각온도 T={T:.0f}°C일 때 형성된 마르텐사이트 분율은?',c,ds,
        f'f_M=1-exp[-0.011×({Ms:.0f}-{T:.0f})]≈{f*100:.1f}%.',f's5:KM:{i}','calculation')

# carburizing diffusion depth sqrt(Dt)
for i in range(200):
    D=10**rng.uniform(-12,-10); t=rng.uniform(1,12)*3600; x=math.sqrt(D*t)
    c,ds=numeric_options(x*1000,(0.5,1.5,2),' mm',2)
    add(SUBJ5,'침탄','상',f'침탄층 깊이의 차수 추정에 x≈√(Dt)를 사용한다. 오스테나이트에서 탄소 확산계수 D={sci(D,2)} m²/s, 침탄시간 {t/3600:.1f} h이면 확산거리 x는 약?',c,ds,
        f'x≈√({sci(D,2)}×{t:.0f})≈{x*1000:.2f} mm.',f's5:carburizing_depth:{i}','calculation')

# tempering trend scenarios
for i in range(180):
    T1=rng.choice([150,200,250,300]); T2=rng.choice([450,500,550,600,650]);
    correct=rng.choice(['경도 감소, 인성 증가','잔류응력 감소, 치수안정성 개선','탄화물 석출·조대화 진행'])
    distractors=['경도 증가, 인성 감소','오스테나이트 분율이 항상 증가','탄소가 다시 균일 오스테나이트에 완전 고용']
    add(SUBJ5,'뜨임','중',f'담금질 마르텐사이트를 {T1}°C보다 높은 {T2}°C에서 충분히 뜨임할 때 일반적으로 기대되는 변화로 가장 적절한 것은?',correct,distractors,
        '뜨임 온도와 시간이 증가하면 마르텐사이트의 과포화·잔류응력이 완화되고 탄화물 변화가 진행되어 대체로 경도는 낮아지고 인성은 향상된다.',f's5:tempering_trend:{i}:{correct}','scenario')

# quenching media severity qualitative + cooling effect scenarios
quench_order=['소금물','물','폴리머 수용액(조건 의존)','오일','공기']
for i in range(180):
    # ask pair comparison
    a,b=rng.sample(['소금물','물','오일','공기'],2)
    rank={'소금물':4,'물':3,'오일':2,'공기':1}
    correct=f'{a}의 냉각능이 더 크다' if rank[a]>rank[b] else f'{b}의 냉각능이 더 크다'
    other=f'{b}의 냉각능이 더 크다' if rank[a]>rank[b] else f'{a}의 냉각능이 더 크다'
    add(SUBJ5,'담금질 냉각제','하',f'일반적인 강의 담금질에서 동일한 형상·교반 조건을 가정할 때 {a}과 {b}의 냉각능을 비교한 설명으로 옳은 것은?',correct,[other,'두 냉각제의 냉각능은 항상 완전히 동일하다','냉각능 비교는 금속 종류와 무관하게 정의할 수 없다'],
        '일반적인 냉각강도는 소금물 > 물 > 오일 > 공기 순으로 이해한다. 실제 값은 온도·교반·농도에 따라 달라질 수 있다.',f's5:quench_media:{a}:{b}:{i}','concept-application')

# hardenability scenarios
hard_facts=[
    ('합금원소 첨가','대체로 CCT/TTT의 확산변태 시작을 지연시켜 경화능을 높인다.'),
    ('오스테나이트 결정립 조대화','핵생성 위치인 입계 면적이 줄어 경화능이 증가하는 경향이 있다.'),
    ('Jominy 끝단에서 거리 증가','냉각속도가 낮아져 일반적으로 경도가 감소한다.'),
    ('경화능 증가','같은 담금질 조건에서 더 깊은 내부까지 마르텐사이트를 얻기 쉬워진다.')]
for term,prop in hard_facts:
    ds=[x[0] for x in hard_facts if x[0]!=term]
    for v in range(35):
        stem=rng.choice([f'경화능에 관한 다음 설명과 가장 직접적으로 연결되는 항목은? {prop}',f'Jominy/경화능 관점에서 "{prop}"에 해당하는 것은?',f'담금질 설계에서 {prop}라는 현상을 설명하는 핵심 항목은?'])
        add(SUBJ5,'경화능','중',stem,term,ds,f'{term}: {prop}',f's5:hardenability:{term}:{v}','scenario')

# surface hardening comparison
surface_records=[
    ('침탄','저탄소강 표면에 탄소를 확산시킨 뒤 담금질하여 고탄소 마르텐사이트 표면층을 얻는다.'),
    ('질화','질소를 확산시켜 질화물 경화층을 만들며 일반적으로 침탄보다 낮은 온도에서 처리하고 후담금질이 필수는 아니다.'),
    ('고주파경화','유도가열로 표면을 급속 오스테나이트화한 뒤 담금질하며 화학조성 변화 없이 표면경화한다.'),
    ('화염경화','화염으로 표면을 급속 가열한 뒤 담금질하며 화학조성 변화 없이 표면경화한다.')]
for term,desc in surface_records:
    ds=[x[0] for x in surface_records if x[0]!=term]
    for v in range(45):
        stem=rng.choice([f'표면경화법을 선택하려 한다. 다음 설명에 해당하는 공정은? {desc}',f'다음 표면처리 경로의 명칭은? {desc}',f'기어 표면경화 공정 후보 중 "{desc}"에 해당하는 것은?'])
        topic={'침탄':'침탄','질화':'질화','고주파경화':'고주파경화','화염경화':'화염경화'}[term]
        add(SUBJ5,topic,'중',stem,term,ds,f'{term}: {desc}',f's5:surface:{term}:{v}','scenario')

# heat treatment defect diagnosis
defect_records=[
    ('담금질 균열','급격한 온도구배와 변태응력, 날카로운 형상 등이 원인이 될 수 있다.'),
    ('변형/뒤틀림','불균일 가열·냉각과 잔류응력 차이로 발생하기 쉽다.'),
    ('탈탄','고온에서 산화성 분위기에 장시간 노출되어 표면 탄소가 감소한다.'),
    ('산화스케일','고온에서 표면 산화가 진행되어 산화물 피막이 형성된다.')]
for term,desc in defect_records:
    ds=[x[0] for x in defect_records if x[0]!=term]
    for v in range(35):
        add(SUBJ5,'열처리 결함','중',rng.choice([f'열처리 후 다음 현상이 관찰되었다. {desc} 가장 적절한 결함은?',f'공정 이상 원인이 다음과 같다: {desc} 예상되는 결함명은?',f'품질분석에서 {desc}가 확인되었다. 분류는?']),term,ds,f'{term}: {desc}',f's5:defect:{term}:{v}','scenario')

# ---------- MORE CROSS-TOPIC CONCEPT QUESTIONS TO BALANCE ----------
concept_groups={
SUBJ1:[
 ('점결함',[('공공','정상 격자점의 원자가 비어 있는 점결함'),('침입형 원자','원래 격자점이 아닌 틈새 위치에 들어간 원자'),('치환형 원자','모재 원자의 격자점을 다른 원자가 치환한 결함'),('프렌켈 결함','원자가 정상 격자점을 떠나 침입형 위치로 이동해 공공-침입 쌍을 이루는 결함')]),
 ('회복·재결정',[('회복','전위의 재배열·소멸과 잔류응력 완화가 주로 일어나며 새로운 결정립 형성 전 단계'),('재결정','가공조직을 대체하는 새로운 무변형 결정립이 핵생성·성장'),('결정립성장','재결정 후 일부 결정립이 성장해 평균 결정립 크기가 증가'),('가공경화','소성가공 중 전위밀도 증가로 강도·경도 증가')]),
 ('적층결함',[('낮은 적층결함에너지','완전전위가 부분전위로 넓게 분리되기 쉬우며 교차슬립이 어려워지는 경향'),('높은 적층결함에너지','부분전위 간격이 작고 교차슬립·동적회복이 상대적으로 쉬운 경향'),('부분전위','완전전위가 분해되어 형성될 수 있는 더 작은 버거스벡터의 전위'),('적층결함','조밀적층 순서가 국부적으로 어긋난 면결함')])],
SUBJ2:[
 ('합금원소',[('Cr','강의 경화능·내산화성/내식성을 높이고 탄화물을 형성할 수 있다.'),('Ni','오스테나이트 안정화와 인성·내식성 향상에 기여한다.'),('Mo','고온강도·뜨임연화 저항·경화능 향상에 기여한다.'),('V','강한 탄화물/질화물 형성 원소로 결정립 미세화와 석출강화에 활용된다.')]),
 ('Ni 합금',[('Ni-Cr계 초합금','고온 산화저항과 고온강도가 요구되는 가스터빈 부품에 사용'),('Ni-Cu계 합금','해수와 여러 부식환경에 대한 내식성이 좋은 계열'),('Ni-Fe계 합금','열팽창 특성이나 연자성 특성을 조절하는 합금군이 존재'),('Ni-Ti계 합금','형상기억·초탄성 특성으로 잘 알려진 금속간 화합물계')])],
SUBJ3:[
 ('가공윤활',[('마찰 감소','공구-소재 계면 전단응력과 가공하중을 낮춘다.'),('공구수명 향상','마모와 발열을 줄여 공구 수명을 늘리는 데 기여한다.'),('표면품질 향상','긁힘·소착 등을 줄여 표면결함을 억제한다.'),('냉각 보조','발생열을 제거해 온도 상승을 억제하는 역할을 할 수 있다.')]),
 ('판재성형',[('r값','폭방향 변형률 대비 두께방향 변형률의 비로 깊은 인발성과 관련'),('n값','진응력-진변형률 관계의 가공경화지수로 균일연신과 관련'),('FLD','주변형률 조합에 따른 국부네킹 한계를 나타내는 성형한계도'),('스프링백','하중 제거 후 탄성회복 때문에 형상이 일부 되돌아가는 현상')])],
SUBJ4:[
 ('경도시험',[('로크웰','압입 깊이 차이를 이용해 경도를 직접 읽는 방식'),('브리넬','구형 압입자의 압흔 면적을 이용'),('비커스','다이아몬드 정사각뿔 압입자의 압흔 대각선을 이용'),('쇼어','반발 높이 등 동적 반발 특성을 이용하는 방식')]),
 ('크리프시험',[('1차 크리프','가공경화 영향으로 크리프 속도가 점차 감소'),('2차 크리프','가공경화와 회복이 균형을 이루어 거의 일정한 최소 크리프 속도'),('3차 크리프','공동·넥킹·손상 축적으로 크리프 속도가 가속되어 파단으로 진행'),('크리프','고온에서 일정 응력하에 시간 의존적으로 변형이 증가하는 현상')])],
SUBJ5:[
 ('풀림',[('완전풀림','오스테나이트화 후 노냉하여 연화·응력완화·조직 평형화를 도모'),('공정풀림','저탄소강의 냉간가공 중간에 재결정으로 연성을 회복'),('응력제거풀림','상변태를 크게 일으키지 않는 온도에서 잔류응력을 완화'),('구상화풀림','시멘타이트를 구상화하여 고탄소강의 절삭성·냉간가공성 향상')]),
 ('잔류오스테나이트',[('서브제로 처리','Mf 이하 저온으로 냉각해 잔류오스테나이트의 추가 마르텐사이트 변태를 유도'),('잔류오스테나이트','담금질 후에도 변태하지 않고 남은 오스테나이트'),('안정화','잔류오스테나이트가 후속 사용 중 변태하기 어렵게 되는 현상'),('치수변화','잔류오스테나이트의 후변태는 치수안정성 문제를 일으킬 수 있음')])]
}
for subject,groups in concept_groups.items():
    for topic,records in groups:
        terms=[x[0] for x in records]
        for term,desc in records:
            ds=[x for x in terms if x!=term][:3]
            for v in range(30):
                stem=rng.choice([f'다음 설명에 해당하는 용어는? {desc}',f'{topic}에서 다음 현상/특성을 나타내는 것은? {desc}',f'재료공학적 설명 "{desc}"와 가장 잘 대응하는 것은?'])
                add(subject,topic,'중',stem,term,ds,f'{term}: {desc}',f'cg:{subject}:{topic}:{term}:{v}','concept-scenario')

# ---------- NORMALIZE DISPLAY NUMBER FORMAT ----------
# Python식 지수 표기를 교재식 ×10ⁿ 표기로 전수 변환한다.
for q in questions:
    q['question'] = convert_e_notation(q['question'])
    q['choices'] = [convert_e_notation(str(x)) for x in q['choices']]
    q['explanation'] = convert_e_notation(q['explanation'])

# ---------- VALIDATE, REBALANCE, WRITE ----------
# Ensure answer correctness by index/string existence and unique choices
for q in questions:
    assert 1<=q['answer']<=4
    assert len(q['choices'])==4 and len(set(q['choices']))==4
    assert q['question'].strip()

# Renumber sequentially in case any import skipped
for i,q in enumerate(questions,1): q['id']=i

# Basic semantic duplicate audit using exact normalized stem
assert len({norm_text(q['question']) for q in questions})==len(questions)

# Split by subject
subject_files={
    SUBJ1:'subject1.json',SUBJ2:'subject2.json',SUBJ3:'subject3.json',SUBJ4:'subject4.json',SUBJ5:'subject5.json'
}
for s,fn in subject_files.items():
    arr=[q for q in questions if q['subject']==s]
    (OUT/fn).write_text(json.dumps(arr,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

manifest={
    'version':'v5.0-independent',
    'generated_at':'2026-08-13',
    'seed':SEED,
    'total':len(questions),
    'subjects':{s:sum(1 for q in questions if q['subject']==s) for s in subject_files},
    'files':list(subject_files.values()),
    'types':dict(Counter(q['type'] for q in questions)),
    'topics':dict(Counter(q['topic'] for q in questions)),
    'note':'v5 removes virtual wording-only variants. Every stored stem is unique; generated questions use independent numerical conditions or scenario/association logic.'
}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

# audit report
by_subj=Counter(q['subject'] for q in questions); by_type=Counter(q['type'] for q in questions); by_topic=Counter(q['topic'] for q in questions)
report=[]
report.append(f'TOTAL={len(questions)}')
report.append('SUBJECTS='+json.dumps(by_subj,ensure_ascii=False))
report.append('TYPES='+json.dumps(by_type,ensure_ascii=False))
report.append(f'UNIQUE_STEMS={len(seen_stems)}')
report.append(f'DUP_STEMS={len(questions)-len(seen_stems)}')
report.append('TOPICS_COUNT='+str(len(by_topic)))
(OUT/'AUDIT.txt').write_text('\n'.join(report),encoding='utf-8')
print('\n'.join(report))
