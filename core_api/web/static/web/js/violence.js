/*
 * violence.js
 * Handles local camera streaming and video upload for the Violence Dashboard.
 */

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('video-upload-form');
    const fileInput = document.getElementById('video-file');
    const fileName = document.getElementById('file-name');
    const resultsDiv = document.getElementById('analysis-results');
    const resultBadge = document.getElementById('result-badge');
    const resultMsg = document.getElementById('result-msg');
    const resultThumb = document.getElementById('result-thumb');

    if (fileInput) {
        fileInput.addEventListener('change', e => {
            if (e.target.files.length) fileName.innerText = e.target.files[0].name.toUpperCase();
        });
    }

    if (form) {
        form.addEventListener('submit', async e => {
            e.preventDefault();
            const file = fileInput.files[0];
            if (!file) return;

            const btn = form.querySelector('button');
            const originalHtml = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = `<svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> ANALYSING...`;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const resp = await fetch(window.API_VIOLENCE_DETECT, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': window.CSRF_TOKEN },
                    body: formData
                });
                const data = await resp.json();

                resultsDiv.classList.remove('hidden');
                if (data.suspicious_detected) {
                    resultBadge.className = 'px-2 py-1 rounded text-[10px] font-black uppercase mb-3 inline-block bg-red-500 text-white';
                    resultBadge.innerText = 'CRITICAL ALERT';
                } else {
                    resultBadge.className = 'px-2 py-1 rounded text-[10px] font-black uppercase mb-3 inline-block bg-green-500 text-white';
                    resultBadge.innerText = 'NO THREAT';
                }
                resultMsg.innerText = data.message;
                if (data.thumbnail_b64) {
                    resultThumb.classList.remove('hidden');
                    resultThumb.querySelector('img').src = `data:image/jpeg;base64,${data.thumbnail_b64}`;
                } else {
                    resultThumb.classList.add('hidden');
                }
            } catch (err) {
                alert('Analysis failed: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        });
    }

    const video = document.getElementById('local-video');
    const canvas = document.getElementById('stream-canvas');
    const placeholder = document.getElementById('connection-placeholder');
    const fpsDisplay = document.getElementById('fps-display');
    const alertStatus = document.getElementById('alert-status');

    window.startLocalStream = function () {
        navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false })
            .then(stream => {
                video.srcObject = stream;
                video.onloadedmetadata = () => {
                    video.play();
                    video.classList.remove('hidden');
                    if (placeholder) placeholder.classList.add('hidden');
                    initStreamWebSocket();
                };
            })
            .catch(err => alert("Camera error: " + err.message));
    };

    function initStreamWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${protocol}//${window.location.host}/ws/ml/stream/violence/`);

        ws.onopen = () => {
            const context = canvas.getContext('2d');
            canvas.width = 640;
            canvas.height = 480;

            setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    context.drawImage(video, 0, 0, canvas.width, canvas.height);
                    const base64 = canvas.toDataURL('image/jpeg', 0.6).split(',')[1];
                    ws.send(JSON.stringify({ frame_b64: base64 }));
                }
            }, 400); // ~2.5 FPS
        };

        ws.onmessage = (e) => {
            const data = JSON.parse(e.data);
            const result = data.result;

            if (result.suspicious_detected) {
                if (alertStatus) alertStatus.classList.remove('hidden');
                const pnl = document.querySelector('.lg\\:col-span-2');
                if (pnl) pnl.classList.add('border-red-600', 'animate-pulse');
            } else {
                if (alertStatus) alertStatus.classList.add('hidden');
                const pnl = document.querySelector('.lg\\:col-span-2');
                if (pnl) pnl.classList.remove('border-red-600', 'animate-pulse');
            }

            if (result.thumbnail_b64) {
                const annotatedFeed = document.getElementById('annotated-feed');
                if (annotatedFeed) {
                    annotatedFeed.src = `data:image/jpeg;base64,${result.thumbnail_b64}`;
                    annotatedFeed.classList.remove('hidden');
                    video.classList.add('opacity-0'); // Hide raw video to show annotation
                }
            }

            if (fpsDisplay) fpsDisplay.innerText = `FPS: ${result.fps ? result.fps.toFixed(1) : '2.5'}`;
        };
    }
});
