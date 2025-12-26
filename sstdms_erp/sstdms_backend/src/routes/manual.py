#!/usr/bin/env python3
"""
SSTDMS 매뉴얼 관리 시스템
등록자용/사용자용 매뉴얼 분리 관리
"""

from flask import Blueprint, request, jsonify, send_file
from routes.secure_auth import require_auth, require_permission
import os
import json
from datetime import datetime

manual_bp = Blueprint('manual', __name__)

def get_manual_content(user_category):
    """사용자 카테고리에 따른 매뉴얼 내용 반환"""
    
    if user_category in ['admin', 'registrar']:
        return get_registrar_manual()
    else:
        return get_user_manual()

def get_registrar_manual():
    """등록자용 매뉴얼"""
    return {
        "title": "SSTDMS 등록자 매뉴얼",
        "version": "1.0.0",
        "last_updated": "2025-07-31",
        "developer": "Seastar Design - 김봉정 (designsir@seastargo.com)",
        "target_audience": "등록자 (Registrar)",
        "description": "프로젝트 생성, 관리 및 문서 관리 권한을 가진 등록자를 위한 완전한 사용 가이드",
        "sections": [
            {
                "id": "intro",
                "title": "1. 시스템 소개",
                "content": """
# SSTDMS (Seastar Design Technical Document Management System)

## 개발자 정보
- **개발자**: 김봉정 (designsir@seastargo.com)
- **소속**: Seastar Design 설계팀 수석설계사
- **개발 목적**: 조선 설계 문서 관리의 효율성 극대화

## 시스템 개요
SSTDMS는 조선 설계 프로젝트의 기술 문서를 체계적으로 관리하기 위해 개발된 전문 시스템입니다.

## 등록자 권한
- ✅ 프로젝트 생성 및 편집
- ✅ 도면 및 문서 업로드/관리
- ✅ 사용자 조회
- ✅ 엑셀 파일 업로드/다운로드
- ✅ 간트차트 생성 및 관리
- ✅ 워터마크 설정
                """
            },
            {
                "id": "login",
                "title": "2. 로그인 및 초기 설정",
                "content": """
# 로그인 및 초기 설정

## 로그인 방법
1. 브라우저에서 SSTDMS 접속
2. Seastar Design 이메일 주소 입력
3. 초기 비밀번호 '1234' 입력
4. **첫 로그인 시 반드시 비밀번호 변경 필요**

## 비밀번호 정책
- 최소 8자 이상
- 대문자, 소문자, 숫자, 특수문자 포함
- 90일마다 변경 권장

## 세션 관리
- 세션 유지 시간: 60분
- 최대 동시 세션: 3개
- 로그인 실패 5회 시 30분 계정 잠금
                """
            },
            {
                "id": "project_management",
                "title": "3. 프로젝트 관리",
                "content": """
# 프로젝트 관리

## 새 프로젝트 생성
1. 대시보드에서 '새 프로젝트' 버튼 클릭
2. 프로젝트 정보 입력:
   - 프로젝트명 (예: SBV, Container Ship A)
   - 선종 (컨테이너선, 벌크선, 탱커 등)
   - 발주처 정보
   - 프로젝트 설명
3. 저장 후 프로젝트 ID 자동 생성

## 프로젝트 편집
- 연필 아이콘(✏️) 클릭으로 편집 모드 진입
- **관리자 또는 프로젝트 생성자만 편집 가능**
- 프로젝트 상태 변경 (진행중/완료/보류)

## 폴더 구조 관리
```
프로젝트명/
├── 기본설계/
│   ├── 일반배치도/
│   └── 선형도/
├── 상세설계/
│   ├── 구조도면/
│   └── 의장도면/
└── 승인도서/
```
                """
            },
            {
                "id": "document_management",
                "title": "4. 문서 및 도면 관리",
                "content": """
# 문서 및 도면 관리

## 파일 업로드
1. 프로젝트 선택 후 '파일 업로드' 클릭
2. 드래그 앤 드롭 또는 파일 선택
3. 파일 분류 선택 (도면/문서/보고서)
4. 리비전 정보 입력
5. 업로드 완료

## 지원 파일 형식
- **도면**: DWG, PDF, DXF
- **문서**: PDF, DOC, DOCX, XLS, XLSX
- **이미지**: JPG, PNG, TIFF
- **최대 파일 크기**: 100MB

## 리비전 관리
- 자동 버전 관리 (Rev.0, Rev.1, Rev.2...)
- 변경 이력 추적
- 이전 버전 다운로드 가능
- 승인 상태 관리

## 배포 관리
- 배포 대상자 선택
- 배포 일시 기록
- 수신 확인 추적
                """
            },
            {
                "id": "excel_integration",
                "title": "5. 엑셀 연동 기능",
                "content": """
# 엑셀 연동 기능

## 도면 리스트 엑셀 업로드
1. '엑셀 업로드' 버튼 클릭
2. 표준 양식의 엑셀 파일 선택
3. 데이터 매핑 확인
4. 일괄 업로드 실행

## 표준 엑셀 양식
| 도면번호 | 도면명 | 분류 | 리비전 | 작성자 | 작성일 | 상태 |
|---------|--------|------|--------|--------|--------|------|
| SBV-001 | 일반배치도 | 기본설계 | Rev.0 | 김설계 | 2025-07-31 | 진행중 |

## 엑셀 내보내기
- 프로젝트별 도면 리스트 엑셀 다운로드
- 필터링된 결과 내보내기
- 사용자 정의 양식 지원

## 데이터 검증
- 필수 필드 확인
- 중복 도면번호 검사
- 날짜 형식 검증
                """
            },
            {
                "id": "gantt_chart",
                "title": "6. 간트차트 관리",
                "content": """
# 간트차트 관리

## 자동 간트차트 생성
1. 프로젝트 일정 정보 입력
2. 마일스톤 설정
3. 작업 의존성 정의
4. 자동 간트차트 생성

## 간트차트 편집
- 작업 기간 조정 (드래그)
- 의존성 관계 수정
- 진행률 업데이트
- 리소스 할당

## 내보내기 옵션
- PDF 형식 내보내기
- PNG 이미지 내보내기
- 엑셀 형식 내보내기
- 프린터 친화적 레이아웃

## 일정 추적
- 실제 vs 계획 비교
- 지연 작업 하이라이트
- 크리티컬 패스 표시
                """
            },
            {
                "id": "watermark",
                "title": "7. 워터마크 시스템",
                "content": """
# 워터마크 시스템

## 워터마크 자동 적용
- PDF 출력 시 자동 워터마크 적용
- Seastar Design 로고 포함
- 문서 보안 강화

## 워터마크 설정
1. 관리자 메뉴 → 워터마크 설정
2. 로고 이미지 업로드
3. 투명도 조정 (권장: 30%)
4. 위치 설정 (중앙/모서리)

## 권한별 제어
- **등록자**: 워터마크 제거 가능
- **일반 사용자**: 워터마크 제거 불가
- **관리자**: 모든 워터마크 설정 관리

## 보안 기능
- 문서 다운로드 시 사용자 정보 삽입
- 배포 추적을 위한 고유 ID 생성
- 무단 복제 방지
                """
            },
            {
                "id": "user_management",
                "title": "8. 사용자 관리",
                "content": """
# 사용자 관리

## 사용자 조회
- 전체 사용자 목록 확인
- 카테고리별 필터링
- 로그인 이력 확인

## 사용자 카테고리
- **관리자**: 시스템 전체 관리
- **등록자**: 프로젝트 생성/관리
- **사용자**: 문서 조회/다운로드

## 권한 확인
- 각 사용자의 권한 레벨 확인
- 프로젝트별 접근 권한 조회
- 최근 활동 내역 확인

## 보안 모니터링
- 로그인 실패 이력
- 계정 잠금 상태
- 세션 관리 현황
                """
            },
            {
                "id": "troubleshooting",
                "title": "9. 문제 해결",
                "content": """
# 문제 해결

## 자주 발생하는 문제

### 로그인 문제
- **증상**: 로그인이 안됨
- **해결**: 비밀번호 확인, 계정 잠금 상태 확인
- **연락처**: admin@seastargo.com

### 파일 업로드 실패
- **증상**: 파일 업로드가 중단됨
- **해결**: 파일 크기 확인 (100MB 이하), 네트워크 상태 확인

### 권한 오류
- **증상**: "권한이 없습니다" 메시지
- **해결**: 관리자에게 권한 요청

## 시스템 요구사항
- **브라우저**: Chrome, Firefox, Safari 최신 버전
- **네트워크**: 안정적인 인터넷 연결
- **화면 해상도**: 1280x720 이상 권장

## 기술 지원
- **개발자**: 김봉정 (designsir@seastargo.com)
- **시스템 관리자**: admin@seastargo.com
- **긴급 연락**: Seastar Design 설계팀
                """
            }
        ]
    }

