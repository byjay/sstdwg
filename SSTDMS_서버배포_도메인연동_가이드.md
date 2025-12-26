# SSTDMS 서버 배포 및 도메인 연동 완전 가이드

## 📋 문서 정보

**시스템명**: SSTDMS (Seastar Design Technical Document Management System)  
**개발자**: 김봉정 (designsir@seastargo.com) - Seastar Design 설계팀 수석설계사  
**문서 작성**: Manus AI  
**작성 일시**: 2025년 7월 31일  
**문서 목적**: 실제 서버 배포 및 NameCheap 도메인 연동 방법 제시  

---

## 🌐 서버 배포 옵션

### 1. 클라우드 서버 배포 (권장)

#### AWS EC2 배포

**1단계: EC2 인스턴스 생성**
```bash
# AWS CLI 설치 및 설정
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# AWS 계정 설정
aws configure
```

**2단계: 보안 그룹 설정**
```bash
# HTTP/HTTPS 포트 개방
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxx \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxx \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0
```

**3단계: 서버 환경 구성**
```bash
# Ubuntu 서버 업데이트
sudo apt update && sudo apt upgrade -y

# Python 3.11 설치
sudo apt install python3.11 python3.11-venv python3-pip -y

# Node.js 설치
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Nginx 설치
sudo apt install nginx -y

# PM2 설치 (프로세스 관리)
sudo npm install -g pm2
```

#### Google Cloud Platform (GCP) 배포

**1단계: Compute Engine 인스턴스 생성**
```bash
# gcloud CLI 설치
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# 인스턴스 생성
gcloud compute instances create sstdms-server \
    --zone=asia-northeast3-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB
```

**2단계: 방화벽 규칙 설정**
```bash
# HTTP/HTTPS 트래픽 허용
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP"

gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTPS"
```

#### Azure Virtual Machine 배포

**1단계: Azure CLI 설치 및 설정**
```bash
# Azure CLI 설치
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Azure 로그인
az login

# 리소스 그룹 생성
az group create --name sstdms-rg --location koreacentral

# VM 생성
az vm create \
    --resource-group sstdms-rg \
    --name sstdms-vm \
    --image Ubuntu2204 \
    --admin-username azureuser \
    --generate-ssh-keys \
    --size Standard_B2s
```

### 2. VPS 서버 배포

#### DigitalOcean Droplet

**1단계: Droplet 생성**
- Ubuntu 22.04 LTS 선택
- 최소 2GB RAM, 1 vCPU 권장
- 서울 리전 선택 (한국 사용자용)

**2단계: 초기 서버 설정**
```bash
# 서버 접속
ssh root@your-server-ip

# 사용자 생성
adduser sstdms
usermod -aG sudo sstdms

# SSH 키 설정
mkdir /home/sstdms/.ssh
cp ~/.ssh/authorized_keys /home/sstdms/.ssh/
chown -R sstdms:sstdms /home/sstdms/.ssh
chmod 700 /home/sstdms/.ssh
chmod 600 /home/sstdms/.ssh/authorized_keys
```

#### Vultr 서버

**1단계: 서버 인스턴스 생성**
- Cloud Compute 선택
- Seoul 위치 선택
- Ubuntu 22.04 x64 선택
- Regular Performance, 2GB RAM 이상

**2단계: 방화벽 설정**
```bash
# UFW 방화벽 설정
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## 🔧 SSTDMS 애플리케이션 배포

### 1. 소스 코드 배포

**Git을 통한 배포**
```bash
# Git 설치
sudo apt install git -y

# 소스 코드 클론 (또는 업로드)
git clone https://github.com/your-repo/sstdms.git
cd sstdms

# 또는 SCP로 파일 업로드
scp -r sstdms_erp/ user@server-ip:/home/user/
```

### 2. 백엔드 배포

**Python 환경 설정**
```bash
cd sstdms_erp/sstdms_backend

# 가상환경 생성
python3.11 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
pip install gunicorn

