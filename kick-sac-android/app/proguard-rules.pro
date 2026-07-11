# Kick Sac keeps JavaScript bridge methods exposed to the embedded WebView.
-keepclassmembers class be.laserart.kicksac.MainActivity$AndroidBridge {
    @android.webkit.JavascriptInterface <methods>;
}
