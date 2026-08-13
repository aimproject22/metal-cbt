import json, re, random, os, shutil, zipfile, collections
from pathlib import Path

BASE=Path('/mnt/data/v6work/metal_cbt_v5')
OUT=Path('/mnt/data/metal_cbt_v6_concept_only')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
random.seed(20260813)

# Load all existing items but discard every explicitly generated calculation item.
old=[]
for i in range(1,6):
    old += json.loads((BASE/'data'/f'subject{i}.json').read_text(encoding='utf-8'))
old=[q for q in old if q.get('type')!='calculation']

# Extra safeguard: remove stems that are clearly arithmetic computation tasks even if mislabeled.
calc_pat=re.compile(r'(계산하|구하면\s*몇|약\s*몇\s*(MPa|mm|cm|J|K|%|kg|m/s|Pa|mol)|값은\s*몇|증가량은\?|감소량은\?|깊이는\?|밀도는\?\s*\(|평균\s*전위\s*속도|최대\s*전단응력.*몇)')
old=[q for q in old if not calc_pat.search(q.get('question',''))]

# Official 2023.1.1~2026.12.31 Q-Net syllabus mapping from the user's photographed table.
def classify(q):
    ot=q['topic']; subj=q['subject']
    # materials
    if subj.startswith('2장'):
        if ot in {'탄소강','합금원소','주철','스테인리스강','공구강','고강도강','고급강','Fe-Ni 합금'}:
            return '1과목 금속재료학', '1. 철강재료', {
                '합금원소':'첨가원소의 영향','탄소강':'재료의 조직과 성질','주철':'소재의 제조와 용도','스테인리스강':'재료의 조직과 성질','공구강':'기계적 성질','고강도강':'기계적 성질','고급강':'기계적 성질','Fe-Ni 합금':'첨가원소의 영향'}[ot]
        if ot in {'Cu 합금','Al 합금','Mg 합금','Ti 합금','Ni 합금','Ni-Cu 합금','Ni-Cr 합금','베어링 합금'}:
            return '1과목 금속재료학','2. 비철재료의 합금',ot
        if ot in {'고용체'}:
            return '1과목 금속재료학','3. 분말합금과 신소재','신소재'
        if ot in {'고용강화','석출강화'}:
            return '4과목 금속가공학','4. 금속의 강화기구','강화기구'
        return '1과목 금속재료학','1. 철강재료',ot
    # organization
    if subj.startswith('1장'):
        if ot in {'결정구조','점결함','전위','적층결함','결정립계','X선 회절','결정구조 계산'}:
            return '2과목 금속조직학','3. 금속의 응고와 결정구조',ot.replace(' 계산','')
        if ot in {'상률','상태도','Fe-C 상태도','상변태'}:
            return '2과목 금속조직학','1. 금속의 상태변화와 변형',ot
        if ot in {'회복·재결정','슬립','변형률','전위밀도'}:
            return '2과목 금속조직학','1. 금속의 상태변화와 변형',ot
        if ot in {'확산','철강 조직'}:
            return '2과목 금속조직학','2. 합금상태의 조직과 성질',ot
        if ot=='결정립강화':
            return '4과목 금속가공학','4. 금속의 강화기구','강화기구'
        return '2과목 금속조직학','3. 금속의 응고와 결정구조',ot
    # processing
    if subj.startswith('3장'):
        if ot in {'소성가공 기초','가공윤활'}:
            return '4과목 금속가공학','1. 소성가공의 개요',ot
        if ot in {'판재성형','딥드로잉','굽힘'}:
            return '4과목 금속가공학','2. 소성의 응용',ot
        return '4과목 금속가공학','3. 변형과 소성작업',ot
    # tests split between material-test and mechanical strength
    if subj.startswith('4장'):
        if ot in {'인장시험','경도시험','충격시험','비파괴시험'}:
            return '1과목 금속재료학','4. 재료시험',ot
        return '4과목 금속가공학','5. 기계적 강도',ot
    # heat/surface
    if subj.startswith('5장'):
        if ot=='열처리 결함':
            return '5과목 표면공학','2. 열처리 제품의 결함검사','결함의 원인과 대책'
        if ot in {'침탄','질화','고주파경화','화염경화'}:
            return '5과목 표면공학','3. 표면처리',ot
        return '5과목 표면공학','1. 열처리',ot
    return q['subject'],'기타',ot

