from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;\ninterface IDisplayToggleService {\n    int toggleDisplays(int mode, in int[] whitelistDisplayIds);\n    String runHonorProbe();\n}\n''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    @Override
    public String runHonorProbe() {
        StringBuilder out = new StringBuilder();
        out.append("MAGIC V2 - HONOR FOLD API PROBE\n");
        out.append("READ-ONLY / SAFE DIAGNOSTIC\n\n");
        String[] commands = new String[] {
            "id",
            "getprop ro.build.display.id",
            "getprop ro.build.version.release",
            "getprop ro.build.version.sdk",
            "cmd device_state state",
            "cmd device_state print-states",
            "cmd display get-displays",
            "service list | grep -Ei 'fold|display|interaction|surface'",
            "service check fold_screen",
            "service check interaction_display",
            "service call fold_screen 1598968902",
            "service call interaction_display 1598968902",
            "dumpsys fold_screen",
            "dumpsys interaction_display",
            "dumpsys display | grep -E 'DeviceStateToLayoutMap|mDeviceState=|mCurrentLayout=|Display State=|mDisplayId=|mState=|address|port' | head -n 260",
            "dumpsys SurfaceFlinger | grep -E 'pacesetterDisplayId|Display 4630946846403687043|Display 4630946324137792644|layerStack' | head -n 180",
            "settings get global hn_fold_display_mode_prepare",
            "settings get global hn_fold_screen_state",
            "settings get global hn_fold_screen_state_hall",
            "getprop | grep -Ei 'fold|coordination|interaction.display' | head -n 220",
            "cmd -l | grep -Ei 'fold|display|device|interaction'",
            "pm list packages -f | grep -Ei 'honor|hihonor|fold|display' | head -n 220",
            "find /system/framework /system_ext/framework /product/framework /vendor/framework -maxdepth 2 -type f 2>/dev/null | grep -Ei 'honor|hihonor|fold|display|interaction' | head -n 220",
            "find /system /system_ext /product /vendor -maxdepth 4 -type f 2>/dev/null | grep -Ei '/[^/]*(fold|interactiondisplay|displayengine)[^/]*\\.(jar|apk|so)$' | head -n 220"
        };
        for (String cmd : commands) {
            out.append("\n===== ").append(cmd).append(" =====\n");
            out.append(runShell(cmd));
            if (out.length() > 180000) {
                out.append("\n[REPORT TRUNCATED]\n");
                break;
            }
        }
        return out.toString();
    }

    private String runShell(String cmd) {
        StringBuilder sb = new StringBuilder();
        try {
            Process p = new ProcessBuilder("/system/bin/sh", "-c", cmd).redirectErrorStream(true).start();
            java.io.BufferedReader r = new java.io.BufferedReader(new java.io.InputStreamReader(p.getInputStream()));
            String line;
            int chars = 0;
            while ((line = r.readLine()) != null) {
                sb.append(line).append('\n');
                chars += line.length() + 1;
                if (chars > 30000) { sb.append("[section truncated]\n"); break; }
            }
            p.waitFor();
            sb.append("[exit=").append(p.exitValue()).append("]\n");
        } catch (Throwable e) {
            sb.append("ERROR: ").append(e).append('\n');
        }
        return sb.toString();
    }

'''
if marker not in s:
    raise SystemExit('service marker not found')
s = s.replace(marker, method + marker)
svc.write_text(s)

activity = root / 'app/src/main/java/com/displaytoggle/extreme/MainActivity.java'
activity.write_text(r'''package com.displaytoggle.extreme;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.ServiceConnection;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.IBinder;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import rikka.shizuku.Shizuku;

public class MainActivity extends Activity {
    private TextView text;
    private Button run, copy;
    private String report = "";

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(24,24,24,24);
        TextView title = new TextView(this);
        title.setText("MAGIC V2 — HONOR FOLD API PROBE");
        title.setTextSize(20f);
        TextView info = new TextView(this);
        info.setText("Safe/read-only probe. It does NOT change display state and does NOT call unknown Honor Binder transactions. Start Shizuku first, then run the probe.\n");
        run = new Button(this); run.setText("RUN SAFE HONOR PROBE");
        copy = new Button(this); copy.setText("COPY REPORT");
        text = new TextView(this); text.setTextSize(11f); text.setTextIsSelectable(true); text.setText("Ready.");
        box.addView(title); box.addView(info); box.addView(run); box.addView(copy); box.addView(text);
        ScrollView sv = new ScrollView(this); sv.addView(box); setContentView(sv);
        run.setOnClickListener(v -> startProbe());
        copy.setOnClickListener(v -> {
            ClipboardManager cm=(ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
            cm.setPrimaryClip(ClipData.newPlainText("MagicV2 Honor probe", report));
            android.widget.Toast.makeText(this,"Report copied",android.widget.Toast.LENGTH_SHORT).show();
        });
    }

    private void startProbe() {
        try {
            if (!Shizuku.pingBinder()) { text.setText("Shizuku is not running."); return; }
            if (Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED) {
                text.setText("Grant Shizuku permission, then press RUN again.");
                Shizuku.requestPermission(97); return;
            }
            run.setEnabled(false); text.setText("Running read-only Honor probe…\nThis can take 10–30 seconds.");
            Shizuku.UserServiceArgs args = new Shizuku.UserServiceArgs(new ComponentName(this, DisplayToggleService.class))
                    .daemon(false).processNameSuffix("magicv2_honor_probe");
            Shizuku.bindUserService(args, new ServiceConnection() {
                @Override public void onServiceConnected(ComponentName n, IBinder b) {
                    new Thread(() -> {
                        String r;
                        try { r = IDisplayToggleService.Stub.asInterface(b).runHonorProbe(); }
                        catch(Throwable e) { r = "ERROR: " + e; }
                        final String fr = r;
                        runOnUiThread(() -> { report=fr; text.setText(fr); run.setEnabled(true); });
                    }).start();
                }
                @Override public void onServiceDisconnected(ComponentName n) {
                    runOnUiThread(() -> { text.append("\nService disconnected."); run.setEnabled(true); });
                }
            });
        } catch(Throwable e) { text.setText("START ERROR: " + e); run.setEnabled(true); }
    }
}
''')
