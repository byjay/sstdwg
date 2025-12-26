"""
질문 및 관리 시스템 라우트
개발자: 김봉정 (designsir@seastargo.com)
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import json
import os

qa_bp = Blueprint('qa', __name__)

# 질문 데이터 저장 경로
QA_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'qa_data.json')

def load_qa_data():
    """Q&A 데이터 로드"""
    if os.path.exists(QA_DATA_FILE):
        with open(QA_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "questions": [],
        "categories": [
            {"id": 1, "name": "시스템 사용법", "description": "SSTDMS 기본 사용 방법"},
            {"id": 2, "name": "파일 관리", "description": "문서 업로드, 다운로드, 관리"},
            {"id": 3, "name": "프로젝트 관리", "description": "프로젝트 생성, 수정, 삭제"},
            {"id": 4, "name": "사용자 권한", "description": "권한 설정 및 관리"},
            {"id": 5, "name": "기술 지원", "description": "기술적 문제 및 오류"},
            {"id": 6, "name": "기능 요청", "description": "새로운 기능 제안"},
            {"id": 7, "name": "서버 배포", "description": "서버 설치 및 배포 관련"},
            {"id": 8, "name": "도메인 연동", "description": "도메인 설정 및 SSL 인증서"}
        ],
        "faqs": [
            {
                "id": 1,
                "category_id": 1,
                "question": "SSTDMS에 처음 로그인하는 방법은?",
                "answer": "관리자가 제공한 이메일과 임시 비밀번호로 로그인 후, 비밀번호를 변경하세요.",
                "created_by": "admin",
                "created_at": "2025-07-31T00:00:00"
            },
            {
                "id": 2,
                "category_id": 2,
                "question": "파일 업로드 시 용량 제한이 있나요?",
                "answer": "기본적으로 100MB까지 업로드 가능하며, 관리자가 설정을 변경할 수 있습니다.",
                "created_by": "admin",
                "created_at": "2025-07-31T00:00:00"
            },
            {
                "id": 3,
                "category_id": 7,
                "question": "서버에 SSTDMS를 배포하려면 어떻게 해야 하나요?",
                "answer": "서버 배포 가이드 문서를 참조하여 단계별로 진행하시면 됩니다. AWS, GCP, Azure 등 다양한 플랫폼을 지원합니다.",
                "created_by": "designsir@seastargo.com",
                "created_at": "2025-07-31T00:00:00"
            }
        ]
    }

def save_qa_data(data):
    """Q&A 데이터 저장"""
    os.makedirs(os.path.dirname(QA_DATA_FILE), exist_ok=True)
    with open(QA_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@qa_bp.route('/api/qa/categories', methods=['GET'])
def get_categories():
    """카테고리 목록 조회"""
    try:
        data = load_qa_data()
        return jsonify({
            'success': True,
            'categories': data['categories']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'카테고리 조회 실패: {str(e)}'
        }), 500

@qa_bp.route('/api/qa/questions', methods=['GET'])
def get_questions():
    """질문 목록 조회"""
    try:
        category_id = request.args.get('category_id', type=int)
        status = request.args.get('status', 'all')
        
        data = load_qa_data()
        questions = data['questions']
        
        # 카테고리 필터링
        if category_id:
            questions = [q for q in questions if q.get('category_id') == category_id]
        
        # 상태 필터링
        if status != 'all':
            questions = [q for q in questions if q.get('status') == status]
        
        # 최신순 정렬
        questions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'questions': questions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'질문 조회 실패: {str(e)}'
        }), 500

@qa_bp.route('/api/qa/questions', methods=['POST'])
def create_question():
    """새 질문 등록"""
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': '로그인이 필요합니다.'
            }), 401
        
        data = request.get_json()
        required_fields = ['title', 'content', 'category_id']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'{field} 필드가 필요합니다.'
                }), 400
        
        qa_data = load_qa_data()
        
        # 새 질문 ID 생성
        question_id = max([q.get('id', 0) for q in qa_data['questions']], default=0) + 1
        
        new_question = {
            'id': question_id,
            'title': data['title'],
            'content': data['content'],
            'category_id': data['category_id'],
            'status': 'pending',
            'priority': data.get('priority', 'normal'),
            'created_by': session.get('email', 'unknown'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'answers': []
        }
        
        qa_data['questions'].append(new_question)
        save_qa_data(qa_data)
        
        return jsonify({
            'success': True,
            'message': '질문이 등록되었습니다.',
            'question': new_question
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'질문 등록 실패: {str(e)}'
        }), 500

@qa_bp.route('/api/qa/questions/<int:question_id>/answer', methods=['POST'])
def answer_question():
    """질문에 답변 등록"""
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': '로그인이 필요합니다.'
            }), 401
        
        # 관리자 또는 등록자만 답변 가능
        user_category = session.get('category', '')
        if user_category not in ['admin', 'registrar']:
            return jsonify({
                'success': False,
                'message': '답변 권한이 없습니다.'
            }), 403
        
        data = request.get_json()
        if 'content' not in data:
            return jsonify({
                'success': False,
                'message': '답변 내용이 필요합니다.'
            }), 400
        
        qa_data = load_qa_data()
        
        # 질문 찾기
        question = None
        for q in qa_data['questions']:
            if q['id'] == question_id:
                question = q
                break
        
        if not question:
            return jsonify({
                'success': False,
                'message': '질문을 찾을 수 없습니다.'
            }), 404
        
        # 답변 추가
        answer = {
            'id': len(question['answers']) + 1,
            'content': data['content'],
            'created_by': session.get('email', 'unknown'),
            'created_at': datetime.now().isoformat(),
            'is_official': user_category == 'admin'
        }
        
        question['answers'].append(answer)
        question['status'] = 'answered'
        question['updated_at'] = datetime.now().isoformat()
        
        save_qa_data(qa_data)
        
        return jsonify({
            'success': True,
            'message': '답변이 등록되었습니다.',
            'answer': answer
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'답변 등록 실패: {str(e)}'
        }), 500

@qa_bp.route('/api/qa/faqs', methods=['GET'])
def get_faqs():
    """자주 묻는 질문 조회"""
    try:
        category_id = request.args.get('category_id', type=int)
        
        data = load_qa_data()
        faqs = data['faqs']
        
        # 카테고리 필터링
        if category_id:
            faqs = [faq for faq in faqs if faq.get('category_id') == category_id]
        
        return jsonify({
            'success': True,
            'faqs': faqs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'FAQ 조회 실패: {str(e)}'
        }), 500

@qa_bp.route('/api/qa/search', methods=['GET'])
def search_qa():
    """Q&A 검색"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'message': '검색어를 입력하세요.'
            }), 400
        
        data = load_qa_data()
        results = []
        
        # 질문 검색
        for question in data['questions']:
            if (query.lower() in question.get('title', '').lower() or 
                query.lower() in question.get('content', '').lower()):
                results.append({
                    'type': 'question',
                    'data': question
                })
        
        # FAQ 검색
        for faq in data['faqs']:
            if (query.lower() in faq.get('question', '').lower() or 
                query.lower() in faq.get('answer', '').lower()):
                results.append({
                    'type': 'faq',
                    'data': faq
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'검색 실패: {str(e)}'
        }), 500

