# Nexora AI — Android App (TWA)

This is a **Trusted Web Activity (TWA)** Android app that wraps the Nexora AI web app
(`https://nexora-ai.vercel.app`) into a native Android APK for Google Play.

TWA gives you:
- Full-screen experience (no browser address bar)
- Native app launcher icon
- Google Play listing
- AdMob integration via web ads (AdSense) or native AdMob SDK

---

## Prerequisites

1. **Android Studio** — [Download here](https://developer.android.com/studio)
   - Install with default settings (includes Android SDK)
2. **Java 17+** — Already installed on your machine ✅
3. **Gradle wrapper** — Included in this project (no separate install needed)

---

## Step 1 — Open in Android Studio

1. Open Android Studio
2. Click **File → Open**
3. Navigate to `nexora-ai/android/` and click **OK**
4. Wait for Gradle sync to complete (~2-3 minutes first time)

---

## Step 2 — Generate a Release Keystore

You need a keystore to sign your APK for Play Store.

Open a terminal and run:

```bash
keytool -genkey -v -keystore nexora-release.jks -alias nexora -keyalg RSA -keysize 2048 -validity 10000
```

Fill in the prompts (name, org, city, etc.). **Save the password — you cannot recover it.**

Move the keystore to the `android/app/` folder.

---

## Step 3 — Get Your SHA-256 Fingerprint

```bash
keytool -list -v -keystore android/app/nexora-release.jks -alias nexora
```

Copy the **SHA-256** fingerprint (looks like `AA:BB:CC:...`).

---

## Step 4 — Update Digital Asset Links

Open `frontend/.well-known/assetlinks.json` and replace:
```
REPLACE_WITH_YOUR_SHA256_CERT_FINGERPRINT
```
with your actual fingerprint (remove the colons, use only the hex, colon-separated — keep the format as-is).

Deploy your updated web app to Vercel so the file is live at:
```
https://nexora-ai.vercel.app/.well-known/assetlinks.json
```

Verify it works:
```
https://digitalassetlinks.googleapis.com/v1/statements:list?source.web.site=https://nexora-ai.vercel.app&relation=delegate_permission/common.handle_all_urls
```

---

## Step 5 — Configure Signing in Android Studio

In Android Studio:
1. Go to **Build → Generate Signed Bundle / APK**
2. Choose **APK**
3. Point to your `nexora-release.jks`
4. Enter alias (`nexora`) and passwords
5. Select **Release** build variant
6. Click **Finish**

Or add to `android/app/build.gradle` (under `android { signingConfigs { ... } }`):

```gradle
signingConfigs {
    release {
        storeFile file('nexora-release.jks')
        storePassword 'YOUR_STORE_PASSWORD'
        keyAlias 'nexora'
        keyPassword 'YOUR_KEY_PASSWORD'
    }
}
buildTypes {
    release {
        signingConfig signingConfigs.release
        ...
    }
}
```

---

## Step 6 — Build the APK

In Android Studio terminal or command prompt inside `android/`:

```bat
gradlew.bat assembleRelease
```

Your signed APK will be at:
```
android/app/build/outputs/apk/release/app-release.apk
```

---

## Step 7 — Publish to Google Play

1. Go to [Google Play Console](https://play.google.com/console)
2. Create a new app
3. Fill in store listing (name: **Nexora AI**, description, screenshots)
4. Upload your APK under **Production → Releases**
5. Set content rating (Health & Fitness)
6. Submit for review (~1-3 days)

---

## AdMob Integration

Since this is a TWA (web inside Android), your **Google AdSense ads already work** inside the app.

For native AdMob (banner/interstitial ads rendered by Android):

1. Create an AdMob account at [admob.google.com](https://admob.google.com)
2. Create an app and get your **App ID**
3. Add to `app/build.gradle`:
   ```gradle
   implementation 'com.google.android.gms:play-services-ads:23.0.0'
   ```
4. Add to `AndroidManifest.xml` inside `<application>`:
   ```xml
   <meta-data
       android:name="com.google.android.gms.ads.APPLICATION_ID"
       android:value="ca-app-pub-XXXXXXXXXXXXXXXX~XXXXXXXXXX"/>
   ```

---

## Updating the App URL

To point to a different URL, edit `AndroidManifest.xml`:
```xml
<meta-data
    android:name="android.support.customtabs.trusted.DEFAULT_URL"
    android:value="https://your-new-url.com" />
```

---

## Troubleshooting

**Browser bar still shows?**
→ Digital Asset Links not verified. Check `assetlinks.json` is live and fingerprint matches.

**App crashes on launch?**
→ Make sure your web app URL is live and returns 200.

**Gradle sync fails?**
→ Check internet connection. Android Studio needs to download dependencies.
