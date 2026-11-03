# Browser Permission Capture — Mini Cybersecurity Demo (Django)

A small, self-contained Django project built as a cybersecurity awareness
demo. It shows a user-facing page with three buttons. Clicking a button
triggers a **native browser permission prompt** (Camera / Microphone /
Location). Only if the user explicitly clicks **Allow** does the frontend
capture a small sample (one photo frame, a 3-second audio clip, or GPS
coordinates) and POST it to the Django backend, where it's logged in a
database and viewable on a `/dashboard/` page.

This is meant to illustrate, in a controlled first-party context, exactly
what a website can access once a permission is granted — useful for
security-awareness talks, portfolio demos, or as a base for testing how
browsers handle `getUserMedia` / `Geolocation` consent flows.

> ⚠️ **Ethics note:** every capture here is gated by the browser's own
> consent dialog — there is no way to bypass it, and that's intentional.
> Only run this against your own test users / devices, and tell anyone who
> uses it what it does (don't deploy this somewhere people wouldn't
> expect to be asked for camera/mic/location access).

## Project layout

```
permission_demo/
├── manage.py
├── requirements.txt
├── permission_demo_project/      # Django project config
│   ├── settings.py
│   └── urls.py
└── tracker/                      # The app
    ├── models.py                 # CapturedEvent model
    ├── views.py                  # index, dashboard, capture_event API
    ├── urls.py
    ├── admin.py                  # Admin panel registration
    ├── templates/tracker/
    │   ├── index.html            # The 3-button demo page
    │   └── dashboard.html        # Backend table of captured events
    └── static/tracker/
        ├── css/style.css
        └── js/capture.js         # Permission requests + capture logic
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

Then open:

- `http://127.0.0.1:8000/` — the demo page with the three buttons
- `http://127.0.0.1:8000/dashboard/` — everything captured so far
- `http://127.0.0.1:8000/admin/` — Django admin (if you created a superuser)

## How it works

1. **Click a button** → JS immediately logs a `requested` event to the
   backend (`/api/capture/`), then calls the matching browser API
   (`getUserMedia`, `navigator.geolocation.getCurrentPosition`).
2. **Browser shows its native permission dialog.** This cannot be
   skipped, faked, or auto-accepted by the page — it's entirely
   controlled by the browser.
3. **If allowed:** the JS captures one artifact (a canvas snapshot from
   the video stream, a `MediaRecorder` audio blob, or GPS coords),
   base64-encodes media, and POSTs it to `/api/capture/`.
4. **If denied:** a `denied` event is logged instead — no data.
5. **Django backend** (`views.capture_event`) validates the payload,
   decodes any base64 media, saves it via the `CapturedEvent` model
   (photo/audio go to `media/captures/...`, location goes to DB fields),
   and returns the new row's id.
6. **`/dashboard/`** lists every event — type, status, timestamp, IP,
   and a link to the captured file / coordinates.

## Ideas to extend it (good for a portfolio write-up)

- Add a consent banner / explicit "this is a demo" disclosure before any
  button is clickable (good practice regardless).
- Log `navigator.userAgentData`, screen resolution, timezone, battery
  status etc. alongside the permission events to show fingerprinting
  surface area.
- Add a second page that demonstrates the **Permissions API**
  (`navigator.permissions.query`) to show permission state *without*
  triggering a prompt, and discuss why that itself is a minor privacy
  leak browsers have had to patch over the years.
- Write a short report comparing how Chrome, Firefox, and Safari phrase
  and persist these permission prompts differently.