# 환경 변수 설정
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=sqlite:///production.db
UPLOAD_FOLDER=/var/www/sstdms/uploads
EOF

# 데이터베이스 초기화
cd src
python init_users.py
```

**Gunicorn 설정**
```bash
# Gunicorn 설정 파일 생성
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
EOF

# 서비스 파일 생성
sudo cat > /etc/systemd/system/sstdms.service << EOF
[Unit]
Description=SSTDMS Flask Application
After=network.target

[Service]
User=sstdms
Group=www-data
WorkingDirectory=/home/sstdms/sstdms_erp/sstdms_backend/src
Environment=PATH=/home/sstdms/sstdms_erp/sstdms_backend/venv/bin
ExecStart=/home/sstdms/sstdms_erp/sstdms_backend/venv/bin/gunicorn -c ../gunicorn.conf.py main:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl enable sstdms
sudo systemctl start sstdms
```

### 3. 프론트엔드 배포

**React 빌드 및 배포**
```bash
cd sstdms_erp/sstdms_frontend

# 의존성 설치
npm install

# 프로덕션 빌드
npm run build

# Nginx 웹 루트로 복사
sudo cp -r dist/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html/
```

### 4. Nginx 설정

**Nginx 설정 파일 생성**
```bash
sudo cat > /etc/nginx/sites-available/sstdms << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # 정적 파일 서빙
    location / {
        root /var/www/html;
        try_files \$uri \$uri/ /index.html;
    }
    
    # API 프록시
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 파일 업로드 크기 제한
    client_max_body_size 100M;
    
    # Gzip 압축
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
EOF

# 사이트 활성화
sudo ln -s /etc/nginx/sites-available/sstdms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🌍 NameCheap 도메인 연동

### 1. NameCheap에서 도메인 구매

**도메인 구매 과정**
1. NameCheap 웹사이트 접속 (namecheap.com)
2. 원하는 도메인 검색 (예: seastardms.com)
3. 도메인 구매 및 결제
4. 계정에서 도메인 관리 페이지 접속

### 2. DNS 설정

**A 레코드 설정**
```
Type: A Record
Host: @
Value: your-server-ip-address
TTL: Automatic

Type: A Record  
Host: www
Value: your-server-ip-address
TTL: Automatic
```

**CNAME 레코드 설정 (선택사항)**
```
Type: CNAME Record
Host: api
Value: your-domain.com
TTL: Automatic

Type: CNAME Record
Host: admin
Value: your-domain.com  
TTL: Automatic
```

### 3. 고급 DNS 설정

**NameCheap DNS 관리 패널에서:**

1. **Advanced DNS 탭 클릭**
2. **Host Records 섹션에서 다음 레코드 추가:**

```
Type        Host    Value                   TTL
A Record    @       123.456.789.123        Automatic
A Record    www     123.456.789.123        Automatic
CNAME       api     your-domain.com        Automatic
CNAME       admin   your-domain.com        Automatic
TXT         @       v=spf1 include:_spf.google.com ~all    Automatic
```

3. **Email Forwarding 설정 (선택사항):**
```
admin@your-domain.com → designsir@seastargo.com
support@your-domain.com → designsir@seastargo.com
```

### 4. SSL 인증서 설정

**Let's Encrypt 무료 SSL 인증서**
```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx -y

# SSL 인증서 발급
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 자동 갱신 설정
sudo crontab -e
# 다음 라인 추가:
0 12 * * * /usr/bin/certbot renew --quiet
```

**SSL 설정 후 Nginx 설정 업데이트**
```bash
sudo cat > /etc/nginx/sites-available/sstdms << EOF
# HTTP to HTTPS 리다이렉트
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS 서버
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL 인증서
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL 보안 설정
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # 보안 헤더
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # 정적 파일 서빙
    location / {
        root /var/www/html;
        try_files \$uri \$uri/ /index.html;
    }
    
    # API 프록시
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 파일 업로드/다운로드
    location /uploads/ {
        alias /var/www/sstdms/uploads/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    client_max_body_size 100M;
    
    # Gzip 압축
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript application/pdf;
}
EOF

sudo nginx -t
sudo systemctl reload nginx
```

