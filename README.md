# Stock Dashboard

개인용 미국주식 포트폴리오 모바일 웹 대시보드입니다.

## 현재 구성
- 현재가
- 당일 등락률 및 상승/하락 표시
- 보유수량 기준 평가금액
- 52주 고점 대비 하락률
- 평균매입가 입력 시 매수가 대비 수익률 및 전체 손익
- 모바일 다크모드

## 1. GitHub에 올리기
이 ZIP을 압축 해제한 뒤 `index.html`, `style.css`, `app.js`, `README.md` 네 파일을
GitHub의 `k9200596-cell/Stock` 저장소 최상위(root)에 업로드합니다.

GitHub 저장소 화면:
1. Add file
2. Upload files
3. 네 파일 선택
4. Commit changes

## 2. GitHub Pages 켜기
저장소에서:
Settings → Pages → Build and deployment → Source: Deploy from a branch
→ Branch: main / (root) → Save

잠시 후 Pages 주소가 표시됩니다.

## 3. 평균매입가 입력
`app.js` 상단의 `portfolio`에서 `avg: 0`을 실제 달러 기준 평균매입가로 바꾸면
매수가 대비 수익률, 총손익, 총수익률이 자동 계산됩니다.

## 중요
현재 시세 조회는 Yahoo Finance 공개 chart endpoint를 사용하는 개인용 프로토타입입니다.
공식 실시간 시세 API가 아니며 지연, 호출 제한, CORS 정책 변경 가능성이 있습니다.
장기적으로 안정적인 운영을 원하면 금융 데이터 API + 서버리스 프록시 방식으로 전환하세요.