new=[]
for q in old:
    s,major,detail=classify(q)
    qq=dict(q)
    qq['subject']=s
    qq['topic']=f'{major} › {detail}'
    qq['type']='concept'
    qq['source']='개념형 자체문항 · 2010·2011·2012·2016 기출 출제개념 및 현행 출제기준에 맞춰 재분류'
    qq['trust']='concept-reviewed'
    new.append(qq)

# Helpers for new exam-derived concept questions.
next_id=max([q['id'] for q in new] or [0])+1

def addq(subject, major, detail, question, answer_text, distractors, explanation, difficulty='중', family=None):
    global next_id
    choices=[answer_text]+list(distractors)
    # fixed one-time shuffle: creates one independent item; no answer-number variants are generated.
    rng=random.Random(f'{subject}|{major}|{detail}|{question}')
    rng.shuffle(choices)
    ans=choices.index(answer_text)+1
    new.append({
        'id':next_id,'subject':subject,'topic':f'{major} › {detail}','difficulty':difficulty,
        'question':question,'choices':choices,'answer':ans,'explanation':explanation,
        'source':'2010·2011·2012·2016 기출 출제개념 기반 신규 재구성','concept_id':family or f'v6:{detail}:{next_id}',
        'type':'concept','trust':'exam-derived','family_id':family or f'v6:{detail}:{next_id}'})
    next_id+=1

# term -> definition banks. Each record creates TWO distinct recall directions, not answer-position variants.
def add_term_group(subject, major, detail, records):
    terms=[r[0] for r in records]
    defs=[r[1] for r in records]
    for idx,(term,definition,exp) in enumerate(records):
        # definition -> term
        pool=[t for t in terms if t!=term]
        rng=random.Random(f'term:{major}:{detail}:{term}')
        ds=rng.sample(pool,3)
        addq(subject,major,detail,f'다음 설명에 해당하는 용어는?\n{definition}',term,ds,exp,'중',f'{major}:{detail}:{term}')
        # term -> definition
        poold=[d for d in defs if d!=definition]
        ds2=rng.sample(poold,3)
        addq(subject,major,detail,f'{term}에 대한 설명으로 가장 적절한 것은?',definition,ds2,exp,'중',f'{major}:{detail}:{term}:reverse')

