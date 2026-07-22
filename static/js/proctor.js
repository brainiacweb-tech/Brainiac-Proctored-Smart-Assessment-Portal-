/**
 * ProctorController — Frontend proctoring module
 *
 * Handles webcam capture, periodic frame upload (1 frame / 2s),
 * Page Visibility API tab-switch detection, window blur events,
 * and server-side CV analysis sync with debounced face violations.
 */

class ProctorController {
    constructor(config) {
        this.attemptId = config.attemptId;
        this.frameIntervalMs = config.frameIntervalMs || 2000;
        this.debounceChecks = config.debounceChecks || 2;
        this.maxWarnings = config.maxWarnings || 3;
        this.timeLimitMins = config.timeLimitMins || 30;

        this.video = null;
        this.canvas = null;
        this.frameTimer = null;
        this.countdownTimer = null;
        this.timeRemainingSec = this.timeLimitMins * 60;

        // Debounce state for CV violations
        this.consecutiveFaceFlags = 0;
        this.lastFlagStatus = 'OK';
        this.isRunning = false;
        this.isSubmitting = false;

        // Callbacks (set by consumer)
        this.onViolation = () => {};
        this.onIntegrityUpdate = () => {};
        this.onFaceStatus = () => {};
        this.onProcessedFrame = () => {};
        this.onDisqualified = () => {};
        this.onTimeUp = () => {};
    }

    /** Initialize webcam, listeners, timers. */
    async init() {
        this.video = document.getElementById('webcam');
        this.canvas = document.getElementById('capture-canvas');

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480, facingMode: 'user' },
                audio: false,
            });
            this.video.srcObject = stream;
            await this.video.play();
        } catch (err) {
            console.error('Webcam access failed:', err);
            this.onFaceStatus('Camera Error');
            return;
        }

        this._bindVisibilityListeners();
        this._startFrameLoop();
        this._startCountdown();
        this.isRunning = true;
    }

    /** Capture current video frame as base64 JPEG. */
    captureFrame(quality = 0.7) {
        if (!this.video || !this.canvas) return '';
        const ctx = this.canvas.getContext('2d');
        this.canvas.width = this.video.videoWidth || 640;
        this.canvas.height = this.video.videoHeight || 480;
        ctx.drawImage(this.video, 0, 0);
        return this.canvas.toDataURL('image/jpeg', quality);
    }

    /** Periodic frame capture and server CV analysis. */
    _startFrameLoop() {
        this.frameTimer = setInterval(() => this._analyzeFrame(), this.frameIntervalMs);
    }

    async _analyzeFrame() {
        if (!this.isRunning || this.isSubmitting) return;

        const frame = this.captureFrame();
        if (!frame) return;

        try {
            const resp = await this._post(`/assessments/api/attempt/${this.attemptId}/analyze/`, {
                frame: frame,
                confirm_strike: false,
            });
            const data = await resp.json();

            this.onFaceStatus(data.status);
            if (data.processed_frame) {
                this.onProcessedFrame(data.processed_frame);
            }

            this._handleCvResult(data.status, frame, data.processed_frame);
        } catch (err) {
            console.error('Frame analysis failed:', err);
        }
    }

    /**
     * Debounce CV flags: require N consecutive bad frames before logging strike.
     */
    async _handleCvResult(status, rawFrame, processedFrame) {
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
                this.onViolation(
                    labels[eventType] || 'Proctoring violation',
                    data.warning_count,
                    data.max_warnings,
                );
                this.onIntegrityUpdate(data.integrity_score);

                if (data.disqualified) {
                    this.stop();
                    this.onDisqualified();
                }
            }
        }
    }

    /** Tab switch / visibility change detection. */
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

    async _logFrontendViolation(eventType, details) {
        const snapshot = this.captureFrame(0.5);
        try {
            const resp = await this._post(`/assessments/api/attempt/${this.attemptId}/violation/`, {
                event_type: eventType,
                snapshot: snapshot.split(',')[1] || snapshot,
                duration_ms: 0,
                details: details,
            });
            const data = await resp.json();

            if (data.logged) {
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

    /** Countdown timer. */
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
        if (this.timeRemainingSec <= 60) {
            el.classList.add('text-red-300');
        }
    }

    /** Collect answers and submit quiz. */
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
            if (data.redirect) {
                window.location.href = data.redirect;
            }
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
        if (this.video && this.video.srcObject) {
            this.video.srcObject.getTracks().forEach((t) => t.stop());
        }
    }

    /** CSRF-aware POST helper. */
    async _post(url, body) {
        const csrfToken = this._getCsrfToken();
        return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
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

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ProctorController };
}
