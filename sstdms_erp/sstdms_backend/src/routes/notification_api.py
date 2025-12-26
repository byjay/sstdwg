from flask import Blueprint, request, jsonify
from utils.email_sender import EmailSender
import os

notification_bp = Blueprint('notification', __name__)

# 이메일 설정 (환경 변수에서 가져오기)
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER', 'your_email@gmail.com')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'your_app_password')

email_sender = EmailSender(SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD)

@notification_bp.route('/send_deployment_notification', methods=['POST'])
def send_deployment_notification():
    """도면 배포 시 관련자들에게 알림 이메일 발송"""
    try:
        data = request.get_json()
        
        # 필수 데이터 검증
        required_fields = ['project_name', 'drawing_name', 'deployed_by', 'recipients']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        project_name = data['project_name']
        drawing_name = data['drawing_name']
        deployed_by = data['deployed_by']
        recipients = data['recipients']  # 이메일 주소 리스트
        admin_email = data.get('admin_email', 'admin@seastar.com')
        
        # 이메일 제목 및 내용 생성
        subject = f"[SSTDMS] {project_name} - {drawing_name} 도면 배포 알림"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #2c5aa0; text-align: center;">SSTDMS 도면 배포 알림</h2>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #495057;">배포 정보</h3>
                    <p><strong>📋 프로젝트명:</strong> {project_name}</p>
                    <p><strong>📐 도면명:</strong> {drawing_name}</p>
                    <p><strong>👤 배포자:</strong> {deployed_by}</p>
                    <p><strong>📅 배포일시:</strong> {data.get('deployment_time', '현재 시간')}</p>
                </div>
                
                <p>해당 도면을 확인하시려면 SSTDMS 시스템에 로그인하여 주시기 바랍니다.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:5000" style="background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">SSTDMS 시스템 접속</a>
                </div>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="text-align: center; color: #6c757d; font-size: 12px;">
                    이 메일은 SSTDMS 시스템에서 자동으로 발송되었습니다.<br>
                    문의사항이 있으시면 시스템 관리자에게 연락해 주세요.
                </p>
            </div>
        </body>
        </html>
        """
        
        # 수신자들에게 이메일 발송
        success_count = 0
        failed_recipients = []
        
        for recipient in recipients:
            success, message = email_sender.send_email(
                sender_email=SMTP_USER,
                receiver_email=recipient,
                subject=subject,
                body=html_body,
                is_html=True
            )
            
            if success:
                success_count += 1
            else:
                failed_recipients.append({'email': recipient, 'error': message})
        
        # 관리자에게도 알림 발송
        admin_subject = f"[SSTDMS 관리자] {project_name} - {drawing_name} 도면 배포 완료"
        admin_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #dc3545; text-align: center;">SSTDMS 관리자 알림</h2>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #495057;">배포 완료 정보</h3>
                    <p><strong>📋 프로젝트명:</strong> {project_name}</p>
                    <p><strong>📐 도면명:</strong> {drawing_name}</p>
                    <p><strong>👤 배포자:</strong> {deployed_by}</p>
                    <p><strong>📅 배포일시:</strong> {data.get('deployment_time', '현재 시간')}</p>
                    <p><strong>📧 알림 발송 성공:</strong> {success_count}명</p>
                    <p><strong>📧 알림 발송 실패:</strong> {len(failed_recipients)}명</p>
                </div>
                
                <p>도면 배포가 완료되었습니다. 시스템을 확인해 주세요.</p>
            </div>
        </body>
        </html>
        """
        
        admin_success, admin_message = email_sender.send_email(
            sender_email=SMTP_USER,
            receiver_email=admin_email,
            subject=admin_subject,
            body=admin_body,
            is_html=True
        )
        
        return jsonify({
            'success': True,
            'message': f'알림 발송 완료: {success_count}명 성공, {len(failed_recipients)}명 실패',
            'success_count': success_count,
            'failed_recipients': failed_recipients,
            'admin_notification': admin_success
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'알림 발송 중 오류 발생: {str(e)}'}), 500

@notification_bp.route('/test_email', methods=['POST'])
def test_email():
    """이메일 발송 테스트"""
    try:
        data = request.get_json()
        test_email = data.get('email', 'designsir@seastar.com')
        
        subject = "SSTDMS 도면 배포 테스트 송신자입니다"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #2c5aa0; text-align: center;">SSTDMS 테스트 메일</h2>
                
                <p>안녕하세요, <strong>{test_email}</strong>님.</p>
                
                <div style="background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>🧪 이것은 SSTDMS 시스템의 이메일 발송 테스트입니다.</strong></p>
                    <p>도면 배포 알림 기능이 정상적으로 작동하는지 확인하기 위한 테스트 메일입니다.</p>
                </div>
                
                <p>이 메일을 받으셨다면 이메일 발송 기능이 정상적으로 작동하고 있습니다.</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="text-align: center; color: #6c757d; font-size: 12px;">
                    SSTDMS 시스템 테스트 메일<br>
                    발송 시간: {data.get('timestamp', '현재 시간')}
                </p>
            </div>
        </body>
        </html>
        """
        
        success, message = email_sender.send_email(
            sender_email=SMTP_USER,
            receiver_email=test_email,
            subject=subject,
            body=body,
            is_html=True
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'테스트 이메일이 {test_email}로 성공적으로 발송되었습니다.'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'테스트 이메일 발송 실패: {message}'
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'테스트 이메일 발송 중 오류 발생: {str(e)}'}), 500

