document.addEventListener("DOMContentLoaded", function() {
    const sendEmailButton = document.getElementById("btn-send-email");

    if (sendEmailButton) {
        // 이메일 전송 버튼 클릭 시 팝업 모달 열기
        sendEmailButton.addEventListener("click", function() {
            // reportManager의 모달 열기 함수 사용
            if (window.reportManager) {
                window.reportManager.showEmailModal();
            } else {
                // reportManager가 없으면 직접 모달 생성
                showEmailModal();
            }
        });
    }
});

// 이메일 전송 모달 표시 함수
function showEmailModal() {
    let reportId = window.reportManager?.currentReportId;

    // 리포트 ID 확인
    if (!reportId) {
        // 리포트 ID를 가져오는 함수를 비동기로 처리
        fetchReportId().then(id => {
            if (id) {
                createEmailModal(id);
            }
        });
    } else {
        createEmailModal(reportId);
    }
}

// 리포트 ID 가져오기
async function fetchReportId() {
    try {
        const response = await fetch('/api/report/latest', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            const result = await response.json();
            if (result.success && result.data && result.data.report_id) {
                return result.data.report_id;
            } else {
                showMessage('생성된 리포트가 없습니다. 먼저 리포트를 생성해주세요.', 'warning');
                return null;
            }
        } else {
            showMessage('리포트를 찾을 수 없습니다. 먼저 리포트를 생성해주세요.', 'warning');
            return null;
        }
    } catch (err) {
        console.error('마지막 리포트 조회 실패:', err);
        showMessage('리포트를 찾을 수 없습니다. 먼저 리포트를 생성해주세요.', 'warning');
        return null;
    }
}

// 이메일 전송 모달 생성
function createEmailModal(reportId) {
    // 기존 모달 제거
    const existingModal = document.querySelector('.email-modal');
    if (existingModal) {
        existingModal.remove();
    }

    // 모달 생성
    const modal = document.createElement('div');
    modal.className = 'share-modal email-modal';
    modal.innerHTML = `
        <div class="share-modal-content">
            <div class="share-modal-header">
                <h3>이메일로 받기</h3>
                <button class="share-modal-close">×</button>
            </div>
            <div class="share-modal-body">
                <div class="share-option">
                    <label>이메일 주소 입력</label>
                    <div class="email-share">
                        <input type="email" id="email-input" placeholder="리포트(PDF)를 전송할 이메일 주소를 입력해주세요">
                        <button id="send-email-btn" class="btn small">전송</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 모달 이벤트 바인딩
    const closeBtn = modal.querySelector('.share-modal-close');
    const sendBtn = modal.querySelector('#send-email-btn');
    const emailInput = modal.querySelector('#email-input');
    
    // 모달 닫기
    closeBtn.addEventListener('click', () => {
        modal.remove();
    });
    
    // 배경 클릭으로 닫기
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    // 이메일 전송
    sendBtn.addEventListener('click', async () => {
        const emailTo = emailInput.value.trim();
        if (!emailTo) {
            showMessage('이메일 주소를 입력해주세요.', 'warning');
            return;
        }
        
        // 이메일 형식 검증
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(emailTo)) {
            showMessage('올바른 이메일 주소를 입력해주세요.', 'warning');
            return;
        }
        
        sendBtn.disabled = true;
        const originalText = sendBtn.textContent;
        sendBtn.textContent = "전송 중...";
        
        try {
            // 서버로 POST 요청
            const response = await fetch("/send-pdf-email", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ report_id: reportId, email: emailTo })
            });
            
            const result = await response.json();
            if (response.ok && result.success) {
                showMessage(`PDF가 ${emailTo}로 전송되었습니다.`, "success");
                modal.remove(); // 성공 시 모달 닫기
            } else {
                showMessage(result.error || "PDF 전송에 실패했습니다.", "error");
            }
        } catch (err) {
            console.error("PDF 이메일 전송 오류:", err);
            showMessage("PDF 전송 중 오류가 발생했습니다.", "error");
        } finally {
            sendBtn.disabled = false;
            sendBtn.textContent = originalText;
        }
    });
    
    // Enter 키로 전송
    emailInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendBtn.click();
        }
    });
    
    // 입력 필드에 포커스
    setTimeout(() => {
        emailInput.focus();
    }, 100);
}

// 기존 alert 방식 (주석처리)
/*
document.addEventListener("DOMContentLoaded", function() {
    const sendEmailButton = document.getElementById("btn-send-email");

    if (sendEmailButton) {
        sendEmailButton.addEventListener("click", async function() {
            let reportId = window.reportManager?.currentReportId;

            // 1. 리포트가 없으면 서버에서 마지막 리포트 조회
            if (!reportId) {
                try {
                    const response = await fetch('/api/report/latest', {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    if (response.ok) {
                        const result = await response.json();
                        if (result.success && result.data && result.data.report_id) {
                            reportId = result.data.report_id;
                            console.log(`마지막 리포트 사용: report_id=${reportId}`);
                        } else {
                            alert('생성된 리포트가 없습니다. 먼저 리포트를 생성해주세요.');
                            return;
                        }
                    } else {
                        alert('리포트를 찾을 수 없습니다. 먼저 리포트를 생성해주세요.');
                        return;
                    }
                } catch (err) {
                    console.error('마지막 리포트 조회 실패:', err);
                    alert('리포트를 찾을 수 없습니다. 먼저 리포트를 생성해주세요.');
                    return;
                }
            }

            // 2. 이메일 입력
            const emailTo = prompt("📤️ 리포트(PDF)를 전송할 이메일 주소를 입력해주세요 :");
            if (!emailTo) return;

            sendEmailButton.disabled = true;
            const originalText = sendEmailButton.textContent;
            sendEmailButton.textContent = "전송 중...";

            try {
                // 3. 서버로 POST 요청
                const response = await fetch("/send-pdf-email", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ report_id: reportId, email: emailTo })
                });

                const result = await response.json();
                if (response.ok && result.success) {
                    showMessage(`PDF가 ${emailTo}로 전송되었습니다.`, "success");
                } else {
                    showMessage(result.error || "PDF 전송에 실패했습니다.", "error");
                }
            } catch (err) {
                console.error("PDF 이메일 전송 오류:", err);
                showMessage("PDF 전송 중 오류가 발생했습니다.", "error");
            } finally {
                sendEmailButton.disabled = false;
                sendEmailButton.textContent = originalText;
            }
        });
    }
});
*/

// 메시지 표시(pdf_export.js와 동일)
function showMessage(message, type = 'info') {
    const existingMessage = document.querySelector('.message-toast');
    if (existingMessage) existingMessage.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message-toast ${type}`;
    messageDiv.innerHTML = `<span>${message}</span><button onclick="this.parentElement.remove()">×</button>`;
    document.body.appendChild(messageDiv);

    setTimeout(() => {
        if (messageDiv.parentElement) messageDiv.remove();
    }, 3000);
}