def get_user_manual():
    """사용자용 매뉴얼"""
    return {
        "title": "SSTDMS 사용자 매뉴얼",
        "version": "1.0.0",
        "last_updated": "2025-07-31",
        "developer": "Seastar Design - 김봉정 (designsir@seastargo.com)",
        "target_audience": "일반 사용자 (User)",
        "description": "문서 조회 및 다운로드 권한을 가진 일반 사용자를 위한 사용 가이드",
        "sections": [
            {
                "id": "intro",
                "title": "1. 시스템 소개",
                "content": """
# SSTDMS (Seastar Design Technical Document Management System)

## 개발자 정보
- **개발자**: 김봉정 (designsir@seastargo.com)
- **소속**: Seastar Design 설계팀 수석설계사
- **개발 목적**: 조선 설계 문서 관리의 효율성 극대화

## 시스템 개요
SSTDMS는 조선 설계 프로젝트의 기술 문서를 체계적으로 관리하기 위해 개발된 전문 시스템입니다.

## 사용자 권한
- ✅ 프로젝트 조회
- ✅ 문서 및 도면 조회
- ✅ 파일 다운로드
- ✅ 간트차트 조회
- ❌ 프로젝트 생성/편집 불가
- ❌ 파일 업로드 불가
                """
            },
            {
                "id": "login",
                "title": "2. 로그인 및 기본 사용법",
                "content": """
# 로그인 및 기본 사용법

## 로그인 방법
1. 브라우저에서 SSTDMS 접속
2. Seastar Design 이메일 주소 입력
3. 초기 비밀번호 '1234' 입력
4. **첫 로그인 시 반드시 비밀번호 변경 필요**

## 비밀번호 정책
- 최소 8자 이상
- 대문자, 소문자, 숫자, 특수문자 포함
- 90일마다 변경 권장

## 대시보드 구성
- **프로젝트 목록**: 접근 가능한 프로젝트 표시
- **최근 문서**: 최근 조회한 문서 목록
- **공지사항**: 시스템 공지 및 업데이트 정보
                """
            },
            {
                "id": "project_view",
                "title": "3. 프로젝트 조회",
                "content": """
# 프로젝트 조회

## 프로젝트 목록 확인
1. 대시보드에서 프로젝트 카드 확인
2. 프로젝트명 클릭으로 상세 정보 조회
3. 프로젝트 상태 및 진행률 확인

## 프로젝트 정보
- **프로젝트명**: 선박명 또는 프로젝트 코드
- **선종**: 컨테이너선, 벌크선, 탱커 등
- **발주처**: 선주사 정보
- **진행 상태**: 진행중/완료/보류
- **생성일**: 프로젝트 시작일

## 접근 권한
- 관리자가 부여한 프로젝트만 조회 가능
- 권한이 없는 프로젝트는 목록에 표시되지 않음
                """
            },
            {
                "id": "document_view",
                "title": "4. 문서 및 도면 조회",
                "content": """
# 문서 및 도면 조회

## 문서 목록 확인
1. 프로젝트 선택 후 '문서' 탭 클릭
2. 폴더 구조로 정리된 문서 확인
3. 파일 형식별 아이콘으로 구분

## 폴더 구조
```
프로젝트명/
├── 기본설계/
│   ├── 일반배치도/
│   └── 선형도/
├── 상세설계/
│   ├── 구조도면/
│   └── 의장도면/
└── 승인도서/
```

## 문서 정보 확인
- **파일명**: 도면번호 및 도면명
- **리비전**: 현재 버전 정보
- **작성자**: 문서 작성자
- **작성일**: 최종 수정일
- **파일 크기**: 다운로드 예상 시간 참고

## 검색 기능
- 파일명으로 검색
- 도면번호로 검색
- 작성자로 검색
- 날짜 범위로 필터링
                """
            },
            {
                "id": "download",
                "title": "5. 파일 다운로드",
                "content": """
# 파일 다운로드

## 단일 파일 다운로드
1. 다운로드할 파일 선택
2. 다운로드 버튼(⬇️) 클릭
3. 브라우저 다운로드 폴더에 저장

## 다중 파일 다운로드
1. 체크박스로 여러 파일 선택
2. '선택 다운로드' 버튼 클릭
3. ZIP 파일로 압축하여 다운로드

## 워터마크 적용
- **PDF 파일**: 자동으로 워터마크 적용
- **Seastar Design 로고** 포함
- **다운로드 정보** 삽입 (사용자명, 날짜)

## 다운로드 이력
- 다운로드한 파일 목록 확인
- 다운로드 일시 기록
- 관리자가 다운로드 이력 추적 가능

## 주의사항
- 다운로드한 파일의 무단 배포 금지
- 워터마크 제거 시도 금지
- 회사 기밀 정보 보안 준수
                """
            },
            {
                "id": "gantt_view",
                "title": "6. 간트차트 조회",
                "content": """
# 간트차트 조회

## 간트차트 접근
1. 프로젝트 선택 후 '일정' 탭 클릭
2. 간트차트 자동 로드
3. 확대/축소로 상세 조회

## 간트차트 정보
- **작업 목록**: 프로젝트 세부 작업
- **일정**: 시작일 및 종료일
- **진행률**: 작업 완료 정도
- **의존성**: 작업 간 연관 관계
- **마일스톤**: 주요 완료 지점

## 조회 기능
- 시간 범위 조정 (일/주/월 단위)
- 작업 필터링
- 크리티컬 패스 확인
- 지연 작업 하이라이트

## 내보내기
- PNG 이미지로 저장
- PDF 형식으로 저장
- 인쇄용 레이아웃 지원
                """
            },
            {
                "id": "profile",
                "title": "7. 프로필 관리",
                "content": """
# 프로필 관리

## 프로필 정보 확인
1. 우상단 사용자명 클릭
2. '프로필' 메뉴 선택
3. 개인 정보 확인

## 개인 정보
- **이름**: 실명
- **이메일**: Seastar Design 이메일
- **부서**: 소속 부서
- **직급**: 현재 직급
- **권한**: 사용자 카테고리
- **가입일**: 계정 생성일
- **최근 로그인**: 마지막 접속 시간

## 비밀번호 변경
1. 프로필 페이지에서 '비밀번호 변경' 클릭
2. 현재 비밀번호 입력
3. 새 비밀번호 입력 (정책 준수)
4. 비밀번호 확인 입력
5. 변경 완료

## 언어 설정
- 한국어 (기본)
- 영어 (선택 가능)
                """
            },
            {
                "id": "troubleshooting",
                "title": "8. 문제 해결",
                "content": """
# 문제 해결

## 자주 발생하는 문제

### 로그인 문제
- **증상**: 로그인이 안됨
- **해결**: 
  1. 이메일 주소 정확히 입력
  2. 비밀번호 대소문자 확인
  3. 계정 잠금 시 30분 후 재시도
- **연락처**: admin@seastargo.com

### 파일 다운로드 실패
- **증상**: 다운로드가 중단됨
- **해결**:
  1. 네트워크 연결 상태 확인
  2. 브라우저 다운로드 설정 확인
  3. 팝업 차단 해제

### 페이지 로딩 문제
- **증상**: 페이지가 느리게 로드됨
- **해결**:
  1. 브라우저 캐시 삭제
  2. 다른 브라우저로 시도
  3. 네트워크 상태 확인

### 권한 관련 문제
- **증상**: "권한이 없습니다" 메시지
- **해결**: 등록자 또는 관리자에게 권한 요청

## 시스템 요구사항
- **브라우저**: Chrome, Firefox, Safari 최신 버전
- **네트워크**: 안정적인 인터넷 연결
- **화면 해상도**: 1280x720 이상 권장

## 기술 지원
- **개발자**: 김봉정 (designsir@seastargo.com)
- **시스템 관리자**: admin@seastargo.com
- **긴급 연락**: Seastar Design 설계팀

## 보안 준수사항
- 계정 정보 타인과 공유 금지
- 정기적인 비밀번호 변경
- 다운로드 파일 보안 관리
- 시스템 로그아웃 생활화
                """
            }
        ]
    }

