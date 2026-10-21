# -*- coding: utf-8 -*-
"""우아단위 정적 사이트 생성기 → _site/.  사용: python scripts/build_site.py"""
import sys, json, re, shutil, time, math
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from common import *

PY = 400 / 121.0          # 1평 = 3.3058㎡ (정의값 400/121)
SQFT = 10.763910417       # 1㎡ = 10.7639 ft²
INCH = 2.54
LB = 0.45359237
MILE = 1.609344
GAL = 3.785411784

def table(heads, rows, num=()):
    th = "".join('<th%s>%s</th>' % (' class="num"' if i in num else "", h) for i, h in enumerate(heads))
    body = "".join("<tr>%s</tr>" % "".join('<td%s>%s</td>' % (' class="num"' if i in num else "", v) for i, v in enumerate(r)) for r in rows)
    return '<div class="tbl-wrap"><table class="tbl"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (th, body)

def chips(items): return '<div class="chips">%s</div>' % "".join('<a class="chip" href="%s">%s</a>' % (u, esc(t)) for t, u in items)

def n2(x, d=2):
    s = ("%." + str(d) + "f") % x
    if "." in s: s = s.rstrip("0").rstrip(".")
    return "{:,}".format(float(s)) if "." not in s else "{:,.{}f}".format(float(s), len(s.split(".")[1]))

def near(lst, v, k=5):
    i = lst.index(v)
    return lst[max(0, i - k): i + k + 1]

# ───────────────────────── 평 ↔ ㎡ ─────────────────────────
PY_LIST = list(range(1, 201))
SQM_LIST = list(range(10, 301)) + list(range(305, 601, 5))
APT = {59: "공급 약 24~25평형(25평형대)", 74: "공급 약 30~31평형", 84: "공급 약 33~34평형(‘국민평형’ 34평형)", 101: "공급 약 39~40평형", 114: "공급 약 44~45평형", 135: "공급 약 52~54평형"}

def py_context(n):
    if n <= 8: return "원룸·고시원·소형 오피스텔 크기"
    if n <= 15: return "원룸~투룸, 소형 오피스텔 크기"
    if n <= 22: return "소형 아파트·빌라 크기"
    if n <= 30: return "중소형 아파트 크기(공급면적 기준 20평대)"
    if n <= 40: return "중형 아파트 크기(34평형이 ‘국민평형’)"
    if n <= 60: return "중대형 아파트 크기"
    return "대형 아파트·단독주택·상가 크기"

def page_pyeong(n):
    m2 = n * PY
    path = "/pyeong/%d평/" % n
    own = n * PY
    apt_lo, apt_hi = own * 0.74, own * 0.84
    lead = (f"<p class=\"lead\"><b>{n}평은 {n2(m2)}㎡</b>입니다(1평 = 3.3058㎡). 제곱피트로는 약 {n2(m2 * SQFT, 1)}ft²이고 {py_context(n)}입니다. 아파트처럼 ‘{n}평형’이 <b>공급면적</b> 기준이라면 실제 전용면적은 전용률 74~84%를 적용해 약 {n2(apt_lo, 1)}~{n2(apt_hi, 1)}㎡({n2(apt_lo / PY, 1)}~{n2(apt_hi / PY, 1)}평) 정도입니다.</p>")
    t = table(["평", "㎡", "ft²"], [['<a href="/pyeong/%d평/">%d평</a>' % (v, v) if v != n else "<b>%d평</b>" % v, n2(v * PY), n2(v * PY * SQFT, 1)] for v in near(PY_LIST, n)], (1, 2))
    body = f"""
<div class="page-head"><h1>{n}평 몇 제곱미터? — {n2(m2)}㎡</h1><p>평 → ㎡ 변환 · 아파트 전용·공급면적 환산</p></div>
{lead}
<div class="stat-row"><div class="stat"><small>평</small><b>{n}평</b></div><div class="stat"><small>제곱미터</small><b>{n2(m2)}㎡</b></div><div class="stat"><small>제곱피트</small><b>{n2(m2 * SQFT, 1)}ft²</b></div></div>
{ad()}
<h2 class="group-title">🔁 비슷한 평수</h2>
{t}
<h2 class="group-title">📌 계산 방법</h2>
<ul class="lead" style="margin-left:20px"><li>평 → ㎡: 평수 × 3.3058 (정확히는 400÷121). {n}평 × 3.3058 = {n2(m2)}㎡</li><li>㎡ → 평: 제곱미터 × 0.3025</li><li>아파트 ‘○○평형’은 보통 공급면적(전용+공용) 기준이라 전용면적은 70~85%(전용률)입니다.</li><li>법적으로 평은 사용이 제한되어 ㎡ 표기가 원칙이지만 부동산 거래에서는 여전히 널리 씁니다.</li></ul>
{chips([("평↔㎡ 변환표", "/pyeong/"), (f"{int(round(m2))}㎡ 몇 평", "/sqm/%d/" % int(round(m2))) if int(round(m2)) in SQM_LIST else ("㎡ → 평", "/sqm/")])}
"""
    faq = [(f"{n}평은 몇 제곱미터인가요?", f"{n2(m2)}㎡입니다(1평=3.3058㎡)."), (f"{n}평은 몇 ft²인가요?", f"약 {n2(m2 * SQFT, 1)}제곱피트입니다."),
           (f"아파트 {n}평형의 전용면적은?", f"공급면적 {n}평형이면 전용률 74~84% 기준 전용 약 {n2(apt_lo, 1)}~{n2(apt_hi, 1)}㎡입니다.")]
    write(path, layout(path, f"{n}평 몇 제곱미터? {n2(m2)}㎡ (평↔㎡ 변환)", f"{n}평은 {n2(m2)}㎡(약 {n2(m2 * SQFT, 1)}ft²). 아파트 {n}평형 전용면적 환산과 변환 방법.", body, faq, [("홈", "/"), ("평↔㎡", "/pyeong/"), (f"{n}평", path)]), "0.7" if n % 5 == 0 else "0.5")

def page_sqm(m):
    py = m / PY
    path = "/sqm/%d/" % m
    apt = APT.get(m)
    lead = (f"<p class=\"lead\"><b>{m}㎡는 약 {n2(py, 2)}평</b>입니다(1㎡ = 0.3025평). 제곱피트로는 약 {n2(m * SQFT, 1)}ft²입니다.{(' 아파트 전용면적 ' + str(m) + '㎡는 보통 ' + apt + '에 해당합니다.') if apt else ''}</p>")
    t = table(["㎡", "평"], [['<a href="/sqm/%d/">%d㎡</a>' % (v, v) if v != m else "<b>%d㎡</b>" % v, n2(v / PY)] for v in near(SQM_LIST, m)], (1,))
    body = f"""
<div class="page-head"><h1>{m}㎡는 몇 평? — {n2(py, 2)}평</h1><p>㎡ → 평 변환 · 아파트 전용면적 환산</p></div>
{lead}
<div class="stat-row"><div class="stat"><small>제곱미터</small><b>{m}㎡</b></div><div class="stat"><small>평</small><b>{n2(py, 2)}평</b></div><div class="stat"><small>제곱피트</small><b>{n2(m * SQFT, 1)}ft²</b></div></div>
{ad()}
<h2 class="group-title">🔁 비슷한 면적</h2>
{t}
<h2 class="group-title">📌 계산 방법</h2>
<ul class="lead" style="margin-left:20px"><li>㎡ → 평: {m} × 0.3025 = {n2(py, 2)}평</li><li>평 → ㎡: 평수 × 3.3058</li><li>아파트 전용면적(㎡)에 1.2~1.35배를 곱하면 공급면적을 대략 가늠할 수 있습니다(단지·평면에 따라 다름).</li></ul>
{chips([("㎡↔평 변환표", "/sqm/"), (f"{int(round(py))}평 몇 ㎡", "/pyeong/%d평/" % int(round(py))) if int(round(py)) in PY_LIST else ("평 → ㎡", "/pyeong/")])}
"""
    faq = [(f"{m}㎡는 몇 평인가요?", f"약 {n2(py, 2)}평입니다."), ("아파트 전용면적 84㎡는 몇 평형인가요?", "전용 84㎡는 공급면적 기준 약 33~34평형(‘국민평형’)이고 전용면적만으로는 약 25.4평입니다.")]
    write(path, layout(path, f"{m}㎡는 몇 평? {n2(py, 2)}평 (㎡↔평 변환)", f"{m}㎡는 약 {n2(py, 2)}평({n2(m * SQFT, 1)}ft²). 아파트 전용면적 환산과 계산 방법.", body, faq, [("홈", "/"), ("㎡→평", "/sqm/"), (f"{m}㎡", path)]), "0.7" if m in APT or m % 10 == 0 else "0.5")

