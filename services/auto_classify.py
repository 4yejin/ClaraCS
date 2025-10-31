from services.db.auto_classify_db import AutoClassifyDB
from utils.classifiers import RuleBasedClassifier, AIClassifier
from utils.logger import get_logger
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any

logger = get_logger(__name__)


class AutoClassifyService:
    """자동분류 관련 비즈니스 로직 서비스"""
    
    def __init__(self):
        self.db = AutoClassifyDB()
        self.classifier = None  # 지연 초기화
    
    def run_classification(self, user_id: int, file_id: int = None, batch_id: int = None, use_ai: bool = False) -> dict:
        """
        자동분류 실행 (단일 파일 또는 배치)
        
        Args:
            user_id: 사용자 ID
            file_id: 파일 ID (단일 파일 분류)
            batch_id: 배치 ID (배치 분류)
            use_ai: AI 분류 엔진 사용 여부
            
        Note:
            file_id와 batch_id 중 하나는 반드시 제공되어야 함
        
        1. DB에서 티켓 조회
        2. 각 티켓 분류 (규칙 기반 또는 AI 기반)
        3. 분류 결과 DB 저장
        4. 집계 데이터 계산
        5. 프론트엔드 응답 생성
        """
        if not file_id and not batch_id:
            raise ValueError("file_id 또는 batch_id 중 하나는 반드시 제공되어야 합니다.")
        
        target_type = "batch" if batch_id else "file"
        target_id = batch_id if batch_id else file_id
        logger.info(f"자동분류 실행 시작: user_id={user_id}, {target_type}_id={target_id}")
        
        try:
            # 1. 카테고리 매핑 조회 및 분류기 초기화
            category_mapping = self.db.get_category_mapping()
            if not category_mapping:
                raise ValueError("카테고리 데이터가 없습니다. database_insert_code_data.sql을 먼저 실행하세요.")
            
            # ============================================================
            # 분류기 초기화 (사용자 선택에 따라 분기)
            # ============================================================
            if use_ai:
                # AI 기반 분류기 (외부 API 또는 로컬 모델)
                from config import Config
                if Config.DL_MODEL_USE_EXTERNAL and Config.DL_MODEL_API_URL:
                    logger.info(f"🤖 AI 기반 분류 엔진 사용 (외부 API: {Config.DL_MODEL_API_URL})")
                else:
                    logger.info("🤖 AI 기반 분류 엔진 사용 (로컬 Hugging Face 모델)")
                
                try:
                    self.classifier = AIClassifier(
                        model_name=Config.DL_MODEL_NAME,
                        category_mapping=category_mapping,
                        api_url=Config.DL_MODEL_API_URL if Config.DL_MODEL_USE_EXTERNAL else None,
                        api_key=Config.DL_MODEL_API_KEY if Config.DL_MODEL_USE_EXTERNAL else None
                    )
                except (ImportError, OSError) as e:
                    logger.error(f"AI 모델 로딩 실패: {e}")
                    logger.info("📝 규칙 기반 분류 엔진으로 대체")
                    self.classifier = RuleBasedClassifier(category_mapping)
                    use_ai = False  # 실제로는 규칙 기반 사용
            else:
                # 규칙 기반 분류기
                logger.info("📝 규칙 기반 분류 엔진 사용")
                self.classifier = RuleBasedClassifier(category_mapping)
            # ============================================================
            
            # 2. 티켓 조회 (파일 또는 배치)
            if batch_id:
                tickets = self.db.get_tickets_by_batch(batch_id)
            else:
                tickets = self.db.get_tickets_by_file(file_id)
            
            if not tickets:
                logger.warning(f"분류할 티켓이 없습니다: {target_type}_id={target_id}")
                return self._empty_response(user_id, file_id, batch_id)
            
            logger.info(f"티켓 {len(tickets)}건 조회 완료")
            
            # 3. 티켓 분류 및 DB 저장
            classification_results = []
            for ticket in tickets:
                result = self.classifier.classify_ticket(ticket)
                classification_results.append({
                    'ticket_id': ticket['ticket_id'],
                    'classification': result
                })
                
                # 티켓 테이블에 분류 결과 업데이트
                self.db.update_ticket_classification(ticket['ticket_id'], result)
            
            logger.info(f"티켓 분류 완료: {len(classification_results)}건")
            
            # 4. 기간 계산
            dates = [t['received_at'] for t in tickets if t.get('received_at')]
            period_from = min(dates).date() if dates else None
            period_to = max(dates).date() if dates else None
            
            # 5. 분류 결과 메타 정보 저장 (배치 지원)
            class_result_id = self.db.insert_classification_result({
                'file_id': file_id,
                'batch_id': batch_id,  # 배치 ID 추가
                'user_id': user_id,
                'engine_name': self.classifier.get_engine_name(),
                'total_tickets': len(tickets),
                'period_from': period_from,
                'period_to': period_to,
                'classified_at': datetime.now(),
                'needs_review': False
            })
            
            # 6. 집계 데이터 계산
            category_stats = self._calculate_category_stats(tickets, classification_results, category_mapping)
            channel_stats = self._calculate_channel_stats(tickets, classification_results)
            reliability_stats = self._calculate_reliability_stats(classification_results)
            
            # 7. 집계 데이터 DB 저장
            self.db.insert_category_results(class_result_id, category_stats)
            self.db.insert_channel_results(class_result_id, channel_stats)
            self.db.insert_reliability_result(class_result_id, reliability_stats)
            
            # 8. 프론트엔드 응답 생성 (배치 지원)
            response = self._build_response(
                class_result_id, user_id, file_id, batch_id,
                period_from, period_to,
                tickets, classification_results,
                category_stats, channel_stats, reliability_stats,
                category_mapping
            )
            
            logger.info(f"자동분류 완료: user_id={user_id}, {target_type}_id={target_id}, class_result_id={class_result_id}")
            return response
            
        except Exception as e:
            logger.error(f"자동분류 실행 실패: {e}", exc_info=True)
            raise
    
    def _calculate_category_stats(self, tickets: List[Dict], classifications: List[Dict], 
                                   category_mapping: Dict[int, str]) -> List[Dict[str, Any]]:
        """카테고리별 집계 계산"""
        category_counts = defaultdict(int)
        category_keywords = defaultdict(set)
        
        for item in classifications:
            cls = item['classification']
            cat_id = cls['category_id']
            category_counts[cat_id] += 1
            
            # 키워드 수집
            for kw in cls.get('keywords', []):
                category_keywords[cat_id].add(kw)
        
        total = len(tickets)
        results = []
        
        for cat_id, count in category_counts.items():
            results.append({
                'category_id': cat_id,
                'category_name': category_mapping.get(cat_id, '알 수 없음'),
                'count': count,
                'ratio': round(count / total, 6) if total > 0 else 0,
                'keywords': list(category_keywords[cat_id])[:10]  # 상위 10개
            })
        
        # count 기준 내림차순 정렬
        results.sort(key=lambda x: x['count'], reverse=True)
        
        return results
    
    def _calculate_channel_stats(self, tickets: List[Dict], classifications: List[Dict]) -> List[Dict[str, Any]]:
        """채널별 카테고리 분포 집계"""
        # channel + category_id 조합별 카운트
        channel_category_counts = defaultdict(lambda: defaultdict(int))
        channel_totals = defaultdict(int)
        
        ticket_map = {t['ticket_id']: t for t in tickets}
        
        for item in classifications:
            ticket_id = item['ticket_id']
            ticket = ticket_map.get(ticket_id)
            if not ticket:
                continue
            
            channel = ticket.get('channel') or '알 수 없음'
            cat_id = item['classification']['category_id']
            
            channel_category_counts[channel][cat_id] += 1
            channel_totals[channel] += 1
        
        # 결과 리스트 생성
        results = []
        total_all = sum(channel_totals.values())
        
        for channel, category_counts in channel_category_counts.items():
            channel_total = channel_totals[channel]
            
            for cat_id, count in category_counts.items():
                results.append({
                    'channel': channel,
                    'category_id': cat_id,
                    'count': count,
                    'ratio': round(count / channel_total, 6) if channel_total > 0 else 0
                })
        
        return results
    
    def _calculate_reliability_stats(self, classifications: List[Dict]) -> Dict[str, Any]:
        """신뢰도 통계 계산 (규칙 기반에 맞는 실제 지표)"""
        confidences = [item['classification']['confidence'] for item in classifications]
        total = len(confidences)
        
        if total == 0:
            return {
                'total_tickets': 0,
                'average_confidence': 0.0,
                'high_confidence_count': 0,
                'medium_confidence_count': 0,
                'low_confidence_count': 0,
                'needs_review_count': 0
            }
        
        # 평균 신뢰도
        avg_confidence = sum(confidences) / total
        
        # 신뢰도 분포 계산
        high_conf = sum(1 for c in confidences if c >= 0.8)      # 80% 이상: 높음
        medium_conf = sum(1 for c in confidences if 0.7 <= c < 0.8)  # 70~80%: 중간
        low_conf = sum(1 for c in confidences if c < 0.7)        # 70% 미만: 낮음
        
        return {
            'total_tickets': total,
            'average_confidence': round(avg_confidence, 3),
            'high_confidence_count': high_conf,
            'high_confidence_ratio': round(high_conf / total, 3),
            'medium_confidence_count': medium_conf,
            'medium_confidence_ratio': round(medium_conf / total, 3),
            'low_confidence_count': low_conf,
            'low_confidence_ratio': round(low_conf / total, 3),
            'needs_review_count': low_conf  # 재검토 필요 (신뢰도 낮은 것)
        }
    
    def _build_response(self, class_result_id: int, user_id: int, file_id: int, batch_id: int,
                       period_from, period_to,
                       tickets: List[Dict], classifications: List[Dict],
                       category_stats: List[Dict], channel_stats: List[Dict],
                       reliability_stats: Dict[str, Any],
                       category_mapping: Dict[int, str]) -> Dict[str, Any]:
        """프론트엔드 응답 JSON 생성 (배치 지원)"""
        
        # 카테고리 정보
        category_info = []
        for stat in category_stats:
            category_info.append({
                'category': stat['category_name'],
                'count': stat['count'],
                'ratio': stat['ratio'],
                'keywords': stat['keywords'][:5]  # 상위 5개만
            })
        
        # 채널별 정보
        channel_info = self._build_channel_info(channel_stats, category_mapping)
        
        # 티켓 샘플 (카테고리별 상위 3개)
        tickets_by_category = self._get_top_tickets_by_category(
            tickets, classifications, category_mapping
        )
        
        return {
            'return_code': 1,
            'class_result_id': class_result_id,
            'period': {
                'from': period_from.isoformat() if period_from else None,
                'to': period_to.isoformat() if period_to else None
            },
            'meta': {
                'user_id': user_id,
                'file_id': file_id,
                'batch_id': batch_id,  # 배치 ID 추가
                'total_tickets': len(tickets),
                'classified_at': datetime.now().isoformat(),
                'engine_name': self.classifier.get_engine_name()
            },
            'ui': {
                'legend_order': ['배송 문의', '환불/교환', '상품 문의', '기술 지원', '불만/클레임', '기타'],
                'colors': {
                    '배송 문의': '#ef4444',      # 빨강
                    '환불/교환': '#f59e0b',      # 주황
                    '상품 문의': '#10b981',      # 초록
                    '기술 지원': '#3b82f6',      # 파랑
                    '불만/클레임': '#ff7875',    # 분홍
                    '기타': '#9ca3af'           # 회색
                },
                'accuracy_color_thresholds': {'good': 0.90, 'warn': 0.75}
            },
            'category_info': category_info,
            'channel_info': channel_info,
            'reliability_info': reliability_stats,
            'tickets': {
                'all_by_category': tickets_by_category  # top3 → all로 변경
            }
        }
    
    def _build_channel_info(self, channel_stats: List[Dict], category_mapping: Dict[int, str]) -> List[Dict]:
        """채널별 정보 구조 생성"""
        # 채널별로 그룹화
        channels = defaultdict(lambda: {'count': 0, 'by_category': {}})
        
        for stat in channel_stats:
            channel = stat['channel']
            cat_id = stat['category_id']
            cat_name = category_mapping.get(cat_id, '알 수 없음')
            count = stat['count']
            
            channels[channel]['count'] += count
            channels[channel]['by_category'][cat_name] = count
        
        # 리스트로 변환
        result = []
        total_all = sum(ch['count'] for ch in channels.values())
        
        for channel, data in channels.items():
            result.append({
                'channel': channel,
                'count': data['count'],
                'ratio': round(data['count'] / total_all, 6) if total_all > 0 else 0,
                'by_category': data['by_category']
            })
        
        # count 기준 내림차순
        result.sort(key=lambda x: x['count'], reverse=True)
        
        return result
    
    def _get_top_tickets_by_category(self, tickets: List[Dict], classifications: List[Dict],
                                     category_mapping: Dict[int, str]) -> Dict[str, List[Dict]]:
        """카테고리별 모든 티켓 반환 (전체 표시)"""
        ticket_map = {t['ticket_id']: t for t in tickets}
        
        # 카테고리별 티켓 그룹화
        by_category = defaultdict(list)
        
        for item in classifications:
            ticket_id = item['ticket_id']
            ticket = ticket_map.get(ticket_id)
            if not ticket:
                continue
            
            cls = item['classification']
            cat_name = category_mapping.get(cls['category_id'], '알 수 없음')
            
            by_category[cat_name].append({
                'received_at': ticket.get('received_at').strftime('%Y-%m-%d') if ticket.get('received_at') else '-',
                'channel': ticket.get('channel') or '-',
                'content': ticket.get('body') or '',
                'preview': (ticket.get('body') or '')[:15] + '...' if ticket.get('body') else '',
                'category': cat_name,
                'keywords': cls.get('keywords', [])[:3],
                'confidence': self._calculate_importance(cls['confidence'])
            })
        
        # 모든 티켓 반환 (상위 3개 제한 제거)
        result = {}
        for cat_name, ticket_list in by_category.items():
            result[cat_name] = ticket_list  # [:3] 제거 - 전체 표시
        
        return result
    
    def _calculate_importance(self, confidence: float) -> str:
        """신뢰도 기반 중요도 계산"""
        if confidence >= 0.9:
            return '상'
        elif confidence >= 0.7:
            return '중'
        else:
            return '하'
    
    def _empty_response(self, user_id: int, file_id: int = None, batch_id: int = None) -> Dict[str, Any]:
        """티켓이 없을 때 빈 응답 (배치 지원)"""
        return {
            'return_code': 0,
            'message': '분류할 티켓이 없습니다.',
            'meta': {
                'user_id': user_id,
                'file_id': file_id,
                'batch_id': batch_id
            },
            'category_info': [],
            'channel_info': [],
            'reliability_info': {},
            'tickets': {'top3_by_category': {}}
        }
