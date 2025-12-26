from flask import Blueprint, request, jsonify, session, send_file
from werkzeug.utils import secure_filename
from models.user import db, User
from routes.user import login_required
import os
import json
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import base64

watermark_bp = Blueprint('watermark', __name__)

# 워터마크 설정 파일 경로
WATERMARK_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config', 'watermark_config.json')
WATERMARK_LOGO_PATH = os.path.join(os.path.dirname(__file__), 'static', 'assets', 'seastar_logo_corrected.png')

# 설정 디렉토리 생성
os.makedirs(os.path.dirname(WATERMARK_CONFIG_FILE), exist_ok=True)

def load_watermark_config():
    """워터마크 설정 로드"""
    try:
        if os.path.exists(WATERMARK_CONFIG_FILE):
            with open(WATERMARK_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 기본 설정
            default_config = {
                'enabled': True,
                'opacity': 0.3,
                'position': 'center',  # center, top-left, top-right, bottom-left, bottom-right
                'text': 'SEASTAR DESIGN',
                'logo_enabled': True,
                'logo_path': WATERMARK_LOGO_PATH,
                'authorized_users': ['admin'],  # 워터마크 제거 권한이 있는 사용자
                'authorized_roles': ['admin']   # 워터마크 제거 권한이 있는 역할
            }
            save_watermark_config(default_config)
            return default_config
    except Exception as e:
        print(f"워터마크 설정 로드 실패: {e}")
        return {}

def save_watermark_config(config):
    """워터마크 설정 저장"""
    try:
        with open(WATERMARK_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"워터마크 설정 저장 실패: {e}")
        return False

def check_watermark_permission(user_id):
    """워터마크 제거 권한 확인"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False
        
        config = load_watermark_config()
        authorized_users = config.get('authorized_users', [])
        authorized_roles = config.get('authorized_roles', [])
        
        # 사용자명 또는 역할로 권한 확인
        return (user.username in authorized_users or 
                user.role in authorized_roles)
    except Exception as e:
        print(f"워터마크 권한 확인 실패: {e}")
        return False

@watermark_bp.route('/watermark/config', methods=['GET'])
@login_required
def get_watermark_config():
    """워터마크 설정 조회"""
    try:
        user_id = session['user_id']
        config = load_watermark_config()
        
        # 사용자 권한 확인
        has_permission = check_watermark_permission(user_id)
        
        return jsonify({
            'config': config,
            'has_permission': has_permission,
            'can_remove_watermark': has_permission
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'워터마크 설정 조회 실패: {str(e)}'}), 500

@watermark_bp.route('/watermark/config', methods=['POST'])
@login_required
def update_watermark_config():
    """워터마크 설정 업데이트 (관리자만)"""
    try:
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        # 관리자 권한 확인
        if user.role != 'admin':
            return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
        
        data = request.get_json()
        config = load_watermark_config()
        
        # 설정 업데이트
        if 'enabled' in data:
            config['enabled'] = data['enabled']
        if 'opacity' in data:
            config['opacity'] = max(0.1, min(1.0, float(data['opacity'])))
        if 'position' in data:
            config['position'] = data['position']
        if 'text' in data:
            config['text'] = data['text']
        if 'logo_enabled' in data:
            config['logo_enabled'] = data['logo_enabled']
        if 'authorized_users' in data:
            config['authorized_users'] = data['authorized_users']
        if 'authorized_roles' in data:
            config['authorized_roles'] = data['authorized_roles']
        
        if save_watermark_config(config):
            return jsonify({
                'message': '워터마크 설정이 성공적으로 업데이트되었습니다.',
                'config': config
            }), 200
        else:
            return jsonify({'error': '설정 저장에 실패했습니다.'}), 500
            
    except Exception as e:
        return jsonify({'error': f'워터마크 설정 업데이트 실패: {str(e)}'}), 500

@watermark_bp.route('/watermark/permissions', methods=['GET'])
@login_required
def get_watermark_permissions():
    """워터마크 권한 사용자 목록 조회 (관리자만)"""
    try:
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        # 관리자 권한 확인
        if user.role != 'admin':
            return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
        
        config = load_watermark_config()
        authorized_users = config.get('authorized_users', [])
        authorized_roles = config.get('authorized_roles', [])
        
        # 모든 사용자 목록 조회
        all_users = User.query.filter_by(is_active=True).all()
        users_list = []
        
        for u in all_users:
            has_permission = (u.username in authorized_users or 
                            u.role in authorized_roles)
            users_list.append({
                'id': u.id,
                'username': u.username,
                'full_name': u.full_name,
                'role': u.role,
                'department': u.department,
                'has_watermark_permission': has_permission
            })
        
        return jsonify({
            'users': users_list,
            'authorized_users': authorized_users,
            'authorized_roles': authorized_roles
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'권한 목록 조회 실패: {str(e)}'}), 500

@watermark_bp.route('/watermark/permissions', methods=['POST'])
@login_required
def update_watermark_permissions():
    """워터마크 권한 업데이트 (관리자만)"""
    try:
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        # 관리자 권한 확인
        if user.role != 'admin':
            return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
        
        data = request.get_json()
        target_user_id = data.get('user_id')
        grant_permission = data.get('grant_permission', False)
        
        if not target_user_id:
            return jsonify({'error': '사용자 ID가 필요합니다.'}), 400
        
        target_user = User.query.get(target_user_id)
        if not target_user:
            return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
        
        config = load_watermark_config()
        authorized_users = config.get('authorized_users', [])
        
        if grant_permission:
            # 권한 부여
            if target_user.username not in authorized_users:
                authorized_users.append(target_user.username)
        else:
            # 권한 제거
            if target_user.username in authorized_users:
                authorized_users.remove(target_user.username)
        
        config['authorized_users'] = authorized_users
        
        if save_watermark_config(config):
            return jsonify({
                'message': f'{target_user.full_name}님의 워터마크 권한이 {"부여" if grant_permission else "제거"}되었습니다.',
                'user': {
                    'username': target_user.username,
                    'full_name': target_user.full_name,
                    'has_permission': grant_permission
                }
            }), 200
        else:
            return jsonify({'error': '권한 설정 저장에 실패했습니다.'}), 500
            
    except Exception as e:
        return jsonify({'error': f'권한 업데이트 실패: {str(e)}'}), 500

@watermark_bp.route('/watermark/apply', methods=['POST'])
@login_required
def apply_watermark():
    """이미지에 워터마크 적용"""
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        image_data = data.get('image_data')  # base64 인코딩된 이미지
        remove_watermark = data.get('remove_watermark', False)
        
        if not image_data:
            return jsonify({'error': '이미지 데이터가 필요합니다.'}), 400
        
        # 워터마크 제거 권한 확인
        if remove_watermark and not check_watermark_permission(user_id):
            return jsonify({'error': '워터마크 제거 권한이 없습니다.'}), 403
        
        # 워터마크 설정 로드
        config = load_watermark_config()
        
        # 워터마크가 비활성화되어 있거나 제거 요청인 경우
        if not config.get('enabled', True) or remove_watermark:
            return jsonify({
                'image_data': image_data,
                'watermark_applied': False
            }), 200
        
        # base64 이미지 디코딩
        image_bytes = base64.b64decode(image_data.split(',')[1])
        image = Image.open(io.BytesIO(image_bytes))
        
        # 워터마크 적용
        watermarked_image = apply_watermark_to_image(image, config)
        
        # 결과 이미지를 base64로 인코딩
        output_buffer = io.BytesIO()
        watermarked_image.save(output_buffer, format='PNG')
        output_buffer.seek(0)
        
        result_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        result_data_url = f"data:image/png;base64,{result_base64}"
        
        return jsonify({
            'image_data': result_data_url,
            'watermark_applied': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'워터마크 적용 실패: {str(e)}'}), 500

def apply_watermark_to_image(image, config):
    """이미지에 워터마크 적용"""
    try:
        # RGBA 모드로 변환
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # 워터마크 레이어 생성
        watermark_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)
        
        # 로고 워터마크 적용
        if config.get('logo_enabled', True) and os.path.exists(config.get('logo_path', '')):
            try:
                logo = Image.open(config['logo_path'])
                if logo.mode != 'RGBA':
                    logo = logo.convert('RGBA')
                
                # 로고 크기 조정 (원본 이미지의 1/4 크기)
                logo_size = min(image.size[0] // 4, image.size[1] // 4)
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                
                # 투명도 적용
                opacity = int(255 * config.get('opacity', 0.3))
                logo_with_opacity = Image.new('RGBA', logo.size, (0, 0, 0, 0))
                for x in range(logo.size[0]):
                    for y in range(logo.size[1]):
                        r, g, b, a = logo.getpixel((x, y))
                        if a > 0:  # 투명하지 않은 픽셀만 처리
                            logo_with_opacity.putpixel((x, y), (r, g, b, min(a, opacity)))
                
                # 위치 계산
                position = config.get('position', 'center')
                if position == 'center':
                    x = (image.size[0] - logo.size[0]) // 2
                    y = (image.size[1] - logo.size[1]) // 2
                elif position == 'top-left':
                    x, y = 20, 20
                elif position == 'top-right':
                    x = image.size[0] - logo.size[0] - 20
                    y = 20
                elif position == 'bottom-left':
                    x = 20
                    y = image.size[1] - logo.size[1] - 20
                elif position == 'bottom-right':
                    x = image.size[0] - logo.size[0] - 20
                    y = image.size[1] - logo.size[1] - 20
                else:
                    x = (image.size[0] - logo.size[0]) // 2
                    y = (image.size[1] - logo.size[1]) // 2
                
                # 로고 붙이기
                watermark_layer.paste(logo_with_opacity, (x, y), logo_with_opacity)
                
            except Exception as e:
                print(f"로고 워터마크 적용 실패: {e}")
        
        # 텍스트 워터마크 적용
        watermark_text = config.get('text', 'SEASTAR DESIGN')
        if watermark_text:
            try:
                # 폰트 크기 계산
                font_size = max(20, min(image.size) // 20)
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                # 텍스트 크기 계산
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # 텍스트 위치 (하단 중앙)
                text_x = (image.size[0] - text_width) // 2
                text_y = image.size[1] - text_height - 30
                
                # 텍스트 색상 (투명도 적용)
                opacity = int(255 * config.get('opacity', 0.3))
                text_color = (128, 128, 128, opacity)
                
                # 텍스트 그리기
                draw.text((text_x, text_y), watermark_text, font=font, fill=text_color)
                
            except Exception as e:
                print(f"텍스트 워터마크 적용 실패: {e}")
        
        # 워터마크 레이어를 원본 이미지에 합성
        result = Image.alpha_composite(image, watermark_layer)
        
        return result
        
    except Exception as e:
        print(f"워터마크 적용 중 오류: {e}")
        return image

