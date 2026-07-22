/**
 * ProctorController — Frontend proctoring module
 *
 * Webcam + microphone monitoring, periodic CV frame upload,
 * tab/focus detection, noise detection, and multi-display detection.
 */

class ProctorController {
    constructor(config) {
        this.attemptId = config.attemptId;
        this.frameIntervalMs = config.frameIntervalMs || 2000;
        this.debounceChecks = config.debounceChecks || 2;
        this.maxWarnings = config.maxWarnings || 3;
        this.timeLimitMins = config.timeLimitMins || 30;

        this.noiseThreshold = config.noiseThreshold ?? 0.38;
        this.noiseDebounceChecks = config.noiseDebounceChecks || 3;
        this.noiseSampleMs = config.noiseSampleMs || 500;
        this.displayCheckMs = config.displayCheckMs || 3000;
        this.displayDebounceChecks = config.displayDebounceChecks || 2;
        this.violationCooldownMs = config.violationCooldownMs || 15000;

        this.video = null;
        this.canvas = null;
        this.frameTimer = null;
        this.countdownTimer = null;
        this.noiseTimer = null;
        this.displayTimer = null;
        this.timeRemainingSec = this.timeLimitMins * 60;

        this.consecutiveFaceFlags = 0;
        this.consecutiveNoiseFlags = 0;
        this.consecutiveDisplayFlags = 0;
        this.lastFlagStatus = 'OK';
        this.isRunning = false;
        this.isSubmitting = false;

        this.audioContext = null;
        this.analyser = null;
        this.noiseBaseline = null;
        this.noiseSamples = 0;
        this.displayScreenCount = 1;
        this.lastViolationAt = {};

        this.onViolation = () => {};
        this.onIntegrityUpdate = () => {};
        this.onFaceStatus = () => {};
        this.onNoiseStatus = () => {};
        this.onDisplayStatus = () => {};
        this.onProcessedFrame = () => {};
        this.onDisqualified = () => {};
        this.onTimeUp = () => {};
    }