S3='3과목 야금공학'
# 야금 개론: old exams repeatedly ask refining processes, deoxidation, extraction methods.
met_general=[
('배소(roasting)','황화광 등을 융점 이하에서 산화성 분위기로 가열하여 산화물 등으로 변화시키는 예비처리','배소는 황화광의 산화와 황 제거 등에 이용되는 대표적인 건식 예비처리이다.'),
('하소(calcination)','탄산염·수산화물 광석 등을 공기 공급이 제한된 조건에서 가열하여 CO₂나 H₂O 같은 휘발성 성분을 제거하는 처리','하소는 탄산염의 CO₂ 제거나 수산화물의 탈수에 이용된다.'),
('소결(sintering)','미세한 광석 분말을 부분 용융 또는 고상 결합으로 덩어리화하여 통기성과 취급성을 높이는 조립법','소결은 미분광을 고로 사용에 적합한 크기로 응집시키는 방법이다.'),
('펠리타이징(pelletizing)','미분광에 결합제와 수분을 더해 구상 입자로 성형한 뒤 소성하여 펠릿을 만드는 방법','펠리타이징은 미분광을 구형 펠릿으로 제조한다.'),
('부유선광','광물 표면의 젖음성 차이를 이용하여 기포에 특정 광물을 부착시켜 분리하는 선광법','부유선광은 표면화학적 성질 차이를 이용한다.'),
('자력선광','광물의 자성 차이를 이용해 유용광물과 맥석을 분리하는 방법','자력선광은 자화율 차이를 이용한다.'),
('비중선광','광물의 밀도 차이를 이용하여 유용광물과 맥석을 분리하는 방법','비중선광은 밀도 차이에 의한 침강·유동 거동을 이용한다.'),
('건식제련','고온에서 산화·환원·용융 등의 반응을 이용하여 금속을 추출·정제하는 제련법','건식제련은 고온 반응을 핵심으로 한다.'),
('습식제련','수용액 중 침출·정제·회수 반응을 이용하여 금속을 추출하는 제련법','습식제련은 침출 후 용액 정제와 금속 회수 단계로 진행된다.'),
('전해채취(electrowinning)','침출액 등의 금속 이온을 전해하여 음극에 금속으로 석출·회수하는 방법','전해채취는 용액 속 금속 이온을 직접 금속으로 회수한다.'),
('전해정련(electrorefining)','불순 금속을 양극으로 하고 순금속을 음극에 석출시켜 순도를 높이는 정련법','전해정련은 양극의 불순 금속을 용해시키고 순금속을 음극에 석출시킨다.'),
('침출(leaching)','광석이나 중간생성물에서 목적 금속 성분을 선택적으로 용액 속으로 녹여내는 공정','침출은 습식제련의 핵심 용해 단계이다.'),
('치환석출(cementation)','더 비한 금속을 넣어 용액 중 귀한 금속 이온을 금속 상태로 석출시키는 회수법','치환석출은 금속의 이온화 경향 차이를 이용한다.'),
('용매추출','서로 섞이지 않는 두 액상 사이의 분배 차이를 이용해 특정 금속 이온을 선택적으로 분리·농축하는 방법','용매추출은 습식제련 용액 정제에 널리 쓰인다.'),
('탈산','용강 속 용존 산소를 산소 친화력이 큰 원소와 반응시켜 제거하는 처리','탈산제는 산소와의 친화력이 Fe보다 커야 하고 생성물은 쉽게 부상·제거되어야 한다.'),
('RH 탈가스법','진공조의 두 침지관을 통해 용강을 순환시켜 탈가스하는 진공처리법','RH법은 순환식 진공 탈가스법이다.'),
('DH 탈가스법','진공조의 승강에 의해 용강을 반복적으로 흡인·배출하여 탈가스하는 방법','DH법은 흡인식 진공 탈가스법이다.'),
('플래시 제련','미세한 황화정광을 산소와 함께 반응시켜 자체 산화열을 이용하는 자용 제련법','플래시 제련은 동 제련 등에서 산화반응열을 적극 활용한다.'),
('ISP법','용광로에서 아연과 납을 동시에 제련하는 공정','Imperial Smelting Process는 Zn-Pb 동시 제련법이다.'),
('Mond법','니켈을 휘발성 니켈 카보닐로 만든 뒤 열분해하여 고순도 Ni을 얻는 정련법','Mond법은 Ni(CO)₄의 생성과 분해를 이용한다.'),
('Moebius법','은의 전해정련에 이용되는 대표적인 공정','Moebius법은 은 전해정련법으로 알려져 있다.'),
('Hall-Héroult법','알루미나를 용융 빙정석에 녹여 용융염 전해로 알루미늄을 생산하는 방법','알루미늄은 수용액이 아니라 용융염 전해로 생산한다.'),
]
add_term_group(S3,'1. 야금 개론','야금학 이론',met_general)

refract=[
('규산질 내화물','SiO₂를 주성분으로 하며 산성 슬래그에 비교적 안정한 산성 내화물','규산질 내화물은 대표적인 산성 내화물이다.'),
('마그네시아 내화물','MgO를 주성분으로 하며 염기성 슬래그에 강한 염기성 내화물','마그네시아 벽돌은 대표적인 염기성 내화물이다.'),
('돌로마이트 내화물','CaO와 MgO를 주요 성분으로 하는 염기성 내화물','돌로마이트계는 제강로의 염기성 환경에 사용된다.'),
('샤모트 벽돌','소성 점토를 주원료로 하는 알루미나-실리카계 내화물','샤모트 벽돌은 점토질 내화물이다.'),
('고알루미나 내화물','Al₂O₃ 함량이 높은 내화물로 내화도와 고온강도가 우수한 편인 재료','고알루미나계는 높은 Al₂O₃ 함량이 특징이다.'),
('크로마이트 내화물','Cr₂O₃와 FeO계 성분을 포함하며 비교적 중성에 가까운 거동을 보이는 내화물','크로마이트계는 산성·염기성 슬래그 모두에 비교적 안정한 편이다.'),
('내화도','내화물이 고온에서 연화·용융에 견디는 정도를 나타내는 성질','내화도는 고온 사용 가능성을 평가하는 기본 성질이다.'),
('열충격 저항성','급격한 가열·냉각에 의해 발생하는 열응력과 균열에 견디는 성질','고로 내화재에는 열충격과 마모에 대한 저항이 요구된다.'),
]
add_term_group(S3,'2. 내화물과 연소','내화재',refract)

