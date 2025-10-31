import openai
import json
from typing import Dict, List, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class AIService:
    """OpenAI ChatGPT 연동 서비스 클래스"""
    
    def __init__(self, api_key: str = None):
        """
        AI 서비스 초기화
        
        Args:
            api_key: OpenAI API 키 (환경변수에서 자동 로드 가능)
        """
        self.api_key = api_key or self._get_api_key()
        if self.api_key:
            openai.api_key = self.api_key
        else:
            logger.warning("OpenAI API 키가 설정되지 않았습니다. 환경변수 OPENAI_API_KEY를 설정하세요.")
    
    def _get_api_key(self) -> Optional[str]:
        """환경변수에서 API 키 가져오기"""
        import os
        return os.getenv('OPENAI_API_KEY')
    
    def analyze_cs_insights(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CS 데이터 인사이트 분석
        
        Args:
            analysis_data: 분석할 데이터 (티켓 요약, 분류 데이터, 트렌드 등)
            
        Returns:
            분석 결과 (인사이트, 솔루션 제안 등)
        """
        logger.info("CS 데이터 인사이트 분석 시작")
        
        try:
            # 프롬프트 구성
            prompt = self._build_analysis_prompt(analysis_data)
            
            # OpenAI API 호출
            response = self._call_openai_api(prompt)
            
            # 응답 파싱
            insights = self._parse_analysis_response(response)
            
            logger.info("CS 데이터 인사이트 분석 완료")
            return insights
            
        except Exception as e:
            logger.error(f"CS 데이터 인사이트 분석 실패: {e}")
            return self._get_fallback_insights()
    
    def generate_solution_recommendations(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """
        솔루션 제안 생성
        
        Args:
            insights: 인사이트 분석 결과
            
        Returns:
            솔루션 제안 결과
        """
        logger.info("솔루션 제안 생성 시작")
        
        try:
            prompt = self._build_solution_prompt(insights)
            response = self._call_openai_api(prompt)
            solutions = self._parse_solution_response(response)
            
            logger.info("솔루션 제안 생성 완료")
            return solutions
            
        except Exception as e:
            logger.error(f"솔루션 제안 생성 실패: {e}")
            return self._get_fallback_solutions()
    
    def generate_comprehensive_report(self, cs_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CS 데이터 기반 종합 리포트 생성 (데이터 요약, 인사이트, 솔루션 통합)
        
        Args:
            cs_data: CS 분석 데이터 (카테고리, 채널, 해결률 등)
            
        Returns:
            종합 리포트 (summary, insight, solution)
        """
        logger.info("=== GPT 기반 종합 리포트 생성 시작 ===")
        
        # API 키 확인
        if not self.api_key:
            logger.warning("⚠️  OpenAI API 키가 없습니다. Fallback 리포트를 사용합니다.")
            logger.warning("환경변수 OPENAI_API_KEY를 설정하면 GPT 기반 분석을 사용할 수 있습니다.")
            return self._get_fallback_comprehensive_report(cs_data)
        
        try:
            # 프롬프트 구성
            logger.info("프롬프트 구성 중...")
            prompt = self._build_comprehensive_report_prompt(cs_data)
            
            # OpenAI API 호출
            logger.info("🤖 GPT API 호출 중... (최대 30초 소요 예상)")
            import time
            start_time = time.time()
            
            response = self._call_openai_api(prompt, max_tokens=7000)
            
            elapsed = time.time() - start_time
            logger.info(f"✅ GPT API 응답 완료 (소요 시간: {elapsed:.2f}초)")
            
            # 응답 파싱
            logger.info("GPT 응답 파싱 중...")
            report = self._parse_comprehensive_report_response(response)
            
            # AI 생성 메타데이터 추가
            report['_is_ai_generated'] = True
            report['_data_source'] = 'gpt-4o-mini'
            
            logger.info("=== 종합 리포트 생성 완료 (GPT 기반) ===")
            return report
            
        except Exception as e:
            logger.error(f"❌ GPT 리포트 생성 실패: {e}")
            logger.warning("⚠️  Fallback 리포트를 사용합니다.")
            return self._get_fallback_comprehensive_report(cs_data)
    
    def _build_analysis_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """인사이트 분석용 프롬프트 구성"""
        prompt = f"""
다음 CS 데이터를 분석하여 인사이트를 도출해주세요.

데이터 요약:
- 총 티켓 수: {len(analysis_data.get('ticket_summaries', []))}
- 카테고리 분포: {analysis_data.get('trend_analysis', {}).get('category_trends', {})}
- 감정 분석: {analysis_data.get('issue_patterns', {}).get('sentiment_analysis', {})}

주요 키워드:
{analysis_data.get('issue_patterns', {}).get('top_keywords', {})}

문제가 많은 카테고리:
{analysis_data.get('issue_patterns', {}).get('problem_categories', {})}

다음 형식으로 분석 결과를 제공해주세요:
1. 주요 인사이트 (3-5개)
2. 문제점 식별
3. 개선 기회
4. 우선순위 제안

JSON 형식으로 응답해주세요:
{{
    "insights": [
        {{"title": "인사이트 제목", "description": "상세 설명", "priority": "high/medium/low"}}
    ],
    "problems": [
        {{"category": "문제 카테고리", "description": "문제 설명", "impact": "영향도"}}
    ],
    "opportunities": [
        {{"area": "개선 영역", "description": "개선 방안", "expected_impact": "예상 효과"}}
    ]
}}
"""
        return prompt
    
    def _build_solution_prompt(self, insights: Dict[str, Any]) -> str:
        """솔루션 제안용 프롬프트 구성"""
        prompt = f"""
다음 인사이트를 바탕으로 구체적인 솔루션을 제안해주세요.

인사이트:
{json.dumps(insights, ensure_ascii=False, indent=2)}

다음 영역별로 솔루션을 제안해주세요:
1. 매크로/자동화 솔루션
2. 프로세스 개선 솔루션  
3. 제품/서비스 개선 솔루션
4. 고객 경험 개선 솔루션

각 솔루션은 다음 정보를 포함해주세요:
- 솔루션명
- 구체적인 실행 방안
- 예상 효과
- 구현 난이도
- 우선순위

JSON 형식으로 응답해주세요:
{{
    "solutions": [
        {{
            "category": "솔루션 카테고리",
            "name": "솔루션명",
            "description": "상세 설명",
            "implementation": "구현 방안",
            "expected_impact": "예상 효과",
            "difficulty": "easy/medium/hard",
            "priority": "high/medium/low"
        }}
    ],
    "recommendations": [
        {{
            "title": "권고사항 제목",
            "description": "권고사항 설명",
            "timeline": "실행 일정",
            "resources": "필요 자원"
        }}
    ]
}}
"""
        return prompt
    
    def _call_openai_api(self, prompt: str, max_tokens: int = 7000) -> str:
        """OpenAI API 호출"""
        if not self.api_key:
            raise Exception("OpenAI API 키가 설정되지 않았습니다.")
        
        try:
            from config import Config
            model_name = Config.OPENAI_MODEL
            
            logger.info(f"GPT 모델 호출: {model_name} (max_tokens={max_tokens})")
            logger.info(f"API 키 앞 10자: {self.api_key[:10]}... (총 길이: {len(self.api_key)})")
            
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "당신은 CS 데이터 분석 전문가입니다. 정확하고 실용적이며 매우 상세한 인사이트와 솔루션을 제공해주세요. 각 항목은 구체적이고 풍부한 내용으로 작성하세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            logger.info(f"GPT 응답 수신 완료 (길이: {len(content)} chars)")
            
            return content
            
        except openai.error.AuthenticationError as e:
            logger.error(f"❌ OpenAI 인증 실패: API 키가 유효하지 않습니다.")
            logger.error(f"상세 오류: {str(e)}")
            raise Exception("OpenAI API 키가 유효하지 않습니다. .env 파일의 OPENAI_API_KEY를 확인하세요.")
        except openai.error.RateLimitError as e:
            logger.error(f"❌ OpenAI 사용량 초과: {e}")
            raise Exception("OpenAI API 사용량 한도를 초과했습니다. 잠시 후 다시 시도하세요.")
        except openai.error.InvalidRequestError as e:
            logger.error(f"❌ OpenAI 잘못된 요청: {e}")
            raise Exception(f"OpenAI API 요청 오류: {str(e)}")
        except Exception as e:
            logger.error(f"❌ OpenAI API 호출 실패: {e}")
            logger.error(f"오류 타입: {type(e).__name__}")
            logger.error(f"상세 오류: {str(e)}")
            raise
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """분석 응답 파싱"""
        try:
            # JSON 응답 파싱 시도
            if response.strip().startswith('{'):
                return json.loads(response)
            else:
                # JSON이 아닌 경우 기본 구조로 변환
                return self._parse_text_response(response, 'analysis')
        except json.JSONDecodeError:
            logger.warning("JSON 파싱 실패, 텍스트 응답으로 처리")
            return self._parse_text_response(response, 'analysis')
    
    def _parse_solution_response(self, response: str) -> Dict[str, Any]:
        """솔루션 응답 파싱"""
        try:
            if response.strip().startswith('{'):
                return json.loads(response)
            else:
                return self._parse_text_response(response, 'solution')
        except json.JSONDecodeError:
            logger.warning("JSON 파싱 실패, 텍스트 응답으로 처리")
            return self._parse_text_response(response, 'solution')
    
    def _parse_text_response(self, response: str, response_type: str) -> Dict[str, Any]:
        """텍스트 응답을 구조화된 데이터로 변환"""
        if response_type == 'analysis':
            return {
                "insights": [
                    {"title": "주요 인사이트", "description": response[:200] + "...", "priority": "medium"}
                ],
                "problems": [
                    {"category": "일반", "description": "데이터 분석 중", "impact": "중간"}
                ],
                "opportunities": [
                    {"area": "전반적", "description": "개선 기회 식별 중", "expected_impact": "긍정적"}
                ]
            }
        else:  # solution
            return {
                "solutions": [
                    {
                        "category": "일반",
                        "name": "솔루션 제안",
                        "description": response[:200] + "...",
                        "implementation": "단계별 실행",
                        "expected_impact": "개선 예상",
                        "difficulty": "medium",
                        "priority": "medium"
                    }
                ],
                "recommendations": [
                    {
                        "title": "권고사항",
                        "description": "추가 검토 필요",
                        "timeline": "1-2주",
                        "resources": "기본 자원"
                    }
                ]
            }
    
    def _get_fallback_insights(self) -> Dict[str, Any]:
        """API 실패 시 대체 인사이트"""
        return {
            "insights": [
                {
                    "title": "데이터 분석 중",
                    "description": "AI 분석 서비스가 일시적으로 사용할 수 없습니다. 기본 분석을 제공합니다.",
                    "priority": "medium"
                }
            ],
            "problems": [
                {
                    "category": "서비스",
                    "description": "AI 분석 서비스 연결 문제",
                    "impact": "낮음"
                }
            ],
            "opportunities": [
                {
                    "area": "시스템",
                    "description": "AI 서비스 안정성 개선",
                    "expected_impact": "높음"
                }
            ]
        }
    
    def _get_fallback_solutions(self) -> Dict[str, Any]:
        """API 실패 시 대체 솔루션"""
        return {
            "solutions": [
                {
                    "category": "시스템",
                    "name": "AI 서비스 복구",
                    "description": "AI 분석 서비스를 복구하여 정상적인 인사이트를 제공합니다.",
                    "implementation": "시스템 관리자 문의",
                    "expected_impact": "높음",
                    "difficulty": "easy",
                    "priority": "high"
                }
            ],
            "recommendations": [
                {
                    "title": "대안 분석",
                    "description": "기본 통계 분석을 활용한 인사이트 제공",
                    "timeline": "즉시",
                    "resources": "기본 자원"
                }
            ]
        }
    
    def _build_comprehensive_report_prompt(self, cs_data: Dict[str, Any]) -> str:
        """종합 리포트 생성용 프롬프트 구성 (개선된 JSON 구조)"""
        
        # CS 데이터를 읽기 쉬운 형식으로 변환
        total_tickets = cs_data.get('total_tickets', 0)
        
        # Decimal을 float로 변환하는 헬퍼 함수
        def safe_float(value, default=0.0):
            """Decimal, int, float를 안전하게 float로 변환"""
            try:
                return float(value) if value is not None else default
            except (ValueError, TypeError):
                return default
        
        def safe_int(value, default=0):
            """값을 안전하게 int로 변환"""
            try:
                return int(value) if value is not None else default
            except (ValueError, TypeError):
                return default
        
        # 카테고리별 분포 (category_id 포함)
        category_info = ""
        category_list = []
        for cat in cs_data.get('category_distribution', []):
            category_info += f"- [ID:{cat.get('category_id', 0)}] {cat['category_name']}: {cat['count']}건 ({cat['percentage']}%)\n"
            category_list.append({
                'id': safe_int(cat.get('category_id', 0)),
                'name': str(cat['category_name']),
                'count': safe_int(cat['count']),
                'percentage': safe_float(cat['percentage'])
            })
        
        # 채널별 분포
        channel_info = ""
        channel_list = []
        for ch in cs_data.get('channel_distribution', []):
            channel_info += f"- {ch['channel']}: {ch['count']}건 ({ch['percentage']}%)\n"
            channel_list.append({
                'name': str(ch['channel']),
                'count': safe_int(ch['count']),
                'percentage': safe_float(ch['percentage'])
            })
        
        # 채널별 해결률
        resolution_info = ""
        resolution_list = []
        for res in cs_data.get('channel_resolution_rates', []):
            resolution_info += f"- {res['channel']}: {res['resolution_rate']}% (해결 {res['resolved']}건 / 전체 {res['total']}건)\n"
            resolution_list.append({
                'channel': str(res.get('channel', '미분류')),
                'total': safe_int(res.get('total', 0)),
                'resolved': safe_int(res.get('resolved', 0)),
                'resolution_rate': safe_float(res.get('resolution_rate', 0.0))
            })
        
        # JSON 문자열로 변환 (f-string 내부에서 안전하게 사용)
        category_list_json = json.dumps(category_list, ensure_ascii=False)
        channel_list_json = json.dumps(channel_list, ensure_ascii=False)
        resolution_list_json = json.dumps(resolution_list, ensure_ascii=False)
        
        prompt = f"""당신은 고객 CS 데이터를 분석하여 자동 분류 및 솔루션을 제안하는 AI 서비스의 분석 전문가입니다.

다음 데이터를 기반으로 아래 4가지 항목에 대해 JSON 형식으로 응답해 주세요.

**CS 데이터:**
- 전체 CS 건수: {total_tickets}건

**카테고리별 분포:**
{category_info}

**채널별 분포:**
{channel_info}

**채널별 해결률:**
{resolution_info}

**사용 가능한 카테고리 목록 (반드시 정확한 ID와 이름 사용):**
{category_list_json}

---

**응답 형식 (중요!):**

다음 4가지 항목을 포함한 JSON 형식으로 응답해주세요:

1. **summary**: 전체 CS 건수, 카테고리별 비율, 채널별 해결률
   - total_cs_count: 전체 건수 (number)
   - categories: 배열 형태 [{{category_id, category_name, count, percentage}}]
   - channels: 배열 형태 [{{channel, total, resolved, resolution_rate}}]

2. **insight**: 카테고리별 인사이트 (상세 분석)
   - by_category: 배열 형태 [{{category_id, category_name, priority, problem, short_term_goal, long_term_goal}}]
     * problem: 문제점을 5-7문장으로 상세히 분석 (원인, 영향, 현황 포함)
     * short_term_goal: 단기 목표를 4-5문장으로 구체적으로 서술 (달성 기준, 예상 효과 포함)
     * long_term_goal: 장기 목표를 4-5문장으로 전략적으로 서술 (비전, 지속가능성 포함)
   - overall: 종합 인사이트 {{summary, notable_issues}}
     * summary: 전체 CS 데이터의 종합 분석을 10-15문장으로 풍부하게 작성 (트렌드, 패턴, 주요 발견사항, 전반적 평가 포함)
     * notable_issues: 주요 이슈를 7-10개로 구체적으로 나열 (각 이슈는 상세한 설명 포함)

3. **solution**: 단기/중기/장기 전략 제안 (구체적 실행 방안)
   - current_status_and_problems: 현황 및 문제점: 요약 {{status, problems}}
     * status: 현재 CS 운영 현황을 7-10문장으로 상세히 분석
     * problems: 주요 문제점을 6-8문장으로 구체적으로 설명 (우선순위, 시급성 포함)
   - short_term: 단기 솔루션 (1-6개월) {{goal_kpi, plan, actions: []}}
     * goal_kpi: 다음 형식으로 작성하세요: "[구체적 목표] (KPI: [측정 가능한 지표])"
       예시: "고객 응답 속도 개선 (KPI: 평균 응답 시간 30% 단축, 첫 응답 시간 5분 이내 달성률 90%)"
       5-6문장으로 목표 달성 기준, 모니터링 방법, 예상 달성 시기를 포함하여 구체적으로 작성하세요.
     * plan: 단기 실행 계획을 4-5문장으로 상세히 설명
     * actions: 5-8개의 구체적인 액션 아이템 (각 액션은 실행 가능하고 측정 가능해야 함)
   - mid_term: 중기 솔루션 (6-12개월) {{goal_kpi, plan, actions: []}}
     * goal_kpi: 다음 형식으로 작성하세요: "[구체적 목표] (KPI: [측정 가능한 지표])"
       예시: "CS 운영 효율성 극대화 (KPI: 처리 시간 40% 단축, 고객 만족도 85점 달성)"
       5-6문장으로 단기 목표와의 연계성, 발전 방향, 측정 지표를 명확히 하세요.
     * plan: 중기 실행 계획을 4-5문장으로 상세히 설명
     * actions: 5-8개의 구체적인 액션 아이템
   - long_term: 장기 솔루션 (12개월+) {{goal_kpi, plan, actions: []}}
     * goal_kpi: 다음 형식으로 작성하세요: "[전략적 비전] (KPI: [장기 성과 지표])"
       예시: "업계 최고 수준의 고객 경험 제공 (KPI: NPS 70점 이상, 재구매율 60% 달성)"
       5-6문장으로 비전, 조직 문화 변화, 지속 가능한 성장 방향, 경쟁력 강화를 포함하세요.
     * plan: 장기 실행 계획을 4-5문장으로 상세히 설명
     * actions: 5-8개의 구체적인 액션 아이템 (장기 전략과 연계)
   - expected_effects_and_risks: 기대효과 및 리스크 관리 {{expected_effects, risk_management}}
     * expected_effects: 예상 효과를 6-8문장으로 구체적으로 설명 (정량적, 정성적 효과 모두 포함)
     * risk_management: 리스크와 관리 방안을 6-8문장으로 상세히 작성 (예방책, 대응책 포함)

**중요 규칙:**
- 카테고리 ID와 이름을 반드시 위 목록에서 선택하세요
- 모든 숫자는 number 타입으로 (문자열 X)
- 비율은 % 기호 없이 숫자만 (예: 40.0)
- 배열 형태로 반환하세요
- 순수한 JSON만 (마크다운 코드 블록 ``` 제외)

예시 (반드시 순수한 JSON만 반환하세요):

다음은 실제 데이터를 기반으로 한 응답 예시입니다. 이 형식을 정확히 따라주세요.
카테고리 목록: {category_list_json}
채널 목록: {channel_list_json}
해결률 데이터: {resolution_list_json}

응답 형식:
{{
  "summary": {{
    "total_cs_count": (숫자),
    "categories": [
      {{"category_id": (숫자), "category_name": "이름", "count": (숫자), "percentage": (숫자)}}
    ],
    "channels": [
      {{"channel": "이름", "total": (숫자), "resolved": (숫자), "resolution_rate": (숫자)}}
    ]
  }},
  "insight": {{
    "by_category": [
      {{
        "category_id": (숫자),
        "category_name": "이름",
        "priority": "high/medium/low",
        "problem": "문제점을 5-7문장으로 상세히 분석. 문제의 원인, 현재 상황, 고객에게 미치는 영향, 비즈니스 임팩트 등을 구체적으로 설명하세요.",
        "short_term_goal": "단기 목표를 4-5문장으로 구체적으로 서술. 달성 기준, 예상 효과, 실행 시기, 측정 방법 등을 포함하세요.",
        "long_term_goal": "장기 목표를 4-5문장으로 전략적으로 서술. 비전, 지속가능한 개선 방향, 기대되는 변화, 조직 차원의 효과 등을 포함하세요."
      }}
    ],
    "overall": {{
      "summary": "전체 CS 데이터의 종합 분석을 10-15문장으로 풍부하게 작성하세요. 주요 트렌드, 패턴, 발견사항, 전반적 평가, 긍정적 측면과 개선이 필요한 측면, 데이터가 보여주는 인사이트 등을 깊이 있게 분석하세요.",
      "notable_issues": [
        "주요 이슈 1 - 구체적이고 상세한 설명 포함",
        "주요 이슈 2 - 구체적이고 상세한 설명 포함",
        "주요 이슈 3 - 구체적이고 상세한 설명 포함",
        "... (7-10개의 이슈를 상세하게 나열)"
      ]
    }}
  }},
  "solution": {{
    "current_status_and_problems": {{
      "status": "현재 CS 운영 현황을 7-10문장으로 상세히 분석하세요. 처리량, 응답 시간, 고객 만족도, 운영 효율성, 리소스 현황, 강점과 약점 등을 포함하세요.",
      "problems": "주요 문제점을 6-8문장으로 구체적으로 설명하세요. 우선순위, 시급성, 비즈니스 임팩트, 근본 원인, 연쇄 효과 등을 포함하세요."
    }},
    "short_term": {{
      "goal_kpi": "고객 응답 속도 개선 (KPI: 평균 응답 시간 30% 단축, 첫 응답 시간 5분 이내 달성률 90%). 이후 4-5문장으로 목표 달성 기준, 모니터링 방법, 예상 달성 시기를 구체적으로 작성하세요.",
      "plan": "단기 실행 계획을 4-5문장으로 상세히 설명하세요. 실행 순서, 필요 리소스, 주요 마일스톤, 책임 부서 등을 포함하세요.",
      "actions": [
        "단기 액션 1 - 구체적이고 실행 가능한 액션 아이템",
        "단기 액션 2 - 구체적이고 실행 가능한 액션 아이템",
        "단기 액션 3 - 구체적이고 실행 가능한 액션 아이템",
        "단기 액션 4 - 구체적이고 실행 가능한 액션 아이템",
        "단기 액션 5 - 구체적이고 실행 가능한 액션 아이템",
        "... (5-8개의 상세한 액션 아이템)"
      ]
    }},
    "mid_term": {{
      "goal_kpi": "CS 운영 효율성 극대화 (KPI: 처리 시간 40% 단축, 고객 만족도 85점 달성, 재문의율 20% 감소). 이후 4-5문장으로 단기 목표와의 연계성, 발전 방향, 측정 지표를 명확히 하세요.",
      "plan": "중기 실행 계획을 4-5문장으로 상세히 설명하세요. 단계별 실행 전략, 필요한 변화, 조직 역량 강화 방안 등을 포함하세요.",
      "actions": [
        "중기 액션 1 - 구체적이고 실행 가능한 액션 아이템",
        "중기 액션 2 - 구체적이고 실행 가능한 액션 아이템",
        "중기 액션 3 - 구체적이고 실행 가능한 액션 아이템",
        "중기 액션 4 - 구체적이고 실행 가능한 액션 아이템",
        "중기 액션 5 - 구체적이고 실행 가능한 액션 아이템",
        "... (5-8개의 상세한 액션 아이템)"
      ]
    }},
    "long_term": {{
      "goal_kpi": "업계 최고 수준의 고객 경험 제공 (KPI: NPS 70점 이상, 재구매율 60% 달성, 고객 이탈률 5% 이하 유지). 이후 4-5문장으로 비전, 조직 문화 변화, 지속 가능한 성장 방향, 경쟁력 강화를 포함하세요.",
      "plan": "장기 실행 계획을 4-5문장으로 상세히 설명하세요. 전략적 방향성, 혁신 계획, 시스템 고도화, 인재 육성 등을 포함하세요.",
      "actions": [
        "장기 액션 1 - 전략적이고 구체적인 액션 아이템",
        "장기 액션 2 - 전략적이고 구체적인 액션 아이템",
        "장기 액션 3 - 전략적이고 구체적인 액션 아이템",
        "장기 액션 4 - 전략적이고 구체적인 액션 아이템",
        "장기 액션 5 - 전략적이고 구체적인 액션 아이템",
        "... (5-8개의 상세한 액션 아이템)"
      ]
    }},
    "expected_effects_and_risks": {{
      "expected_effects": "예상 효과를 6-8문장으로 구체적으로 설명하세요. 정량적 효과 (비용 절감, 효율성 증가, 만족도 향상 등의 수치), 정성적 효과 (브랜드 이미지, 고객 충성도, 조직 문화 등), 단계별 효과 등을 모두 포함하세요.",
      "risk_management": "리스크와 관리 방안을 6-8문장으로 상세히 작성하세요. 예상되는 주요 리스크, 리스크 발생 시 영향도, 사전 예방책, 발생 시 대응 방안, 모니터링 체계 등을 구체적으로 설명하세요."
    }}
  }}
}}
"""
        return prompt
    
    def _parse_comprehensive_report_response(self, response: str) -> Dict[str, Any]:
        """종합 리포트 응답 파싱"""
        try:
            # JSON 코드 블록 제거 (```json ... ``` 형식)
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            # JSON 파싱
            report = json.loads(response)
            
            # 필수 키 검증 (새 구조에 맞춰 수정)
            required_keys = ['summary', 'insight', 'solution']
            for key in required_keys:
                if key not in report:
                    logger.warning(f"필수 키 '{key}'가 응답에 없습니다. 기본값 설정")
                    if key == 'summary':
                        report[key] = {'total_cs_count': 0, 'categories': [], 'channels': []}
                    elif key == 'insight':
                        report[key] = {'by_category': [], 'overall': {'summary': '', 'notable_issues': []}}
                    elif key == 'solution':
                        report[key] = {
                            'current_status_and_problems': {'status': '', 'problems': ''},
                            'short_term': {'goal_kpi': '', 'plan': '', 'actions': []},
                            'mid_term': {'goal_kpi': '', 'plan': '', 'actions': []},
                            'long_term': {'goal_kpi': '', 'plan': '', 'actions': []},
                            'expected_effects_and_risks': {'expected_effects': '', 'risk_management': ''}
                        }
            
            logger.info(f"GPT 응답 파싱 성공")
            return report
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 파싱 실패: {e}")
            logger.error(f"원본 응답 (처음 500자): {response[:500]}")
            return self._get_fallback_comprehensive_report({})
        except Exception as e:
            logger.error(f"❌ 응답 파싱 중 오류: {e}")
            logger.error(f"오류 타입: {type(e).__name__}")
            return self._get_fallback_comprehensive_report({})
    
    def _get_fallback_comprehensive_report(self, cs_data: Dict[str, Any]) -> Dict[str, Any]:
        """API 실패 시 대체 리포트 (개선된 JSON 구조) - DB 데이터 활용"""
        logger.info("Fallback 리포트 생성: DB 데이터 기반 요약만 제공")
        
        total_tickets = cs_data.get('total_tickets', 0)
        
        # 카테고리 데이터 변환 (DB에서 가져온 실제 데이터)
        categories = []
        for cat in cs_data.get('category_distribution', []):
            categories.append({
                'category_id': cat.get('category_id', 0),
                'category_name': cat['category_name'],
                'count': cat['count'],
                'percentage': cat['percentage']
            })
        
        # 채널 데이터 변환 (DB에서 가져온 실제 데이터)
        channels = []
        for res in cs_data.get('channel_resolution_rates', []):
            channels.append({
                'channel': res['channel'],
                'total': res['total'],
                'resolved': res['resolved'],
                'resolution_rate': res['resolution_rate']
            })
        
        return {
            "summary": {
                "total_cs_count": total_tickets,
                "categories": categories,
                "channels": channels
            },
            "insight": {
                "by_category": [],  # AI 없이는 빈 배열
                "overall": {
                    "summary": "",
                    "notable_issues": []
                }
            },
            "solution": {
                "current_status_and_problems": {
                    "status": "",
                    "problems": ""
                },
                "short_term": {
                    "goal_kpi": "",
                    "plan": "",
                    "actions": []
                },
                "mid_term": {
                    "goal_kpi": "",
                    "plan": "",
                    "actions": []
                },
                "long_term": {
                    "goal_kpi": "",
                    "plan": "",
                    "actions": []
                },
                "expected_effects_and_risks": {
                    "expected_effects": "",
                    "risk_management": ""
                }
            },
            "_is_ai_generated": False,  # Fallback 표시
            "_data_source": "fallback",
            "_fallback_reason": "OpenAI API 연동 실패"
        }

# 싱글톤 인스턴스
ai_service = AIService()
