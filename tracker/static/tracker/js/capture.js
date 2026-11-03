// capture.js — drives the permission demo buttons.
// All browser permission prompts here are native: the browser itself
// always shows the user an explicit Allow/Block dialog before any
// data flows. This file only reacts to that decision and logs it.

function setStatus(key, message, kind) {
    const el = document.getElementById(`status-${key}`);
    el.textContent = message;
    el.className = `status ${kind || ""}`;
}

async function sendEvent(body) {
    const res = await fetch(CAPTURE_ENDPOINT, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": CSRF_TOKEN,
        },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        throw new Error(`Backend rejected event: ${res.status}`);
    }
    return res.json();
}

/* ---------------- Camera ---------------- */
document.getElementById("btn-camera").addEventListener("click", async () => {
    const btn = document.getElementById("btn-camera");
    btn.disabled = true;
    await sendEvent({ permission_type: "camera", status: "requested" });

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        await sendEvent({ permission_type: "camera", status: "granted", extra: { note: "permission granted" } });

        const video = document.getElementById("camera-preview");
        video.style.display = "block";
        video.srcObject = stream;
        await video.play();

        // Give the stream a brief moment to render a real frame, then snap it.
        await new Promise((r) => setTimeout(r, 500));

        const canvas = document.getElementById("camera-canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0);
        const imageData = canvas.toDataURL("image/png");

        stream.getTracks().forEach((t) => t.stop());
        video.style.display = "none";

        const result = await sendEvent({
            permission_type: "camera",
            status: "granted",
            image_data: imageData,
        });
        setStatus("camera", `Captured and saved (event #${result.event_id}).`, "ok");
    } catch (err) {
        await sendEvent({ permission_type: "camera", status: "denied", extra: { error: String(err) } });
        setStatus("camera", "Permission denied or unavailable.", "err");
    } finally {
        btn.disabled = false;
    }
});

/* ---------------- Microphone ---------------- */
document.getElementById("btn-mic").addEventListener("click", async () => {
    const btn = document.getElementById("btn-mic");
    btn.disabled = true;
    await sendEvent({ permission_type: "microphone", status: "requested" });

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        await sendEvent({ permission_type: "microphone", status: "granted", extra: { note: "permission granted" } });

        setStatus("mic", "Recording 3s clip...", "");
        const recorder = new MediaRecorder(stream);
        const chunks = [];
        recorder.ondataavailable = (e) => chunks.push(e.data);

        const stopped = new Promise((resolve) => (recorder.onstop = resolve));
        recorder.start();
        await new Promise((r) => setTimeout(r, 3000));
        recorder.stop();
        await stopped;

        stream.getTracks().forEach((t) => t.stop());

        const blob = new Blob(chunks, { type: "audio/webm" });
        const audioData = await new Promise((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.readAsDataURL(blob);
        });

        const result = await sendEvent({
            permission_type: "microphone",
            status: "granted",
            audio_data: audioData,
        });
        setStatus("mic", `Captured and saved (event #${result.event_id}).`, "ok");
    } catch (err) {
        await sendEvent({ permission_type: "microphone", status: "denied", extra: { error: String(err) } });
        setStatus("mic", "Permission denied or unavailable.", "err");
    } finally {
        btn.disabled = false;
    }
});

/* ---------------- Location ---------------- */
document.getElementById("btn-location").addEventListener("click", async () => {
    const btn = document.getElementById("btn-location");
    btn.disabled = true;
    await sendEvent({ permission_type: "location", status: "requested" });

    if (!("geolocation" in navigator)) {
        setStatus("location", "Geolocation API not supported.", "err");
        btn.disabled = false;
        return;
    }

    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const { latitude, longitude, accuracy } = position.coords;
            const result = await sendEvent({
                permission_type: "location",
                status: "granted",
                latitude,
                longitude,
                accuracy,
            });
            setStatus(
                "location",
                `Captured (${latitude.toFixed(4)}, ${longitude.toFixed(4)}) — event #${result.event_id}.`,
                "ok"
            );
            btn.disabled = false;
        },
        async (err) => {
            await sendEvent({ permission_type: "location", status: "denied", extra: { error: err.message } });
            setStatus("location", "Permission denied or unavailable.", "err");
            btn.disabled = false;
        }
    );
});
