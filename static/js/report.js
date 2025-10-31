/**
 * 분석 리포트 기능 JavaScript (실제 스키마 기반)
 */

class ReportManager {
    constructor() {
        this.currentFileId = null;  // 파일 ID (자동 선택)
        this.currentReportId = null;  // 리포트 ID (PDF 다운로드용)
        this.currentUserId = this.getUserId();  // 동적으로 가져오기
        this.isGenerating = false;
        this.chartInstances = {};  // Chart.js 인스턴스 저장
        this.modalChartInstance = null;  // 모달용 차트 인스턴스
        
        this.init();
    }
    
    getUserId() {
        // 세션 스토리지에서 user_id 가져오기
        const sessionUserId = sessionStorage.getItem('user_id');
        if (sessionUserId) {
            return parseInt(sessionUserId);
        }
        
        // 로컬 스토리지에서 가져오기
        const localUserId = localStorage.getItem('user_id');
        if (localUserId) {
            return parseInt(localUserId);
        }
        
        // 기본값 1 (환경변수에서 가져온 값)
        return window.DEFAULT_USER_ID || 1;
    }
    
    init() {
        this.bindEvents();
        this.loadReportSection();
        this.createChartModal();
        this.loadLastReportData(); // 마지막 리포트 데이터 자동 로드
    }
    