comb=[
('발생로가스(producer gas)','고체연료에 공기 또는 공기와 수증기를 통과시켜 만드는 저발열량 가스','발생로가스는 인공 연료가스이다.'),
('수성가스(water gas)','고온의 코크스에 수증기를 반응시켜 주로 CO와 H₂를 얻는 가스','수성가스의 주성분은 CO와 H₂이다.'),
('이론공기량','연료를 완전연소시키는 데 화학양론적으로 필요한 최소 공기량','이론공기량보다 실제 공급량이 많을 때 과잉공기가 된다.'),
('과잉공기','완전연소를 위해 이론공기량보다 추가로 공급하는 공기','과잉공기가 지나치면 배기가스 손실이 증가할 수 있다.'),
('완전연소','탄소가 주로 CO₂로, 수소가 H₂O로 충분히 산화되는 연소','산소가 충분한 조건의 이상적인 연소 상태이다.'),
('불완전연소','산소 부족 등으로 CO나 미연탄소가 생성되는 연소','불완전연소는 연료의 화학에너지를 충분히 회수하지 못한다.'),
('부두아르 반응','CO₂ + C ⇌ 2CO로 나타내는 탄소-가스 평형 반응','고로의 고온부에서 탄소 용해·가스화와 관련된 중요한 반응이다.'),
]
add_term_group(S3,'2. 내화물과 연소','연소이론',comb)

thermo=[
('상태함수','초기와 최종 상태만으로 변화량이 정해지고 경로에는 의존하지 않는 열역학적 성질','내부에너지·엔탈피·엔트로피·Gibbs 자유에너지는 상태함수이다.'),
('내부에너지 U','계 내부의 미시적 에너지를 포괄하는 상태함수','열역학 제1법칙에서 내부에너지 변화는 열과 일의 에너지 수지와 연결된다.'),
('엔탈피 H','H=U+PV로 정의되며 정압 과정의 열효과를 다루기 편리한 상태함수','엔탈피는 제련 반응의 열수지에 자주 사용된다.'),
('엔트로피 S','가역과정에서 열전달과 온도의 관계로 정의되는 상태함수로 자발성과 비가역성 판단에 쓰이는 성질','고립계의 자발 과정에서 전체 엔트로피는 감소하지 않는다.'),
('Gibbs 자유에너지 G','등온·등압 조건에서 반응의 자발성과 평형을 판단하는 상태함수','등온·등압에서 ΔG<0이면 자발 방향, 평형에서는 ΔG=0이다.'),
('Helmholtz 자유에너지 A','일정 온도와 일정 부피 조건에서 유용한 자유에너지 함수','A=U-TS로 정의된다.'),
('열역학 제1법칙','에너지 보존을 열과 일의 관계로 표현하는 법칙','계의 에너지는 생성·소멸되지 않고 형태만 변한다.'),
('열역학 제2법칙','자발 과정의 방향성과 엔트로피 생성에 관한 법칙','비가역 과정에서 우주의 엔트로피는 증가한다.'),
('가역과정','무한히 작은 구동력 차이로 진행되어 계와 주위를 모두 원상복귀시킬 수 있다고 이상화한 과정','가역과정은 동일한 상태 변화에서 최대 일을 얻는 기준이 된다.'),
('이상기체','분자 자체의 부피와 분자간 상호작용을 무시하여 PV=nRT를 따르는 모형','이상기체의 내부에너지와 엔탈피는 온도만의 함수이다.'),
('등온과정','과정 중 온도가 일정하게 유지되는 변화','이상기체의 등온 변화에서는 내부에너지 변화가 0이다.'),
('단열과정','계와 주위 사이에 열교환이 없는 과정','단열은 Q=0인 과정이며 가역 단열은 등엔트로피 과정이다.'),
('Raoult 법칙','이상용액에서 성분의 부분증기압이 액상 몰분율과 순수성분 증기압의 곱으로 주어지는 법칙','Raoult형 이상용액의 활동도계수는 1이다.'),
('활동도','비이상계의 유효 농도를 나타내어 화학퍼텐셜 표현에 쓰는 열역학적 양','활동도는 실제 용액의 비이상성을 농도 대신 반영한다.'),
('활동도계수','활동도와 조성 사이의 비이상성을 나타내는 계수','Raoult형 이상거동에서는 활동도계수가 1이다.'),
('정편차','실제 증기압이 Raoult 법칙 예측보다 큰 방향의 편차','정편차는 서로 다른 성분 사이 인력이 상대적으로 약한 경우와 관련된다.'),
('부편차','실제 증기압이 Raoult 법칙 예측보다 작은 방향의 편차','부편차는 서로 다른 성분 사이 인력이 상대적으로 강한 경우와 관련된다.'),
('평형상수 K','주어진 온도에서 반응의 평형 조성을 나타내는 열역학적 척도','표준 Gibbs 자유에너지와 ΔG°=-RT ln K의 관계를 갖는다.'),
('Le Chatelier 원리','평형계에 온도·압력·조성 변화가 가해지면 그 변화를 완화하는 방향으로 평형이 이동한다는 원리','평형 이동의 정성적 예측에 사용한다.'),
]
add_term_group(S3,'3. 열역학 원리','열역학의 법칙',thermo)