---

## 💾 로컬 드라이브 연동 방법

### 1. 네트워크 파일 시스템 (NFS) 설정

**서버 측 NFS 설정**
```bash
# NFS 서버 설치
sudo apt install nfs-kernel-server -y

# 공유 디렉토리 생성
sudo mkdir -p /var/nfs/sstdms_files
sudo chown nobody:nogroup /var/nfs/sstdms_files
sudo chmod 755 /var/nfs/sstdms_files

# NFS 내보내기 설정
sudo cat >> /etc/exports << EOF
/var/nfs/sstdms_files    your-local-ip/24(rw,sync,no_subtree_check,no_root_squash)
EOF

# NFS 서비스 재시작
sudo exportfs -a
sudo systemctl restart nfs-kernel-server
```

**로컬 컴퓨터 NFS 클라이언트 설정**
```bash
# Windows (PowerShell 관리자 권한)
Enable-WindowsOptionalFeature -Online -FeatureName ServicesForNFS-ClientOnly

# 네트워크 드라이브 연결
net use Z: \\server-ip\var\nfs\sstdms_files

# Linux/Mac
sudo apt install nfs-common  # Ubuntu
brew install nfs-utils       # macOS

# 마운트
sudo mkdir /mnt/sstdms
sudo mount -t nfs server-ip:/var/nfs/sstdms_files /mnt/sstdms
```

### 2. SFTP/SCP 연동

**SFTP 서버 설정**
```bash
# OpenSSH 서버 설정
sudo cat >> /etc/ssh/sshd_config << EOF
# SFTP 전용 사용자 그룹
Match Group sftponly
    ChrootDirectory /var/sftp/%u
    ForceCommand internal-sftp
    AllowTcpForwarding no
    X11Forwarding no
EOF

# SFTP 사용자 생성
sudo groupadd sftponly
sudo useradd -g sftponly -d /var/sftp/sstdms -s /sbin/nologin sstdms-sftp
sudo passwd sstdms-sftp

# SFTP 디렉토리 설정
sudo mkdir -p /var/sftp/sstdms/uploads
sudo chown root:root /var/sftp/sstdms
sudo chmod 755 /var/sftp/sstdms
sudo chown sstdms-sftp:sftponly /var/sftp/sstdms/uploads
sudo chmod 755 /var/sftp/sstdms/uploads

sudo systemctl restart ssh
```

**로컬 컴퓨터에서 SFTP 연결**
```bash
# FileZilla, WinSCP 등 SFTP 클라이언트 사용
# 또는 명령줄:
sftp sstdms-sftp@your-server-ip
```

### 3. 클라우드 스토리지 연동

**AWS S3 연동**
```python
# SSTDMS 백엔드에 S3 연동 추가
import boto3
from botocore.exceptions import ClientError

class S3FileManager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id='your-access-key',
            aws_secret_access_key='your-secret-key',
            region_name='ap-northeast-2'
        )
        self.bucket_name = 'sstdms-files'
    
    def upload_file(self, file_path, object_name):
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_name)
            return True
        except ClientError as e:
            return False
    
    def download_file(self, object_name, file_path):
        try:
            self.s3_client.download_file(self.bucket_name, object_name, file_path)
            return True
        except ClientError as e:
            return False
```

**Google Drive API 연동**
```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class GoogleDriveManager:
    def __init__(self, credentials_file):
        self.creds = Credentials.from_authorized_user_file(credentials_file)
        self.service = build('drive', 'v3', credentials=self.creds)
    
    def upload_file(self, file_path, folder_id=None):
        file_metadata = {'name': os.path.basename(file_path)}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        media = MediaFileUpload(file_path)
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        return file.get('id')
```

---

## 🔒 보안 및 권한 관리

### 1. 파일 접근 권한 설정

