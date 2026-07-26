# User Guide

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [Features.md](./Features.md), [FAQ.md](../FAQ.md)

---

## Getting Started

### Accessing SafeVixAI
Open the app in any modern browser at your deployment URL, or install it as a PWA:

1. Visit the app URL
2. Click "Install" or "Add to Home Screen" in the browser address bar
3. The app will appear on your home screen like a native app

### Creating an Account
1. Click "Sign Up" on the login page
2. Enter your email and create a password
3. Fill in your profile (name, vehicle number, blood group — optional)
4. All medical info is stored **only on your device** for privacy

### Language Selection
1. Go to Settings
2. Select your preferred language from the list (14 Indian languages supported)
3. The UI and chatbot will switch to your language

---

## Emergency Features

### SOS Activation
1. Press and hold the SOS button for 2 seconds
2. The app captures your GPS location
3. Emergency contacts receive SMS/WhatsApp alerts with your location
4. Real-time family tracking begins via WebSocket
5. Cancel dispatch if the alert was accidental

**Offline:** If you're offline, the SOS is queued and sent automatically when connectivity returns.

### Emergency Locator
1. The home screen shows nearby emergency services
2. Tap "Hospitals," "Police," or "Fire" to filter
3. Each result shows distance, phone number, and address
4. Tap "Call" to contact directly
5. Tap "Navigate" to open directions

### Bystander Mode
No login required. Witnesses can:
1. Tap "Bystander Mode" on the home screen
2. Report an accident with GPS coordinates
3. Receive first-aid guidance
4. Call 108 (ambulance) directly

---

## AI Chatbot

### Asking Questions
Type your question in the chat input at the bottom of the screen. The chatbot can answer:

- **Traffic laws**: "What is the fine for not wearing a helmet?"
- **Challan calculations**: "How much is the fine for drunk driving?"
- **First aid**: "How do I treat a burn?"
- **Legal information**: "What does Section 185 of the Motor Vehicles Act say?"
- **Weather**: "What's the weather like on my route?"

### Voice Input
1. Tap the microphone icon next to the chat input
2. Speak your question
3. The app converts speech to text and sends it
4. Works in 14 Indian languages

### Language Detection
The chatbot automatically detects your language:
- Hindi, Tamil, Telugu, etc. → Auto-routed to Sarvam AI (Indian language specialist)
- English → Default fast provider

### Offline AI
1. In the assistant page, tap "Use Offline AI"
2. Downloads the AI model (2.2GB, one-time download)
3. Once downloaded, the chatbot works without internet

---

## Challan Calculator

### Calculate a Fine
1. Go to the Challan page
2. Select a violation (e.g., "Drunk Driving," "No Helmet")
3. Select your state (fine amounts vary by state)
4. Toggle "Repeat Offender" if applicable (fines double)
5. Tap "Calculate"
6. View the fine amount, legal section, and violation details

### Offline Mode
Challan calculations work offline using DuckDB-Wasm (runs in your browser). No internet needed after the first page load.

---

## Road Reporter

### Submit a Report
1. Go to the Report page
2. Take or upload a photo of the road issue
3. Select a category (pothole, damaged road, missing sign, etc.)
4. Your GPS location is automatically captured
5. Add a description
6. Submit

### Track Your Report
1. Go to "Report Track"
2. Enter your report ID or scanning the QR code
3. View status: Submitted → Under Review → In Progress → Resolved
4. Upvote other reports to signal urgency

### Offline
Reports are saved to IndexedDB and automatically submitted when you're back online.

---

## Profile & Settings

### Profile Page
- View and edit your name, vehicle number, blood group, emergency contact
- Toggle features: Crash Detection, V8 Offline Voice, Push Hub
- Your data is stored on your device (IndexedDB) for privacy

### Settings
- **Theme**: Light, Dark, or System
- **Language**: Choose from 14 Indian languages
- **Sign Out**: End your session
- **Purge Cache**: Clear local data
- **Export Profile**: Download your profile data

---

## Live Tracking

### Starting Tracking
When you activate SOS, family tracking starts automatically. A tracking link is generated that you can share with family members.

### Viewing a Tracked Session
1. Open the tracking link
2. See the person's location on a map in real time
3. View speed, battery level, and movement history
4. Call 112 or 108 directly from the tracking page

### Session States
- **Active**: Live tracking in progress
- **Inactive**: Person is safe, tracking ended
- **Expired**: Session timed out

---

## Command Center (For Officials)

The Command Center is for municipal authorities, police, and emergency services.

### Dashboard
- Real-time incident map with active issues
- Agency status (police, fire, hospitals) with response metrics
- Incident log with timeline and resolution tracking
- Trending incidents by category

### Managing Reports
- View submitted road issue reports
- Assign reports to teams
- Update status (In Progress, Resolved)
- View before/after photos

---

## Privacy

- **Blood group and medical data** are stored only on your device
- **Location data** is used only during active SOS/tracking sessions
- **Analytics** are opt-in (Settings → Share anonymous usage data)
- **Your data, your control**: Export or delete at any time

See [PRIVACY.md](./PRIVACY.md) for complete privacy policy.

---

## Getting Help

- In-app help: Use the chatbot with "help"
- [FAQ.md](../FAQ.md) — Frequently asked questions
- [GitHub Issues](https://github.com/SafeVixAI/SafeVixAI/issues) — Bug reports and feature requests
- [SUPPORT.md](../SUPPORT.md) — All support channels
