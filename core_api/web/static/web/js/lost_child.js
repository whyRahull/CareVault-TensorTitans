/* 
 * lost_child.js
 * Handles Biometric Match Modal and Live Camera Streaming for the Lost Child Dashboard.
 */

/* ------------------------------------------------------------------ */
/* Biometric Search Modal                                             */
/* ------------------------------------------------------------------ */
let currentPersonId = null;

function openSearchModal(id, name) {
    currentPersonId = id;
    document.getElementById('search-person-id').value = id;
    document.getElementById('modal-person-name').innerText = name;
    document.getElementById('search-modal').classList.remove('hidden');
    document.getElementById('search-modal').classList.add('flex');
    document.getElementById('search-results').classList.add('hidden');
    const fileLabel = document.getElementById('file-label');
    if (fileLabel) fileLabel.innerText = 'Select capture for matching';
}

function closeSearchModal() {
    document.getElementById('search-modal').classList.add('hidden');
    document.getElementById('search-modal').classList.remove('flex');
}

document.addEventListener('DOMContentLoaded', function () {
    const searchForm = document.getElementById('search-form');
    if (!searchForm) return;

    const searchImage = document.getElementById('search-image');
    const fileLabel = document.getElementById('file-label');
    const resultsDiv = document.getElementById('search-results');
    const badge = document.getElementById('search-badge');
    const msg = document.getElementById('search-msg');
    const thumb = document.getElementById('search-thumb');

    searchImage.addEventListener('change', e => {
        if (e.target.files.length) fileLabel.innerText = e.target.files[0].name;
    });

    searchForm.addEventListener('submit', async e => {
        e.preventDefault();
        const file = searchImage.files[0];
        const personId = document.getElementById('search-person-id').value;
        if (!file) return;

        const btn = searchForm.querySelector('button');
        const originalText = btn.innerText;
        btn.disabled = true;
        btn.innerText = 'CALIBRATING & MATCHING...';

        const formData = new FormData();
        formData.append('file', file);
        formData.append('person_id', personId);

        try {
            // Note: window.API_LOST_CHILD_SEARCH must be defined in the HTML template's head
            const resp = await fetch(window.API_LOST_CHILD_SEARCH, {
                method: 'POST',
                headers: { 'X-CSRFToken': window.CSRF_TOKEN },
                body: formData
            });
            const data = await resp.json();

            resultsDiv.classList.remove('hidden');
            if (data.matched) {
                badge.className = 'px-3 py-1 rounded-full text-[10px] font-black uppercase mb-4 inline-block bg-green-100 text-green-700';
                badge.innerText = `Matched (${data.confidence})`;
            } else {
                badge.className = 'px-3 py-1 rounded-full text-[10px] font-black uppercase mb-4 inline-block bg-red-100 text-red-700';
                badge.innerText = `No Match (${data.confidence})`;
            }
            msg.innerText = data.message;
            if (data.annotated_image_b64) {
                thumb.classList.remove('hidden');
                thumb.querySelector('img').src = `data:image/jpeg;base64,${data.annotated_image_b64}`;
            } else {
                thumb.classList.add('hidden');
            }
        } catch (err) {
            alert('Search failed: ' + err.message);
        } finally {
            btn.disabled = false;
            btn.innerText = originalText;
        }
    });
});


/* ------------------------------------------------------------------ */
/* Live Camera Biometric Scan                                         */
/* ------------------------------------------------------------------ */
let lcWs = null;
let lcInterval = null;
let lcMatchTimeout = null;

function startLCCamera() {
    const video = document.getElementById('lc-video');
    const placeholder = document.getElementById('lc-placeholder');
    const status = document.getElementById('lc-status');
    const fpsEl = document.getElementById('lc-fps');

    navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false })
        .then(stream => {
            video.srcObject = stream;
            video.onloadedmetadata = () => {
                video.play();
                video.classList.remove('hidden');
                placeholder.classList.add('hidden');
                status.innerText = 'ONLINE';
                status.className = 'bg-green-500 text-white text-[9px] px-2 py-0.5 rounded font-black uppercase tracking-widest';
                fpsEl.classList.remove('hidden');
                initLCWebSocket();
            };
        })
        .catch(err => alert("Camera error: " + err.message));
}

function initLCWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    lcWs = new WebSocket(`${protocol}//${window.location.host}/ws/ml/stream/hand_sos/`);

    lcWs.onopen = () => {
        const video = document.getElementById('lc-video');
        const canvas = document.getElementById('lc-canvas');
        const context = canvas.getContext('2d');
        canvas.width = 640;
        canvas.height = 480;

        lcInterval = setInterval(() => {
            if (lcWs.readyState !== WebSocket.OPEN) {
                clearInterval(lcInterval);
                return;
            }

            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            const base64 = canvas.toDataURL('image/jpeg', 0.6).split(',')[1];
            const personId = document.getElementById('person-selector').value;

            const payload = { type: 'lost_child', frame_b64: base64 };
            if (personId) payload.person_id = parseInt(personId);

            lcWs.send(JSON.stringify(payload));
        }, 500); // 2 FPS
    };

    lcWs.onmessage = (e) => {
        const data = JSON.parse(e.data);
        const result = data.result;

        const matchOverlay = document.getElementById('lc-match-overlay');
        const annotatedImg = document.getElementById('lc-annotated');
        const video = document.getElementById('lc-video');
        const fpsEl = document.getElementById('lc-fps');
        const infoBar = document.getElementById('lc-info-bar');
        const infoBadge = document.getElementById('lc-info-badge');

        // Show annotated frame with face rectangles
        if (result.annotated_image_b64) {
            annotatedImg.src = `data:image/jpeg;base64,${result.annotated_image_b64}`;
            annotatedImg.classList.remove('hidden');
            video.classList.add('opacity-0');
        }

        fpsEl.innerText = `FPS: 2.0`;

        if (result.matched) {
            // Match found — show big green overlay
            matchOverlay.classList.remove('hidden');
            infoBar.classList.remove('hidden');
            infoBadge.className = 'bg-green-600/80 backdrop-blur-md text-white text-xs font-bold px-4 py-2 rounded-lg border border-green-400 inline-block';
            infoBadge.innerText = `MATCH FOUND — Confidence: ${result.confidence || 'N/A'}`;

            if (lcMatchTimeout) clearTimeout(lcMatchTimeout);
            lcMatchTimeout = setTimeout(() => {
                matchOverlay.classList.add('hidden');
            }, 5000);
        } else if (result.status === 'no_faces') {
            infoBar.classList.add('hidden');
            matchOverlay.classList.add('hidden');
        } else {
            // Faces detected but no match (or no person_id selected)
            matchOverlay.classList.add('hidden');
            infoBar.classList.remove('hidden');
            infoBadge.className = 'bg-black/60 backdrop-blur-md text-white text-xs font-bold px-4 py-2 rounded-lg border border-white/10 inline-block';
            infoBadge.innerText = result.message || 'Scanning...';
        }
    };
}
