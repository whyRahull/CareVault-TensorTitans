/*
 * vigilance.js
 * Handles multi-camera WebSocket streaming for Vigilance Dashboard.
 */

let streams = {};

function initWebSocket(camId) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/ml/stream/local_cam_${camId}/`);

    ws.onopen = () => {
        console.log(`WS Connected for Cam ${camId}`);
        startStreaming(camId, ws);
    };

    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        handleDetection(camId, data);
    };

    streams[camId] = ws;
}

function startStreaming(camId, ws) {
    const video = document.getElementById(`video-${camId}`);
    const canvas = document.getElementById(`canvas-${camId}`);
    const context = canvas.getContext('2d');

    canvas.width = 640;
    canvas.height = 480;

    const interval = setInterval(() => {
        if (ws.readyState !== WebSocket.OPEN) {
            clearInterval(interval);
            return;
        }

        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.6);
        const base64 = dataUrl.split(',')[1];

        // Send for multiple detections sequentially
        ws.send(JSON.stringify({
            type: 'violence',
            frame_b64: base64
        }));

        // Also send for Hand SOS detection
        ws.send(JSON.stringify({
            type: 'hand_sos',
            frame_b64: base64
        }));

        // Also send for Lost Child face detection
        ws.send(JSON.stringify({
            type: 'lost_child',
            frame_b64: base64
        }));

    }, 500); // 2 FPS to reduce overhead
}

function handleDetection(camId, data) {
    const border = document.getElementById(`border-${camId}`);
    const resultDiv = document.getElementById(`result-${camId}`);
    const badge = document.getElementById(`badge-${camId}`);
    const video = document.getElementById(`video-${camId}`);
    const annotatedImg = document.getElementById(`annotated-${camId}`);

    const res = data.result;
    const isThreat = (data.model === 'violence' && res.suspicious_detected) ||
        (data.model === 'hand_sos' && res.sos_detected) ||
        (data.model === 'lost_child' && res.matched);

    // Update annotated frame if available
    const b64 = res.thumbnail_b64 || res.annotated_image_b64;
    if (b64) {
        annotatedImg.src = `data:image/jpeg;base64,${b64}`;
        annotatedImg.classList.remove('hidden');
        video.classList.add('opacity-0');
    }

    if (isThreat) {
        border.style.borderColor = 'rgba(220, 38, 38, 0.8)'; // Red-600
        resultDiv.classList.remove('hidden', 'translate-y-2', 'opacity-0');
        badge.innerText = data.model === 'violence' ? 'VIOLENCE ALERT' : data.model === 'hand_sos' ? 'SOS SIGNAL' : 'FACE MATCH';

        // Flash effect
        border.classList.add('animate-pulse');

        // Auto-hide threat badge after 3 seconds of no threat
        if (streams[camId].timeout) clearTimeout(streams[camId].timeout);
        streams[camId].timeout = setTimeout(() => {
            border.style.borderColor = 'transparent';
            border.classList.remove('animate-pulse');
            resultDiv.classList.add('translate-y-2', 'opacity-0');
        }, 3000);
    }
}
