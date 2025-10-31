import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """애플리케이션 설정"""
    
    # OpenAI 설정
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # 데이터베이스 설정
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_NAME = os.getenv('DB_NAME', 'clara_cs')
    
    # 애플리케이션 설정
    DEFAULT_USER_ID = int(os.getenv('DEFAULT_USER_ID', '1'))  # 기본 사용자 ID
    
    # 리포트 설정
    CHART_DAYS_RANGE = int(os.getenv('CHART_DAYS_RANGE', '365'))  # 차트 조회 기간 (일)
    
    # 로깅 설정
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Flask 설정
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

    # 이메일 설정
    EMAIL_SENDER = os.getenv('EMAIL_ADDRESS')      # 보내는 이메일 주소
    SMTP_SERVER = os.getenv('MAIL_SERVER')        # SMTP 서버
    SMTP_PORT = int(os.getenv('MAIL_PORT', 587))  # SMTP 포트
    SMTP_USER = os.getenv('EMAIL_ADDRESS')        # SMTP 로그인 사용자
    SMTP_PASSWORD = os.getenv('EMAIL_PASSWORD')  # SMTP 앱 비밀번호
    
    # 딥러닝 모델 API 설정 (외부 API 연동용)
    DL_MODEL_API_URL = os.getenv('DL_MODEL_API_URL', '')  # 외부 딥러닝 모델 API URL
    DL_MODEL_API_KEY = os.getenv('DL_MODEL_API_KEY', '')  # 외부 API 키 (필요시)
    DL_MODEL_USE_EXTERNAL = os.getenv('DL_MODEL_USE_EXTERNAL', 'False').lower() == 'true'  # 외부 API 사용 여부
    DL_MODEL_NAME = os.getenv('DL_MODEL_NAME', 'facebook/bart-large-mnli')  # Hugging Face 모델 이름 또는 외부 모델 ID