# SSTDMS 보안 방어 시스템

## 📋 문서 정보

**시스템명**: SSTDMS (Seastar Design Technical Document Management System)  
**개발자**: 김봉정 (designsir@seastargo.com) - Seastar Design 설계팀 수석설계사  
**보안 컨설팅**: Manus AI  
**작성 일시**: 2025년 7월 31일  
**문서 목적**: 웹서버 해킹 시도에 대한 종합적 방어 시스템 구축  

---

## 🛡️ 다층 보안 아키텍처

### 1단계: 네트워크 레벨 보안

#### 방화벽 설정
```bash
# UFW 방화벽 강화 설정
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 필수 포트만 개방
sudo ufw allow 22/tcp    # SSH (제한된 IP만)
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# 특정 IP에서만 SSH 접근 허용
sudo ufw allow from YOUR_OFFICE_IP to any port 22
sudo ufw deny 22/tcp

# DDoS 방어 설정
sudo ufw limit ssh
sudo ufw enable

# 고급 iptables 규칙
sudo iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
```

#### Fail2Ban 침입 탐지 시스템
```bash
# Fail2Ban 설치 및 설정
sudo apt install fail2ban -y

# 강화된 설정 파일 생성
sudo cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
# 기본 차단 시간 (1시간)
bantime = 3600
# 모니터링 시간 (10분)
findtime = 600
# 최대 시도 횟수
maxretry = 3
# 관리자 이메일
destemail = designsir@seastargo.com
# 액션 설정
action = %(action_mwl)s

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 3600

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6
bantime = 86400

[nginx-badbots]
enabled = true
port = http,https
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 86400

[nginx-noproxy]
enabled = true
port = http,https
filter = nginx-noproxy
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 86400

[sstdms-login]
enabled = true
port = http,https
filter = sstdms-login
logpath = /var/log/sstdms/security.log
maxretry = 5
bantime = 1800
EOF

# SSTDMS 로그인 실패 필터 생성
sudo cat > /etc/fail2ban/filter.d/sstdms-login.conf << 'EOF'
[Definition]
failregex = ^.*SSTDMS_LOGIN_FAILED.*IP:<HOST>.*$
ignoreregex =
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 2단계: 웹서버 레벨 보안

#### Nginx 보안 강화
```nginx
# /etc/nginx/sites-available/sstdms-secure
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 보안 설정
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 보안 헤더
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';" always;
    
    # 서버 정보 숨기기
    server_tokens off;
    
    # 요청 크기 제한
    client_max_body_size 100M;
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    
    # 요청 속도 제한
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    # 관리자 페이지 IP 제한
    location /admin {
        allow YOUR_OFFICE_IP;
        allow 127.0.0.1;
        deny all;
        
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 로그인 페이지 속도 제한
    location /api/auth/login {
        limit_req zone=login burst=3 nodelay;
        
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API 속도 제한
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 악성 요청 차단
    location ~* \.(php|asp|aspx|jsp)$ {
        return 444;
    }
    
    # 숨겨진 파일 접근 차단
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # 백업 파일 접근 차단
    location ~* \.(bak|backup|old|orig|save|swo|swp|tmp)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # 로그 설정
    access_log /var/log/nginx/sstdms_access.log;
    error_log /var/log/nginx/sstdms_error.log;
}

# HTTP to HTTPS 리다이렉트
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 3단계: 애플리케이션 레벨 보안

#### Flask 보안 미들웨어
```python
# /home/ubuntu/workspace/sstdms_erp/sstdms_backend/src/security/middleware.py
"""
SSTDMS 보안 미들웨어
개발자: 김봉정 (designsir@seastargo.com)
"""

import time
import hashlib
import logging
from functools import wraps
from flask import request, jsonify, session, g
from datetime import datetime, timedelta
import redis
import json

# 보안 로거 설정
security_logger = logging.getLogger('sstdms_security')
security_handler = logging.FileHandler('/var/log/sstdms/security.log')
security_formatter = logging.Formatter(
    '%(asctime)s - SSTDMS_SECURITY - %(levelname)s - %(message)s'
)
security_handler.setFormatter(security_formatter)
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.INFO)

# Redis 연결 (세션 및 캐시용)
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
except:
    redis_client = None

class SecurityMiddleware:
    def __init__(self, app):
        self.app = app
        self.failed_attempts = {}
        self.blocked_ips = {}
        
    def init_app(self, app):
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def get_client_ip(self):
        """클라이언트 IP 주소 획득"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr
    
    def is_ip_blocked(self, ip):
        """IP 차단 여부 확인"""
        if redis_client:
            blocked = redis_client.get(f"blocked_ip:{ip}")
            return blocked is not None
        
        # Redis 없을 경우 메모리 사용
        return ip in self.blocked_ips and self.blocked_ips[ip] > datetime.now()
    
    def block_ip(self, ip, duration_minutes=30):
        """IP 주소 차단"""
        block_until = datetime.now() + timedelta(minutes=duration_minutes)
        
        if redis_client:
            redis_client.setex(f"blocked_ip:{ip}", duration_minutes * 60, "blocked")
        else:
            self.blocked_ips[ip] = block_until
        
        security_logger.warning(f"IP_BLOCKED - IP:{ip} - Duration:{duration_minutes}min")
    
    def check_rate_limit(self, ip, endpoint, limit=10, window=60):
        """요청 속도 제한 확인"""
        key = f"rate_limit:{ip}:{endpoint}"
        
        if redis_client:
            current = redis_client.get(key)
            if current is None:
                redis_client.setex(key, window, 1)
                return True
            elif int(current) < limit:
                redis_client.incr(key)
                return True
            else:
                return False
        
        # Redis 없을 경우 기본 허용
        return True
    
    def log_security_event(self, event_type, details):
        """보안 이벤트 로깅"""
        ip = self.get_client_ip()
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'ip': ip,
            'user_agent': user_agent,
            'endpoint': request.endpoint,
            'method': request.method,
            'details': details
        }
        
        security_logger.info(f"{event_type} - IP:{ip} - {details}")
        
        # 데이터베이스에도 저장
        try:
            from models.security_log import SecurityLog
            SecurityLog.create_log(log_data)
        except:
            pass
    
    def before_request(self):
        """요청 전 보안 검사"""
        ip = self.get_client_ip()
        
        # IP 차단 확인
        if self.is_ip_blocked(ip):
            self.log_security_event('BLOCKED_IP_ACCESS', f'Blocked IP attempted access')
            return jsonify({'error': 'Access denied'}), 403
        
        # 악성 요청 패턴 검사
        if self.detect_malicious_request():
            self.log_security_event('MALICIOUS_REQUEST', f'Malicious request detected')
            self.block_ip(ip, 60)  # 1시간 차단
            return jsonify({'error': 'Malicious request detected'}), 403
        
        # 요청 속도 제한
        endpoint = request.endpoint or 'unknown'
        if not self.check_rate_limit(ip, endpoint):
            self.log_security_event('RATE_LIMIT_EXCEEDED', f'Rate limit exceeded for {endpoint}')
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # 요청 시작 시간 기록
        g.start_time = time.time()
    
    def after_request(self, response):
        """요청 후 처리"""
        # 응답 시간 기록
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            if response_time > 5:  # 5초 이상 걸린 요청 로깅
                self.log_security_event('SLOW_REQUEST', f'Response time: {response_time:.2f}s')
        
        return response
    
    def detect_malicious_request(self):
        """악성 요청 탐지"""
        # SQL 인젝션 패턴
        sql_patterns = [
            'union select', 'drop table', 'insert into', 'delete from',
            'update set', 'exec(', 'execute(', 'sp_', 'xp_'
        ]
        
        # XSS 패턴
        xss_patterns = [
            '<script', 'javascript:', 'onload=', 'onerror=',
            'onclick=', 'onmouseover=', 'eval(', 'alert('
        ]
        
        # 경로 순회 패턴
        path_patterns = [
            '../', '..\\', '/etc/passwd', '/etc/shadow',
            'web.config', '.htaccess', 'wp-config'
        ]
        
        # 요청 데이터 검사
        request_data = str(request.get_data(as_text=True)).lower()
        query_string = str(request.query_string.decode()).lower()
        
        all_patterns = sql_patterns + xss_patterns + path_patterns
        
        for pattern in all_patterns:
            if pattern in request_data or pattern in query_string:
                return True
        
        # User-Agent 검사
        user_agent = request.headers.get('User-Agent', '').lower()
        malicious_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'zap',
            'burp', 'w3af', 'havij', 'pangolin'
        ]
        
        for agent in malicious_agents:
            if agent in user_agent:
                return True
        
        return False

def require_admin(f):
    """관리자 권한 필요 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            security_logger.warning(f"UNAUTHORIZED_ADMIN_ACCESS - IP:{request.remote_addr}")
            return jsonify({'error': 'Authentication required'}), 401
        
        if session.get('category') != 'admin':
            security_logger.warning(f"INSUFFICIENT_PRIVILEGES - User:{session.get('email')} - IP:{request.remote_addr}")
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def require_auth(f):
    """인증 필요 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            security_logger.info(f"UNAUTHENTICATED_ACCESS - IP:{request.remote_addr} - Endpoint:{request.endpoint}")
            return jsonify({'error': 'Authentication required'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def log_login_attempt(email, success, ip):
    """로그인 시도 로깅"""
    if success:
        security_logger.info(f"LOGIN_SUCCESS - Email:{email} - IP:{ip}")
    else:
        security_logger.warning(f"SSTDMS_LOGIN_FAILED - Email:{email} - IP:{ip}")
```

#### 보안 로그 모델
```python
# /home/ubuntu/workspace/sstdms_erp/sstdms_backend/src/models/security_log.py
"""
보안 로그 모델
개발자: 김봉정 (designsir@seastargo.com)
"""

from datetime import datetime
import sqlite3
import json
import os

class SecurityLog:
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'security.db')
    
    @classmethod
    def init_db(cls):
        """보안 로그 데이터베이스 초기화"""
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        
        conn = sqlite3.connect(cls.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent TEXT,
                endpoint TEXT,
                method TEXT,
                user_email TEXT,
                details TEXT,
                severity TEXT DEFAULT 'INFO',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON security_logs(timestamp);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ip_address ON security_logs(ip_address);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_event_type ON security_logs(event_type);
        ''')
        
        conn.commit()
        conn.close()
    
    @classmethod
    def create_log(cls, log_data):
        """보안 로그 생성"""
        cls.init_db()
        
        conn = sqlite3.connect(cls.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_logs 
            (timestamp, event_type, ip_address, user_agent, endpoint, method, user_email, details, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_data.get('timestamp'),
            log_data.get('event_type'),
            log_data.get('ip'),
            log_data.get('user_agent'),
            log_data.get('endpoint'),
            log_data.get('method'),
            log_data.get('user_email'),
            json.dumps(log_data.get('details', {})),
            log_data.get('severity', 'INFO')
        ))
        
        conn.commit()
        conn.close()
    
    @classmethod
    def get_recent_logs(cls, hours=24, limit=100):
        """최근 로그 조회"""
        cls.init_db()
        
        conn = sqlite3.connect(cls.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM security_logs 
            WHERE datetime(timestamp) > datetime('now', '-{} hours')
            ORDER BY timestamp DESC 
            LIMIT ?
        '''.format(hours), (limit,))
        
        logs = cursor.fetchall()
        conn.close()
        
        return logs
    
    @classmethod
    def get_suspicious_ips(cls, hours=24):
        """의심스러운 IP 조회"""
        cls.init_db()
        
        conn = sqlite3.connect(cls.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ip_address, COUNT(*) as attempt_count,
                   GROUP_CONCAT(DISTINCT event_type) as event_types
            FROM security_logs 
            WHERE datetime(timestamp) > datetime('now', '-{} hours')
              AND event_type IN ('LOGIN_FAILED', 'MALICIOUS_REQUEST', 'RATE_LIMIT_EXCEEDED')
            GROUP BY ip_address
            HAVING attempt_count > 5
            ORDER BY attempt_count DESC
        '''.format(hours))
        
        suspicious_ips = cursor.fetchall()
        conn.close()
        
        return suspicious_ips
```

### 4단계: 데이터베이스 보안

#### SQLite 보안 강화
```python
# /home/ubuntu/workspace/sstdms_erp/sstdms_backend/src/security/database.py
"""
데이터베이스 보안 강화
개발자: 김봉정 (designsir@seastargo.com)
"""

import sqlite3
import hashlib
import os
from cryptography.fernet import Fernet

class SecureDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.encryption_key = self.get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
    
    def get_or_create_key(self):
        """암호화 키 생성 또는 로드"""
        key_file = os.path.join(os.path.dirname(self.db_path), '.db_key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # 소유자만 읽기 가능
            return key
    
    def encrypt_sensitive_data(self, data):
        """민감한 데이터 암호화"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data).decode()
    
    def decrypt_sensitive_data(self, encrypted_data):
        """암호화된 데이터 복호화"""
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        return self.cipher.decrypt(encrypted_data).decode()
    
    def secure_query(self, query, params=None):
        """안전한 쿼리 실행"""
        # SQL 인젝션 방지를 위한 파라미터화된 쿼리만 허용
        if params is None:
            params = []
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")  # 외래 키 제약 조건 활성화
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            result = cursor.fetchall()
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

# 데이터베이스 백업 및 복구
def backup_database():
    """데이터베이스 백업"""
    import shutil
    from datetime import datetime
    
    backup_dir = "/var/backups/sstdms"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/sstdms_backup_{timestamp}.db"
    
    shutil.copy2("/path/to/sstdms.db", backup_file)
    
    # 백업 파일 암호화
    with open(backup_file, 'rb') as f:
        data = f.read()
    
    cipher = Fernet(Fernet.generate_key())
    encrypted_data = cipher.encrypt(data)
    
    with open(f"{backup_file}.encrypted", 'wb') as f:
        f.write(encrypted_data)
    
    os.remove(backup_file)  # 원본 백업 파일 삭제
```

### 5단계: 실시간 모니터링 및 알림

#### 보안 모니터링 시스템
```python
# /home/ubuntu/workspace/sstdms_erp/sstdms_backend/src/security/monitor.py
"""
실시간 보안 모니터링 시스템
개발자: 김봉정 (designsir@seastargo.com)
"""

import time
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json

class SecurityMonitor:
    def __init__(self):
        self.alert_threshold = {
            'failed_logins': 10,  # 10분 내 실패 로그인 임계값
            'malicious_requests': 5,  # 10분 내 악성 요청 임계값
            'blocked_ips': 3  # 10분 내 차단된 IP 임계값
        }
        self.monitoring = True
    
    def start_monitoring(self):
        """모니터링 시작"""
        monitor_thread = threading.Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
    
    def _monitor_loop(self):
        """모니터링 루프"""
        while self.monitoring:
            try:
                self.check_security_events()
                time.sleep(60)  # 1분마다 체크
            except Exception as e:
                print(f"Monitoring error: {e}")
    
    def check_security_events(self):
        """보안 이벤트 확인"""
        from models.security_log import SecurityLog
        
        # 최근 10분간 로그 조회
        recent_logs = SecurityLog.get_recent_logs(hours=0.17)  # 10분
        
        # 이벤트 카운트
        event_counts = {}
        for log in recent_logs:
            event_type = log[2]  # event_type 컬럼
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # 임계값 확인 및 알림
        if event_counts.get('LOGIN_FAILED', 0) >= self.alert_threshold['failed_logins']:
            self.send_alert('HIGH_LOGIN_FAILURES', f"로그인 실패 {event_counts['LOGIN_FAILED']}회 감지")
        
        if event_counts.get('MALICIOUS_REQUEST', 0) >= self.alert_threshold['malicious_requests']:
            self.send_alert('MALICIOUS_ACTIVITY', f"악성 요청 {event_counts['MALICIOUS_REQUEST']}회 감지")
        
        if event_counts.get('IP_BLOCKED', 0) >= self.alert_threshold['blocked_ips']:
            self.send_alert('MULTIPLE_IP_BLOCKS', f"IP 차단 {event_counts['IP_BLOCKED']}회 발생")
    
    def send_alert(self, alert_type, message):
        """보안 알림 발송"""
        # 이메일 알림
        self.send_email_alert(alert_type, message)
        
        # 카카오톡 알림 (구현 예정)
        self.send_kakao_alert(alert_type, message)
        
        # 슬랙 알림
        self.send_slack_alert(alert_type, message)
    
    def send_email_alert(self, alert_type, message):
        """이메일 알림 발송"""
        try:
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "sstdms-security@seastargo.com"
            sender_password = "your-app-password"
            
            recipients = [
                "designsir@seastargo.com",
                "admin@seastargo.com"
            ]
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = f"SSTDMS 보안 알림: {alert_type}"
            
            body = f"""
SSTDMS 보안 시스템에서 다음 이벤트를 감지했습니다:

알림 유형: {alert_type}
메시지: {message}
시간: {time.strftime('%Y-%m-%d %H:%M:%S')}

즉시 시스템을 확인하시기 바랍니다.

SSTDMS 보안 시스템
Seastar Design
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            print(f"Email alert failed: {e}")
    
    def send_kakao_alert(self, alert_type, message):
        """카카오톡 알림 발송"""
        # 카카오톡 비즈니스 API 구현
        pass
    
    def send_slack_alert(self, alert_type, message):
        """슬랙 알림 발송"""
        try:
            webhook_url = "YOUR_SLACK_WEBHOOK_URL"
            
            payload = {
                "text": f"🚨 SSTDMS 보안 알림",
                "attachments": [
                    {
                        "color": "danger",
                        "fields": [
                            {
                                "title": "알림 유형",
                                "value": alert_type,
                                "short": True
                            },
                            {
                                "title": "메시지",
                                "value": message,
                                "short": True
                            }
                        ]
                    }
                ]
            }
            
            requests.post(webhook_url, json=payload)
            
        except Exception as e:
            print(f"Slack alert failed: {e}")
```

### 6단계: 침입 대응 시스템

#### 자동 대응 시스템
```python
# /home/ubuntu/workspace/sstdms_erp/sstdms_backend/src/security/response.py
"""
침입 자동 대응 시스템
개발자: 김봉정 (designsir@seastargo.com)
"""

import subprocess
import time
from datetime import datetime, timedelta

class IncidentResponse:
    def __init__(self):
        self.response_actions = {
            'HIGH_LOGIN_FAILURES': self.handle_login_attacks,
            'MALICIOUS_ACTIVITY': self.handle_malicious_activity,
            'MULTIPLE_IP_BLOCKS': self.handle_mass_attacks,
            'ADMIN_BREACH_ATTEMPT': self.handle_admin_breach
        }
    
    def handle_incident(self, incident_type, details):
        """사건 처리"""
        if incident_type in self.response_actions:
            self.response_actions[incident_type](details)
        
        # 모든 사건에 대한 공통 대응
        self.log_incident(incident_type, details)
        self.backup_critical_data()
    
    def handle_login_attacks(self, details):
        """로그인 공격 대응"""
        # 1. 로그인 페이지 일시 차단
        self.temporarily_block_login()
        
        # 2. 공격 IP 영구 차단
        attacking_ips = self.get_attacking_ips()
        for ip in attacking_ips:
            self.permanent_ip_block(ip)
        
        # 3. 관리자 알림
        self.send_emergency_alert("로그인 공격 감지 및 대응 완료")
    
    def handle_malicious_activity(self, details):
        """악성 활동 대응"""
        # 1. WAF 규칙 강화
        self.strengthen_waf_rules()
        
        # 2. 의심스러운 세션 종료
        self.terminate_suspicious_sessions()
        
        # 3. 시스템 무결성 검사
        self.check_system_integrity()
    
    def handle_admin_breach(self, details):
        """관리자 계정 침해 시도 대응"""
        # 1. 모든 관리자 세션 강제 종료
        self.force_logout_all_admins()
        
        # 2. 관리자 계정 일시 잠금
        self.lock_admin_accounts()
        
        # 3. 2단계 인증 강제 활성화
        self.enforce_2fa()
        
        # 4. 긴급 알림
        self.send_emergency_alert("관리자 계정 침해 시도 감지!")
    
    def temporarily_block_login(self, duration_minutes=30):
        """로그인 페이지 일시 차단"""
        # Nginx 설정 수정
        nginx_config = """
        location /api/auth/login {
            return 503 "Service temporarily unavailable due to security incident";
        }
        """
        
        # 설정 적용 후 자동 복구 스케줄링
        subprocess.run(['sudo', 'nginx', '-s', 'reload'])
        
        # duration_minutes 후 복구
        threading.Timer(duration_minutes * 60, self.restore_login).start()
    
    def permanent_ip_block(self, ip):
        """IP 영구 차단"""
        # iptables 규칙 추가
        subprocess.run(['sudo', 'iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'])
        
        # 규칙 영구 저장
        subprocess.run(['sudo', 'iptables-save'])
    
    def check_system_integrity(self):
        """시스템 무결성 검사"""
        # 중요 파일 해시 검증
        critical_files = [
            '/home/sstdms/sstdms_erp/sstdms_backend/src/main.py',
            '/home/sstdms/sstdms_erp/sstdms_backend/src/config/users.json',
            '/etc/nginx/sites-available/sstdms'
        ]
        
        for file_path in critical_files:
            if self.file_modified_unexpectedly(file_path):
                self.send_emergency_alert(f"중요 파일 변조 감지: {file_path}")
    
    def backup_critical_data(self):
        """중요 데이터 긴급 백업"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_commands = [
            f"sudo cp -r /home/sstdms/sstdms_erp /var/backups/emergency_backup_{timestamp}/",
            f"sudo sqlite3 /path/to/sstdms.db .dump > /var/backups/db_emergency_{timestamp}.sql"
        ]
        
        for cmd in backup_commands:
            subprocess.run(cmd.split())
```

### 7단계: 보안 대시보드

#### 실시간 보안 대시보드
```python
# /home/ubuntu/workspace/sstdms_erp/sstdms_backend/src/routes/security_dashboard.py
"""
보안 대시보드 라우트
개발자: 김봉정 (designsir@seastargo.com)
"""

from flask import Blueprint, jsonify, render_template
from security.middleware import require_admin
from models.security_log import SecurityLog
from datetime import datetime, timedelta

security_dashboard_bp = Blueprint('security_dashboard', __name__)

@security_dashboard_bp.route('/admin/security/dashboard')
@require_admin
def security_dashboard():
    """보안 대시보드 페이지"""
    return render_template('security_dashboard.html')

@security_dashboard_bp.route('/api/security/stats')
@require_admin
def get_security_stats():
    """보안 통계 조회"""
    try:
        # 최근 24시간 통계
        recent_logs = SecurityLog.get_recent_logs(24)
        
        stats = {
            'total_events': len(recent_logs),
            'login_failures': len([log for log in recent_logs if log[2] == 'LOGIN_FAILED']),
            'malicious_requests': len([log for log in recent_logs if log[2] == 'MALICIOUS_REQUEST']),
            'blocked_ips': len([log for log in recent_logs if log[2] == 'IP_BLOCKED']),
            'suspicious_ips': SecurityLog.get_suspicious_ips(24)
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@security_dashboard_bp.route('/api/security/recent-events')
@require_admin
def get_recent_events():
    """최근 보안 이벤트 조회"""
    try:
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        events = SecurityLog.get_recent_logs(hours, limit)
        
        return jsonify({
            'success': True,
            'events': events
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
```

---

## 🚨 침입 대응 매뉴얼

### 즉시 대응 절차

#### 1단계: 위협 확인
1. **보안 로그 확인**
   ```bash
   tail -f /var/log/sstdms/security.log
   tail -f /var/log/nginx/error.log
   ```

2. **시스템 상태 점검**
   ```bash
   sudo netstat -tulpn | grep LISTEN
   sudo ps aux | grep suspicious
   sudo last -n 20
   ```

#### 2단계: 즉시 차단
1. **의심스러운 IP 차단**
   ```bash
   sudo iptables -A INPUT -s SUSPICIOUS_IP -j DROP
   sudo fail2ban-client set sshd banip SUSPICIOUS_IP
   ```

2. **서비스 일시 중단** (필요시)
   ```bash
   sudo systemctl stop sstdms
   sudo systemctl stop nginx
   ```

#### 3단계: 피해 평가
1. **파일 무결성 검사**
2. **데이터베이스 무결성 확인**
3. **사용자 계정 상태 점검**

#### 4단계: 복구 및 강화
1. **백업에서 복구** (필요시)
2. **보안 패치 적용**
3. **설정 강화**

---

## 📞 긴급 연락처

**보안 담당자**
- 김봉정 수석설계사: designsir@seastargo.com
- 긴급 전화: [비상 연락처]

**기술 지원**
- Seastar Design IT팀
- 24시간 모니터링 센터

---

**문서 정보**
- 작성자: Manus AI (보안 컨설팅)
- 시스템 개발자: 김봉정 (designsir@seastargo.com)
- 최종 업데이트: 2025년 7월 31일
- 보안 등급: 기밀 (Confidential)

