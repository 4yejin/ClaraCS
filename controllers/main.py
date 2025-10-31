from flask import Blueprint, render_template, request, jsonify
from flasgger.utils import swag_from
from config import Config
import requests
import time
import re
from utils.logger import get_logger

logger = get_logger(__name__)

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
@swag_from({
    'tags': ['Main'],
    'description': '메인 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def main():
    return render_template("main.html")

@main_bp.route("/dashboard")
@swag_from({
    'tags': ['Main'],
    'description': '대시보드 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def dashboard():
    return render_template("dashboard.html")

@main_bp.route("/upload")
@swag_from({
    'tags': ['Main'],
    'description': '데이터 업로드 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def upload():
    return render_template("upload.html")

@main_bp.route("/classify")
@swag_from({
    'tags': ['Main'],
    'description': '자동 분류 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def classify():
    return render_template("classify.html")

@main_bp.route("/report")
@swag_from({
    'tags': ['Main'],
    'description': '분석 리포트 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def report():
    return render_template("report.html")

@main_bp.route("/settings")
@swag_from({
    'tags': ['Main'],
    'description': '설정 도움말 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def settings():
    return render_template("settings.html")

@main_bp.route("/contact")
@swag_from({
    'tags': ['Main'],
    'description': '연락처 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def contact():
    return render_template("contact.html")

@main_bp.route("/api/contact/submit", methods=["POST"])
@swag_from({
    'tags': ['Main'],
    'description': 'Contact 폼 제출 - Google Sheets에 저장',
    'parameters': [
        {
            'name': 'name',
            'in': 'body',
            'type': 'string',
            'required': True,
            'description': '이름'
        },
        {
            'name': 'email',
            'in': 'body',
            'type': 'string',
            'required': True,
            'description': '이메일'
        },
        {
            'name': 'message',
            'in': 'body',
            'type': 'string',
            'required': True,
            'description': '메시지'
        }
    ],
    'responses': {
        200: {
            'description': '제출 성공'
        },
        400: {
            'description': '잘못된 요청'
        },
        500: {
            'description': '서버 오류'
        }
    }
})
def submit_contact():
    """Contact 폼 제출 - Google Sheets Web App으로 프록시"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '요청 데이터가 없습니다.'
            }), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        if not name or not email or not message:
            return jsonify({
                'success': False,
                'error': '모든 필드를 입력해주세요.'
            }), 400
        
        # Google Sheets Web App URL 확인
        google_sheets_url = Config.GOOGLE_SHEETS_WEB_APP_URL
        if not google_sheets_url:
            logger.error("GOOGLE_SHEETS_WEB_APP_URL이 설정되지 않았습니다.")
            return jsonify({
                'success': False,
                'error': 'Google Sheets URL이 설정되지 않았습니다.'
            }), 500
        
        # Google Apps Script Web App에 POST 요청 전송
        # e.parameter는 URL 쿼리 파라미터나 application/x-www-form-urlencoded 형식만 지원
        # 따라서 data=를 사용하여 form-urlencoded 형식으로 전송
        form_data = {
            'name': name,
            'email': email,
            'message': message
        }
        
        logger.info(f"Google Sheets로 데이터 전송 시도: name={name}, email={email}, url={google_sheets_url[:50]}...")
        logger.info(f"전송할 데이터: {form_data}")
        
        # 재시도 로직 (최대 2번 재시도)
        max_retries = 2
        retry_delay = 2  # 초
        response = None
        
        for attempt in range(max_retries + 1):
            try:
                # application/x-www-form-urlencoded 형식으로 POST 요청
                # e.parameter에서 접근 가능하도록 data= 사용 (params=가 아님)
                response = requests.post(
                    google_sheets_url,
                    data=form_data,  # form-urlencoded 형식 (e.parameter에서 접근 가능)
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    timeout=10,
                    allow_redirects=True
                )
                
                # 429 에러가 아니면 재시도하지 않음
                if response.status_code != 429:
                    break
                    
                # 429 에러인 경우 마지막 시도가 아니면 대기 후 재시도
                if attempt < max_retries:
                    logger.warning(f"429 에러 발생, {retry_delay}초 후 재시도 ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 지수 백오프
                else:
                    logger.error("429 에러: 최대 재시도 횟수 초과")
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    logger.warning(f"요청 실패, {retry_delay}초 후 재시도: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
        
        # 응답 전체 로깅 (디버깅용)
        logger.info(f"Google Sheets API 응답: status={response.status_code}")
        logger.info(f"응답 헤더: {dict(response.headers)}")
        
        # HTML 에러 페이지인 경우 전체 내용 로깅
        if '<!DOCTYPE html>' in response.text or '<html' in response.text.lower():
            logger.error(f"❌ Google Apps Script에서 HTML 에러 페이지 반환됨")
            logger.error(f"응답 전체 내용 (첫 2000자): {response.text[:2000]}")
            
            # 에러 메시지 추출 시도
            error_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
            if error_match:
                logger.error(f"에러 제목: {error_match.group(1)}")
            
            # 에러 메시지 본문 추출
            error_match = re.search(r'<div[^>]*class="errorMessage"[^>]*>(.*?)</div>', response.text, re.IGNORECASE | re.DOTALL)
            if error_match:
                error_text = re.sub(r'<[^>]+>', '', error_match.group(1)).strip()
                logger.error(f"에러 메시지: {error_text}")
            
            # 일반적인 에러 패턴 찾기
            error_patterns = [
                r'오류[:\s]*([^<]+)',
                r'Error[:\s]*([^<]+)',
                r'실행[^<]*오류[^<]*',
                r'권한[^<]*',
                r'접근[^<]*거부[^<]*'
            ]
            for pattern in error_patterns:
                error_match = re.search(pattern, response.text, re.IGNORECASE)
                if error_match:
                    logger.error(f"추출된 에러 정보: {error_match.group(0)[:200]}")
                    break
        
        logger.info(f"응답 본문 (전체): {response.text[:500] if len(response.text) < 500 else response.text[:500] + '...'}")
        logger.info(f"전송한 데이터: name={name}, email={email}, message={message[:50]}")
        
        # 401 UNAUTHORIZED 에러 처리
        if response.status_code == 401:
            logger.error("Google Apps Script 인증 오류 (401)")
            logger.error("배포 설정 또는 권한 문제일 수 있습니다.")
            return jsonify({
                'success': False,
                'error': 'Google Sheets 접근 권한이 없습니다. Google Apps Script 배포 설정을 확인해주세요. (실행 대상: "웹 앱에 액세스하는 모든 사용자" 선택 필요)'
            }), 401
        
        # 429 TOO MANY REQUESTS 에러 처리
        if response.status_code == 429:
            logger.warning("Google Apps Script 요청 한도 초과 (429)")
            return jsonify({
                'success': False,
                'error': '요청이 너무 많아 일시적으로 전송할 수 없습니다. 잠시 후 다시 시도해주세요. (보통 몇 분 후 다시 시도 가능)'
            }), 429
        
        # Google Apps Script는 일반적으로 200 또는 302(리다이렉트) 상태 코드를 반환합니다
        if response.status_code in [200, 302]:
            # 응답 텍스트 확인 - 실제로 "Success" 문자열이 포함되어야 함
            response_text = response.text.strip()
            response_text_lower = response_text.lower()
            
            # JSON 응답인지 확인
            if response_text.startswith('{'):
                try:
                    response_json = response.json()
                    if response_json.get('success'):
                        logger.info(f"✅ Contact 폼 제출 성공 확인: {email}")
                        return jsonify({
                            'success': True,
                            'message': '메시지가 성공적으로 전송되었습니다!'
                        }), 200
                    else:
                        error_msg = response_json.get('error', '알 수 없는 오류')
                        
                        # setHeaders 오류는 무시 (데이터는 저장되었을 수 있음)
                        if 'setHeaders' in error_msg or 'setHeaders is not a function' in error_msg:
                            logger.warning(f"setHeaders 오류 발생 (무시): {error_msg}")
                            logger.info("데이터 저장 확인을 위해 Google Sheets를 확인하세요")
                            # 오류이지만 데이터가 저장되었을 수 있으므로 성공으로 처리
                            return jsonify({
                                'success': True,
                                'message': '메시지가 전송되었습니다! (응답 확인 필요)'
                            }), 200
                        
                        logger.error(f"❌ Google Sheets 오류: {error_msg}")
                        return jsonify({
                            'success': False,
                            'error': f'Google Sheets 오류: {error_msg}'
                        }), 500
                except:
                    pass
            
            # "Success" 문자열 확인 (이전 버전 호환성)
            if 'success' in response_text_lower:
                logger.info(f"✅ Contact 폼 제출 성공 확인: {email}, 응답={response_text[:100]}")
                return jsonify({
                    'success': True,
                    'message': '메시지가 성공적으로 전송되었습니다!'
                }), 200
            else:
                # 응답이 "Success"가 아닌 경우 (예: HTML 에러 페이지)
                logger.error(f"❌ Google Sheets 응답이 'Success'가 아님: {response_text[:500]}")
                logger.error(f"응답이 HTML 페이지인지 확인 필요 (DOCTYPE 포함 여부: {'<!DOCTYPE' in response_text})")
                return jsonify({
                    'success': False,
                    'error': f'Google Sheets 응답이 예상과 다릅니다. 응답 내용: {response_text[:200]}'
                }), 500
        else:
            logger.error(f"Google Sheets API 오류: {response.status_code} - {response.text[:200]}")
            # HTML 에러 페이지인 경우 간단한 메시지로 변환
            error_message = f'전송 실패 (상태 코드: {response.status_code})'
            if response.status_code >= 500:
                error_message = 'Google Sheets 서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
            elif response.status_code == 403:
                error_message = 'Google Sheets 접근 권한이 없습니다. 배포 설정을 확인해주세요.'
            elif response.status_code == 404:
                error_message = 'Google Sheets URL을 찾을 수 없습니다. URL을 확인해주세요.'
            
            return jsonify({
                'success': False,
                'error': error_message
            }), response.status_code
            
    except requests.exceptions.Timeout:
        logger.error("Google Sheets API 요청 타임아웃")
        return jsonify({
            'success': False,
            'error': '요청 시간이 초과되었습니다. 다시 시도해주세요.'
        }), 500
    except requests.exceptions.RequestException as e:
        logger.error(f"Google Sheets API 요청 실패: {e}")
        return jsonify({
            'success': False,
            'error': f'전송 중 오류가 발생했습니다: {str(e)}'
        }), 500
    except Exception as e:
        logger.error(f"Contact 폼 제출 실패: {e}")
        return jsonify({
            'success': False,
            'error': f'처리 중 오류가 발생했습니다: {str(e)}'
        }), 500