def hub_pyeong():
    rows = [['<a href="/pyeong/%d평/">%d평</a>' % (n, n), n2(n * PY), '<a href="/sqm/%d/">%d㎡ → %s평</a>' % (round(n * PY), round(n * PY), n2(round(n * PY) / PY)) if round(n * PY) in SQM_LIST else "-"] for n in range(5, 101, 5)]
    body = f"""
<div class="page-head"><h1>평수 계산기 — 평↔㎡ 변환표</h1><p>1평 = 3.3058㎡ · 1㎡ = 0.3025평</p></div>
<p class="lead">평과 제곱미터를 바꾸는 방법과 변환표입니다. <b>1평은 3.3058㎡</b>이고 1㎡는 0.3025평입니다. 평수를 눌러 자세한 변환과 아파트 전용·공급면적 환산을 확인하세요.</p>
<div class="tool-box"><div class="tool-row"><div><label for="v">값</label><input id="v" type="number" value="30" style="width:110px"></div><div><label for="d">변환</label><select id="d"><option value="p2m">평 → ㎡</option><option value="m2p">㎡ → 평</option></select></div><button class="btn-p" id="go">변환</button></div><div class="tool-out" id="out">값을 입력하고 변환을 눌러 주세요.</div></div>
{ad()}
{table(['평', '제곱미터', '㎡ → 평'], rows, (1,))}
<h2 class="group-title">🏢 아파트 전용면적별 평형 (대략)</h2>
{table(['전용면적', '전용 평수', '공급 평형(대략)'], [['<a href="/sqm/%d/">%d㎡</a>' % (m, m), n2(m / PY, 1) + "평", t] for m, t in APT.items()])}
{chips([("㎡→평 표", "/sqm/")])}
<script src="/assets/js/converter.js"></script>
"""
    faq = [("1평은 몇 제곱미터인가요?", "3.3058㎡입니다(400÷121)."), ("30평은 몇 제곱미터인가요?", f"{n2(30 * PY)}㎡입니다."), ("전용면적과 공급면적은 어떻게 다른가요?", "전용면적은 집 안쪽 실제 사용 면적이고 공급면적은 전용면적에 계단·복도 등 공용면적(주거공용)을 더한 면적입니다. ‘○○평형’은 보통 공급면적 기준입니다.")]
    write("/pyeong/", layout("/pyeong/", "평수 계산기 — 평↔㎡ 변환표 (1평 = 3.3058㎡)", "평을 ㎡로, ㎡를 평으로 바꾸는 변환표와 계산기. 아파트 전용면적별 평형 환산과 1평=3.3058㎡ 계산법.", body, faq, [("홈", "/"), ("평↔㎡", "/pyeong/")], coupang=True), "0.9")
    rows = [['<a href="/sqm/%d/">%d㎡</a>' % (m, m), n2(m / PY) + "평"] for m in SQM_LIST if m % 10 == 0 and m <= 300]
    body = f"""
<div class="page-head"><h1>㎡를 평으로 바꾸기 — ㎡→평 변환표</h1><p>1㎡ = 0.3025평</p></div>
<p class="lead">제곱미터(㎡)를 평으로 바꾸려면 <b>0.3025를 곱</b>합니다. 아파트 전용면적 59㎡·84㎡ 등은 개별 페이지에서 평형과 함께 확인하세요.</p>
{ad()}
{table(['제곱미터', '평'], rows, (1,))}
{chips([("평→㎡ 변환기", "/pyeong/")])}
"""
    write("/sqm/", layout("/sqm/", "㎡를 평으로 — ㎡→평 변환표 (1㎡ = 0.3025평)", "제곱미터를 평으로 바꾸는 변환표. 아파트 전용면적 59㎡·84㎡ 등 몇 평인지 한눈에.", body, [("㎡를 평으로 바꾸는 법은?", "㎡ 값에 0.3025를 곱합니다. 84㎡ × 0.3025 = 약 25.4평입니다.")], [("홈", "/"), ("㎡→평", "/sqm/")]), "0.8")

# ───────────────────────── 신발 사이즈 ─────────────────────────
EU_M = {4: 36, 4.5: 36.5, 5: 37.5, 5.5: 38, 6: 38.5, 6.5: 39, 7: 40, 7.5: 40.5, 8: 41, 8.5: 42, 9: 42.5, 9.5: 43, 10: 44, 10.5: 44.5, 11: 45, 11.5: 45.5, 12: 46}
SHOES = list(range(220, 305, 5))
KIDS = list(range(100, 225, 5))
KID_AGE = [(100, 110, "신생아~3개월"), (110, 120, "3~6개월"), (120, 130, "6~12개월(돌 전)"), (130, 140, "12~18개월(돌 무렵)"), (140, 150, "18~24개월"), (150, 160, "만 2~3세"), (160, 170, "만 3~4세"),
            (170, 180, "만 4~5세"), (180, 190, "만 5~6세"), (190, 200, "만 6~7세(초1)"), (200, 210, "만 7~8세(초2)"), (210, 220, "만 8~10세(초3~4)"), (220, 230, "만 10~12세(초5~6)")]

def sz(x): return ("%g" % x)

