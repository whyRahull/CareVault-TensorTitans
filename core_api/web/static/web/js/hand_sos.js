/*
 * hand_sos.js
 * Handles local camera streaming and image upload for the Hand SOS Dashboard.
 */

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('image-upload-form');
    const fileInput = document.getElementById('image-file');
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
            const originalText = btn.innerText;
            btn.disabled = true;
            btn.innerText = 'PROCESSING...';

            const formData = new FormData();
            formData.append('file', file);

            try {
                const resp = await fetch(window.API_HAND_SOS_DETECT, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': window.CSRF_TOKEN },
                    body: formData
                });
                const data = await resp.json();

                resultsDiv.classList.remove('hidden');
                if (data.sos_detected) {
                    resultBadge.className = 'px-2 py-0.5 rounded-[4px] text-[9px] font-black uppercase mb-2 inline-block bg-red-600 text-white';
                    resultBadge.innerText = 'SOS DETECTED';
                } else {
                    resultBadge.className = 'px-2 py-0.5 rounded-[4px] text-[9px] font-black uppercase mb-2 inline-block bg-amber-100 text-amber-700';
                    resultBadge.innerText = 'NORMAL GESTURE';
                }
                resultMsg.innerText = `Detected: ${data.gesture.toUpperCase()} (${data.hands_found} hand(s))`;
                if (data.annotated_image_b64) {
                    resultThumb.classList.remove('hidden');
                    resultThumb.querySelector('img').src = `data:image/jpeg;base64,${data.annotated_image_b64}`;
                } else {
                    resultThumb.classList.add('hidden');
                }
            } catch (err) {
                alert('Analysis failed: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerText = originalText;
            }
        });
    }

    const video = document.getElementById('local-video');
    const canvas = document.getElementById('stream-canvas');
    const placeholder = document.getElementById('connection-placeholder');
    const fpsDisplay = document.getElementById('fps-display');
    const sosOverlay = document.getElementById('sos-alert-overlay');

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
        const ws = new WebSocket(`${protocol}//${window.location.host}/ws/ml/stream/hand_sos/`);

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

            if (result.sos_detected) {
                if (sosOverlay) sosOverlay.classList.remove('hidden');
            } else {
                if (sosOverlay) sosOverlay.classList.add('hidden');
            }

            if (result.annotated_image_b64) {
                const annotatedFeed = document.getElementById('annotated-feed');
                if (annotatedFeed) {
                    annotatedFeed.src = `data:image/jpeg;base64,${result.annotated_image_b64}`;
                    annotatedFeed.classList.remove('hidden');
                    video.classList.add('opacity-0'); // Hide raw video to show annotation
                }
            }

            if (fpsDisplay) fpsDisplay.innerText = `FPS: ${result.fps || '2.5'}`;
        };
    }
});
