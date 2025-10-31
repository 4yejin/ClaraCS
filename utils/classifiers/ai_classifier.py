"""
AI 기반 분류 엔진 (Hugging Face Transformers 또는 외부 API)
사전 학습된 한국어 텍스트 분류 모델 사용 또는 외부 딥러닝 모델 API 연동
"""
from typing import Dict, List, Any, Optional
from .base_classifier import BaseClassifier
from utils.logger import get_logger
from config import Config
import re
import requests

logger = get_logger(__name__)


class AIClassifier(BaseClassifier):
    """Hugging Face Transformers 기반 AI 분류 엔진 또는 외부 API 연동"""
    
    def __init__(self, model_name: str = None, category_mapping: Dict[int, str] = None, 
                 api_url: str = None, api_key: str = None):
        """
        Args:
            model_name: Hugging Face 모델 이름 또는 외부 모델 ID
                - 'facebook/bart-large-mnli' (영어, 메모리 효율적, 추천)
                - 'MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7' (다국어)
                - 'joeddav/xlm-roberta-large-xnli' (다국어)
            category_mapping: {category_id: category_name} 딕셔너리
            api_url: 외부 딥러닝 모델 API URL (선택)
            api_key: 외부 API 키 (선택)
        """
        # 설정에서 기본값 가져오기
        self.use_external_api = Config.DL_MODEL_USE_EXTERNAL
        self.api_url = api_url or Config.DL_MODEL_API_URL
        self.api_key = api_key or Config.DL_MODEL_API_KEY
        self.model_name = model_name or Config.DL_MODEL_NAME
        
        self.category_mapping = category_mapping or {}
        self.reverse_mapping = {v: k for k, v in self.category_mapping.items()}
        
        # 모델 및 토크나이저 지연 로딩 (로컬 모델 사용 시)
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        
        # 카테고리 레이블 (학습된 순서대로)
        self.category_labels = list(self.reverse_mapping.keys())
        
        if self.use_external_api and self.api_url:
            logger.info(f"AIClassifier 초기화: 외부 API 사용 (URL={self.api_url})")
        else:
            logger.info(f"AIClassifier 초기화: 로컬 모델 사용 (model={self.model_name})")
    
    def _load_model(self):
        """모델 로딩 (최초 1회만)"""
        if self.pipeline is not None:
            return
        
        try:
            from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
            import torch
            
            logger.info(f"Hugging Face 모델 로딩 중: {self.model_name}")
            
            # Zero-shot classification 사용 (레이블 학습 불필요)
            # CPU 메모리 부족 방지를 위해 device=-1 (CPU 전용) 사용
            self.pipeline = pipeline(
                "zero-shot-classification",
                model=self.model_name,
                device=-1  # CPU 전용 (메모리 효율)
            )
            
            logger.info(f"모델 로딩 완료: {self.model_name}")
            logger.info(f"디바이스: CPU (메모리 효율 모드)")
            
        except ImportError:
            logger.error("transformers 라이브러리가 설치되지 않았습니다.")
            logger.error("pip install transformers torch 를 실행하세요.")
            raise
        except Exception as e:
            logger.error(f"모델 로딩 실패: {e}")
            raise
    
    def classify_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        티켓 분류 (외부 API 또는 로컬 모델 사용)
        
        Args:
            ticket: 티켓 데이터
            
        Returns:
            분류 결과
        """
        # 텍스트 준비
        body = ticket.get('body') or ''
        title = ticket.get('title') or ''
        text = f"{title} {body}".strip()
        
        if not text:
            logger.warning(f"티켓 {ticket.get('ticket_id')}의 본문이 비어있습니다.")
            return self._fallback_classification()
        
        # 외부 API 사용 여부 확인
        if self.use_external_api and self.api_url:
            return self._classify_via_api(text)
        else:
            return self._classify_via_local_model(text)
    
    def _classify_via_api(self, text: str) -> Dict[str, Any]:
        """외부 딥러닝 모델 API를 통한 분류"""
        try:
            # 텍스트 길이 제한
            text = text[:500]
            
            # API 요청 준비
            headers = {
                'Content-Type': 'application/json'
            }
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            payload = {
                'text': text,
                'candidates': self.category_labels,
                'model': self.model_name if self.model_name else None
            }
            
            logger.info(f"외부 API 호출: {self.api_url}")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30  # 30초 타임아웃
            )
            
            if response.status_code != 200:
                logger.error(f"외부 API 오류: {response.status_code} - {response.text}")
                return self._fallback_classification()
            
            result = response.json()
            
            # API 응답 형식에 따라 파싱
            # 형식 1: {'label': '카테고리명', 'confidence': 0.95, ...}
            # 형식 2: {'category': '카테고리명', 'score': 0.95, ...}
            # 형식 3: {'labels': ['카테고리1', '카테고리2'], 'scores': [0.95, 0.05], ...}
            
            best_label = None
            best_score = 0.0
            
            if 'labels' in result and 'scores' in result:
                # Hugging Face 형식
                best_label = result['labels'][0]
                best_score = float(result['scores'][0])
            elif 'label' in result:
                best_label = result['label']
                best_score = float(result.get('confidence', result.get('score', 0.0)))
            elif 'category' in result:
                best_label = result['category']
                best_score = float(result.get('score', result.get('confidence', 0.0)))
            else:
                logger.error(f"외부 API 응답 형식을 인식할 수 없습니다: {result}")
                return self._fallback_classification()
            
            category_id = self.reverse_mapping.get(best_label)
            keywords = self._extract_keywords(text, best_label)
            
            logger.debug(f"외부 API 분류 결과: {best_label} (신뢰도: {best_score:.3f})")
            
            return {
                'category_id': category_id,
                'category_name': best_label,
                'confidence': float(best_score),
                'keywords': keywords,
                'method': 'ai_external_api',
                'model_name': self.model_name or 'external'
            }
            
        except requests.exceptions.Timeout:
            logger.error("외부 API 타임아웃")
            return self._fallback_classification()
        except requests.exceptions.RequestException as e:
            logger.error(f"외부 API 요청 실패: {e}")
            return self._fallback_classification()
        except Exception as e:
            logger.error(f"외부 API 분류 실패: {e}")
            return self._fallback_classification()
    
    def _classify_via_local_model(self, text: str) -> Dict[str, Any]:
        """로컬 Hugging Face 모델을 통한 분류"""
        # 모델 로딩 (지연 로딩)
        self._load_model()
        
        # 텍스트 길이 제한 (512 토큰 제한)
        text = text[:500]
        
        try:
            # Zero-shot classification 실행
            result = self.pipeline(
                text,
                candidate_labels=self.category_labels,
                hypothesis_template="This text is about {}."  # 영어 템플릿 (모델에 맞춤)
            )
            
            # 결과 파싱
            best_label = result['labels'][0]
            best_score = result['scores'][0]
            
            category_id = self.reverse_mapping.get(best_label)
            
            # 키워드 추출 (간단한 방식)
            keywords = self._extract_keywords(text, best_label)
            
            logger.debug(f"로컬 모델 분류 결과: {best_label} (신뢰도: {best_score:.3f})")
            
            return {
                'category_id': category_id,
                'category_name': best_label,
                'confidence': float(best_score),
                'keywords': keywords,
                'method': 'ai_huggingface',
                'model_name': self.model_name
            }
            
        except Exception as e:
            logger.error(f"로컬 모델 분류 실패: {e}")
            return self._fallback_classification()
    
    def _extract_keywords(self, text: str, category: str) -> List[str]:
        """
        본문에서 실제로 발견된 키워드 추출
        (AI 분류 후 해당 카테고리의 대표 키워드 확인)
        """
        # 카테고리별 대표 키워드 패턴
        keyword_patterns = {
            '배송 문의': ['배송', '택배', '운송', '배달', '지연', '추적'],
            '환불/교환': ['환불', '교환', '반품', '취소', '결제'],
            '상품 문의': ['상품', '제품', '재고', '가격', '할인'],
            '기술 지원': ['사용법', '고장', 'AS', '수리', '설치'],
            '불만/클레임': ['불만', '클레임', '불량', '파손', '품질'],
            '기타': ['문의', '확인', '안내']
        }
        
        keywords_found = []
        patterns = keyword_patterns.get(category, [])
        
        # 실제로 본문에 있는 키워드만 추출
        for keyword in patterns:
            if keyword in text:
                keywords_found.append(keyword)
                if len(keywords_found) >= 5:
                    break
        
        # AI 분류이므로 키워드가 없어도 분류는 가능
        return keywords_found if keywords_found else ['AI분류']
    
    def _fallback_classification(self) -> Dict[str, Any]:
        """AI 분류 실패 시 기본값"""
        default_category = '기타'
        category_id = self.reverse_mapping.get(default_category, 6)
        
        return {
            'category_id': category_id,
            'category_name': default_category,
            'confidence': 0.3,
            'keywords': [],
            'method': 'ai_fallback'
        }
    
    def get_engine_name(self) -> str:
        """엔진 이름 반환"""
        if self.use_external_api and self.api_url:
            model_id = self.model_name.split("/")[-1] if self.model_name else "external"
            return f'ai_external_api_{model_id}'
        else:
            return f'ai_huggingface_{self.model_name.split("/")[-1]}'
    
    def set_category_mapping(self, category_mapping: Dict[int, str]):
        """카테고리 매핑 업데이트"""
        self.category_mapping = category_mapping
        self.reverse_mapping = {v: k for k, v in category_mapping.items()}
        self.category_labels = list(self.reverse_mapping.keys())
        logger.info(f"카테고리 매핑 업데이트: {len(category_mapping)}개")


# ============================================================================
# 참고: 커스텀 학습 모델 사용 예시 (Fine-tuned model)
# ============================================================================
"""
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

class CustomAIClassifier(BaseClassifier):
    def __init__(self, model_path: str, category_mapping: Dict[int, str]):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.category_mapping = category_mapping
        
    def classify_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        text = f"{ticket.get('title', '')} {ticket.get('body', '')}".strip()
        
        # 토큰화
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        # 추론
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
        # 결과
        predicted_class = torch.argmax(predictions, dim=-1).item()
        confidence = predictions[0][predicted_class].item()
        
        category_id = predicted_class + 1  # 1-based indexing
        category_name = self.category_mapping.get(category_id, '기타')
        
        return {
            'category_id': category_id,
            'category_name': category_name,
            'confidence': confidence,
            'keywords': [],
            'method': 'ai_custom'
        }
"""