def page_shoe(mm):
    us = (mm - 180) / 10.0
    uw = us + 1.5; uk = us - 1; eu = EU_M.get(us)
    path = "/shoe-size/%dmm/" % mm
    lead = (f"<p class=\"lead\">발 길이(한국 신발 사이즈) <b>{mm}mm</b>는 남성 US <b>{sz(us)}</b>, 여성 US <b>{sz(uw)}</b>, UK {sz(uk)}, 유럽(EU) 약 {sz(eu)}, 일본 {mm / 10:g}cm에 해당합니다(나이키 사이즈표 기준 근삿값). 브랜드마다 ±0.5 사이즈 차이가 날 수 있어 해외 직구 때는 해당 브랜드의 사이즈표를 확인하세요.</p>")
    t = table(["한국(mm)", "남성 US", "여성 US", "UK", "EU(약)"], [[('<a href="/shoe-size/%dmm/">%d</a>' % (v, v)) if v != mm else "<b>%d</b>" % v, sz((v - 180) / 10.0), sz((v - 180) / 10.0 + 1.5), sz((v - 180) / 10.0 - 1), sz(EU_M.get((v - 180) / 10.0))] for v in near(SHOES, mm, 4)], (1, 2, 3, 4))
    body = f"""
<div class="page-head"><h1>신발 사이즈 {mm}mm — 미국·유럽·일본 사이즈 변환</h1><p>남성·여성 US · UK · EU · 일본 cm</p></div>
{lead}
<div class="stat-row"><div class="stat"><small>한국</small><b>{mm}mm</b></div><div class="stat"><small>남성 US</small><b>{sz(us)}</b></div><div class="stat"><small>여성 US</small><b>{sz(uw)}</b></div><div class="stat"><small>EU</small><b>~{sz(eu)}</b></div></div>
{ad()}
<h2 class="group-title">🔁 비슷한 사이즈</h2>
{t}
<h2 class="group-title">📌 알아두기</h2>
<ul class="lead" style="margin-left:20px"><li>한국 사이즈는 발 길이를 mm로 나타내므로 {mm}mm는 {mm / 10:g}cm입니다. 실제 발 길이보다 5~10mm 여유를 둔 사이즈를 고르는 것이 일반적입니다.</li><li>남성 US = (mm − 180) ÷ 10, 여성 US는 남성 US + 1.5, UK는 남성 US − 1로 근사합니다.</li><li>발볼이 넓거나 브랜드(나이키·아디다스·뉴발란스 등)에 따라 반 사이즈 차이가 날 수 있습니다.</li></ul>
{chips([("신발 사이즈 변환표", "/shoe-size/"), ("아기·어린이 신발 사이즈", "/shoe-size/kids/")])}
"""
    faq = [(f"신발 {mm}mm는 US 몇 사이즈인가요?", f"남성 US {sz(us)}, 여성 US {sz(uw)}에 해당합니다(나이키 기준 근삿값)."), (f"{mm}mm는 EU 몇 사이즈인가요?", f"약 {sz(eu)}입니다."), ("브랜드마다 사이즈가 다른가요?", "네. 같은 mm라도 브랜드·모델·발볼에 따라 반 사이즈 정도 차이가 날 수 있어 구매 전 공식 사이즈표를 확인하세요.")]
    write(path, layout(path, f"신발 사이즈 {mm}mm는 US {sz(us)}(남)·{sz(uw)}(여) — EU·일본 변환", f"한국 신발 {mm}mm = 남성 US {sz(us)}, 여성 US {sz(uw)}, UK {sz(uk)}, EU 약 {sz(eu)}. 직구용 신발 사이즈 변환표.", body, faq, [("홈", "/"), ("신발 사이즈", "/shoe-size/"), (f"{mm}mm", path)]), "0.7")

def page_kid_shoe(mm):
    age = next((a for lo, hi, a in KID_AGE if lo <= mm < hi), "")
    path = "/shoe-size/kids/%dmm/" % mm
    lead = f"<p class=\"lead\">아이 발 길이 <b>{mm}mm</b>에 맞는 신발은 보통 <b>{mm + 5}~{mm + 10}mm</b>(발 길이+0.5~1cm 여유)입니다. 이 크기는 대략 <b>{age}</b> 아이의 평균 신발 사이즈 범위에 해당하지만 아이마다 발 크기 차이가 큽니다.</p>"
    t = table(["발 길이(mm)", "추천 신발(mm)", "월령·나이(평균)"], [['<a href="/shoe-size/kids/%dmm/">%d</a>' % (v, v) if v != mm else "<b>%d</b>" % v, "%d~%d" % (v + 5, v + 10), next((a for lo, hi, a in KID_AGE if lo <= v < hi), "-")] for v in near(KIDS, mm, 4)], (1,))
    body = f"""
<div class="page-head"><h1>아기·어린이 신발 사이즈 {mm}mm — 몇 개월·몇 살?</h1><p>발 길이 {mm}mm · 추천 신발 {mm + 5}~{mm + 10}mm</p></div>
{lead}
{ad()}
{t}
<ul class="lead" style="margin-left:20px"><li>아이 발 길이는 서 있을 때 뒤꿈치에서 가장 긴 발가락 끝까지 재고, 신발은 5~10mm 여유를 둡니다.</li><li>발은 빨리 자라 어린 아이는 2~3개월마다 한 번씩 확인하는 것이 좋습니다.</li><li>월령·나이는 평균일 뿐이며 개인차가 큽니다.</li></ul>
{chips([("어린이 신발 사이즈표", "/shoe-size/kids/"), ("성인 신발 사이즈 변환", "/shoe-size/")])}
"""
    faq = [(f"{mm}mm 신발은 몇 살 사이즈인가요?", f"평균적으로 {age} 정도입니다."), ("아이 신발은 얼마나 크게 사야 하나요?", "발 길이보다 5~10mm 큰 사이즈가 적당합니다.")]
    write(path, layout(path, f"아기 신발 {mm}mm는 몇 개월·몇 살? (발 길이 {mm}mm)", f"발 길이 {mm}mm 아이의 추천 신발 {mm + 5}~{mm + 10}mm와 평균 월령·나이({age}).", body, faq, [("홈", "/"), ("신발 사이즈", "/shoe-size/"), ("어린이", "/shoe-size/kids/"), (f"{mm}mm", path)]), "0.5")

def hub_shoe():
    rows = [['<a href="/shoe-size/%dmm/">%d</a>' % (v, v), sz((v - 180) / 10.0), sz((v - 180) / 10.0 + 1.5), sz((v - 180) / 10.0 - 1), sz(EU_M.get((v - 180) / 10.0)), "%g" % (v / 10)] for v in SHOES]
    body = f"""
<div class="page-head"><h1>신발 사이즈 변환표 — 한국 mm ↔ 미국·유럽·일본</h1><p>남성·여성 US · UK · EU (나이키 사이즈표 기준 근삿값)</p></div>
<p class="lead">한국 신발 사이즈(mm)를 미국(US), 영국(UK), 유럽(EU), 일본(cm) 사이즈로 바꾸는 표입니다. 사이즈를 눌러 자세한 변환을 확인하세요. 브랜드·모델에 따라 반 사이즈 정도 차이가 날 수 있습니다.</p>
{ad()}
{table(['한국(mm)', '남성 US', '여성 US', 'UK', 'EU(약)', '일본(cm)'], rows, (1, 2, 3, 4, 5))}
{chips([("아기·어린이 신발 사이즈", "/shoe-size/kids/")])}
"""
    write("/shoe-size/", layout("/shoe-size/", "신발 사이즈 변환표 — 한국 mm·미국 US·유럽 EU·일본 (남녀)", "한국 신발 사이즈 220~300mm를 미국·영국·유럽·일본 사이즈로 변환한 표. 남성·여성 US 사이즈와 직구 팁.", body,
          [("신발 250mm는 US 몇 사이즈인가요?", "남성 US 7, 여성 US 8.5에 해당합니다(나이키 기준)."), ("260mm는 US 몇 사이즈인가요?", "남성 US 8, 여성 US 9.5입니다.")], [("홈", "/"), ("신발 사이즈", "/shoe-size/")], coupang=True), "0.9")
    rows = [[str(lo) + "~" + str(hi - 1), "%d~%d" % (lo + 5, hi + 4), age, '<a href="/shoe-size/kids/%dmm/">%dmm 자세히</a>' % (lo, lo)] for lo, hi, age in KID_AGE if lo in KIDS]
    body = f"""
<div class="page-head"><h1>아기·어린이 신발 사이즈표 — 개월수·나이별 mm</h1><p>발 길이 100~220mm</p></div>
<p class="lead">아기와 어린이의 월령·나이별 평균 발 길이와 추천 신발 사이즈입니다. 신발은 발 길이보다 5~10mm 큰 것을 고르세요. 평균값이라 아이마다 다를 수 있습니다.</p>
{ad()}
{table(['발 길이(mm)', '추천 신발(mm)', '월령·나이(평균)', '자세히'], rows)}
{chips([("성인 신발 사이즈 변환", "/shoe-size/")])}
"""
    write("/shoe-size/kids/", layout("/shoe-size/kids/", "아기·어린이 신발 사이즈표 — 개월수·나이별 mm", "아기·어린이 월령별 평균 발 길이와 추천 신발 사이즈표. 100~220mm.", body, [("돌 아기 신발 사이즈는?", "돌 무렵(12~18개월)은 발 길이 130~140mm, 추천 신발은 140~150mm 정도입니다.")], [("홈", "/"), ("신발 사이즈", "/shoe-size/"), ("어린이", "/shoe-size/kids/")], coupang=True), "0.8")

