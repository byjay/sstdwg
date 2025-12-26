# SSTDMS ERP System

**Seastar Design Technical Document Management System**

오픈소스 기반의 독립적인 ERP 시스템으로, 조선소 및 설계 회사의 프로젝트 관리, 도면 관리, 문서 관리를 위한 통합 솔루션입니다.

## 🚀 주요 기능

### 📋 프로젝트 관리
- 프로젝트 생성 및 관리
- 프로젝트별 권한 관리
- 진행 상황 추적

### 📐 도면 관리
- 카테고리별 도면 분류 (COMMON, HULL, ACCOMMODATION, OUTFITTING, PIPING, ELECTRICAL)
- 도면 유형 관리 (BASIC, APPROVAL, PRODUCTION)
- 진행률 및 상태 추적
- 자동 간트차트 생성

### 📁 파일 관리
- 프로젝트별 폴더 구조 자동 생성
- 로컬 네트워크 저장소 연동
- 파일 암호화 및 워터마크 적용
- 버전 관리 및 백업

### 👥 사용자 관리
- 관리자/등록자 역할 구분
- 프로젝트별 권한 부여
- Seastar Design 직원 계정 사전 설정

### 📊 엑셀 연동
- 도면 리스트 엑셀 업로드/다운로드
- 간트차트 엑셀 내보내기
- 사용자 정의 양식 지원

## 🛠 기술 스택

### Backend
- **Flask** - Python 웹 프레임워크
- **SQLite** - 데이터베이스
- **SQLAlchemy** - ORM
- **Werkzeug** - 보안 및 유틸리티

### Frontend
- **React** - 사용자 인터페이스
- **Tailwind CSS** - 스타일링
- **Lucide React** - 아이콘

### 파일 처리
- **Pillow** - 이미지 처리 및 워터마크
- **openpyxl** - 엑셀 파일 처리
- **cryptography** - 파일 암호화

## 📦 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/byjay/cstar1.git
cd cstar1
```

### 2. Backend 설정
```bash
cd sstdms_backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend 설정
```bash
cd sstdms_frontend
npm install
npm run build
```

### 4. 데이터베이스 초기화
```bash
cd sstdms_backend/src
python init_users.py
python create_sbv_project.py
```

### 5. 시스템 실행
```bash
cd sstdms_backend/src
python main.py
```

브라우저에서 `http://localhost:5000` 접속

## 👤 기본 계정

### 관리자 계정
- **ID**: admin@seastargo.com
- **초기 비밀번호**: 1234 (최초 로그인 시 변경 필요)

### 등록자 계정 (15명)
모든 Seastar Design 직원 계정이 사전 설정되어 있습니다.
- **초기 비밀번호**: 1234 (최초 로그인 시 변경 필요)

## 📁 프로젝트 구조

```
sstdms_erp/
├── sstdms_backend/          # Flask 백엔드
│   ├── src/
│   │   ├── models/          # 데이터베이스 모델
│   │   ├── routes/          # API 라우트
│   │   ├── utils/           # 유틸리티 함수
│   │   ├── database/        # 데이터베이스 파일
│   │   └── static/          # 정적 파일
│   └── requirements.txt
├── sstdms_frontend/         # React 프론트엔드
│   ├── src/
│   │   ├── components/      # React 컴포넌트
│   │   └── assets/          # 정적 자원
│   ├── package.json
│   └── dist/               # 빌드 결과물
└── README.md
```

## 🔧 설정

### 저장소 경로 설정
관리자 계정으로 로그인 후 설정 메뉴에서 파일 저장 경로를 설정할 수 있습니다.

### 프로젝트 권한 관리
관리자는 각 프로젝트별로 등록자들의 접근 권한을 부여할 수 있습니다.

## 🚀 배포 옵션

### 1. 로컬 서버 배포
- 사내 서버에 직접 설치
- 네트워크 공유 폴더 연동

### 2. 클라우드 배포
- Heroku, Railway, Oracle Cloud 등
- 환경변수 설정 필요

### 3. Docker 배포
```bash
# Dockerfile 생성 후
docker build -t sstdms .
docker run -p 5000:5000 sstdms
```

## 📈 향후 개선 방향

### 파일 저장소 확장
- **NAS 연동**: Synology, QNAP 등 NAS 시스템 연동
- **클라우드 스토리지**: AWS S3, Google Drive, OneDrive 연동
- **네트워크 드라이브**: Windows 공유 폴더, SMB/CIFS 프로토콜 지원

### 보안 강화
- LDAP/Active Directory 연동
- 2단계 인증 (2FA)
- SSL/TLS 암호화

### 기능 확장
- 모바일 앱 개발
- 실시간 알림 시스템
- 고급 리포팅 기능
- API 연동 확장

### 성능 최적화
- 데이터베이스 최적화 (PostgreSQL, MySQL 지원)
- 캐싱 시스템 (Redis)
- 로드 밸런싱

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원

문의사항이나 기술 지원이 필요한 경우:
- 이슈 등록: [GitHub Issues](https://github.com/byjay/cstar1/issues)
- 이메일: admin@seastargo.com

## 🙏 감사의 말

이 프로젝트는 Seastar Design의 업무 효율성 향상을 위해 개발되었습니다.

---

**Seastar Design - World Shipbuilding & Offshore Design Provider**

