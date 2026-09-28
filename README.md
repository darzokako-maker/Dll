# Chess Coach (Android)

A local-first Android chess **analysis and training** starter. Paste a FEN position, ask a locally bundled Stockfish-compatible engine for a recommendation, and review the suggested move on an in-app board.

## Safety and fair play

This project intentionally does **not** capture another app's screen, draw over another app, use root privileges, or inject touches. Those behaviours enable unfair play and can violate platform/game rules. Use it for positions you own, study, and offline analysis.

## Run

1. Open this folder in Android Studio.
2. Sync Gradle and run on Android 8.0+.
3. Enter a valid FEN on **Analyse**, then tap **Analyse position**.

`LocalEngine` is a small interface boundary for a UCI Stockfish implementation. The included `DemoEngine` gives the UI a deterministic response until a compliant local engine adapter is supplied.