# ───────────────────────── 반지 호수 ─────────────────────────
RINGS = list(range(1, 31))
def ring_us(circ): return round((circ - 36.5) / 2.55 * 2) / 2

def page_ring(n):
    circ = n + 40; dia = circ / math.pi; us = ring_us(circ)
    path = "/ring-size/%d호/" % n
    lead = f"<p class=\"lead\">반지 <b>{n}호</b>는 손가락 둘레 약 <b>{circ}mm</b>(안지름 약 {dia:.1f}mm)이고 미국(US) 사이즈로 약 <b>{sz(us)}</b>, 유럽(ISO) 사이즈는 {circ}에 해당합니다. 한국과 일본은 같은 호수 체계를 씁니다. 근삿값이므로 정확한 사이즈는 실측이나 매장 측정으로 확인하세요.</p>"
    t = table(["한국·일본 호수", "둘레(mm)", "안지름(mm)", "미국 US", "유럽 EU"], [[('<a href="/ring-size/%d호/">%d호</a>' % (v, v)) if v != n else "<b>%d호</b>" % v, v + 40, "%.1f" % ((v + 40) / math.pi), sz(ring_us(v + 40)), v + 40] for v in near(RINGS, n, 4)], (1, 2, 3, 4))
    body = f"""
<div class="page-head"><h1>반지 {n}호 사이즈 — 둘레 {circ}mm, 미국 US {sz(us)}</h1><p>한국·일본 호수 ↔ 미국·유럽 반지 사이즈</p></div>
{lead}
<div class="stat-row"><div class="stat"><small>호수</small><b>{n}호</b></div><div class="stat"><small>둘레</small><b>{circ}mm</b></div><div class="stat"><small>안지름</small><b>{dia:.1f}mm</b></div><div class="stat"><small>미국 US</small><b>{sz(us)}</b></div></div>
{ad()}
{t}
<h2 class="group-title">📌 손가락 둘레 재는 법</h2>
<ul class="lead" style="margin-left:20px"><li>실이나 종이 띠를 손가락 마디에 감아 겹치는 길이를 재면 둘레(mm)이고, 호수 = 둘레(mm) − 40입니다.</li><li>저녁에 손가락이 가장 크게 붓고 겨울엔 작아지므로 하루 중 여러 번 재 보세요.</li><li>넓은 반지는 한 호수 크게 고르는 것이 편합니다.</li></ul>
{chips([("반지 호수 변환표", "/ring-size/")])}
"""
    faq = [(f"반지 {n}호는 둘레가 얼마인가요?", f"약 {circ}mm(안지름 {dia:.1f}mm)입니다."), (f"반지 {n}호는 미국 사이즈로 몇인가요?", f"약 US {sz(us)}입니다."), ("반지 호수는 어떻게 계산하나요?", "손가락 둘레(mm)에서 40을 뺀 값이 호수입니다.")]
    write(path, layout(path, f"반지 {n}호 사이즈 — 둘레 {circ}mm, 미국 US {sz(us)}", f"반지 {n}호는 둘레 {circ}mm, 안지름 {dia:.1f}mm, 미국 사이즈 약 {sz(us)}. 호수 변환표와 손가락 둘레 재는 법.", body, faq, [("홈", "/"), ("반지 호수", "/ring-size/"), (f"{n}호", path)]), "0.6")

def hub_ring():
    rows = [['<a href="/ring-size/%d호/">%d호</a>' % (v, v), v + 40, "%.1f" % ((v + 40) / math.pi), sz(ring_us(v + 40))] for v in RINGS]
    body = f"""
<div class="page-head"><h1>반지 호수 변환표 — 한국 호수·미국 US·유럽 사이즈</h1><p>둘레(mm) − 40 = 호수</p></div>
<p class="lead">한국 반지 호수(일본과 동일)는 손가락 둘레(mm)에서 40을 뺀 값입니다. 호수를 눌러 둘레·안지름·미국(US) 사이즈 변환을 확인하세요. 여성은 보통 9~14호, 남성은 15~23호입니다.</p>
{ad()}
{table(['호수', '둘레(mm)', '안지름(mm)', '미국 US'], rows, (1, 2, 3))}
"""
    write("/ring-size/", layout("/ring-size/", "반지 호수 변환표 — 한국 호수·미국 US·유럽 사이즈", "반지 호수 1~30호의 둘레·안지름과 미국 US 사이즈 변환표. 손가락 둘레 재는 법.", body, [("반지 호수는 어떻게 재나요?", "손가락 둘레(mm)에서 40을 빼면 호수입니다.")], [("홈", "/"), ("반지 호수", "/ring-size/")], coupang=True), "0.9")

# ───────────────────────── 온도 ─────────────────────────
CS = list(range(-30, 46)); FS = list(range(0, 121))
def c2f(c): return c * 9 / 5 + 32
def f2c(f): return (f - 32) * 5 / 9
def c_context(c):
    if c <= -10: return "한파 수준의 매우 추운 날씨"
    if c <= 0: return "영하의 추운 날씨(물이 어는 온도)"
    if c <= 10: return "쌀쌀한 날씨"
    if c <= 20: return "선선하고 활동하기 좋은 날씨"
    if c <= 27: return "따뜻하고 쾌적한 날씨"
    if c <= 33: return "더운 날씨"
    return "폭염 수준의 매우 더운 날씨"

def page_c(c):
    f = c2f(c); path = "/temperature/c/%d/" % c
    lead = f"<p class=\"lead\"><b>섭씨 {c}도(℃)는 화씨 {n2(f, 1)}도(℉)</b>입니다. {c_context(c)}에 해당합니다. 계산은 {c} × 9/5 + 32 = {n2(f, 1)}입니다.</p>"
    t = table(["섭씨(℃)", "화씨(℉)"], [['<a href="/temperature/c/%d/">%d℃</a>' % (v, v) if v != c else "<b>%d℃</b>" % v, n2(c2f(v), 1)] for v in near(CS, c, 5)], (1,))
    body = f"""
<div class="page-head"><h1>섭씨 {c}도는 화씨 몇 도? — {n2(f, 1)}℉</h1><p>℃ → ℉ 변환</p></div>
{lead}
{ad()}
{t}
<ul class="lead" style="margin-left:20px"><li>섭씨 → 화씨: ℃ × 9/5 + 32</li><li>화씨 → 섭씨: (℉ − 32) × 5/9</li><li>물의 어는점은 0℃(32℉), 끓는점은 100℃(212℉), 체온은 약 36.5℃(97.7℉)입니다.</li></ul>
{chips([("온도 변환표", "/temperature/"), (f"화씨 {round(f)}도는 섭씨", "/temperature/f/%d/" % round(f)) if round(f) in FS else ("화씨→섭씨", "/temperature/")])}
"""
    faq = [(f"섭씨 {c}도는 화씨 몇 도인가요?", f"{n2(f, 1)}℉입니다."), ("섭씨를 화씨로 바꾸는 공식은?", "섭씨에 9/5를 곱하고 32를 더합니다.")]
    write(path, layout(path, f"섭씨 {c}도는 화씨 몇 도? {n2(f, 1)}℉ (℃→℉ 변환)", f"섭씨 {c}℃ = 화씨 {n2(f, 1)}℉. 섭씨·화씨 변환 공식과 비슷한 온도 표.", body, faq, [("홈", "/"), ("온도", "/temperature/"), (f"{c}℃", path)]), "0.6" if c % 5 == 0 else "0.4")