@manual_bp.route('/manual', methods=['GET'])
@require_auth
def get_manual():
    """사용자 카테고리에 따른 매뉴얼 제공"""
    try:
        user_category = request.current_user.get('category', 'user')
        manual_content = get_manual_content(user_category)
        
        return jsonify({
            'success': True,
            'manual': manual_content
        })
        
    except Exception as e:
        return jsonify({'error': f'매뉴얼 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@manual_bp.route('/manual/section/<section_id>', methods=['GET'])
@require_auth
def get_manual_section(section_id):
    """특정 매뉴얼 섹션 조회"""
    try:
        user_category = request.current_user.get('category', 'user')
        manual_content = get_manual_content(user_category)
        
        section = next((s for s in manual_content['sections'] if s['id'] == section_id), None)
        if not section:
            return jsonify({'error': '해당 섹션을 찾을 수 없습니다.'}), 404
        
        return jsonify({
            'success': True,
            'section': section,
            'manual_info': {
                'title': manual_content['title'],
                'version': manual_content['version'],
                'developer': manual_content['developer']
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'매뉴얼 섹션 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@manual_bp.route('/manual/download', methods=['GET'])
@require_auth
def download_manual():
    """매뉴얼 PDF 다운로드"""
    try:
        user_category = request.current_user.get('category', 'user')
        manual_content = get_manual_content(user_category)
        
        # PDF 생성 로직 (추후 구현)
        # 현재는 JSON 형태로 다운로드
        
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(manual_content, f, ensure_ascii=False, indent=2)
            temp_path = f.name
        
        filename = f"SSTDMS_{user_category}_manual_v{manual_content['version']}.json"
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        return jsonify({'error': f'매뉴얼 다운로드 중 오류가 발생했습니다: {str(e)}'}), 500

@manual_bp.route('/manual/search', methods=['GET'])
@require_auth
def search_manual():
    """매뉴얼 내용 검색"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': '검색어를 입력해주세요.'}), 400
        
        user_category = request.current_user.get('category', 'user')
        manual_content = get_manual_content(user_category)
        
        results = []
        for section in manual_content['sections']:
            if (query.lower() in section['title'].lower() or 
                query.lower() in section['content'].lower()):
                results.append({
                    'section_id': section['id'],
                    'title': section['title'],
                    'preview': section['content'][:200] + '...'
                })
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': f'매뉴얼 검색 중 오류가 발생했습니다: {str(e)}'}), 500