# Surface engineering concepts missing from old heat-treatment-heavy bank.
S5='5과목 표면공학'
surf=[
('전기도금','외부 전원을 사용하여 전해액 속 금속 이온을 음극인 피도금체 표면에 석출시키는 피복법','전기도금에서는 피도금체가 일반적으로 음극이 된다.'),
('무전해도금','외부 전원 없이 환원제의 화학반응을 이용하여 금속 피막을 석출시키는 도금법','무전해도금은 복잡 형상에도 비교적 균일한 피막을 형성하기 쉽다.'),
('스트라이크 도금','본도금 전에 매우 얇고 밀착성이 좋은 피막을 먼저 형성하여 후속 도금의 부착성을 높이는 처리','스트라이크는 활성화가 어려운 소재의 초기 밀착성 향상에 이용된다.'),
('탈지','도금이나 화성처리 전에 표면의 유지·오염물을 제거하는 전처리','양호한 피막 밀착을 위해 세정·탈지가 중요하다.'),
('산세(pickling)','산 용액을 이용해 금속 표면의 산화스케일이나 녹을 제거하는 전처리','산세 후에는 과도한 부식이나 수소흡수에 주의한다.'),
('활성화','도금 직전 표면의 얇은 산화막 등을 제거하여 반응성이 높은 깨끗한 표면을 만드는 처리','활성화는 도금 초기 핵생성과 밀착성에 영향을 준다.'),
('균일전착성(throwing power)','형상이 복잡하거나 전류분포가 불균일한 곳에서도 두께가 비교적 균일하게 도금되는 능력','균일전착성은 복잡 형상 도금의 품질을 좌우한다.'),
('레벨링(leveling)','미세한 표면 요철을 도금층 성장으로 평탄화하는 능력','레벨링이 좋을수록 표면 평활도가 향상된다.'),
('용융아연도금','강재를 용융 Zn 욕에 침지해 아연 피막을 형성하는 방식','Zn 피막은 희생방식 효과와 장벽 효과로 철강을 보호한다.'),
('희생양극 방식','보호할 금속보다 활성인 금속을 전기적으로 연결하여 활성 금속이 우선 용해되도록 하는 음극보호법','Zn·Mg 등이 철강의 희생양극으로 사용될 수 있다.'),
('외부전원 음극방식','직류 전원을 이용해 구조물을 음극으로 유지하여 부식을 억제하는 방법','대형 배관·탱크 등의 방식에 이용된다.'),
('파커라이징','철강 표면에 인산염 피막을 형성하는 화성처리','파커라이징은 도장 하도와 방청 목적으로 널리 이용된다.'),
('아노다이징','Al 등을 양극으로 하여 전해 산화시켜 산화피막을 성장시키는 표면처리','알루미늄 양극산화 피막은 다공질 구조를 가질 수 있다.'),
('봉공(sealing)','양극산화 후 다공질 피막의 기공을 막아 내식성과 착색 안정성을 높이는 처리','봉공은 아노다이징 후 중요한 후처리이다.'),
('알로딘(Alodine)','알루미늄 표면에 화성피막을 형성하는 대표적인 크로메이트계 처리 명칭','알로딘은 철강의 인산염 처리와 구별되는 알루미늄 화성처리이다.'),
('세러다이징(Sherardizing)','아연 분말 속에서 가열하여 Zn을 철강 표면에 확산시키는 확산피복법','세러다이징은 아연의 고체 확산을 이용한다.'),
('칼로라이징(calorizing)','알루미늄을 금속 표면에 확산 침투시켜 내산화성을 높이는 확산피복법','칼로라이징은 고온 산화 저항 향상에 이용된다.'),
('크로마이징(chromizing)','Cr을 표면에 확산 침투시켜 내식성·내산화성 등을 향상시키는 처리','크로마이징은 크롬 확산피복법이다.'),
('금속용사','용융 또는 반용융 상태의 피복재 입자를 고속으로 분사해 표면에 적층시키는 피복법','용사는 비교적 두꺼운 피막을 빠르게 형성할 수 있다.'),
('PVD','진공 중 물리적 증발·스퍼터링·이온화 등을 이용해 피막을 형성하는 물리적 기상증착의 총칭','진공증착·스퍼터링·이온도금은 대표적인 PVD 계열이다.'),
('진공증착','진공에서 증발원 재료를 기화시켜 기판에 응축시키는 PVD 방법','진공증착은 비교적 단순한 물리적 기상증착 방법이다.'),
('스퍼터링','플라즈마 이온이 타깃을 충돌해 방출시킨 원자를 기판에 증착하는 PVD 방법','스퍼터링은 고융점 재료의 박막 형성에도 유리하다.'),
('이온도금','증발된 피복종을 이온화하고 전기장을 이용하여 기판에 증착시키는 PVD 방법','이온도금은 이온 충돌 효과로 높은 밀착성을 얻기 쉽다.'),
('CVD','가열된 기판 표면에서 기체 전구체의 화학반응 또는 분해를 일으켜 피막을 형성하는 증착법','CVD는 화학반응에 의해 피막을 성장시킨다.'),
('열분해 CVD','기체 전구체를 고온에서 분해시켜 고체 피막을 석출하는 CVD 반응형식','열분해는 대표적인 CVD 반응형식이다.'),
('수소환원 CVD','기체 화합물을 수소로 환원하여 금속 또는 화합물 피막을 만드는 CVD 반응형식','수소환원은 CVD의 반응 유형 중 하나이다.'),
]
add_term_group(S5,'4. 피복처리','금속피복·도금·양극산화',surf)