def page_f(f):
    c = f2c(f); path = "/temperature/f/%d/" % f
    ctx = c_context(round(c))
    lead = f"<p class=\"lead\"><b>화씨 {f}도(℉)는 섭씨 {n2(c, 1)}도(℃)</b>입니다. {ctx}에 해당합니다. 계산은 ({f} − 32) × 5/9 = {n2(c, 1)}입니다.</p>"
    t = table(["화씨(℉)", "섭씨(℃)"], [['<a href="/temperature/f/%d/">%d℉</a>' % (v, v) if v != f else "<b>%d℉</b>" % v, n2(f2c(v), 1)] for v in near(FS, f, 5)], (1,))
    body = f"""
<div class="page-head"><h1>화씨 {f}도는 섭씨 몇 도? — {n2(c, 1)}℃</h1><p>℉ → ℃ 변환</p></div>
{lead}
{ad()}
{t}
<ul class="lead" style="margin-left:20px"><li>화씨 → 섭씨: (℉ − 32) × 5/9</li><li>섭씨 → 화씨: ℃ × 9/5 + 32</li><li>오븐 요리에서 350℉는 약 175℃, 400℉는 약 205℃입니다.</li></ul>
{chips([("온도 변환표", "/temperature/"), (f"섭씨 {round(c)}도는 화씨", "/temperature/c/%d/" % round(c)) if round(c) in CS else ("섭씨→화씨", "/temperature/")])}
"""
    faq = [(f"화씨 {f}도는 섭씨 몇 도인가요?", f"{n2(c, 1)}℃입니다."), ("화씨를 섭씨로 바꾸는 공식은?", "화씨에서 32를 빼고 5/9를 곱합니다.")]
    write(path, layout(path, f"화씨 {f}도는 섭씨 몇 도? {n2(c, 1)}℃ (℉→℃ 변환)", f"화씨 {f}℉ = 섭씨 {n2(c, 1)}℃. 화씨·섭씨 변환 공식과 비슷한 온도 표.", body, faq, [("홈", "/"), ("온도", "/temperature/"), (f"{f}℉", path)]), "0.6" if f % 10 == 0 else "0.4")

def hub_temp():
    rows = [[('<a href="/temperature/c/%d/">%d℃</a>' % (c, c)), n2(c2f(c), 1), ('<a href="/temperature/f/%d/">%d℉</a>' % (f, f)), n2(f2c(f), 1)] for c, f in zip(range(-20, 41, 5), range(0, 121, 10))]
    body = f"""
<div class="page-head"><h1>섭씨 화씨 변환표 — ℃↔℉ 온도 변환</h1><p>℃ × 9/5 + 32 = ℉</p></div>
<p class="lead">섭씨(℃)와 화씨(℉)를 바꾸는 공식과 변환표입니다. 섭씨에 9/5를 곱하고 32를 더하면 화씨, 화씨에서 32를 빼고 5/9를 곱하면 섭씨입니다. 온도를 눌러 자세한 변환을 확인하세요.</p>
{ad()}
{table(['섭씨', '→ 화씨', '화씨', '→ 섭씨'], rows, (1, 3))}
"""
    write("/temperature/", layout("/temperature/", "섭씨 화씨 변환표 — ℃↔℉ (20도·30도·100도)", "섭씨·화씨 온도 변환 공식과 변환표. 섭씨 20도·25도·30도는 화씨 몇 도인지 한눈에.", body, [("섭씨 25도는 화씨 몇 도인가요?", "77℉입니다."), ("화씨 100도는 섭씨 몇 도인가요?", "약 37.8℃입니다.")], [("홈", "/"), ("온도", "/temperature/")]), "0.9")