    async init() {
        this.video = document.getElementById('webcam');
        this.canvas = document.getElementById('capture-canvas');

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480, facingMode: 'user' },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: false,
                    autoGainControl: false,
                },
            });
            this.video.srcObject = stream;
            await this.video.play();
            this._initAudioMonitor(stream);
        } catch (err) {
            console.error('Media access failed:', err);
            this.onFaceStatus('Camera/Mic Error');
            return;
        }

        this._bindVisibilityListeners();
        this._startFrameLoop();
        this._startDisplayMonitor();
        this._startCountdown();
        this.isRunning = true;

        await this._checkDisplays(true);
    }

    captureFrame(quality = 0.7) {
        if (!this.video || !this.canvas) return '';
        const ctx = this.canvas.getContext('2d');
        this.canvas.width = this.video.videoWidth || 640;
        this.canvas.height = this.video.videoHeight || 480;
        ctx.drawImage(this.video, 0, 0);
        return this.canvas.toDataURL('image/jpeg', quality);
    }

    _initAudioMonitor(stream) {
        const audioTracks = stream.getAudioTracks();
        if (!audioTracks.length) {
            this.onNoiseStatus('Mic unavailable');
            return;
        }

        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = this.audioContext.createMediaStreamSource(stream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 512;
            this.analyser.smoothingTimeConstant = 0.4;
            source.connect(this.analyser);

            this.noiseTimer = setInterval(() => this._sampleNoise(), this.noiseSampleMs);
        } catch (err) {
            console.error('Audio monitor failed:', err);
            this.onNoiseStatus('Audio error');
        }
    }

    _sampleNoise() {
        if (!this.isRunning || !this.analyser) return;

        const buffer = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(buffer);

        let sum = 0;
        for (let i = 0; i < buffer.length; i += 1) sum += buffer[i];
        const level = sum / buffer.length / 255;

        if (this.noiseSamples < 6) {
            this.noiseBaseline = this.noiseBaseline == null
                ? level
                : (this.noiseBaseline * this.noiseSamples + level) / (this.noiseSamples + 1);
            this.noiseSamples += 1;
            this.onNoiseStatus('Calibrating…');
            return;
        }

        const adjusted = Math.max(0, level - (this.noiseBaseline * 0.6));
        const isLoud = adjusted >= this.noiseThreshold;

        this.onNoiseStatus(isLoud ? 'High noise' : 'Quiet');

        if (isLoud) {
            this.consecutiveNoiseFlags += 1;
        } else {
            this.consecutiveNoiseFlags = 0;
        }

        if (this.consecutiveNoiseFlags >= this.noiseDebounceChecks) {
            this.consecutiveNoiseFlags = 0;
            this._logFrontendViolation(
                'NOISE_DETECTED',
                `Excessive background noise detected (level ${Math.round(adjusted * 100)}%)`,
            );
        }
    }

    _startFrameLoop() {
        this.frameTimer = setInterval(() => this._analyzeFrame(), this.frameIntervalMs);
    }

    _startDisplayMonitor() {
        this.displayTimer = setInterval(() => this._checkDisplays(false), this.displayCheckMs);
        window.addEventListener('resize', () => this._checkDisplays(false));
    }

    async _checkDisplays(isInitial) {
        if (!this.isRunning && !isInitial) return;

        let screenCount = 1;
        let extended = Boolean(window.screen.isExtended);
        let details = '';

        if (typeof window.getScreenDetails === 'function') {
            try {
                const screenDetails = await window.getScreenDetails();
                screenCount = screenDetails.screens.length;
                extended = screenCount > 1;
                details = screenDetails.screens
                    .map((s, i) => `Display ${i + 1}: ${s.width}x${s.height}`)
                    .join('; ');
            } catch (err) {
                details = 'Window-management permission not granted';
            }
        }

        const primary = window.screen;
        const left = window.screenX ?? window.screenLeft ?? 0;
        const top = window.screenY ?? window.screenTop ?? 0;
        const right = left + window.outerWidth;
        const bottom = top + window.outerHeight;
        const primaryRight = (primary.availLeft || 0) + primary.availWidth;
        const primaryBottom = (primary.availTop || 0) + primary.availHeight;

        const outsidePrimary = left < (primary.availLeft || 0) - 2
            || top < (primary.availTop || 0) - 2
            || right > primaryRight + 2
            || bottom > primaryBottom + 2;

        this.displayScreenCount = Math.max(screenCount, extended ? 2 : 1);
        const suspicious = extended || screenCount > 1 || outsidePrimary;

        if (suspicious) {
            this.onDisplayStatus(`${this.displayScreenCount} display(s) detected`);
            this.consecutiveDisplayFlags += 1;

            if (this.consecutiveDisplayFlags >= this.displayDebounceChecks) {
                this.consecutiveDisplayFlags = 0;
                const msg = screenCount > 1
                    ? `Multiple displays detected (${screenCount} screens — HDMI/external monitor)`
                    : 'Extended display setup detected (window spans or secondary monitor)';
                this._logFrontendViolation('MULTIPLE_DISPLAY', details ? `${msg}. ${details}` : msg);
            }
        } else {
            this.consecutiveDisplayFlags = 0;
            this.onDisplayStatus('Single display');
        }
    }

    async _analyzeFrame() {
        if (!this.isRunning || this.isSubmitting) return;

        const frame = this.captureFrame();
        if (!frame) return;

        try {
            const resp = await this._post(`/assessments/api/attempt/${this.attemptId}/analyze/`, {
                frame,
                confirm_strike: false,
            });
            const data = await resp.json();

            this.onFaceStatus(data.status);
            if (data.processed_frame) this.onProcessedFrame(data.processed_frame);
            this._handleCvResult(data.status, frame, data.processed_frame);
        } catch (err) {
            console.error('Frame analysis failed:', err);
        }
    }

    async _handleCvResult(status, rawFrame) {
        const isFlag = status !== 'OK';

        if (isFlag && status === this.lastFlagStatus) {
            this.consecutiveFaceFlags += 1;
        } else if (isFlag) {
            this.consecutiveFaceFlags = 1;
            this.lastFlagStatus = status;
        } else {
            this.consecutiveFaceFlags = 0;
            this.lastFlagStatus = 'OK';
            return;
        }

        if (this.consecutiveFaceFlags >= this.debounceChecks) {
            this.consecutiveFaceFlags = 0;

            const eventMap = {
                FLAG_NO_FACE: 'NO_FACE',
                FLAG_MULTIPLE_FACES: 'MULTIPLE_FACES',
                FLAG_HEAD_TURNED: 'HEAD_TURNED',
            };
            const eventType = eventMap[status] || 'NO_FACE';

            const resp = await this._post(`/assessments/api/attempt/${this.attemptId}/analyze/`, {
                frame: rawFrame,
                confirm_strike: true,
            });
            const data = await resp.json();

            if (data.strike_logged) {
                const labels = {
                    NO_FACE: 'No face detected',
                    MULTIPLE_FACES: 'Multiple faces detected',
                    HEAD_TURNED: 'Head turned away',
                };
                this.onViolation(labels[eventType] || 'Proctoring violation', data.warning_count, data.max_warnings);
                this.onIntegrityUpdate(data.integrity_score);
                if (data.disqualified) {
                    this.stop();
                    this.onDisqualified();
                }
            }
        }
    }

    _bindVisibilityListeners() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.isRunning) {
                this._logFrontendViolation('TAB_SWITCH', 'Tab switched or window hidden');
            }
        });

        window.addEventListener('blur', () => {
            if (this.isRunning) {
                this._logFrontendViolation('WINDOW_BLUR', 'Window lost focus');
            }
        });
    }

    _canLogViolation(eventType) {
        const last = this.lastViolationAt[eventType] || 0;
        return Date.now() - last >= this.violationCooldownMs;
    }

    async _logFrontendViolation(eventType, details) {
        if (!this._canLogViolation(eventType)) return;

        const snapshot = this.captureFrame(0.5);
        try {
            const resp = await this._post(`/assessments/api/attempt/${this.attemptId}/violation/`, {
                event_type: eventType,
                snapshot: snapshot.split(',')[1] || snapshot,
                duration_ms: 0,
                details,
            });
            const data = await resp.json();

            if (data.logged) {
                this.lastViolationAt[eventType] = Date.now();
                this.onViolation(details, data.warning_count, data.max_warnings);
                this.onIntegrityUpdate(data.integrity_score);
                if (data.disqualified) {
                    this.stop();
                    this.onDisqualified();
                }
            }
        } catch (err) {
            console.error('Violation logging failed:', err);
        }
    }

    _startCountdown() {
        this._updateTimerDisplay();
        this.countdownTimer = setInterval(() => {
            this.timeRemainingSec -= 1;
            this._updateTimerDisplay();
            if (this.timeRemainingSec <= 0) {
                this.stop();
                this.onTimeUp();
            }
        }, 1000);
    }

    _updateTimerDisplay() {
        const el = document.getElementById('timer');
        if (!el) return;
        const m = Math.floor(this.timeRemainingSec / 60);
        const s = this.timeRemainingSec % 60;
        el.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        if (this.timeRemainingSec <= 60) el.classList.add('text-red-300');
    }

    async submitQuiz() {
        if (this.isSubmitting) return;
        this.isSubmitting = true;
        this.stop();

        const form = document.getElementById('quiz-form');
        const answers = {};
        form.querySelectorAll('[name^="q_"]').forEach((el) => {
            const qId = el.name.replace('q_', '');
            if (el.type === 'radio') {
                if (el.checked) answers[qId] = el.value;
            } else {
                answers[qId] = el.value;
            }
        });

        try {
            const resp = await this._post(`/assessments/api/attempt/${this.attemptId}/submit/`, { answers });
            const data = await resp.json();
            if (data.redirect) window.location.href = data.redirect;
        } catch (err) {
            console.error('Submit failed:', err);
            alert('Failed to submit quiz. Please try again.');
            this.isSubmitting = false;
        }
    }

    stop() {
        this.isRunning = false;
        if (this.frameTimer) clearInterval(this.frameTimer);
        if (this.countdownTimer) clearInterval(this.countdownTimer);
        if (this.noiseTimer) clearInterval(this.noiseTimer);
        if (this.displayTimer) clearInterval(this.displayTimer);
        if (this.audioContext) {
            this.audioContext.close().catch(() => {});
            this.audioContext = null;
        }
        if (this.video && this.video.srcObject) {
            this.video.srcObject.getTracks().forEach((t) => t.stop());
        }
    }

    async _post(url, body) {
        return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this._getCsrfToken(),
            },
            body: JSON.stringify(body),
        });
    }

    _getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) return meta.content;
        const cookie = document.cookie
            .split(';')
            .map((c) => c.trim())
            .find((c) => c.startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ProctorController };
}