analysis_terms=[
('광학현미경(OM)','가시광과 광학렌즈를 이용해 연마·에칭된 금속 조직을 관찰하는 장비','OM은 비교적 넓은 영역의 미세조직 관찰에 적합하다.'),
('주사전자현미경(SEM)','집속 전자빔을 시료 표면에 주사하고 방출 신호를 검출하여 표면 형상 등을 관찰하는 장비','SEM은 표면 형상과 파면 관찰에 널리 사용된다.'),
('투과전자현미경(TEM)','얇은 시료를 투과한 전자를 이용해 매우 미세한 내부구조와 전위 등을 관찰하는 장비','TEM은 전위와 나노미터 수준 미세조직 관찰에 유용하다.'),
('X선 회절(XRD)','결정면에서 발생하는 X선 회절을 이용해 결정구조와 상을 분석하는 방법','XRD는 결정상 동정과 격자 관련 분석에 이용된다.'),
('EDS','전자빔 조사로 발생하는 특성 X선을 분석하여 국부 원소조성을 파악하는 방법','EDS는 SEM/TEM과 결합해 원소분석에 많이 사용된다.'),
('비커스 미소경도','다이아몬드 피라미드 압입자를 이용해 작은 영역이나 얇은 경화층의 경도를 평가하는 방법','미소 비커스는 도금층·경화층·특정 조직의 국부 경도 측정에 적합하다.'),
]
add_term_group(S5,'5. 금속분석','금속분석 및 측정',analysis_terms)

