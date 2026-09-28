# Chess Mentor

Türkçe, erişilebilir bir Android satranç analiz yardımcısı. Tahtayı uygulama içinde kurun veya ekrandaki konumu FEN biçiminde girin; uygulama size hamle önerisi, plan ve taş güvenliği özeti verir.

> Bu uygulama eğitim ve analiz içindir. Başka uygulamaları okumaz, ekran kaydı yapmaz ve hamleleri otomatik oynatmaz. Çevrimiçi maçlarda platform kurallarına uyun.

## APK oluşturma

GitHub Actions çalışması her push ve pull request için `app-debug.apk` yapıtını üretir. Yerelde:

```bash
./gradlew assembleDebug
```

APK: `app/build/outputs/apk/debug/app-debug.apk`
