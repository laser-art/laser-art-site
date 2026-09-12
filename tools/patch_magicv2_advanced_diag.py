from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;
interface IDisplayToggleService {
    int toggleDisplays(int mode, in int[] whitelistDisplayIds);
    String runDiagnostics();
}
''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    @Override
    public String runDiagnostics() {
        StringBuilder out = new StringBuilder();
        out.append("Magic V2 advanced system diagnostic\n");
        out.append("SDK=").append(Build.VERSION.SDK_INT).append("\n\n");
        String[] tests = new String[] {
            "id",
            "dumpsys SurfaceFlinger --display-id 2>&1",
            "dumpsys SurfaceFlinger 2>&1 | grep -Ei 'physical|display|panel|internal|external|activeMode|HWC|connector' | head -n 260",
            "dumpsys display 2>&1 | grep -Ei 'DisplayDeviceInfo|uniqueId|address|mDisplayId|displayId|state|modeId|supportedModes|fold|deviceState|port|type=' | head -n 280",
            "cmd display help 2>&1 | head -n 140",
            "cmd display get-displays 2>&1 | head -n 180",
            "service list 2>&1 | grep -Ei 'display|surface|fold|hinge|honor|hw' | head -n 180",
            "getprop 2>&1 | grep -Ei 'fold|hinge|display|panel|screen' | head -n 220",
            "settings list global 2>&1 | grep -Ei 'fold|hinge|display|screen' | head -n 160",
            "settings list system 2>&1 | grep -Ei 'fold|hinge|display|screen' | head -n 160",
            "ls -la /sys/class/drm 2>&1 | head -n 160",
            "for x in /sys/class/drm/*/status; do echo ===$x===; cat $x 2>&1; done | head -n 180",
            "ls -la /sys/class/graphics 2>&1 | head -n 120",
            "ls -la /sys/class/backlight 2>&1 | head -n 120",
            "find /sys -maxdepth 4 \\( -iname '*panel*' -o -iname '*fold*' -o -iname '*hinge*' \\) 2>/dev/null | head -n 180"
        };
        for (String cmd : tests) {
            out.append("\n===== ").append(cmd).append(" =====\n");
            out.append(runShell(cmd));
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
                if (chars > 60000) { sb.append("[truncated]\n"); break; }
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
import android.hardware.display.DisplayManager;
import android.os.Bundle;
import android.os.IBinder;
import android.view.Display;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import rikka.shizuku.Shizuku;

public class MainActivity extends Activity {
    private TextView text;
    private Button run, copy;
    private Shizuku.UserServiceArgs args;
    private String report = "";

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        args = new Shizuku.UserServiceArgs(new ComponentName(this, DisplayToggleService.class))
                .daemon(false).processNameSuffix("magicv2_advanced_diag");
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(24,24,24,24);
        TextView title = new TextView(this);
        title.setText("MAGIC V2 - ADVANCED DISPLAY DIAGNOSTIC");
        title.setTextSize(20f);
        run = new Button(this);
        run.setText("RUN FULL DIAGNOSTIC");
        copy = new Button(this);
        copy.setText("COPY REPORT");
        text = new TextView(this);
        text.setTextSize(12f);
        text.setTextIsSelectable(true);
        box.addView(title); box.addView(run); box.addView(copy); box.addView(text);
        ScrollView sv = new ScrollView(this); sv.addView(box); setContentView(sv);
        run.setOnClickListener(v -> startDiag());
        copy.setOnClickListener(v -> {
            ClipboardManager cm=(ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
            cm.setPrimaryClip(ClipData.newPlainText("MagicV2 diagnostic", report));
            android.widget.Toast.makeText(this,"Report copied",android.widget.Toast.LENGTH_SHORT).show();
        });
        if (Shizuku.pingBinder() && Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED) {
            Shizuku.requestPermission(77);
        }
        updateHeader();
    }

    private void updateHeader() {
        StringBuilder sb=new StringBuilder();
        sb.append("Shizuku: ").append(Shizuku.pingBinder()?"RUNNING":"STOPPED").append("\n");
        sb.append("Permission: ").append(Shizuku.checkSelfPermission()==0?"GRANTED":"NO").append("\n\n");
        DisplayManager dm=getSystemService(DisplayManager.class);
        Display[] ds=dm.getDisplays();
        sb.append("DisplayManager count=").append(ds.length).append("\n");
        for(Display d:ds){
            Display.Mode m=d.getMode();
            sb.append("ID ").append(d.getDisplayId()).append(" ").append(d.getName())
              .append(" state=").append(d.getState()).append(" mode=")
              .append(m.getPhysicalWidth()).append("x").append(m.getPhysicalHeight()).append("\n");
        }
        sb.append("\nPress RUN FULL DIAGNOSTIC. Read-only: no screen power commands are sent.\n");
        text.setText(sb.toString());
    }

    private void startDiag() {
        if (!Shizuku.pingBinder() || Shizuku.checkSelfPermission()!=0) {
            updateHeader();
            android.widget.Toast.makeText(this,"Shizuku permission required",android.widget.Toast.LENGTH_LONG).show();
            return;
        }
        run.setEnabled(false);
        text.setText("Running tests... this can take 10-30 seconds.\n");
        Shizuku.bindUserService(args, new ServiceConnection() {
            @Override public void onServiceConnected(ComponentName n, IBinder b) {
                new Thread(() -> {
                    String r;
                    try { r=IDisplayToggleService.Stub.asInterface(b).runDiagnostics(); }
                    catch(Exception e){ r="ERROR: "+e; }
                    final String fr=r;
                    runOnUiThread(() -> { report=fr; text.setText(fr); run.setEnabled(true); });
                }).start();
            }
            @Override public void onServiceDisconnected(ComponentName n) {}
        });
    }
}
''')