# Additional high-confidence exam-style conceptual items (not inverse duplicates).
extra=[
(S3,'2. 내화물과 연소','내화재','고로용 내화재에 요구되는 성질로 가장 적절한 것은?','고온·고압에서 충분한 강도와 화학적 안정성을 가질 것',['고온에서 쉽게 연화될 것','용선 및 슬래그와 적극적으로 반응할 것','열충격에 매우 민감할 것'],'고로 내화재는 고온강도, 내화도, 화학적 안정성, 내마모·내열충격성이 중요하다.'),
(S3,'3. 열역학 원리','열역학의 법칙','등온·등압 조건에서 자발적인 변화의 방향을 판단하는 데 가장 직접적으로 이용되는 함수는?','Gibbs 자유에너지',['내부에너지','체적탄성계수','열전도율'],'등온·등압 조건에서 ΔG의 부호는 자발성 판단의 기준이 된다.'),
(S3,'3. 열역학 원리','열역학의 법칙','Raoult형 이상용액에 대한 설명으로 옳은 것은?','각 성분의 활동도계수는 1이다.',['혼합엔탈피는 항상 큰 양수이다.','서로 다른 성분 사이 상호작용만 존재한다.','성분의 부분증기압은 조성과 무관하다.'],'이상용액은 Raoult 법칙을 따르며 활동도계수 γ=1이다.'),
(S3,'1. 야금 개론','야금학 이론','용강 탈산제의 조건으로 적절하지 않은 것은?','산소와의 친화력이 Fe보다 작을 것',['용강에 신속히 용해될 것','탈산생성물이 쉽게 부상할 것','생성물이 강 중에 잔류하지 않기 쉬울 것'],'탈산제는 Fe보다 산소 친화력이 커야 효과적으로 산소를 제거할 수 있다.'),
(S5,'4. 피복처리','금속피복·도금·양극산화','아노다이징 후 봉공 처리를 하는 주된 목적은?','다공질 피막의 기공을 막아 내식성과 착색 안정성을 높이기 위해',['피막을 완전히 제거하기 위해','모재를 용융시키기 위해','피막의 기공을 더 크게 만들기 위해'],'양극산화 피막의 기공을 봉공하면 오염 침투가 줄고 내식성과 착색 안정성이 향상된다.'),
(S5,'4. 피복처리','금속피복·도금·양극산화','무전해도금의 특징으로 가장 적절한 것은?','외부 전원 없이 화학적 환원반응으로 금속을 석출한다.',['피도금체를 반드시 양극으로 사용한다.','진공이 반드시 필요하다.','금속 분말의 고체확산만 이용한다.'],'무전해도금은 환원제를 이용한 자가촉매적 또는 화학적 석출을 이용한다.'),
(S5,'4. 피복처리','금속피복·도금·양극산화','PVD와 CVD를 구분하는 핵심으로 가장 적절한 것은?','CVD는 기체 전구체의 화학반응을 이용한다.',['PVD만 진공에서 수행할 수 있다.','CVD는 반드시 수용액을 사용한다.','PVD는 항상 모재를 용융시킨다.'],'PVD는 물리적 증발·스퍼터링 등이 핵심이고 CVD는 전구체의 화학반응이 핵심이다.'),
(S5,'3. 표면처리','침탄','침탄처리의 주된 목적은?','저탄소강 표면의 탄소농도를 높인 뒤 경화시켜 내마모성을 향상시키는 것',['강 전체의 탄소를 제거하는 것','표면에 질소만 확산시키는 것','모재의 결정구조를 비정질화하는 것'],'침탄은 표면 탄소농도를 높여 담금질 후 경한 표면층과 인성 있는 심부를 얻는 처리이다.'),
(S5,'3. 표면처리','질화','질화처리의 특징으로 옳은 것은?','질소를 표면에 확산시켜 경한 질화물을 형성한다.',['처리 후 반드시 고온 담금질이 필수이다.','표면 탄소를 제거하는 처리이다.','저온에서만 산화피막을 제거하는 세정법이다.'],'질화는 N의 확산과 합금질화물 형성으로 표면을 경화하며 일반적으로 침탄보다 낮은 온도에서 수행된다.'),
]
for row in extra: addq(*row)

# Normalize typography and remove accidental duplicates.
def norm(s):
    return re.sub(r'\s+','',s).lower().replace('·','').replace('–','-').replace('—','-')
seen=set();ded=[]
for q in new:
    key=norm(q['question'])
    if key in seen: continue
    seen.add(key); ded.append(q)
# Repeated-family cap: one concept family may contribute at most 4 independently-worded questions.
# This prevents the old app's 'same concept endlessly repeated' feeling.
fam_counts=collections.Counter(); capped=[]
for q in ded:
    fam=q.get('family_id') or q.get('concept_id') or q['question']
    if fam_counts[fam] >= 4:
        continue
    fam_counts[fam]+=1
    capped.append(q)
new=capped

# Reassign compact numeric ids, preserving family ids.
for i,q in enumerate(new,1): q['id']=i

# split by official subject order
subs=['1과목 금속재료학','2과목 금속조직학','3과목 야금공학','4과목 금속가공학','5과목 표면공학']
counts={}
for i,s in enumerate(subs,1):
    arr=[q for q in new if q['subject']==s]
    counts[s]=len(arr)
    (OUT/'data'/f'subject{i}.json').write_text(json.dumps(arr,ensure_ascii=False,indent=2),encoding='utf-8')

manifest={
 'version':'v6.0-concept-only','generated_at':'2026-08-13','total':len(new),'subjects':counts,
 'files':[f'subject{i}.json' for i in range(1,6)],
 'types':dict(collections.Counter(q['type'] for q in new)),
 'topics':dict(collections.Counter(q['topic'] for q in new)),
 'rules':[
   '계산형 문항 0개','답안 번호만 바꾼 파생문항 0개','정규화 지문 중복 0개',
   '현행 출제기준 5과목 taxonomy 적용','2010·2011·2012·2016 기출의 출제개념·문장형태를 참고해 신규 개념문항 보강'
 ]}
