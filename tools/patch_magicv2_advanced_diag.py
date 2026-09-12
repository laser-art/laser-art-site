from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;
interface IDisplayToggleService {
    int toggleDisplays(int mode, in int[] whitelistDisplayIds);
    String runStateProbe();
}
''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    @Override
    public String runStateProbe() {
        StringBuilder out = new StringBuilder();
        out.append("MAGIC V2 DEVICE-STATE / HONOR FOLD PROBE\n\n");

        out.append("===== CURRENT DEVICE STATE =====\n");
        out.append(runShell("cmd device_state state 2>&1"));
        out.append("\n===== SUPPORTED STATES =====\n");
        out.append(runShell("cmd device_state print-states 2>&1"));
        out.append("\n===== SUPPORTED STATE IDS =====\n");
        out.append(runShell("cmd device_state print-states-simple 2>&1"));
        out.append("\n===== HONOR FOLD SERVICE DUMP =====\n");
        out.append(runShell("dumpsys fold_screen 2>&1 | head -n 350"));
        out.append("\n===== DISPLAY LAYOUT MAP =====\n");
        out.append(runShell("dumpsys display 2>&1 | sed -n '/DeviceStateToLayoutMap:/,/DisplayStates:/p' | head -n 220"));

        out.append("\n===== TEMP TEST: DEVICE STATE -1 =====\n");
        out.append("Android will reject this if -1 is not requestable. If accepted, we inspect whether the fallback layout enables both panels.\n");
        out.append(runShell("cmd device_state state -1 2>&1"));
        sleepMs(1800);
        out.append(runShell("cmd device_state state 2>&1"));
        out.append(runShell("dumpsys display 2>&1 | grep -E 'mCurrentLayout=|mDeviceState=|Display State=|mDisplayId=|mState=|mCommittedState=' | head -n 140"));
        out.append(runShell("dumpsys SurfaceFlinger 2>&1 | grep -E 'pacesetterDisplayId|Display 4630946846403687043 \\(active|inactive\\)|Display 4630946324137792644 \\(active|inactive\\)' | head -n 60"));

        out.append("\n===== RESET DEVICE STATE =====\n");
        out.append(runShell("cmd device_state state reset 2>&1"));
        sleepMs(1000);
        out.append(runShell("cmd device_state state 2>&1"));
        out.append("\nProbe complete.\n");
        return out.toString();
    }

    private void sleepMs(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException ignored) {}
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
                if (chars > 70000) { sb.append("[truncated]\n"); break; }
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
    private Shizuku.UserServiceArgs args;
    private String report = "";

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        args = new Shizuku.UserServiceArgs(new ComponentName(this, DisplayToggleService.class))
                .daemon(false).processNameSuffix("magicv2_state_probe");
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(24,24,24,24);
        TextView title = new TextView(this);
        title.setText("MAGIC V2 - DEVICE STATE PROBE");
        title.setTextSize(20f);
        TextView info = new TextView(this);
        info.setText("Keep the phone fully open. This reads Honor/Android fold states, then briefly tries state -1. Android rejects it if unsupported. The app resets the state automatically.\n");
        run = new Button(this); run.setText("RUN STATE PROBE");
        copy = new Button(this); copy.setText("COPY REPORT");
        text = new TextView(this); text.setTextSize(12f); text.setTextIsSelectable(true);
        box.addView(title); box.addView(info); box.addView(run); box.addView(copy); box.addView(text);
        ScrollView sv = new ScrollView(this); sv.addView(box); setContentView(sv);
        run.setOnClickListener(v -> startTest());
        copy.setOnClickListener(v -> {
            ClipboardManager cm=(ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
            cm.setPrimaryClip(ClipData.newPlainText("MagicV2 state probe", report));
            android.widget.Toast.makeText(this,"Report copied",android.widget.Toast.LENGTH_SHORT).show();
        });
        if (Shizuku.pingBinder() && Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED) Shizuku.requestPermission(90);
        text.setText("Shizuku=" + (Shizuku.pingBinder()?"RUNNING":"STOPPED") + " permission=" + (Shizuku.checkSelfPermission()==0?"GRANTED":"NO"));
    }

    private void startTest() {
        if (!Shizuku.pingBinder() || Shizuku.checkSelfPermission()!=0) { text.setText("Shizuku permission required"); return; }
        run.setEnabled(false);
        text.setText("Probing device states... keep phone fully open.\n");
        Shizuku.bindUserService(args, new ServiceConnection() {
            @Override public void onServiceConnected(ComponentName n, IBinder b) {
                new Thread(() -> {
                    String r;
                    try { r=IDisplayToggleService.Stub.asInterface(b).runStateProbe(); }
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
