from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;\ninterface IDisplayToggleService {\n    int toggleDisplays(int mode, in int[] whitelistDisplayIds);\n    String runHandoffTimingProbe(int durationMs, int intervalMs);\n    String readFoldTimerInfo();\n}\n''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    private String readNode(String path) {
        try {
            java.io.File f = new java.io.File(path);
            if (!f.exists()) return "NA";
            byte[] b = java.nio.file.Files.readAllBytes(f.toPath());
            return new String(b, java.nio.charset.StandardCharsets.UTF_8).trim();
        } catch (Throwable e) {
            return "ERR";
        }
    }

    private String runShellShort(String cmd, long timeoutMs) {
        StringBuilder out = new StringBuilder();
        Process p = null;
        try {
            p = new ProcessBuilder("/system/bin/sh", "-c", cmd).redirectErrorStream(true).start();
            boolean done = p.waitFor(timeoutMs, java.util.concurrent.TimeUnit.MILLISECONDS);
            if (!done) {
                p.destroyForcibly();
                return "TIMEOUT";
            }
            try (java.io.BufferedReader r = new java.io.BufferedReader(new java.io.InputStreamReader(p.getInputStream()))) {
                String line;
                while ((line = r.readLine()) != null) out.append(line).append('\n');
            }
            return out.toString().trim();
        } catch (Throwable e) {
            try { if (p != null) p.destroyForcibly(); } catch (Throwable ignored) {}
            return "ERROR: " + e;
        }
    }

    @Override public String readFoldTimerInfo() {
        String off = runShellShort("getprop msc.power.fdtimer_screenOff", 1000);
        String on  = runShellShort("getprop msc.power.fdtimer_screenOn", 1000);
        String prep = runShellShort("settings get global hn_fold_display_mode_prepare", 1000);
        String state = runShellShort("settings get global hn_fold_screen_state", 1000);
        StringBuilder o = new StringBuilder();
        o.append("FOLD TIMER INFO\n");
        o.append("msc.power.fdtimer_screenOff=").append(off).append('\n');
        o.append("msc.power.fdtimer_screenOn=").append(on).append('\n');
        o.append("hn_fold_display_mode_prepare=").append(prep).append('\n');
        o.append("hn_fold_screen_state=").append(state).append('\n');
        o.append("same-value write test screenOff: ").append(runShellShort("setprop msc.power.fdtimer_screenOff '"+off+"' 2>&1; echo rc=$?; getprop msc.power.fdtimer_screenOff", 1200)).append('\n');
        o.append("same-value write test screenOn: ").append(runShellShort("setprop msc.power.fdtimer_screenOn '"+on+"' 2>&1; echo rc=$?; getprop msc.power.fdtimer_screenOn", 1200)).append('\n');
        return o.toString();
    }

    @Override public String runHandoffTimingProbe(int durationMs, int intervalMs) {
        if (durationMs < 1000) durationMs = 1000;
        if (durationMs > 15000) durationMs = 15000;
        if (intervalMs < 5) intervalMs = 5;
        if (intervalMs > 100) intervalMs = 100;

        final String[] nodes = new String[] {
            "/sys/class/backlight/panel0/actual_brightness",
            "/sys/class/backlight/panel0/brightness",
            "/sys/class/backlight/panel0/bl_power",
            "/sys/class/backlight/panel1/actual_brightness",
            "/sys/class/backlight/panel1/brightness",
            "/sys/class/backlight/panel1/bl_power",
            "/sys/class/drm/card0-DSI-1/status",
            "/sys/class/drm/card0-DSI-2/status"
        };

        StringBuilder o = new StringBuilder();
        o.append("MAGIC V2 HANDOFF TIMING PROBE v1\n");
        o.append("durationMs=").append(durationMs).append(" intervalMs=").append(intervalMs).append('\n');
        o.append("Start fully OPEN, press CAPTURE, then close through the normal handoff once.\n");
        o.append("Columns: t_ms p0_actual p0_brightness p0_bl_power p1_actual p1_brightness p1_bl_power dsi1 dsi2\n");
        for (String n : nodes) o.append("NODE ").append(n).append(" => ").append(readNode(n)).append('\n');
        o.append("--- SAMPLES ---\n");

        long start = android.os.SystemClock.elapsedRealtimeNanos();
        long end = start + durationMs * 1000000L;
        long next = start;
        int bothActualOn = 0;
        int p0Only = 0, p1Only = 0, bothOff = 0, unknown = 0;
        long firstBothMs = -1, lastBothMs = -1;

        while (android.os.SystemClock.elapsedRealtimeNanos() < end) {
            long now = android.os.SystemClock.elapsedRealtimeNanos();
            long t = (now - start) / 1000000L;
            String a0 = readNode(nodes[0]);
            String b0 = readNode(nodes[1]);
            String bp0 = readNode(nodes[2]);
            String a1 = readNode(nodes[3]);
            String b1 = readNode(nodes[4]);
            String bp1 = readNode(nodes[5]);
            String d1 = readNode(nodes[6]);
            String d2 = readNode(nodes[7]);
            o.append(t).append(' ').append(a0).append(' ').append(b0).append(' ').append(bp0).append(' ')
             .append(a1).append(' ').append(b1).append(' ').append(bp1).append(' ')
             .append(d1).append(' ').append(d2).append('\n');
            try {
                long v0 = Long.parseLong(a0);
                long v1 = Long.parseLong(a1);
                if (v0 > 0 && v1 > 0) {
                    bothActualOn++;
                    if (firstBothMs < 0) firstBothMs = t;
                    lastBothMs = t;
                } else if (v0 > 0) p0Only++;
                else if (v1 > 0) p1Only++;
                else bothOff++;
            } catch (Throwable e) { unknown++; }

            next += intervalMs * 1000000L;
            long sleepNs = next - android.os.SystemClock.elapsedRealtimeNanos();
            if (sleepNs > 0) {
                try {
                    long ms = sleepNs / 1000000L;
                    int ns = (int)(sleepNs % 1000000L);
                    Thread.sleep(ms, ns);
                } catch (Throwable ignored) {}
            }
        }
        o.append("--- SUMMARY ---\n");
        o.append("both_actual_brightness>0 samples=").append(bothActualOn).append('\n');
        o.append("p0_only=").append(p0Only).append(" p1_only=").append(p1Only).append(" both_off=").append(bothOff).append(" unknown=").append(unknown).append('\n');
        if (bothActualOn > 0) {
            o.append("FIRST_BOTH_ON_MS=").append(firstBothMs).append(" LAST_BOTH_ON_MS=").append(lastBothMs)
             .append(" observed_window_ms~").append(lastBothMs-firstBothMs+intervalMs).append('\n');
        } else {
            o.append("NO_SIMULTANEOUS_NONZERO_ACTUAL_BRIGHTNESS_OBSERVED\n");
        }
        o.append("\n").append(readFoldTimerInfo());
        return o.toString();
    }