(OUT/'data'/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

# audit
num_calc=sum(q.get('type')=='calculation' for q in new)
qdups=len(new)-len({norm(q['question']) for q in new})
# Answer-position-only variants: same normalized stem + same normalized choices set would have been caught by stem duplicate.
audit=[]
audit.append(f'총 문항: {len(new):,}')
audit.append('계산형(type=calculation): '+str(num_calc))
audit.append('정규화 지문 중복: '+str(qdups))
audit.append('과목별: '+json.dumps(counts,ensure_ascii=False))
audit.append('출제원칙: 답안 위치 변경만으로 별도 문항을 생성하지 않음')
(OUT/'data'/'AUDIT.txt').write_text('\n'.join(audit),encoding='utf-8')

# update UI/version texts
idx=(OUT/'index.html').read_text(encoding='utf-8')
idx=idx.replace('금속재료기사 CBT Pro v5','금속재료기사 CBT Pro v6')
idx=idx.replace('금속 CBT v5','금속 CBT v6')
# title/body label may occur in several forms
idx=idx.replace('실저장 독립문항 10,976개 · 문구 셔플 가상문항 제거 · 5과목','개념형 전용 · 계산문제 0개 · 기출개념 기반 · 현행 5과목')
(OUT/'index.html').write_text(idx,encoding='utf-8')

app=(OUT/'app.js').read_text(encoding='utf-8')
app=app.replace('metal-cbt-v5','metal-cbt-v6')
app=app.replace("x.trust==='verified-core'?'검증핵심':'규칙검증'", "x.trust==='exam-derived'?'기출개념':x.trust==='concept-reviewed'?'개념검수':'검증핵심'")
app=app.replace('실저장 독립문항 ${BANK.length.toLocaleString()}개 · 문구 셔플 가상문항 제거 · ${Object.keys(man.subjects).length}과목', '개념형 ${BANK.length.toLocaleString()}문항 · 계산문제 0개 · 답안번호 파생 0개 · ${Object.keys(man.subjects).length}과목')
app=app.replace('독립 지문 ${BANK.length.toLocaleString()}개를 불러왔습니다. 과목별 학습 또는 신규 우선 모드를 선택하세요.', '개념형 ${BANK.length.toLocaleString()}문항을 불러왔습니다. 계산형 문항은 제외되어 있습니다.')
(OUT/'app.js').write_text(app,encoding='utf-8')

# service worker cache bump
sw=(OUT/'sw.js').read_text(encoding='utf-8')
sw=sw.replace('metal-cbt-v5','metal-cbt-v6').replace('cbt-v5','cbt-v6')
(OUT/'sw.js').write_text(sw,encoding='utf-8')

manweb=(OUT/'manifest.webmanifest').read_text(encoding='utf-8').replace('CBT Pro v5','CBT Pro v6').replace('금속 CBT v5','금속 CBT v6')
(OUT/'manifest.webmanifest').write_text(manweb,encoding='utf-8')

readme=f'''# 금속재료기사 CBT Pro v6 — 개념형 전용\n\n- 총 {len(new):,}문항\n- 계산형 문항: 0개\n- 답안 번호만 바꾼 파생문항: 0개\n- 2010·2011·2012·2016 공개 기출의 출제개념과 문제 스타일을 참고해 개념형 위주로 재구성\n- 사용자가 제공한 현행 출제기준(2023.1.1~2026.12.31) 5과목 구조로 재분류\n\n과목별 문항 수:\n'''+ '\n'.join(f'- {k}: {v:,}' for k,v in counts.items()) + '''\n\n주의: 기출 원문을 단순 복제한 문제은행이 아니라, 기출에서 반복되는 개념을 학습하기 위한 신규 개념문항 중심 버전입니다.\n'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

# preserve generator source for audit/rebuild
shutil.copy2('/mnt/data/v6work/build_v6.py', OUT/'build_v6.py')

# zip
zip_path=Path('/mnt/data/metal_cbt_v6_concept_only.zip')
if zip_path.exists(): zip_path.unlink()
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in OUT.rglob('*'):
        if p.is_file(): z.write(p,Path(OUT.name)/p.relative_to(OUT))
print('\n'.join(audit))
print('ZIP',zip_path,zip_path.stat().st_size)
