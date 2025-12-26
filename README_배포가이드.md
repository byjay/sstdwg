# SSTDMS 완전판 배포 가이드

## 📦 패키지 내용

이 ZIP 파일에는 김봉정 수석설계사(designsir@seastargo.com)가 개발한 SSTDMS의 완전한 시스템이 포함되어 있습니다.

### 포함된 파일 및 폴더

```
SSTDMS_완전판_최종배포.zip
├── sstdms_erp/
│   ├── sstdms_backend/
│   │   ├── src/                    # 백엔드 소스 코드
│   │   │   ├── routes/            # API 라우트
│   │   │   ├── models/            # 데이터 모델
│   │   │   ├── utils/             # 유틸리티 함수
│   │   │   ├── config/            # 설정 파일
│   │   │   └── static/            # 정적 파일
│   │   └── requirements.txt       # Python 의존성
│   └── sstdms_frontend/
│       ├── src/                   # 프론트엔드 소스 코드
│       ├── public/                # 공개 파일
│       ├── package.json           # Node.js 의존성
│       ├── vite.config.js         # Vite 설정
│       └── tailwind.config.js     # Tailwind CSS 설정
├── SSTDMS_통합매뉴얼_완전판.md      # 완전한 사용자 매뉴얼
├── SSTDMS_30회_테스트_보고서.md     # 테스트 보고서
├── SSTDMS_확장성_기능_상세기록.md    # 확장성 기능 문서
└── test_screenshots/              # 테스트 스크린샷
```

## 🚀 설치 및 실행 가이드

### 1. 시스템 요구사항

**서버 환경**:
- Python 3.8 이상 (권장: 3.11)
- Node.js 16.0 이상 (권장: 20.x LTS)
- 메모리: 최소 4GB RAM
- 저장공간: 최소 10GB

**클라이언트 환경**:
- 모던 웹 브라우저 (Chrome, Firefox, Safari, Edge)
- 화면 해상도: 최소 1280x720

### 2. 백엔드 설치

```bash
# 1. 프로젝트 디렉토리로 이동
cd sstdms_erp/sstdms_backend

# 2. Python 가상환경 생성
python3 -m venv venv

# 3. 가상환경 활성화
source venv/bin/activate  # Linux/Mac
# 또는 venv\Scripts\activate  # Windows

# 4. 의존성 설치
pip install -r requirements.txt

# 5. 추가 보안 패키지 설치
pip install bcrypt cryptography

# 6. 데이터베이스 초기화
cd src
python init_users.py

# 7. 보안 사용자 시스템 초기화
python -c "
from utils.user_manager import SecureUserManager
user_manager = SecureUserManager()
user_manager.initialize_default_users()
"

# 8. 서버 시작
python main.py
```

### 3. 프론트엔드 설치

```bash
# 1. 프론트엔드 디렉토리로 이동
cd sstdms_erp/sstdms_frontend

# 2. 의존성 설치
npm install

# 3. 개발 서버 시작
npm run dev

# 또는 프로덕션 빌드
npm run build
```

### 4. 접속 및 로그인

**시스템 접속**: http://localhost:5000

**기본 계정 정보**:
- 관리자: admin@seastargo.com / 1234
- 개발자: designsir@seastargo.com / (임시 비밀번호)

## 🔧 설정 및 커스터마이징

### 보안 설정

**비밀번호 정책** (config/users.json):
```json
{
  "security": {
    "password_policy": {
      "min_length": 8,
      "require_uppercase": true,
      "require_lowercase": true,
      "require_numbers": true,
      "require_special": true,
      "max_age_days": 90
    }
  }
}
```

**세션 설정**:
```json
{
  "session": {
    "timeout_minutes": 60,
    "max_concurrent_sessions": 3
  }
}
```

### 브랜딩 커스터마이징

**로고 변경**:
- 파일 위치: `sstdms_backend/src/static/assets/`
- 권장 크기: 200x60px (PNG 형식)

**색상 테마 변경**:
- 파일: `sstdms_frontend/tailwind.config.js`
- Seastar Design 브랜드 컬러 적용됨

## 📚 문서 및 매뉴얼

### 1. 통합 매뉴얼
`SSTDMS_통합매뉴얼_완전판.md` - 전체 시스템 사용법

### 2. 테스트 보고서
`SSTDMS_30회_테스트_보고서.md` - 시스템 테스트 결과

### 3. 확장성 문서
`SSTDMS_확장성_기능_상세기록.md` - 시스템 확장 방안

## 🔒 보안 주의사항

### 프로덕션 배포 시 필수 사항

1. **비밀번호 변경**: 모든 기본 비밀번호 변경
2. **HTTPS 적용**: SSL 인증서 설치
3. **방화벽 설정**: 필요한 포트만 개방
4. **정기 백업**: 데이터베이스 및 파일 백업
5. **로그 모니터링**: 보안 이벤트 모니터링

### 권장 보안 설정

```bash
# 방화벽 설정 (Ubuntu)
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable

# SSL 인증서 설치 (Let's Encrypt)
sudo apt install certbot
sudo certbot --nginx -d yourdomain.com
```

## 🚀 프로덕션 배포

### Docker 배포 (권장)

```dockerfile
# Dockerfile 예시
FROM python:3.11-slim

WORKDIR /app
COPY sstdms_backend/requirements.txt .
RUN pip install -r requirements.txt

COPY sstdms_backend/src/ .
EXPOSE 5000

CMD ["python", "main.py"]
```

### 클라우드 배포

**AWS 배포**:
- EC2 인스턴스 사용
- RDS 데이터베이스 연동
- S3 파일 스토리지 활용

**Azure 배포**:
- App Service 사용
- Azure Database 연동
- Blob Storage 활용

## 📞 지원 및 문의

**개발자 연락처**:
- 김봉정 수석설계사: designsir@seastargo.com
- 회사: Seastar Design
- 슬로건: "World Shipbuilding & Offshore Design Provider"

**기술 지원**:
- 시스템 사용법 문의
- 커스터마이징 요청
- 버그 신고 및 개선 제안

## 📄 라이선스 및 저작권

본 시스템의 모든 권리는 Seastar Design에 있으며, 김봉정 수석설계사가 개발했습니다.
무단 복제 및 배포를 금지하며, 사용 시 반드시 개발자에게 문의하시기 바랍니다.

---

**배포 정보**
- 배포 일시: 2025년 7월 31일
- 버전: 1.0.0
- 개발자: 김봉정 (designsir@seastargo.com)


