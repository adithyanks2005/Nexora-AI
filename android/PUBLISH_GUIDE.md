# Nexora AI — Play Store Publishing Guide

> Created by **ADITHYAN KS**

This guide walks you through every step to publish Nexora AI as a **free app** on the Google Play Store.

---

## Prerequisites Checklist

- [ ] Java 17+ installed (`java -version` to check)
- [ ] Android Studio installed (for Gradle and adb tools)
- [ ] Nexora AI Vercel deployment is live at `https://nexora-ai.vercel.app`
- [ ] Google Play Developer account (one-time **$25 registration fee**)
  → Sign up at https://play.google.com/console

---

## Step 1 — Generate Your Signing Keystore

**Run once. Keep the keystore and password safe forever.**

```bat
cd android
generate-keystore.bat
```

This script will:
1. Generate `android/app/nexora-release.jks`
2. Print your **SHA-256 fingerprint** (copy it — you need it in Step 2)

> ⚠️ **Never lose your keystore or password.** If you lose it, you cannot update your app on Play Store.

---

## Step 2 — Set Up Signing Credentials

Create the file `android/local.properties` (do NOT commit this to git):

```properties
STORE_FILE=app/nexora-release.jks
STORE_PASSWORD=your_keystore_password_here
KEY_ALIAS=nexora
KEY_PASSWORD=your_key_password_here
```

A template is available at `android/local.properties.template`.

---

## Step 3 — Update Digital Asset Links

Open `frontend/.well-known/assetlinks.json` and replace:
```
REPLACE_WITH_YOUR_SHA256_CERT_FINGERPRINT
```
with your actual SHA-256 fingerprint from Step 1 (keep the colon-separated format, e.g. `AA:BB:CC:...`).

Then deploy to Vercel:
```bash
git add frontend/.well-known/assetlinks.json
git commit -m "chore: add release keystore fingerprint to assetlinks.json"
git push
```

Verify it's live (wait ~1 minute after push):
```
https://digitalassetlinks.googleapis.com/v1/statements:list?source.web.site=https://nexora-ai.vercel.app&relation=delegate_permission/common.handle_all_urls
```
You should see a JSON response with `"complete": true`.

---

## Step 4 — Build the Android App Bundle

```bat
cd android
build-aab.bat
```

Output: `android/app/build/outputs/bundle/release/app-release.aab`

---

## Step 5 — Create Your Google Play Listing

Go to https://play.google.com/console and:

1. Click **Create app**
2. Fill in:
   - **App name**: `Nexora AI`
   - **Default language**: English (United Kingdom) or your preference
   - **App or game**: App
   - **Free or paid**: **Free**
3. Accept the declarations and click **Create app**

---

## Step 6 — Fill In the Store Listing

### Main Store Listing

| Field | Value |
|---|---|
| App name | Nexora AI |
| Short description | Copy from `store-listing/short-description.txt` |
| Full description | Copy from `store-listing/description.txt` |
| App icon | 512×512 PNG — export from `frontend/static/icons/icon.svg` |
| Feature graphic | 1024×500 PNG — create a branded banner |
| Category | **Health & Fitness** |
| Tags | health, AI, chatbot, symptoms, BMI, medication |

### Screenshots (required)
Capture at least **2 phone screenshots** (1080×1920 or 1080×2400):
- Chat screen with an AI response visible
- Health calculators screen
- Symptom checker screen
- Health records screen

Use Android Studio Emulator or a real device with the debug APK installed.

### Content Rating
1. Go to **Policy → App content → Content rating**
2. Complete the questionnaire
3. Category: **Health & Fitness / Medical**
4. Answer "No" to violence, sexual content, etc.

### Privacy Policy
Required for health apps. You can use a free generator like https://privacypolicygenerator.info  
Host it at your Vercel domain or GitHub Pages and paste the URL.

---

## Step 7 — Upload the AAB

1. Go to **Release → Production**
2. Click **Create new release**
3. Upload `app-release.aab`
4. Enter release notes:
   ```
   Initial release of Nexora AI — your AI health companion.
   Features: AI chat, symptom checker, health calculators,
   medication reminders, and health records.
   ```
5. Click **Save** then **Review release**

---

## Step 8 — Submit for Review

1. Fix any policy warnings shown on the review screen
2. Click **Start rollout to Production**
3. Wait **1–3 business days** for Google's review

You'll receive an email when the app is approved and live.

---

## Updating the App in the Future

When you update your web app (Vercel), users get the update automatically — **no new APK/AAB needed**. 

When you change the Android shell (permissions, icons, etc.):
1. Bump `versionCode` and `versionName` in `android/app/build.gradle`
2. Run `build-aab.bat` again
3. Upload the new AAB to Play Console as a new release

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Browser address bar shows in app | Digital Asset Links not verified — check Step 3 |
| App crashes on launch | Vercel URL is down or returning an error |
| Gradle sync fails | Check internet connection; run `gradlew.bat --refresh-dependencies` |
| Play review rejected | Read the rejection email carefully; usually missing privacy policy or content rating |
| SHA-256 not matching | Make sure you're using the **release** keystore, not debug |
