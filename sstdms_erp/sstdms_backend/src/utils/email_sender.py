import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailSender:
    def __init__(self, smtp_server, smtp_port, smtp_user, smtp_password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

    def send_email(self, sender_email, receiver_email, subject, body, is_html=False):
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject

        if is_html:
            msg.attach(MIMEText(body, "html", "utf-8"))
        else:
            msg.attach(MIMEText(body, "plain", "utf-8"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            return True, "Email sent successfully!"
        except Exception as e:
            return False, f"Failed to send email: {e}"

# Example Usage (for testing purposes, replace with actual credentials)
if __name__ == "__main__":
    # 이메일 설정 (실제 사용 시 환경 변수나 보안 설정 파일에서 불러오세요)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "your_email@gmail.com"  # 실제 발신자 이메일
    SMTP_PASSWORD = "your_app_password" # Gmail 앱 비밀번호 또는 실제 비밀번호

    sender = EmailSender(SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD)

    # 테스트 이메일 발송
    test_receiver_email = "designsir@seastar.com"
    test_subject = "SSTDMS 도면 배포 테스트 송신자입니다."
    test_body = "안녕하세요, designsir@seastar.com님.\n\nSSTDMS 시스템에서 도면 배포 테스트 메일을 보내드립니다.\n\n감사합니다."

    success, message = sender.send_email(
        sender_email=SMTP_USER,
        receiver_email=test_receiver_email,
        subject=test_subject,
        body=test_body
    )

    print(f"Test Email Result: {message}")

    # HTML 이메일 테스트
    html_body = """
    <html>
    <body>
        <p>안녕하세요, <b>designsir@seastar.com</b>님.</p>
        <p>SSTDMS 시스템에서 <b>도면 배포 테스트 메일</b>을 보내드립니다.</p>
        <p>감사합니다.</p>
    </body>
    </html>
    """
    success_html, message_html = sender.send_email(
        sender_email=SMTP_USER,
        receiver_email=test_receiver_email,
        subject="SSTDMS 도면 배포 테스트 (HTML)",
        body=html_body,
        is_html=True
    )
    print(f"Test HTML Email Result: {message_html}")