'''
if marker not in s: raise SystemExit('service marker not found')
s = s.replace(marker, method + marker)
svc.write_text(s)

activity = root / 'app/src/main/java/com/displaytoggle/extreme/MainActivity.java'
activity.write_text(r'''package com.displaytoggle.extreme;

import android.app.Activity;
import android.content.*;
import android.content.pm.PackageManager;
import android.os.*;
import android.widget.*;
import rikka.shizuku.Shizuku;

public class MainActivity extends Activity {
    private TextView text;
    private Button capture, timer, copy;
    private String report="";
    private Shizuku.UserServiceArgs args;

    @Override protected void onCreate(Bundle b){
        super.onCreate(b);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(24,24,24,24);
        TextView title=new TextView(this); title.setText("MAGIC V2 — HANDOFF TIMING PROBE"); title.setTextSize(20f);
        TextView info=new TextView(this); info.setText("Test 1: fully open the phone. Press CAPTURE 8s and close it once through the normal ~43° handoff. The Shizuku service keeps sampling even while the active panel changes.\n");
        capture=new Button(this); capture.setText("CAPTURE 8s @ 10ms");
        timer=new Button(this); timer.setText("READ FOLD TIMER INFO");
        copy=new Button(this); copy.setText("COPY REPORT");
        text=new TextView(this); text.setTextIsSelectable(true); text.setTextSize(9f); text.setText("Ready.");
        box.addView(title); box.addView(info); box.addView(capture); box.addView(timer); box.addView(copy); box.addView(text);
        ScrollView sv=new ScrollView(this); sv.addView(box); setContentView(sv);
        capture.setOnClickListener(v->runProbe(true));
        timer.setOnClickListener(v->runProbe(false));
        copy.setOnClickListener(v->{((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("MagicV2 timing report",report)); Toast.makeText(this,"Report copied",Toast.LENGTH_SHORT).show();});
    }

    private void runProbe(boolean captureMode){
        if(!Shizuku.pingBinder()){text.setText("Shizuku is not running.");return;}
        if(Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED){Shizuku.requestPermission(99);text.setText("Grant Shizuku permission, then press again.");return;}
        capture.setEnabled(false); timer.setEnabled(false);
        text.setText(captureMode ? "CAPTURING… Close the phone once now. Wait 8 seconds.\n" : "Reading timer properties…\n");
        args=new Shizuku.UserServiceArgs(new ComponentName(this,DisplayToggleService.class)).daemon(false).processNameSuffix("magicv2_handoff_timing");
        Shizuku.bindUserService(args,new ServiceConnection(){
            @Override public void onServiceConnected(ComponentName n,IBinder b){
                final IDisplayToggleService svc=IDisplayToggleService.Stub.asInterface(b);
                new Thread(()->{
                    String r;
                    try { r=captureMode ? svc.runHandoffTimingProbe(8000,10) : svc.readFoldTimerInfo(); }
                    catch(Throwable e){ r="ERROR: "+e; }
                    final String fr=r;
                    runOnUiThread(()->{report=fr;text.setText(fr);capture.setEnabled(true);timer.setEnabled(true);});
                }).start();
            }
            @Override public void onServiceDisconnected(ComponentName n){runOnUiThread(()->{text.append("\nService disconnected.\n");capture.setEnabled(true);timer.setEnabled(true);});}
        });
    }
}
''')