# ───────────────────────── 길이(키) ─────────────────────────
CM = list(range(100, 221)); INCHES = list(range(1, 101))
def cm_ft(cm):
    inch = cm / INCH; ft = int(inch // 12); rem = inch - ft * 12
    return ft, rem, inch

def page_cm(cm):
    ft, rem, inch = cm_ft(cm); path = "/length/cm/%d/" % cm
    lead = f"<p class=\"lead\"><b>{cm}cm는 {ft}피트 {rem:.1f}인치</b>입니다(총 {inch:.1f}인치). 키가 {cm}cm라면 영어권에서는 {ft}′{rem:.1f}″처럼 씁니다. 1인치는 2.54cm, 1피트는 30.48cm입니다.</p>"
    t = table(["cm", "피트·인치", "인치"], [['<a href="/length/cm/%d/">%d</a>' % (v, v) if v != cm else "<b>%d</b>" % v, "%d′%.1f″" % (cm_ft(v)[0], cm_ft(v)[1]), "%.1f" % cm_ft(v)[2]] for v in near(CM, cm, 5)], (1, 2))
    body = f"""
<div class="page-head"><h1>{cm}cm 몇 피트 몇 인치? — {ft}′{rem:.1f}″</h1><p>cm → 피트·인치 변환 (키·길이)</p></div>
{lead}
{ad()}
{t}
<ul class="lead" style="margin-left:20px"><li>cm → 인치: cm ÷ 2.54</li><li>피트 = 인치 ÷ 12(나머지가 인치)</li><li>미국·영국 쇼핑몰의 키·사이즈 표기를 한국 cm로 바꿀 때 유용합니다.</li></ul>
{chips([("키 cm↔피트 변환표", "/length/"), ("인치→cm", "/length/inch/%d/" % (round(inch) if 1 <= round(inch) <= 100 else 10))])}
"""
    faq = [(f"{cm}cm는 몇 피트인가요?", f"{ft}피트 {rem:.1f}인치(약 {cm / 30.48:.2f}피트)입니다."), ("1인치는 몇 cm인가요?", "2.54cm입니다.")]
    write(path, layout(path, f"{cm}cm 몇 피트 몇 인치? {ft}′{rem:.1f}″ (키 변환)", f"{cm}cm = {ft}피트 {rem:.1f}인치({inch:.1f}인치). cm를 피트·인치로 바꾸는 방법과 키 변환표.", body, faq, [("홈", "/"), ("키·길이", "/length/"), (f"{cm}cm", path)]), "0.6" if cm % 5 == 0 else "0.4")

def page_inch(i):
    cm = i * INCH; path = "/length/inch/%d/" % i
    lead = f"<p class=\"lead\"><b>{i}인치는 {n2(cm, 2)}cm</b>입니다(1인치 = 2.54cm). {n2(cm * 10, 1)}mm이고 {i / 12:.2f}피트입니다.</p>"
    t = table(["인치", "cm"], [['<a href="/length/inch/%d/">%d</a>' % (v, v) if v != i else "<b>%d</b>" % v, n2(v * INCH, 2)] for v in near(INCHES, i, 5)], (1,))
    body = f"""
<div class="page-head"><h1>{i}인치는 몇 cm? — {n2(cm, 2)}cm</h1><p>인치 → cm 변환 (모니터·TV·화면 크기)</p></div>
{lead}
{ad()}
{t}
<ul class="lead" style="margin-left:20px"><li>인치 → cm: 인치 × 2.54</li><li>TV·모니터 인치는 화면 대각선 길이입니다. {i}인치 화면의 대각선은 약 {n2(cm, 1)}cm입니다.</li></ul>
{chips([("인치↔cm 변환표", "/length/")])}
"""
    faq = [(f"{i}인치는 몇 cm인가요?", f"{n2(cm, 2)}cm입니다."), (f"{i}인치 TV 크기는?", f"화면 대각선이 약 {n2(cm, 1)}cm입니다(가로·세로는 화면 비율에 따라 다름).")]
    write(path, layout(path, f"{i}인치는 몇 cm? {n2(cm, 2)}cm (인치↔cm 변환)", f"{i}인치 = {n2(cm, 2)}cm. 모니터·TV 화면 크기와 인치를 cm로 바꾸는 방법.", body, faq, [("홈", "/"), ("키·길이", "/length/"), (f"{i}인치", path)]), "0.6" if i % 5 == 0 else "0.4")

def hub_length():
    rows = [['<a href="/length/cm/%d/">%d</a>' % (c, c), "%d′%.1f″" % (cm_ft(c)[0], cm_ft(c)[1])] for c in range(140, 201, 5)]
    rows2 = [['<a href="/length/inch/%d/">%d인치</a>' % (i, i), n2(i * INCH, 1) + "cm"] for i in (10, 15, 20, 24, 27, 32, 40, 43, 50, 55, 65, 75)]
    body = f"""
<div class="page-head"><h1>키 cm → 피트·인치 변환표 / 인치 → cm</h1><p>1인치 = 2.54cm</p></div>
<p class="lead">키(cm)를 피트·인치로, 인치를 cm로 바꾸는 표입니다. 1인치는 2.54cm, 1피트는 30.48cm입니다. 값을 눌러 자세한 변환을 확인하세요.</p>
{ad()}
{table(['키(cm)', '피트·인치'], rows, (1,))}
<h2 class="group-title">🖥️ 화면 인치 → cm</h2>
{table(['인치', 'cm'], rows2, (1,))}
"""
    write("/length/", layout("/length/", "키 cm 피트 인치 변환표 — 170cm·180cm 몇 피트? / 인치→cm", "키 cm를 피트·인치로, 인치를 cm로 바꾸는 변환표. 170cm·175cm·180cm 키 변환과 TV·모니터 인치 크기.", body, [("키 170cm는 몇 피트인가요?", "5피트 6.9인치(약 5′7″)입니다."), ("키 180cm는?", "5피트 10.9인치(약 5′11″)입니다.")], [("홈", "/"), ("키·길이", "/length/")]), "0.9")

# ───────────────────────── 몸무게 ─────────────────────────
KG = list(range(30, 201)); LBS = list(range(70, 301))
def page_kg(k):
    lb = k / LB; path = "/weight/kg/%d/" % k
    lead = f"<p class=\"lead\"><b>{k}kg는 약 {lb:.1f}파운드(lb)</b>입니다(1kg = 2.2046lb). 스톤으로는 약 {lb / 14:.1f}st입니다.</p>"
    t = table(["kg", "파운드(lb)"], [['<a href="/weight/kg/%d/">%d</a>' % (v, v) if v != k else "<b>%d</b>" % v, "%.1f" % (v / LB)] for v in near(KG, k, 5)], (1,))
    body = f"""
<div class="page-head"><h1>{k}kg는 몇 파운드(lb)? — {lb:.1f}lb</h1><p>kg → 파운드 변환 (몸무게)</p></div>
{lead}
{ad()}
{t}
<ul class="lead" style="margin-left:20px"><li>kg → lb: kg × 2.20462</li><li>lb → kg: lb × 0.45359</li><li>미국·영국 체중 표기나 운동 기구(바벨 원판) 무게를 kg로 바꿀 때 사용합니다.</li></ul>
{chips([("몸무게 kg↔lb 변환표", "/weight/"), ("파운드→kg", "/weight/lb/%d/" % (round(lb) if 70 <= round(lb) <= 300 else 150))])}
"""
    faq = [(f"{k}kg는 몇 파운드인가요?", f"약 {lb:.1f}파운드입니다."), ("1kg는 몇 파운드인가요?", "약 2.2046파운드입니다.")]
    write(path, layout(path, f"{k}kg는 몇 파운드(lb)? {lb:.1f}lb (몸무게 변환)", f"{k}kg = {lb:.1f}파운드(lb). kg를 파운드로 바꾸는 방법과 몸무게 변환표.", body, faq, [("홈", "/"), ("몸무게", "/weight/"), (f"{k}kg", path)]), "0.6" if k % 5 == 0 else "0.4")

def page_lb(l):
    kg = l * LB; path = "/weight/lb/%d/" % l
    lead = f"<p class=\"lead\"><b>{l}파운드(lb)는 약 {kg:.1f}kg</b>입니다(1lb = 0.45359kg). 스톤으로는 {l / 14:.1f}st입니다.</p>"
    t = table(["파운드(lb)", "kg"], [['<a href="/weight/lb/%d/">%d</a>' % (v, v) if v != l else "<b>%d</b>" % v, "%.1f" % (v * LB)] for v in near(LBS, l, 5)], (1,))
    body = f"""
<div class="page-head"><h1>{l}파운드는 몇 kg? — {kg:.1f}kg</h1><p>lb → kg 변환 (체중·운동 기구)</p></div>
{lead}
{ad()}
{t}
<ul class="lead" style="margin-left:20px"><li>lb → kg: 파운드 × 0.45359</li><li>kg → lb: kg × 2.20462</li></ul>
{chips([("몸무게 kg↔lb 변환표", "/weight/")])}
"""
    faq = [(f"{l}파운드는 몇 kg인가요?", f"약 {kg:.1f}kg입니다."), ("1파운드는 몇 g인가요?", "약 453.6g입니다.")]
    write(path, layout(path, f"{l}파운드(lb)는 몇 kg? {kg:.1f}kg (lb→kg 변환)", f"{l}lb = {kg:.1f}kg. 파운드를 kg로 바꾸는 방법과 변환표.", body, faq, [("홈", "/"), ("몸무게", "/weight/"), (f"{l}lb", path)]), "0.6" if l % 10 == 0 else "0.4")

def hub_weight():
    rows = [['<a href="/weight/kg/%d/">%d</a>' % (k, k), "%.1f" % (k / LB), '<a href="/weight/lb/%d/">%d</a>' % (l, l), "%.1f" % (l * LB)] for k, l in zip(range(40, 121, 5), range(90, 300, 12))]
    body = f"""
<div class="page-head"><h1>kg 파운드 변환표 — 몸무게 kg↔lb</h1><p>1kg = 2.2046lb · 1lb = 0.4536kg</p></div>
<p class="lead">킬로그램(kg)과 파운드(lb)를 바꾸는 변환표입니다. kg에 2.20462를 곱하면 파운드, 파운드에 0.45359를 곱하면 kg입니다. 값을 눌러 자세한 변환을 확인하세요.</p>
{ad()}
{table(['kg', '→ 파운드', '파운드', '→ kg'], rows, (1, 3))}
"""
    write("/weight/", layout("/weight/", "kg 파운드 변환표 — 60kg·70kg·80kg 몇 파운드?", "몸무게 kg를 파운드(lb)로, 파운드를 kg로 바꾸는 변환표와 공식.", body, [("70kg는 몇 파운드인가요?", "약 154.3파운드입니다."), ("150파운드는 몇 kg인가요?", "약 68kg입니다.")], [("홈", "/"), ("몸무게", "/weight/")]), "0.9")

# ───────────────────────── 거리·부피 ─────────────────────────
NUMS = list(range(1, 101)); GALS = list(range(1, 51))
def page_mile(n):
    km = n * MILE; path = "/distance/mile/%d/" % n
    lead = f"<p class=\"lead\"><b>{n}마일은 {km:.2f}km</b>입니다(1마일 = 1.609km)."
    lead += " 시속으로 {n}mph는 약 {km:.1f}km/h입니다.</p>".format(n=n, km=km)
    t = table(["마일", "km"], [['<a href="/distance/mile/%d/">%d</a>' % (v, v) if v != n else "<b>%d</b>" % v, "%.2f" % (v * MILE)] for v in near(NUMS, n, 5)], (1,))
    body = f"""
<div class="page-head"><h1>{n}마일은 몇 km? — {km:.2f}km</h1><p>마일 → km 변환 (거리·속도)</p></div>
{lead}
{ad()}
{t}
<ul class="lead" style="margin-left:20px"><li>마일 → km: 마일 × 1.609344</li><li>km → 마일: km × 0.621371</li></ul>
{chips([("km→마일", "/distance/km/%d/" % n), ("거리 변환표", "/distance/")])}
"""
    faq = [(f"{n}마일은 몇 km인가요?", f"{km:.2f}km입니다."), (f"{n}km는 몇 마일인가요?", f"약 {n / MILE:.2f}마일입니다.")]
    write(path, layout(path, f"{n}마일은 몇 km? {km:.2f}km (마일→km 변환)", f"{n}마일 = {km:.2f}km. 마일을 km로 바꾸는 방법과 변환표.", body, faq, [("홈", "/"), ("거리", "/distance/"), (f"{n}마일", path)]), "0.5")

def page_km(n):
    mi = n / MILE; path = "/distance/km/%d/" % n
    lead = f"<p class=\"lead\"><b>{n}km는 약 {mi:.2f}마일</b>입니다(1km = 0.6214마일). 시속 {n}km/h는 약 {mi:.1f}mph입니다.</p>"
    t = table(["km", "마일"], [['<a href="/distance/km/%d/">%d</a>' % (v, v) if v != n else "<b>%d</b>" % v, "%.2f" % (v / MILE)] for v in near(NUMS, n, 5)], (1,))
    body = f"""
<div class="page-head"><h1>{n}km는 몇 마일? — {mi:.2f}마일</h1><p>km → 마일 변환 (거리·러닝·속도)</p></div>
{lead}
{ad()}
{t}
<ul class="lead" style="margin-left:20px"><li>km → 마일: km × 0.621371</li><li>마라톤 42.195km는 약 26.2마일, 하프마라톤 21.0975km는 약 13.1마일입니다.</li></ul>
{chips([("마일→km", "/distance/mile/%d/" % n), ("거리 변환표", "/distance/")])}
"""
    faq = [(f"{n}km는 몇 마일인가요?", f"약 {mi:.2f}마일입니다."), ("마라톤은 몇 마일인가요?", "42.195km로 약 26.2마일입니다.")]
    write(path, layout(path, f"{n}km는 몇 마일? {mi:.2f}마일 (km→마일 변환)", f"{n}km = {mi:.2f}마일. km를 마일로 바꾸는 방법과 변환표.", body, faq, [("홈", "/"), ("거리", "/distance/"), (f"{n}km", path)]), "0.5")

def page_gal(n):
    l = n * GAL; path = "/volume/gallon/%d/" % n
    lead = f"<p class=\"lead\"><b>{n}갤런(미국)은 약 {l:.2f}리터(L)</b>입니다(1갤런 = 3.785L). 영국 갤런(4.546L)은 약 {n * 4.54609:.2f}L입니다.</p>"
    t = table(["갤런(US)", "리터"], [['<a href="/volume/gallon/%d/">%d</a>' % (v, v) if v != n else "<b>%d</b>" % v, "%.2f" % (v * GAL)] for v in near(GALS, n, 5)], (1,))
    body = f"""
<div class="page-head"><h1>{n}갤런은 몇 리터? — {l:.2f}L</h1><p>갤런 → 리터 변환 (미국 갤런 기준)</p></div>
{lead}
{ad()}
{t}
<ul class="lead" style="margin-left:20px"><li>미국 갤런 → 리터: 갤런 × 3.785</li><li>리터 → 갤런: 리터 × 0.2642</li><li>연비 mpg를 km/L로 바꿀 때는 mpg × 0.4251입니다.</li></ul>
{chips([("갤런·마일 변환", "/distance/")])}
"""
    faq = [(f"{n}갤런은 몇 리터인가요?", f"미국 갤런 기준 약 {l:.2f}L입니다."), ("30mpg는 몇 km/L인가요?", "약 12.8km/L입니다.")]
    write(path, layout(path, f"{n}갤런은 몇 리터? {l:.2f}L (갤런→L 변환)", f"{n}갤런(미국) = {l:.2f}리터. 갤런을 리터로 바꾸는 방법과 변환표.", body, faq, [("홈", "/"), ("거리·부피", "/distance/"), (f"{n}갤런", path)]), "0.4")

def hub_distance():
    rows = [['<a href="/distance/mile/%d/">%d마일</a>' % (n, n), "%.2f" % (n * MILE), '<a href="/distance/km/%d/">%dkm</a>' % (n, n), "%.2f" % (n / MILE)] for n in (1, 3, 5, 10, 20, 30, 50, 60, 70, 100)]
    body = f"""
<div class="page-head"><h1>마일 km 변환표 — 거리·갤런 리터 변환</h1><p>1마일 = 1.609km · 1갤런 = 3.785L</p></div>
<p class="lead">마일과 km, 갤런과 리터를 바꾸는 변환표입니다. 마일에 1.609를 곱하면 km, km에 0.6214를 곱하면 마일입니다. 값을 눌러 자세한 변환을 확인하세요.</p>
{ad()}
{table(['마일', '→ km', 'km', '→ 마일'], rows, (1, 3))}
{chips([("10갤런 몇 리터", "/volume/gallon/10/"), ("5갤런 몇 리터", "/volume/gallon/5/")])}
"""
    write("/distance/", layout("/distance/", "마일 km 변환표 — 1마일 몇 km? 갤런 리터 변환", "마일을 km로, km를 마일로 바꾸는 변환표와 갤런→리터 변환. 60마일·100마일 몇 km인지 한눈에.", body, [("1마일은 몇 km인가요?", "약 1.609km입니다."), ("60마일은 몇 km인가요?", "약 96.56km입니다.")], [("홈", "/"), ("거리", "/distance/")]), "0.9")

# ───────────────────────── 홈·기타 ─────────────────────────
def page_home():
    body = f"""
<div class="hero"><h1>📏 단위 변환 — 평·신발·반지·온도·키·몸무게</h1><p>자주 찾는 단위와 사이즈를 값별로 바로 확인하세요.</p></div>
{ad()}
<div class="card-grid">
<a class="card" href="/pyeong/"><b>🏠 평↔㎡</b><span>30평은 몇 ㎡? 84㎡는 몇 평?</span></a>
<a class="card" href="/shoe-size/"><b>👟 신발 사이즈</b><span>한국 mm ↔ 미국·유럽·일본</span></a>
<a class="card" href="/ring-size/"><b>💍 반지 호수</b><span>호수 ↔ 둘레·미국 사이즈</span></a>
<a class="card" href="/temperature/"><b>🌡️ 섭씨↔화씨</b><span>20℃는 화씨 몇 도?</span></a>
<a class="card" href="/length/"><b>📐 키·인치</b><span>170cm 몇 피트? 인치→cm</span></a>
<a class="card" href="/weight/"><b>⚖️ kg↔파운드</b><span>70kg는 몇 lb?</span></a>
<a class="card" href="/distance/"><b>🛣️ 마일↔km·갤런</b><span>60마일은 몇 km?</span></a>
</div>
<h2 class="group-title">🔥 많이 찾는 변환</h2>
{chips([("30평", "/pyeong/30평/"), ("34평", "/pyeong/34평/"), ("84㎡", "/sqm/84/"), ("59㎡", "/sqm/59/"), ("신발 250mm", "/shoe-size/250mm/"), ("신발 270mm", "/shoe-size/270mm/"), ("섭씨 25도", "/temperature/c/25/"), ("170cm", "/length/cm/170/"), ("70kg", "/weight/kg/70/")])}
<p class="lead">우아단위는 평·㎡, 신발·반지 사이즈, 온도, 키·길이, 몸무게, 거리 같은 자주 쓰는 단위를 값별 페이지로 정리했습니다. 정의값으로 계산한 변환은 정확하지만 신발·반지 사이즈는 브랜드별로 다른 <b>근삿값</b>입니다. 자세한 기준은 <a href="/about/">변환 기준</a>을 참고하세요.</p>
"""
    faq = [("1평은 몇 제곱미터인가요?", "3.3058㎡입니다."), ("신발 사이즈 변환은 정확한가요?", "나이키 사이즈표 기준의 근삿값입니다. 브랜드마다 반 사이즈 정도 차이가 날 수 있습니다.")]
    write("/", layout("/", "우아단위 — 평·신발 사이즈·반지 호수·온도·키·몸무게 변환", "평↔㎡, 신발 사이즈(mm↔US·EU), 반지 호수, 섭씨↔화씨, 키 cm↔피트, kg↔파운드 변환을 값별로 바로 확인하세요.", body, faq), "1.0")

def page_about():
    body = """
<div class="page-head"><h1>변환 기준</h1><p>어떤 값을 기준으로 계산했는지 공개합니다</p></div>
<h2 class="group-title">📐 정의값으로 계산하는 변환</h2><p class="lead">1평 = 400/121㎡(약 3.3058㎡), 1㎡ = 10.7639ft², 1인치 = 2.54cm, 1파운드 = 0.45359237kg, 1마일 = 1.609344km, 1미국 갤런 = 3.785411784L, 섭씨↔화씨 = ℃×9/5+32. 이 값들은 정의로 정해진 것이라 결과가 정확합니다.</p>
<h2 class="group-title">👟 근삿값으로 정리하는 사이즈 변환</h2><p class="lead">신발 사이즈는 한국 발 길이(mm)를 기준으로 남성 US = (mm−180)÷10, 여성 US = 남성 US+1.5, UK = 남성 US−1로 계산하고 EU는 나이키 사이즈표 값을 따랐습니다. 반지는 호수 = 손가락 둘레(mm)−40, 미국 사이즈 = (둘레−36.5)÷2.55로 계산했습니다. 브랜드·모델·발볼에 따라 반 사이즈 정도 차이가 날 수 있으므로 구매 전 해당 브랜드의 공식 사이즈표를 확인하세요. 아기·어린이 신발의 월령·나이는 평균적인 안내입니다.</p>
<h2 class="group-title">🏢 아파트 평형</h2><p class="lead">‘○○평형’은 보통 공급면적(전용+주거공용) 기준이며 전용률(전용면적÷공급면적)은 단지에 따라 대략 70~85%입니다. 이 사이트의 환산은 대략적인 안내이며 정확한 면적은 분양 공고·건축물대장으로 확인하세요.</p>
<h2 class="group-title">📬 문의·정정</h2><p class="lead">오류 제보는 <a href="mailto:ingmaster83@gmail.com">ingmaster83@gmail.com</a> 으로 보내 주세요.</p>
"""
    write("/about/", layout("/about/", "변환 기준 — 정의값과 근삿값", "우아단위가 사용하는 단위 변환 정의값과 신발·반지 사이즈 근사 기준을 공개합니다.", body, None, [("홈", "/"), ("변환 기준", "/about/")]), "0.5")

def page_privacy():
    body = """
<div class="page-head"><h1>개인정보처리방침</h1></div>
<p class="lead">우아단위(wooaunit.wooahouse.com, 이하 “서비스”)는 회원가입·로그인을 요구하지 않으며 이용자의 개인정보를 직접 수집하지 않습니다. 변환기에 입력한 값은 브라우저 안에서만 처리됩니다.</p>
<h3>자동 수집 정보</h3><p class="lead">서비스 개선을 위해 Google Analytics로 방문자 수·페이지뷰 등 익명 통계를 수집하며, Google AdSense와 쿠팡 파트너스는 맞춤 광고를 위해 쿠키를 사용할 수 있습니다. 쿠키는 브라우저 설정에서 비활성화할 수 있습니다. (<a href="https://policies.google.com/privacy">Google 개인정보처리방침</a>, <a href="https://policies.google.com/technologies/ads">Google 광고 정책</a>)</p>
<h3>쿠팡 파트너스</h3><p class="lead">일부 페이지에는 쿠팡 파트너스 활동의 일환으로 광고가 포함되어 있으며 이에 따른 수수료를 제공받을 수 있습니다.</p>
<h3>문의</h3><p class="lead"><a href="mailto:ingmaster83@gmail.com">ingmaster83@gmail.com</a></p>
<p class="note">최종 수정일: 2026년 10월 21일</p>
"""
    write("/privacy/", layout("/privacy/", "개인정보처리방침", "우아단위 개인정보처리방침", body, None, [("홈", "/"), ("개인정보처리방침", "/privacy/")]), sitemap=False)

def make_og():
    f = ROOT / "assets" / "og-image.png"
    if f.exists(): return
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return
    im = Image.new("RGB", (1200, 630), (124, 58, 237)); dr = ImageDraw.Draw(im)
    def font(sz):
        for n in ("malgunbd.ttf", "malgun.ttf", "NanumGothicBold.ttf"):
            try: return ImageFont.truetype(n, sz)
            except Exception: pass
        return ImageFont.load_default()
    dr.rounded_rectangle((90, 90, 1110, 540), 40, fill=(255, 255, 255))
    dr.text((150, 150), "우아단위", font=font(110), fill=(91, 33, 182))
    dr.text((150, 300), "평 · 신발 · 반지 · 온도 · 키 · 몸무게", font=font(52), fill=(31, 41, 55))
    dr.text((150, 380), "단위·사이즈 변환", font=font(54), fill=(31, 41, 55))
    dr.text((150, 470), "wooaunit.wooahouse.com", font=font(34), fill=(107, 114, 128))
    im.save(f)

def main():
    t0 = time.time(); make_og()
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)
    for nf in ROOT.glob("naver*.html"): shutil.copy(nf, OUT / nf.name)
    for n in PY_LIST: page_pyeong(n)
    for m in SQM_LIST: page_sqm(m)
    hub_pyeong()
    for mm in SHOES: page_shoe(mm)
    for mm in KIDS: page_kid_shoe(mm)
    hub_shoe()
    for n in RINGS: page_ring(n)
    hub_ring()
    for c in CS: page_c(c)
    for f in FS: page_f(f)
    hub_temp()
    for cm in CM: page_cm(cm)
    for i in INCHES: page_inch(i)
    hub_length()
    for k in KG: page_kg(k)
    for l in LBS: page_lb(l)
    hub_weight()
    for n in NUMS: page_mile(n); page_km(n)
    for n in GALS: page_gal(n)
    hub_distance(); page_home(); page_about(); page_privacy()
    today = time.strftime("%Y-%m-%d")
    chunks = [WRITTEN[i:i + 40000] for i in range(0, len(WRITTEN), 40000)]
    urls = "".join("<url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>" % (BASE, q(p), today, pr) for p, pr in WRITTEN)
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>\n' % urls, encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % BASE, encoding="utf-8")
    (OUT / "CNAME").write_text("wooaunit.wooahouse.com\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    nf = layout("/404.html", "페이지를 찾을 수 없습니다", "요청한 페이지를 찾을 수 없습니다.", '<div class="page-head"><h1>페이지를 찾을 수 없습니다</h1></div><div class="chips"><a class="chip" href="/">홈</a><a class="chip" href="/pyeong/">평↔㎡</a></div>', None, None, noindex=True)
    (OUT / "404.html").write_text(nf, encoding="utf-8")
    print("pages", len(WRITTEN), "elapsed", round(time.time() - t0), "s")

if __name__ == "__main__":
    main()