**Linux 파일 권한**
```bash
# 업로드 디렉토리 권한 설정
sudo mkdir -p /var/www/sstdms/uploads
sudo chown -R www-data:sstdms /var/www/sstdms/uploads
sudo chmod -R 775 /var/www/sstdms/uploads

# SELinux 설정 (CentOS/RHEL)
sudo setsebool -P httpd_can_network_connect 1
sudo setsebool -P httpd_can_network_relay 1
```

**SSTDMS 권한 시스템 연동**
```python
# 파일 접근 권한 검증
def check_file_permission(user_id, file_path, action):
    user = get_user_by_id(user_id)
    
    # 관리자는 모든 파일 접근 가능
    if user.category == 'admin':
        return True
    
    # 등록자는 자신이 업로드한 파일만 수정 가능
    if user.category == 'registrar':
        file_owner = get_file_owner(file_path)
        if action in ['read', 'download']:
            return True
        elif action in ['write', 'delete']:
            return file_owner == user_id
    
    # 일반 사용자는 읽기만 가능
    if user.category == 'user':
        return action in ['read', 'download']
    
    return False
```

### 2. 네트워크 보안

**방화벽 설정**
```bash
# UFW 방화벽 규칙
sudo ufw allow from your-office-ip to any port 22
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 5000/tcp  # Flask 직접 접근 차단
sudo ufw enable
```

**Fail2Ban 설정**
```bash
# Fail2Ban 설치
sudo apt install fail2ban -y

# SSH 보호 설정
sudo cat > /etc/fail2ban/jail.local << EOF
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 5
bantime = 1800
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 📊 모니터링 및 백업

### 1. 시스템 모니터링

**Prometheus + Grafana 설정**
```bash
# Prometheus 설치
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
sudo mv prometheus-2.40.0.linux-amd64 /opt/prometheus

# Grafana 설치
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana
```

### 2. 자동 백업 시스템

**데이터베이스 백업**
```bash
#!/bin/bash
# /home/sstdms/backup_script.sh

BACKUP_DIR="/var/backups/sstdms"
DATE=$(date +%Y%m%d_%H%M%S)

# 디렉토리 생성
mkdir -p $BACKUP_DIR

# 데이터베이스 백업
cp /home/sstdms/sstdms_erp/sstdms_backend/src/database/app.db $BACKUP_DIR/app_$DATE.db

# 파일 백업
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /var/www/sstdms/uploads/

# 오래된 백업 삭제 (30일 이상)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

# 크론탭에 추가
# 0 2 * * * /home/sstdms/backup_script.sh
```

---

## 🚀 성능 최적화

### 1. 캐싱 설정

**Redis 캐시 서버**
```bash
# Redis 설치
sudo apt install redis-server -y

# Redis 설정
sudo sed -i 's/supervised no/supervised systemd/' /etc/redis/redis.conf
sudo systemctl restart redis
sudo systemctl enable redis
```

**Nginx 캐싱**
```nginx
# Nginx 설정에 추가
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# API 응답 캐싱
location /api/static/ {
    proxy_pass http://127.0.0.1:5000;
    proxy_cache_valid 200 1h;
    proxy_cache_key "$scheme$request_method$host$request_uri";
}
```

### 2. CDN 설정

**CloudFlare CDN 연동**
1. CloudFlare 계정 생성
2. 도메인 추가 및 네임서버 변경
3. SSL/TLS 설정을 "Full (strict)" 모드로 변경
4. 캐싱 규칙 설정

---

## 📞 문의 및 지원

**기술 지원**
- 개발자: 김봉정 (designsir@seastargo.com)
- 회사: Seastar Design
- 전화: [회사 전화번호]

**배포 관련 문의사항**
- 서버 설정 문제
- 도메인 연동 이슈
- 성능 최적화 요청
- 보안 강화 방안

---

**문서 정보**
- 작성자: Manus AI
- 시스템 개발자: 김봉정 (designsir@seastargo.com)
- 최종 업데이트: 2025년 7월 31일
- 다음 업데이트 예정: 필요시 수시 업데이트

