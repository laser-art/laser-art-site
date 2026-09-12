from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;\ninterface IDisplayToggleService {\n    int toggleDisplays(int mode, in int[] whitelistDisplayIds);\n    String runDualProbe(int mode);\n}\n''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    @Override
    public String runDualProbe(int mode) {
        StringBuilder out = new StringBuilder();
        out.append("MAGIC V2 DUAL SCREEN PROBE\n");
        out.append("uid=").append(run("id")).append("\n");
        if (mode == 0) {
            out.append(snapshot("SNAPSHOT"));
            return out.toString();
        }
        if (mode == 1) {
            // INNER ONLY
            out.append(run("cmd device_state state reset"));
            out.append(run("cmd device_state state 1"));
            sleep(700);
            out.append(snapshot("INNER ONLY"));
            return out.toString();
        }
        if (mode == 2) {
            // OUTER ONLY
            out.append(run("cmd device_state state reset"));
            out.append(run("cmd device_state state 4"));
            sleep(700);
            out.append(snapshot("OUTER ONLY"));
            return out.toString();
        }
        if (mode == 3) {
            out.append("\n=== SAFE BOTH-DISPLAY RECIPES ===\n");
            // Recipe A: current layout + enable both logical displays.
            out.append(run("cmd device_state state reset"));
            out.append(run("cmd display enable-display 0"));
            out.append(run("cmd display enable-display 1"));
            out.append(run("cmd display power-reset 0"));
            out.append(run("cmd display power-reset 1"));
            sleep(900);
            String a = snapshot("RECIPE A: RESET + ENABLE 0/1 + POWER RESET");
            out.append(a);
            if (bothActive(a)) { out.append("\nSUCCESS: BOTH PHYSICAL DISPLAYS ACTIVE. LEFT AS-IS.\n"); return out.toString(); }

            // Recipe B: Honor coordination display mode, then enable both.
            out.append(run("cmd device_state state 14"));
            sleep(500);
            out.append(run("cmd display enable-display 0"));
            out.append(run("cmd display enable-display 1"));
            out.append(run("cmd display power-reset 0"));
            out.append(run("cmd display power-reset 1"));
            sleep(900);
            String b = snapshot("RECIPE B: STATE 14 + ENABLE 0/1");
            out.append(b);
            if (bothActive(b)) { out.append("\nSUCCESS: BOTH PHYSICAL DISPLAYS ACTIVE. LEFT AS-IS.\n"); return out.toString(); }

            // Recipe C: cover state, then explicitly enable the inactive logical display.
            out.append(run("cmd device_state state 4"));
            sleep(500);
            out.append(run("cmd display enable-display 0"));
            out.append(run("cmd display enable-display 1"));
            out.append(run("cmd display power-reset 0"));
            out.append(run("cmd display power-reset 1"));
            sleep(900);
            String c = snapshot("RECIPE C: STATE 4 + ENABLE 0/1");
            out.append(c);
            if (bothActive(c)) { out.append("\nSUCCESS: BOTH PHYSICAL DISPLAYS ACTIVE. LEFT AS-IS.\n"); return out.toString(); }

            out.append("\nNO SAFE RECIPE PRODUCED TWO ACTIVE PHYSICAL DISPLAYS. RESETTING.\n");
            out.append(run("cmd device_state state reset"));
            sleep(500);
            out.append(snapshot("FINAL RESET"));
            return out.toString();
        }
        if (mode == 4) {
            out.append(run("cmd device_state state reset"));
            sleep(500);
            out.append(snapshot("RESET"));
            return out.toString();
        }
        return "Unknown mode";
    }

    private boolean bothActive(String s) {
        return s.contains("4630946846403687043 (active") && s.contains("4630946324137792644 (active");
    }

    private String snapshot(String title) {
        StringBuilder x = new StringBuilder();
        x.append("\n===== ").append(title).append(" =====\n");
        x.append(run("cmd device_state state"));
        x.append(run("cmd display get-displays"));
        x.append(run("dumpsys display | grep -E 'mDeviceState=|mCurrentLayout=|mDisplayId=|Display State=|mState=' | head -n 180"));
        x.append(run("dumpsys SurfaceFlinger | grep -E 'pacesetterDisplayId|Display 4630946846403687043 \\(active|inactive\\)|Display 4630946324137792644 \\(active|inactive\\)' | head -n 80"));
        return x.toString();
    }

    private String run(String cmd) {
        StringBuilder sb = new StringBuilder();
        sb.append("$ ").append(cmd).append('\n');
        try {
            Process p = new ProcessBuilder("/system/bin/sh", "-c", cmd + " 2>&1").redirectErrorStream(true).start();
            java.io.BufferedReader r = new java.io.BufferedReader(new java.io.InputStreamReader(p.getInputStream()));
            String line;
            int chars = 0;
            while ((line = r.readLine()) != null) {
                sb.append(line).append('\n');
                chars += line.length() + 1;
                if (chars > 60000) { sb.append("[truncated]\n"); break; }
            }
            p.waitFor();
            sb.append("[exit=").append(p.exitValue()).append("]\n");
        } catch (Throwable e) {
            sb.append("ERROR: ").append(e).append('\n');
        }
        return sb.toString();
    }

    private void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException ignored) {} }