    bindEvents() {
        // 리포트 생성 버튼 이벤트
        const generateBtn = document.querySelector('#btn-generate-report');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateReport());
        }
        
        // 템플릿 선택 이벤트
        const templateSelect = document.querySelector('#template-select');
        if (templateSelect) {
            templateSelect.addEventListener('change', () => this.handleTemplateChange());
        }
        
        // 비교 분석 옵션 이벤트
        const periodSelect = document.querySelector('#period-select');
        const compareTypeSelect = document.querySelector('#compare-type');
        
        if (periodSelect) {
            periodSelect.addEventListener('change', () => this.updateComparisonOptions());
        }
        
        if (compareTypeSelect) {
            compareTypeSelect.addEventListener('change', () => this.updateComparisonOptions());
        }
        
        // 공유 버튼 이벤트
        const shareBtn = document.querySelector('#btn-share-report');
        if (shareBtn) {
            shareBtn.addEventListener('click', () => this.showShareModal());
        }
    }
    
    async generateReport() {
        if (this.isGenerating) {
            this.showMessage('리포트 생성 중입니다. 잠시만 기다려주세요.', 'warning');
            return;
        }
        
        this.isGenerating = true;
        this.showLoading(true);
        
        try {
            console.log('GPT 기반 리포트 생성 시작...');
            
            // 선택된 템플릿 가져오기
            const templateSelect = document.getElementById('template-select');
            const selectedTemplate = templateSelect ? templateSelect.value : 'standard';
            
            // 1. 리포트 생성 API 호출 (최신 파일 자동 선택)
            const reportData = await this.callGenerateReportAPI(selectedTemplate);
            
            // 리포트 ID 저장 (PDF 다운로드용)
            this.currentReportId = reportData.report_id;
            this.currentFileId = reportData.file_id;
            
            // 2. AI 생성 여부 확인 및 경고 표시
            if (!reportData.is_ai_generated || reportData.data_source === 'fallback') {
                this.showMessage(`⚠️ AI 연동 실패. 기본 분석 데이터를 표시합니다. (OPENAI_API_KEY 확인 필요)`, 'warning');
                console.warn('AI 생성 실패: Fallback 데이터 사용 중');
            } else {
                this.showMessage(`✅ AI 리포트가 성공적으로 생성되었습니다. (Report ID: ${reportData.report_id})`, 'success');
                console.log('GPT 기반 리포트 생성 완료:', reportData.data_source);
            }
            
            // 3. 템플릿별 렌더링
            this.renderByTemplate(selectedTemplate, reportData);
            
            // 4. localStorage에 리포트 데이터 저장 (자동 복원용)
            const currentTime = new Date().toLocaleString('ko-KR');
            localStorage.setItem('report:last_data', JSON.stringify(reportData));
            localStorage.setItem('report:last_generated_at', currentTime);
            console.log('리포트 데이터가 localStorage에 저장되었습니다.');
            
        } catch (error) {
            console.error('리포트 생성 실패:', error);
            this.showMessage(error.message || '리포트 생성 중 오류가 발생했습니다.', 'error');
        } finally {
            this.isGenerating = false;
            this.showLoading(false);
        }
    }
    
    async callGenerateReportAPI(template = 'standard') {
        // 선택된 카테고리 가져오기
        const categorySelect = document.getElementById('category-select');
        const selectedCategory = categorySelect ? categorySelect.value : 'ClaraCS';
        
        const response = await fetch('/api/report/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: this.currentUserId,  // file_id는 자동 선택
                template: template,
                company_name: selectedCategory  // 선택된 카테고리를 회사명으로 전달
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || '리포트 생성 실패');
        }
        
        return result.data;
    }
    
    renderChannelTrends(channelTrends) {
        console.log('채널별 추이 렌더링 시작...', channelTrends);
        
        const container = document.getElementById('channel-charts-container');
        if (!container) return;
        
        // 기존 차트 및 Empty State 제거
        Object.values(this.chartInstances).forEach(chart => chart.destroy());
        this.chartInstances = {};
        container.innerHTML = '';
        
        // 채널별 추이 카드 표시
        const chartCard = document.getElementById('channel-trends-card');
        if (chartCard) {
            chartCard.style.display = 'block';
        }
        
        // 채널 데이터가 없는 경우
        if (!channelTrends || Object.keys(channelTrends).length === 0) {
            container.classList.remove('has-charts');  // 그리드 클래스 제거
            container.innerHTML = '<div class="empty-state"><p class="empty-icon">📊</p><p class="empty-desc">채널별 데이터가 없습니다.</p></div>';
            return;
        }
        
        // 그리드 레이아웃 활성화
        container.classList.add('has-charts');
        
        // 각 채널별로 차트 생성
        Object.entries(channelTrends).forEach(([channel, trendData]) => {
            this.createChannelChart(container, channel, trendData);
        });
        
        // 드래그 앤 드롭 기능 초기화
        this.initDragAndDrop(container);
    }
    
    createChannelChart(container, channel, trendData) {
        console.log(`차트 생성: ${channel}`, trendData);
        
        const categories = trendData.categories || [];
        const dates = trendData.dates || [];
        const dataMatrix = trendData.data || [];
        
        if (dates.length === 0 || categories.length === 0) {
            console.warn(`${channel} 채널 데이터가 비어있습니다.`);
            return;
        }
        
        // 전체 합계 계산
        const totalCount = dataMatrix.reduce((sum, row) => 
            sum + row.reduce((a, b) => a + (b || 0), 0), 0
        );
        
        // 채널별 컨테이너 생성
        const channelDiv = document.createElement('div');
        channelDiv.className = 'channel-chart-wrapper';
        channelDiv.innerHTML = `
            <h4>${channel}</h4>
            <div class="ch-sub">${totalCount.toLocaleString()}건</div>
            <div>
                <canvas id="chart-${this.sanitizeId(channel)}"></canvas>
            </div>
        `;
        
        // 클릭 이벤트 추가 (모달 열기)
        channelDiv.addEventListener('click', () => {
            this.openChartModal(channel, trendData);
        });
        
        container.appendChild(channelDiv);
        
        // Chart.js 데이터셋 준비
        const datasets = [];
        const categoryColors = this.getCategoryColors();
        
        // 2. 전체 합계 꺾은선 그래프 (먼저 추가 → 막대 위에 표시)
        const totalData = dataMatrix.map(row => 
            row.reduce((sum, val) => sum + (val || 0), 0)
        );
        
        datasets.push({
            type: 'line',
            label: '전체 합계',
            data: totalData,
            borderColor: '#e74c3c',
            backgroundColor: 'rgba(231, 76, 60, 0.1)',
            borderWidth: 2,
            fill: false,
            tension: 0.3,
            pointRadius: 2,  // 작은 점
            pointHoverRadius: 4,  // 호버 시 크기
            pointBackgroundColor: '#e74c3c',
            pointBorderColor: '#fff',
            pointBorderWidth: 1,
            yAxisID: 'y',
            order: 1  // ✅ 막대 위에 표시 (낮은 숫자 = 위)
        });
        
        // 1. 카테고리별 스택 막대그래프 (나중에 추가 → 아래 레이어)
        categories.forEach((category, catIdx) => {
            const categoryData = dataMatrix.map(row => row[catIdx] || 0);
            
            datasets.push({
                type: 'bar',
                label: category,
                data: categoryData,
                backgroundColor: categoryColors[category] || this.getRandomColor(catIdx),
                borderColor: categoryColors[category] || this.getRandomColor(catIdx),
                borderWidth: 1,
                stack: 'stack1',  // 스택 그룹
                order: 2  // ✅ 아래 레이어
            });
        });
        
        // Chart.js 설정
        const config = {
            type: 'bar',
            data: {
                labels: dates,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    title: {
                        display: false
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 10,
                            font: {
                                size: 11
                            },
                            boxWidth: 12,
                            boxHeight: 12
                        },
                        maxHeight: 80
                    },
                    tooltip: {
                        callbacks: {
                            footer: (tooltipItems) => {
                                let sum = 0;
                                tooltipItems.forEach(item => {
                                    if (item.dataset.type === 'bar') {
                                        sum += item.parsed.y;
                                    }
                                });
                                return '합계: ' + sum + '건';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        title: {
                            display: true,
                            text: '날짜',
                            font: {
                                size: 11
                            }
                        },
                        ticks: {
                            font: {
                                size: 10
                            },
                            maxRotation: 45,
                            minRotation: 0
                        }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'CS 건수',
                            font: {
                                size: 11
                            }
                        },
                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    }
                }
            }
        };
        
        // 차트 생성
        const chartId = `chart-${this.sanitizeId(channel)}`;
        const ctx = document.getElementById(chartId).getContext('2d');
        this.chartInstances[channel] = new Chart(ctx, config);
    }
    
    sanitizeId(str) {
        return str.replace(/[^a-zA-Z0-9가-힣]/g, '-');
    }
    
    getCategoryColors() {
        return {
            // 새로운 8개 카테고리
            '품질/하자': '#FF6384',
            '서비스': '#36A2EB',
            '배송': '#FFCE56',
            'AS/수리': '#4BC0C0',
            '결제': '#9966FF',
            '이벤트': '#FF9F40',
            '일반': '#C9CBCF',
            '기타': '#E7E9ED',
            
            // 호환성을 위한 기존 카테고리 매핑
            '품질': '#FF6384',
            '품질불만': '#FF6384',
            '제품 하자': '#FF6384',
            '배송 문의': '#FFCE56',
            '배송지연': '#FFCE56',
            '환불': '#9966FF',
            '환불/교환': '#9966FF',
            '환불문의': '#9966FF',
            'AS': '#4BC0C0',
            'AS요청': '#4BC0C0',
            '기술 지원': '#4BC0C0',
            '상품 문의': '#C9CBCF',
            '기타문의': '#E7E9ED',
            '불만/클레임': '#36A2EB',
            '미분류': '#E7E9ED'
        };
    }
    
    getRandomColor(index) {
        const colors = [
            '#FF6384',
            '#36A2EB',
            '#FFCE56',
            '#4BC0C0',
            '#9966FF',
            '#FF9F40',
            '#C9CBCF',
            '#E7E9ED'
        ];
        return colors[index % colors.length];
    }
    
    renderSummary(summary) {
        console.log('데이터 요약 렌더링 시작...', summary);
        
        // 데이터 요약 컨테이너 (grid.cols-3 안의 첫 번째 카드)
        const container = document.querySelector('#report .grid.cols-3 .card:nth-child(1) .subtle');
        if (!container) return;
        
        const totalCount = summary.total_cs_count || 0;
        const categories = summary.categories || [];
        const channels = summary.channels || [];
        
        // 카테고리별 비율 리스트 (배열 기반)
        const categoryList = categories
            .map(cat => `<li><b>${cat.category_name}</b>: ${cat.count}건 (${cat.percentage}%)</li>`)
            .join('');
        
        // 채널별 해결률 리스트 (배열 기반)
        const channelList = channels
            .map(ch => `<li><b>${ch.channel}</b>: ${ch.resolution_rate}% (${ch.resolved}/${ch.total}건)</li>`)
            .join('');
        
        container.innerHTML = `
            <li><strong>전체 CS 건수:</strong> <b>${totalCount.toLocaleString()}건</b></li>
            <li><strong>카테고리별:</strong>
                <ul style="margin-left: 20px; margin-top: 5px;">
                    ${categoryList || '<li>데이터 없음</li>'}
                </ul>
            </li>
            <li><strong>채널별 해결률:</strong>
                <ul style="margin-left: 20px; margin-top: 5px;">
                    ${channelList || '<li>데이터 없음</li>'}
                </ul>
            </li>
        `;
    }
    
        renderInsights(insight) {
            console.log('인사이트 렌더링 시작...', insight);
            
            // 인사이트 도출 컨테이너 (grid.cols-3 안의 두 번째 카드)
            const container = document.querySelector('#report .grid.cols-3 .card:nth-child(2) .subtle');
            if (!container) return;
            
            let insightsHTML = '';
            
            const byCategory = insight.by_category || [];
            const overall = insight.overall || {};
            
            // AI 연동 실패 시 명확한 메시지 표시
            if (byCategory.length === 0 && (!overall.summary || overall.summary === '')) {
                insightsHTML = `
                    <li style="color: #e74c3c; font-weight: 600;">
                        ⚠️ AI 연동 실패
                    </li>
                    <li style="color: #666; font-size: 14px; margin-top: 8px;">
                        인사이트 분석을 위해서는 OpenAI API 연동이 필요합니다.<br/>
                        .env 파일에 <code>OPENAI_API_KEY</code>를 설정하고 서버를 재시작하세요.
                    </li>
                `;
                container.innerHTML = insightsHTML;
                return;
            }
            
            // ✨ 상단 요약 추가 (종합 인사이트를 맨 위에 표시)
            if (overall && (overall.summary || (overall.notable_issues && overall.notable_issues.length > 0))) {
                insightsHTML += `
                    <li style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                               padding: 16px; 
                               border-radius: 8px; 
                               margin-bottom: 16px;
                               color: white;
                               box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <strong style="font-size: 16px; display: block; margin-bottom: 12px; color: #fff;">📊 종합 분석 요약</strong>
                `;
                
                if (overall.summary) {
                    insightsHTML += `
                        <div style="background: rgba(255,255,255,0.15); 
                                   padding: 12px; 
                                   border-radius: 6px; 
                                   margin-bottom: 10px;
                                   line-height: 1.6;
                                   font-size: 14px;">
                            ${overall.summary}
                        </div>
                    `;
                }
                
                if (overall.notable_issues && Array.isArray(overall.notable_issues) && overall.notable_issues.length > 0) {
                    insightsHTML += `
                        <div style="background: rgba(255,255,255,0.15); 
                                   padding: 12px; 
                                   border-radius: 6px;
                                   line-height: 1.6;">
                            <strong style="display: block; margin-bottom: 8px; font-size: 14px;">⚠️ 주요 이슈</strong>
                            <ul style="margin: 0; padding-left: 20px; font-size: 14px;">
                                ${overall.notable_issues.map(issue => `<li>${issue}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }
                
                insightsHTML += '</li>';
            }
            
            // 카테고리별 인사이트 (배열 기반)
            if (byCategory.length > 0) {
                insightsHTML += '<li><strong>카테고리별 세부 인사이트:</strong><ul style="margin-left: 20px; margin-top: 5px;">';
                
                byCategory.forEach(cat => {
                    const priorityBadge = cat.priority === 'high' ? '🔴' : cat.priority === 'medium' ? '🟡' : '🟢';
                    insightsHTML += `
                        <li>
                            <strong>${cat.category_name} ${priorityBadge}</strong>
                            <ul style="margin-left: 15px; font-size: 14px;">
                                <li><strong>📊 현황 및 문제점:</strong><div style="margin-left: 10px; white-space: pre-line;">${cat.problem || '-'}</div></li>
                                <li><strong>🎯 단기 목표:</strong><div style="margin-left: 10px; white-space: pre-line;">${cat.short_term_goal || '-'}</div></li>
                                <li><strong>🚀 장기 목표:</strong><div style="margin-left: 10px; white-space: pre-line;">${cat.long_term_goal || '-'}</div></li>
                            </ul>
                        </li>
                    `;
                });
                
                insightsHTML += '</ul></li>';
            }
            
            container.innerHTML = insightsHTML;
        }
    
        renderSolutions(solution) {
            console.log('솔루션 렌더링 시작...', solution);
            
            // 솔루션 제안 컨테이너 (grid.cols-3 안의 세 번째 카드)
            const container = document.querySelector('#report .grid.cols-3 .card:nth-child(3) .subtle');
            if (!container) return;
            
            let solutionsHTML = '';
            
            const currentStatusProblems = solution.current_status_and_problems || {};
            const shortTerm = solution.short_term || {};
            const midTerm = solution.mid_term || {};
            const longTerm = solution.long_term || {};
            const effectsRisks = solution.expected_effects_and_risks || {};
            
            // AI 연동 실패 시 명확한 메시지 표시
            if (!currentStatusProblems.status && !currentStatusProblems.problems && 
                !shortTerm.goal_kpi && !midTerm.goal_kpi && !longTerm.goal_kpi) {
                solutionsHTML = `
                    <li style="color: #e74c3c; font-weight: 600;">
                        ⚠️ AI 연동 실패
                    </li>
                    <li style="color: #666; font-size: 14px; margin-top: 8px;">
                        솔루션 제안을 위해서는 OpenAI API 연동이 필요합니다.<br/>
                        .env 파일에 <code>OPENAI_API_KEY</code>를 설정하고 서버를 재시작하세요.
                    </li>
                `;
                container.innerHTML = solutionsHTML;
                return;
            }
            
            // ✨ 상단 요약 추가 (현황 및 문제점:을 강조하여 맨 위에 표시)
            if (currentStatusProblems.status || currentStatusProblems.problems) {
                solutionsHTML += `
                    <li style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                               padding: 16px; 
                               border-radius: 8px; 
                               margin-bottom: 16px;
                               color: white;
                               box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <strong style="font-size: 16px; display: block; margin-bottom: 12px; color: #fff;">🎯 핵심 현황 및 우선순위</strong>
                `;
                
                if (currentStatusProblems.status) {
                    solutionsHTML += `
                        <div style="background: rgba(255,255,255,0.15); 
                                   padding: 12px; 
                                   border-radius: 6px; 
                                   margin-bottom: 10px;
                                   line-height: 1.6;">
                            <strong style="display: block; margin-bottom: 6px; font-size: 14px;">📌 현황</strong>
                            <div style="font-size: 14px; white-space: pre-line;">${currentStatusProblems.status}</div>
                        </div>
                    `;
                }
                
                if (currentStatusProblems.problems) {
                    solutionsHTML += `
                        <div style="background: rgba(255,255,255,0.15); 
                                   padding: 12px; 
                                   border-radius: 6px;
                                   line-height: 1.6;">
                            <strong style="display: block; margin-bottom: 6px; font-size: 14px;">⚠️ 주요 문제점</strong>
                            <div style="font-size: 14px; white-space: pre-line;">${currentStatusProblems.problems}</div>
                        </div>
                    `;
                }
                
                solutionsHTML += '</li>';
            }
            
            // 단기 솔루션 (1-6개월)
            if (shortTerm.goal_kpi || shortTerm.plan || (shortTerm.actions && shortTerm.actions.length > 0)) {
                solutionsHTML += `
                    <li><strong>단기 (1-6개월)</strong>
                        <ul style="margin-left: 20px; margin-top: 5px;">
                            ${shortTerm.goal_kpi ? `<li><strong>1️⃣ 단기 목표:</strong><div style="margin-left: 10px; white-space: pre-line;">${shortTerm.goal_kpi}</div></li>` : ''}
                            ${shortTerm.plan ? `<li><strong>2️⃣ 단기 플랜:</strong><div style="margin-left: 10px; white-space: pre-line;">${shortTerm.plan}</div></li>` : ''}
                            ${shortTerm.actions && shortTerm.actions.length > 0 ? `
                                <li><strong>3️⃣ 단기 액션:</strong>
                                    <ul style="margin-left: 20px;">
                                        ${shortTerm.actions.map(action => `<li>• ${action}</li>`).join('')}
                                    </ul>
                                </li>
                            ` : ''}
                        </ul>
                    </li>
                `;
            }
            
            // 중기 솔루션 (6-12개월)
            if (midTerm.goal_kpi || midTerm.plan || (midTerm.actions && midTerm.actions.length > 0)) {
                solutionsHTML += `
                    <li><strong>중기 (6-12개월)</strong>
                        <ul style="margin-left: 20px; margin-top: 5px;">
                            ${midTerm.goal_kpi ? `<li><strong>4️⃣ 중기 목표:</strong><div style="margin-left: 10px; white-space: pre-line;">${midTerm.goal_kpi}</div></li>` : ''}
                            ${midTerm.plan ? `<li><strong>5️⃣ 중기 플랜:</strong><div style="margin-left: 10px; white-space: pre-line;">${midTerm.plan}</div></li>` : ''}
                            ${midTerm.actions && midTerm.actions.length > 0 ? `
                                <li><strong>6️⃣ 중기 액션:</strong>
                                    <ul style="margin-left: 20px;">
                                        ${midTerm.actions.map(action => `<li>• ${action}</li>`).join('')}
                                    </ul>
                                </li>
                            ` : ''}
                        </ul>
                    </li>
                `;
            }
            
            // 장기 솔루션 (12개월 이상)
            if (longTerm.goal_kpi || longTerm.plan || (longTerm.actions && longTerm.actions.length > 0)) {
                solutionsHTML += `
                    <li><strong>장기 (12개월 이상)</strong>
                        <ul style="margin-left: 20px; margin-top: 5px;">
                            ${longTerm.goal_kpi ? `<li><strong>7️⃣ 장기 목표:</strong><div style="margin-left: 10px; white-space: pre-line;">${longTerm.goal_kpi}</div></li>` : ''}
                            ${longTerm.plan ? `<li><strong>8️⃣ 장기 플랜:</strong><div style="margin-left: 10px; white-space: pre-line;">${longTerm.plan}</div></li>` : ''}
                            ${longTerm.actions && longTerm.actions.length > 0 ? `
                                <li><strong>9️⃣ 장기 액션:</strong>
                                    <ul style="margin-left: 20px;">
                                        ${longTerm.actions.map(action => `<li>• ${action}</li>`).join('')}
                                    </ul>
                                </li>
                            ` : ''}
                        </ul>
                    </li>
                `;
            }
            
            // 기대효과 및 리스크 관리
            if (effectsRisks.expected_effects || effectsRisks.risk_management) {
                solutionsHTML += `
                    <li><strong>기대효과 및 리스크 관리</strong>
                        <ul style="margin-left: 20px; margin-top: 5px;">
                            ${effectsRisks.expected_effects ? `<li><strong>기대효과:</strong> ${effectsRisks.expected_effects}</li>` : ''}
                            ${effectsRisks.risk_management ? `<li><strong>리스크 관리:</strong> ${effectsRisks.risk_management}</li>` : ''}
                        </ul>
                    </li>
                `;
            }
            
            container.innerHTML = solutionsHTML;
        }
    
    renderByTemplate(template, reportData) {
        console.log(`템플릿 렌더링: ${template}`);
        
        switch (template) {
            case 'executive':
                this.renderExecutiveReport(reportData);
                break;
            case 'detailed':
                this.renderDetailedReport(reportData);
                break;
            case 'trend':
                this.renderTrendReport(reportData);
                break;
            case 'comparison':
                this.renderComparisonReport(reportData);
                break;
            default: // 'standard'
                this.renderStandardReport(reportData);
                break;
        }
    }
    
    renderStandardReport(reportData) {
        // 표준 리포트 - 모든 섹션 표시
        this.renderChannelTrends(reportData.channel_trends);
        this.renderSummary(reportData.summary);
        this.renderInsights(reportData.insight);
        this.renderSolutions(reportData.solution);
    }
    
    renderExecutiveReport(reportData) {
        // 경영진용 요약 - 핵심 지표와 인사이트만
        this.renderChannelTrends(reportData.channel_trends);
        this.renderSummary(reportData.summary);
        this.renderInsights(reportData.insight);
        // 솔루션 섹션 숨김
        this.hideSection('solutions');
    }
    
    renderDetailedReport(reportData) {
        // 상세 분석 - 모든 섹션 + 추가 분석
        this.renderChannelTrends(reportData.channel_trends);
        this.renderSummary(reportData.summary);
        this.renderInsights(reportData.insight);
        this.renderSolutions(reportData.solution);
        // 추가 상세 분석 섹션 표시
        this.renderDetailedAnalysis(reportData);
    }
    
    renderTrendReport(reportData) {
        // 트렌드 분석 - 시계열 데이터 중심
        this.renderChannelTrends(reportData.channel_trends);
        this.renderTrendAnalysis(reportData);
        this.renderInsights(reportData.insight);
    }
    
    renderComparisonReport(reportData) {
        // 비교 분석 - 기간별/채널별 비교
        this.renderChannelTrends(reportData.channel_trends);
        this.renderSummary(reportData.summary);
        this.renderComparisonAnalysis(reportData);
        this.renderInsights(reportData.insight);
    }
    
    hideSection(sectionName) {
        const section = document.querySelector(`#${sectionName}`);
        if (section) {
            section.style.display = 'none';
        }
    }
    
    showSection(sectionName) {
        const section = document.querySelector(`#${sectionName}`);
        if (section) {
            section.style.display = 'block';
        }
    }
    
    renderDetailedAnalysis(reportData) {
        // 상세 분석 섹션 추가 (향후 구현)
        console.log('상세 분석 렌더링');
    }
    
    renderTrendAnalysis(reportData) {
        // 트렌드 분석 섹션 추가 (향후 구현)
        console.log('트렌드 분석 렌더링');
    }
    
    renderComparisonAnalysis(reportData) {
        // 비교 분석 섹션 추가 (향후 구현)
        console.log('비교 분석 렌더링');
    }

    handleTemplateChange() {
        const templateSelect = document.getElementById('template-select');
        const comparisonOptions = document.getElementById('comparison-options');
        
        if (templateSelect && comparisonOptions) {
            if (templateSelect.value === 'comparison') {
                comparisonOptions.style.display = 'flex';
            } else {
                comparisonOptions.style.display = 'none';
            }
        }
    }
    
    updateComparisonOptions() {
        const periodSelect = document.getElementById('period-select');
        const compareTypeSelect = document.getElementById('compare-type');
        
        if (periodSelect && compareTypeSelect) {
            const period = periodSelect.value;
            const compareType = compareTypeSelect.value;
            
            console.log(`비교 분석 설정: ${compareType} - ${period}`);
            
            // 비교 분석 옵션에 따른 UI 업데이트
            this.updateComparisonUI(compareType, period);
        }
    }
    
    updateComparisonUI(compareType, period) {
        // 비교 분석 UI 업데이트 (향후 구현)
        console.log(`UI 업데이트: ${compareType} 비교, ${period} 기간`);
    }

    showShareModal() {
        if (!this.currentReportId) {
            this.showMessage('먼저 리포트를 생성해주세요.', 'warning');
            return;
        }
        
        // 공유 모달 생성
        const modal = document.createElement('div');
        modal.className = 'share-modal';
        // modal.innerHTML = `
        //     <div class="share-modal-content">
        //         <div class="share-modal-header">
        //             <h3>리포트 공유</h3>
        //             <button class="share-modal-close">×</button>
        //         </div>
        //         <div class="share-modal-body">
        //             <div class="share-option">
        //                 <label>공유 링크 생성</label>
        //                 <div class="share-link-container">
        //                     <input type="text" id="share-link" readonly value="리포트 링크가 생성됩니다...">
        //                     <button id="copy-link" class="btn small">복사</button>
        //                 </div>
        //             </div>
                    
        //             <div class="share-option">
        //                 <label>이메일 공유</label>
        //                 <div class="email-share">
        //                     <input type="email" id="share-email" placeholder="이메일 주소를 입력하세요">
        //                     <button id="send-email" class="btn small">전송</button>
        //                 </div>
        //             </div>
                    
        //             <div class="share-option">
        //                 <label>공유 설정</label>
        //                 <div class="share-settings">
        //                     <label class="checkbox-label">
        //                         <input type="checkbox" id="allow-download" checked>
        //                         <span>PDF 다운로드 허용</span>
        //                     </label>
        //                     <label class="checkbox-label">
        //                         <input type="checkbox" id="allow-edit">
        //                         <span>편집 권한 부여</span>
        //                     </label>
        //                 </div>
        //             </div>
        //         </div>
        //     </div>
        // `;
        modal.innerHTML = `
            <div class="share-modal-content">
                <div class="share-modal-header">
                    <h3>리포트 공유</h3>
                    <button class="share-modal-close">×</button>
                </div>
                <div class="share-modal-body">
                    <div class="share-option">
                        <label>이메일 공유</label>
                        <div class="email-share">
                            <input type="email" id="share-email" placeholder="이메일 주소를 입력하세요">
                            <button id="send-email" class="btn small">전송</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 모달 이벤트 바인딩
        this.bindShareModalEvents(modal);
    }
    
    bindShareModalEvents(modal) {
        const closeBtn = modal.querySelector('.share-modal-close');
        const copyBtn = modal.querySelector('#copy-link');
        const sendBtn = modal.querySelector('#send-email');
        
        // 모달 닫기
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                modal.remove();
            });
        }
        
        // 배경 클릭으로 닫기
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        // 링크 복사 (있을 경우만)
        if (copyBtn) {
            copyBtn.addEventListener('click', () => {
                const linkInput = modal.querySelector('#share-link');
                if (linkInput) {
                    linkInput.select();
                    document.execCommand('copy');
                    this.showMessage('링크가 클립보드에 복사되었습니다.', 'success');
                }
            });
        }
        
        // 이메일 전송 (있을 경우만)
        if (sendBtn) {
            sendBtn.addEventListener('click', () => {
                const emailInput = modal.querySelector('#share-email');
                if (!emailInput) return;
                
                const email = emailInput.value.trim();
                if (!email) {
                    this.showMessage('이메일 주소를 입력해주세요.', 'warning');
                    return;
                }
                
                // 이메일 형식 검증
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(email)) {
                    this.showMessage('올바른 이메일 주소를 입력해주세요.', 'warning');
                    return;
                }
                
                // 리포트 공유 버튼 가져오기
                const shareReportBtn = document.querySelector('#btn-share-report');
                
                // 팝업 닫기
                modal.remove();
                
                // 리포트 공유 버튼 상태 변경 (진행 중 표시)
                if (shareReportBtn) {
                    shareReportBtn.disabled = true;
                    const originalText = shareReportBtn.textContent;
                    shareReportBtn.textContent = "전송 중...";
                    
                    this.sendEmailShare(email, shareReportBtn, originalText);
                } else {
                    // 버튼을 찾을 수 없으면 일반 전송
                    this.sendEmailShare(email);
                }
            });
        }
    }
    
    generateShareLink() {
        // 공유 링크 생성 (실제 구현에서는 서버에서 처리)
        const shareLink = `${window.location.origin}/shared/report/${this.currentReportId}`;
        const linkInput = document.querySelector('#share-link');
        if (linkInput) {
            linkInput.value = shareLink;
        }
    }
    
    sendEmailShare(email, shareReportBtn = null, originalText = null) {
        // 이메일 공유 기능 - 실제 이메일 전송 구현
        if (!this.currentReportId) {
            this.showMessage('리포트 ID가 없습니다. 먼저 리포트를 생성해주세요.', 'warning');
            // 버튼 복원
            if (shareReportBtn && originalText) {
                shareReportBtn.disabled = false;
                shareReportBtn.textContent = originalText;
            }
            return;
        }
        
        // 이메일 전송 API 호출
        fetch("/send-pdf-email", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ report_id: this.currentReportId, email: email })
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                this.showMessage(`PDF가 ${email}로 전송되었습니다.`, 'success');
            } else {
                this.showMessage(result.error || "PDF 전송에 실패했습니다.", "error");
            }
        })
        .catch(err => {
            console.error("PDF 이메일 전송 오류:", err);
            this.showMessage("PDF 전송 중 오류가 발생했습니다.", "error");
        })
        .finally(() => {
            // 리포트 공유 버튼 복원
            if (shareReportBtn && originalText) {
                shareReportBtn.disabled = false;
                shareReportBtn.textContent = originalText;
            }
        });
    }

    showTemplateSelector() {
        this.showMessage('템플릿 선택 기능이 활성화되었습니다.', 'info');
    }
    
    showLoading(show) {
        const reportSection = document.querySelector('#report');
        if (!reportSection) return;
        
        if (show) {
            reportSection.classList.add('loading');
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading-indicator';
            loadingDiv.innerHTML = '<div class="spinner"></div><p>리포트 생성 중...</p>';
            reportSection.appendChild(loadingDiv);
        } else {
            reportSection.classList.remove('loading');
            const loadingDiv = reportSection.querySelector('.loading-indicator');
            if (loadingDiv) {
                loadingDiv.remove();
            }
        }
    }
    
    showMessage(message, type = 'info') {
        // 기존 메시지 제거
        const existingMessage = document.querySelector('.message-toast');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        // 새 메시지 생성
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-toast ${type}`;
        messageDiv.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">×</button>
        `;
        
        document.body.appendChild(messageDiv);
        
        // 3초 후 자동 제거
        setTimeout(() => {
            if (messageDiv.parentElement) {
                messageDiv.remove();
            }
        }, 3000);
    }
    
    loadReportSection() {
        // 리포트 섹션이 로드될 때 초기화
        const reportSection = document.querySelector('#report');
        if (reportSection) {
            console.log('리포트 섹션 로드됨 (file_id 기반)');
        }
    }
    
    async loadLastReportData() {
        try {
            // localStorage에서 마지막 리포트 데이터 확인
            const lastReportData = localStorage.getItem('report:last_data');
            const lastReportTime = localStorage.getItem('report:last_generated_at');
            
            if (lastReportData && lastReportTime) {
                console.log('마지막 리포트 데이터 복원 중...', lastReportTime);
                
                const reportData = JSON.parse(lastReportData);
                
                // 리포트 ID와 파일 ID 저장
                this.currentReportId = reportData.report_id;
                this.currentFileId = reportData.file_id;
                
                // 각 섹션별 데이터 렌더링
                this.renderChannelTrends(reportData.channel_trends);
                this.renderSummary(reportData.summary);
                this.renderInsights(reportData.insight);
                this.renderSolutions(reportData.solution);
                
                // 성공 메시지 표시
                this.showMessage(`✅ 마지막 생성된 리포트를 불러왔습니다. (${lastReportTime})`, 'success');
                
                console.log('마지막 리포트 데이터 복원 완료');
            } else {
                console.log('저장된 리포트 데이터가 없습니다. 새로 생성하세요.');
            }
        } catch (error) {
            console.error('마지막 리포트 데이터 복원 실패:', error);
        }
    }
    
    initDragAndDrop(container) {
        /**
         * SortableJS를 사용한 드래그 앤 드롭 초기화
         * 그래프 카드들을 자유롭게 재배치할 수 있습니다
         */
        if (typeof Sortable === 'undefined') {
            console.warn('SortableJS 라이브러리가 로드되지 않았습니다.');
            return;
        }
        
        new Sortable(container, {
            animation: 200, // 애니메이션 속도 (ms)
            easing: "cubic-bezier(1, 0, 0, 1)", // 애니메이션 easing
            ghostClass: 'sortable-ghost', // 드래그 중인 위치에 표시되는 클래스
            chosenClass: 'sortable-chosen', // 선택된 아이템 클래스
            dragClass: 'sortable-drag', // 드래그 중인 아이템 클래스
            forceFallback: false, // HTML5 드래그 앤 드롭 사용
            fallbackOnBody: true,
            swapThreshold: 0.65, // 스왑 임계값
            
            // 드래그 시작
            onStart: function(evt) {
                console.log('드래그 시작:', evt.item);
            },
            
            // 드래그 종료 (순서 변경됨)
            onEnd: function(evt) {
                console.log(`그래프 순서 변경: ${evt.oldIndex} → ${evt.newIndex}`);
                
                // 순서 변경 완료 메시지 (선택사항)
                if (evt.oldIndex !== evt.newIndex) {
                    // 토스트 메시지 표시 (선택사항)
                    // showMessage('그래프 순서가 변경되었습니다.', 'info');
                }
            }
        });
        
        console.log('✅ 드래그 앤 드롭 활성화: 그래프를 드래그하여 순서를 변경할 수 있습니다.');
    }
    
    createChartModal() {
        // 모달 HTML 생성
        const modalHTML = `
            <div class="chart-modal" id="chartModal">
                <div class="chart-modal-content">
                    <div class="chart-modal-header">
                        <div>
                            <h3 class="chart-modal-title" id="modalChartTitle">채널명</h3>
                            <p class="chart-modal-subtitle" id="modalChartSubtitle">건수</p>
                        </div>
                        <button class="chart-modal-close" id="modalCloseBtn">×</button>
                    </div>
                    <div class="chart-modal-body">
                        <div class="chart-modal-canvas-wrapper">
                            <canvas id="modalChartCanvas"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // body에 모달 추가
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // 모달 이벤트 바인딩
        const modal = document.getElementById('chartModal');
        const closeBtn = document.getElementById('modalCloseBtn');
        
        // X 버튼 클릭
        closeBtn.addEventListener('click', () => this.closeChartModal());
        
        // 배경 클릭 (모달 외부 클릭)
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeChartModal();
            }
        });
        
        // ESC 키 누르기
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('active')) {
                this.closeChartModal();
            }
        });
    }
    
    openChartModal(channel, trendData) {
        const modal = document.getElementById('chartModal');
        const titleEl = document.getElementById('modalChartTitle');
        const subtitleEl = document.getElementById('modalChartSubtitle');
        
        // 모달 열기
        modal.classList.add('active');
        
        // 제목 설정
        titleEl.textContent = channel;
        
        // 전체 건수 계산
        const dataMatrix = trendData.data || [];
        const totalCount = dataMatrix.reduce((sum, row) => 
            sum + row.reduce((a, b) => a + (b || 0), 0), 0
        );
        subtitleEl.textContent = `총 ${totalCount.toLocaleString()}건`;
        
        // 기존 차트 제거
        if (this.modalChartInstance) {
            this.modalChartInstance.destroy();
        }
        
        // 차트 생성
        const canvas = document.getElementById('modalChartCanvas');
        const ctx = canvas.getContext('2d');
        
        const categories = trendData.categories || [];
        const dates = trendData.dates || [];
        const datasets = [];
        const categoryColors = this.getCategoryColors();
        
        // 전체 합계 꺾은선 그래프
        const totalData = dataMatrix.map(row => 
            row.reduce((sum, val) => sum + (val || 0), 0)
        );
        
        datasets.push({
            type: 'line',
            label: '전체 합계',
            data: totalData,
            borderColor: '#e74c3c',
            backgroundColor: 'rgba(231, 76, 60, 0.1)',
            borderWidth: 3,
            fill: false,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: '#e74c3c',
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            yAxisID: 'y',
            order: 1
        });
        
        // 카테고리별 스택 막대그래프
        categories.forEach((category, catIdx) => {
            const categoryData = dataMatrix.map(row => row[catIdx] || 0);
            
            datasets.push({
                type: 'bar',
                label: category,
                data: categoryData,
                backgroundColor: categoryColors[category] || this.getRandomColor(catIdx),
                borderColor: categoryColors[category] || this.getRandomColor(catIdx),
                borderWidth: 1,
                stack: 'stack1',
                order: 2
            });
        });
        
        // Chart.js 설정
        const config = {
            type: 'bar',
            data: {
                labels: dates,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    title: {
                        display: false
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: {
                                size: 13
                            },
                            boxWidth: 15,
                            boxHeight: 15
                        }
                    },
                    tooltip: {
                        callbacks: {
                            footer: (tooltipItems) => {
                                let sum = 0;
                                tooltipItems.forEach(item => {
                                    if (item.dataset.type === 'bar') {
                                        sum += item.parsed.y;
                                    }
                                });
                                return '합계: ' + sum + '건';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        title: {
                            display: true,
                            text: '날짜',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            font: {
                                size: 12
                            },
                            maxRotation: 45,
                            minRotation: 0
                        }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'CS 건수',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        };
        
        this.modalChartInstance = new Chart(ctx, config);
    }
    
    closeChartModal() {
        const modal = document.getElementById('chartModal');
        modal.classList.remove('active');
        
        // 차트 인스턴스 제거
        if (this.modalChartInstance) {
            this.modalChartInstance.destroy();
            this.modalChartInstance = null;
        }
    }
}

// 페이지 로드 시 ReportManager 초기화
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.reportManager === 'undefined') {
        window.reportManager = new ReportManager();
    }
});

// 페이지 로드 시 자동으로 섹션 표시
document.addEventListener('DOMContentLoaded', function() {
    const reportSection = document.querySelector('#report');
    if (reportSection) {
        console.log('리포트 페이지가 로드되었습니다.');
    }
});
