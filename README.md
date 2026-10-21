# 우아단위 (wooaunit.wooahouse.com)
평↔㎡, 신발 사이즈, 반지 호수, 섭씨↔화씨, 키 cm↔피트, kg↔lb, 마일↔km, 갤런 변환 pSEO 정적 사이트(1,704페이지).
- 빌드: `python scripts/build_site.py` → `_site/` / 검증: `python scripts/check_site.py`
- 정의값(평=400/121㎡, 인치=2.54cm 등)은 정확, 신발·반지 사이즈는 나이키 표 기준 근삿값
- 배포: GitHub Actions(deploy.yml). 네이버 토큰은 `scripts/common.py` NAVER_TOKEN, 인증 파일은 루트 `naver*.html`
