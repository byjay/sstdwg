# SSTDMS 프로젝트 시작 가이드

## 🚀 즉시 시작하기

### 1. 압축 파일 해제 후 환경 설정
```bash
# 압축 해제
unzip SSTDMS_현재완료파일_v1.0.zip
cd SSTDMS_현재완료파일_v1.0

# 백엔드 환경 설정
cd sstdms_erp/sstdms_backend
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors pandas bcrypt cryptography

# 데이터베이스 초기화
cd src
python init_users.py

# 서버 실행
python main.py
```

### 2. 테스트 계정
- **관리자**: admin@seastargo.com / admin123
- **등록자**: designsir@seastargo.com / OKpmknu4v6_K3mDu
- **사용자**: user@seastargo.com / user123

### 3. 접속 URL
- **웹 시스템**: http://localhost:5000
- **API 문서**: http://localhost:5000/api/docs

## 📋 A/B 역할별 즉시 할 일

### A 역할 (백엔드 개발자) - 우선순위 1
1. 로그인 시스템 수정
2. 실시간 알림 시스템 구현
3. 보안 시스템 통합

### B 역할 (프론트엔드 개발자) - 우선순위 1  
1. 모바일 앱 CSS/JS 완성
2. React 컴포넌트 완성
3. 사용자별 매뉴얼 작성

## 🔧 문제 해결
로그인 실패 시: `rm database/app.db && python init_users.py`