@qa_bp.route('/api/qa/admin/questions/<int:question_id>/status', methods=['PUT'])
def update_question_status():
    """질문 상태 업데이트 (관리자 전용)"""
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': '로그인이 필요합니다.'
            }), 401
        
        # 관리자만 상태 변경 가능
        if session.get('category') != 'admin':
            return jsonify({
                'success': False,
                'message': '관리자 권한이 필요합니다.'
            }), 403
        
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pending', 'answered', 'closed', 'resolved']:
            return jsonify({
                'success': False,
                'message': '유효하지 않은 상태입니다.'
            }), 400
        
        qa_data = load_qa_data()
        
        # 질문 찾기 및 상태 업데이트
        for question in qa_data['questions']:
            if question['id'] == question_id:
                question['status'] = new_status
                question['updated_at'] = datetime.now().isoformat()
                save_qa_data(qa_data)
                
                return jsonify({
                    'success': True,
                    'message': '상태가 업데이트되었습니다.',
                    'question': question
                })
        
        return jsonify({
            'success': False,
            'message': '질문을 찾을 수 없습니다.'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'상태 업데이트 실패: {str(e)}'
        }), 500

@qa_bp.route('/api/qa/stats', methods=['GET'])
def get_qa_stats():
    """Q&A 통계 조회"""
    try:
        data = load_qa_data()
        questions = data['questions']
        
        stats = {
            'total_questions': len(questions),
            'pending_questions': len([q for q in questions if q.get('status') == 'pending']),
            'answered_questions': len([q for q in questions if q.get('status') == 'answered']),
            'closed_questions': len([q for q in questions if q.get('status') == 'closed']),
            'total_faqs': len(data['faqs']),
            'categories': []
        }
        
        # 카테고리별 통계
        for category in data['categories']:
            cat_questions = [q for q in questions if q.get('category_id') == category['id']]
            stats['categories'].append({
                'id': category['id'],
                'name': category['name'],
                'question_count': len(cat_questions)
            })
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'통계 조회 실패: {str(e)}'
        }), 500