'''
if marker not in s:
    raise SystemExit('service marker not found')
s = s.replace(marker, method + marker)
svc.write_text(s)

activity = root / 'app/src/main/java/com/displaytoggle/extreme/MainActivity.java'
activity.write_text(r'''package com.displaytoggle.extreme;

import android.app.Activity;
import android.content.*;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.IBinder;
import android.widget.*;
import rikka.shizuku.Shizuku;

public class MainActivity extends Activity {
    private TextView status;
    private Button both, inner, outer, snap, reset, copy;
    private String report = "";

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(24,24,24,24);
        TextView title = new TextView(this); title.setText("MAGIC V2 — DUAL SCREEN PROBE"); title.setTextSize(21f);
        TextView info = new TextView(this); info.setText("Goal: keep INNER + OUTER physical panels active at the same time. No hinge-angle logic. FORCE BOTH only uses documented shell commands and state 14/4 combinations; no hidden binder calls or native SurfaceControl.");
        both = btn("FORCE BOTH — SAFE RECIPES");
        inner = btn("INNER ONLY");
        outer = btn("OUTER ONLY");
        snap = btn("SNAPSHOT");
        reset = btn("RESET NORMAL");
        copy = btn("COPY REPORT");
        status = new TextView(this); status.setTextSize(12f); status.setTextIsSelectable(true); status.setText("App ready. Start Shizuku, then use FORCE BOTH.");
        box.addView(title); box.addView(info); box.addView(both); box.addView(inner); box.addView(outer); box.addView(snap); box.addView(reset); box.addView(copy); box.addView(status);
        ScrollView sv = new ScrollView(this); sv.addView(box); setContentView(sv);
        both.setOnClickListener(v -> runProbe(3));
        inner.setOnClickListener(v -> runProbe(1));
        outer.setOnClickListener(v -> runProbe(2));
        snap.setOnClickListener(v -> runProbe(0));
        reset.setOnClickListener(v -> runProbe(4));
        copy.setOnClickListener(v -> { ((android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(android.content.ClipData.newPlainText("MagicV2 dual probe", report)); Toast.makeText(this,"Report copied",Toast.LENGTH_SHORT).show(); });
    }

    private Button btn(String s){ Button b=new Button(this); b.setText(s); return b; }

    private void runProbe(int mode) {
        if (!Shizuku.pingBinder()) { status.setText("Shizuku is not running."); return; }
        if (Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED) { Shizuku.requestPermission(97); status.setText("Grant Shizuku permission, then press the button again."); return; }
        setButtons(false);
        status.setText(mode==3 ? "Trying safe dual-screen recipes… Watch BOTH panels for the next few seconds." : "Running…");
        Shizuku.UserServiceArgs args = new Shizuku.UserServiceArgs(new ComponentName(this, DisplayToggleService.class)).daemon(false).processNameSuffix("magicv2_dual_probe");
        Shizuku.bindUserService(args, new ServiceConnection() {
            @Override public void onServiceConnected(ComponentName n, IBinder binder) {
                new Thread(() -> {
                    String r;
                    try { r = IDisplayToggleService.Stub.asInterface(binder).runDualProbe(mode); }
                    catch (Throwable e) { r = "ERROR: " + e; }
                    final String rr=r;
                    runOnUiThread(() -> { report=rr; status.setText(rr); setButtons(true); });
                }).start();
            }
            @Override public void onServiceDisconnected(ComponentName n) { runOnUiThread(() -> { status.append("\nService disconnected."); setButtons(true); }); }
        });
    }

    private void setButtons(boolean e){ both.setEnabled(e); inner.setEnabled(e); outer.setEnabled(e); snap.setEnabled(e); reset.setEnabled(e); copy.setEnabled(e); }
}
''')
