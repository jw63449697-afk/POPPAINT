/**
 * Touch Event Handler for Mobile Drawing
 * 이 파일은 모바일 기기에서 터치로 그림을 그릴 수 있도록 합니다.
 * 기존 마우스 이벤트 처리와 호환됩니다.
 */

(function() {
    'use strict';

    // 캔버스와 컨텍스트 가져오기
    const canvas = document.getElementById('paintCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let isDrawing = false;

    /**
     * 터치/마우스 위치를 정규화된 캔버스 좌표로 변환
     */
    function getPosition(event) {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;

        let clientX, clientY;

        if (event.touches) {
            // 터치 이벤트
            clientX = event.touches[0].clientX;
            clientY = event.touches[0].clientY;
        } else {
            // 마우스 이벤트
            clientX = event.clientX;
            clientY = event.clientY;
        }

        return {
            x: (clientX - rect.left) * scaleX,
            y: (clientY - rect.top) * scaleY
        };
    }

    /**
     * 그리기 시작 (터치 또는 마우스)
     */
    function startDrawing(event) {
        // 메타 터치는 무시 (다중 터치 제외)
        if (event.touches && event.touches.length > 1) return;

        isDrawing = true;
        event.preventDefault();

        const position = getPosition(event);
        ctx.beginPath();
        ctx.moveTo(position.x, position.y);
    }

    /**
     * 그리기 진행 (터치 또는 마우스)
     */
    function draw(event) {
        if (!isDrawing) return;
        if (event.touches && event.touches.length > 1) return;

        event.preventDefault();

        const position = getPosition(event);
        ctx.lineTo(position.x, position.y);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(position.x, position.y);
    }

    /**
     * 그리기 종료
     */
    function stopDrawing(event) {
        if (!isDrawing) return;

        isDrawing = false;
        ctx.beginPath();
        event.preventDefault();
    }

    // ============================================
    // 터치 이벤트 리스너 등록
    // ============================================

    canvas.addEventListener('touchstart', startDrawing, { passive: false });
    canvas.addEventListener('touchmove', draw, { passive: false });
    canvas.addEventListener('touchend', stopDrawing, { passive: false });
    canvas.addEventListener('touchcancel', stopDrawing, { passive: false });

    // ============================================
    // 마우스 이벤트도 계속 지원 (기존 코드와 호환)
    // ============================================

    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseleave', stopDrawing);

    // ============================================
    // 모바일 최적화: 더블탭 줌 비활성화
    // ============================================

    document.addEventListener('touchmove', function(event) {
        if (event.target === canvas) {
            event.preventDefault();
        }
    }, { passive: false });

    console.log('📱 Touch drawing support enabled');
})();
