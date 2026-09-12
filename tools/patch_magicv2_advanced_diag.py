from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;
interface IDisplayToggleService {
    int toggleDisplays(int mode, in int[] whitelistDisplayIds);
    String runStateSwitchTest();
}
''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    @Override
    public String runStateSwitchTest() {
        StringBuilder out = new StringBuilder();
        out.append("MAGIC V2 STATE 4 / 8 SWITCH TEST\n\n");
        String cur = runShell("cmd device_state state 2>&1");
        out.append("START STATE:\n").append(cur).append('\n');
        if (!cur.contains("identifier=1")) {
            out.append("STOP: phone must be fully open in STATE_FLAT (1).\n");
            return out.toString();
        }

        int[] states = new int[]{4, 8};
        String[] names = new String[]{"STATE_CLOSED", "STATE_REAR"};
        for (int i = 0; i < states.length; i++) {
            int st = states[i];
            out.append("\n===== TEST ").append(st).append(" ").append(names[i]).append(" =====\n");
            out.append(runShell("cmd device_state state " + st + " 2>&1"));
            sleepMs(1800);
            out.append(runShell("cmd device_state state 2>&1"));
            out.append(runShell("dumpsys display 2>&1 | grep -E 'mCurrentLayout=|mDeviceState=|Display State=|mDisplayId=|mState=|mCommittedState=' | head -n 120"));
            out.append(runShell("dumpsys SurfaceFlinger 2>&1 | grep -E 'pacesetterDisplayId|Display 4630946846403687043 \\(active|inactive\\)|Display 4630946324137792644 \\(active|inactive\\)' | head -n 60"));
            out.append("LOOK AT COVER SCREEN NOW - holding 4 seconds.\n");
            sleepMs(4000);
            out.append("RESET after state ").append(st).append("\n");
            out.append(runShell("cmd device_state state reset 2>&1"));
            sleepMs(1600);
            out.append(runShell("cmd device_state state 2>&1"));
        }

        out.append("\n===== FINAL =====\n");
        out.append(runShell("dumpsys display 2>&1 | grep -E 'mCurrentLayout=|mDeviceState=|Display State=|mDisplayId=|mState=|mCommittedState=' | head -n 120"));
        out.append("\nTest complete.\n");
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
                .daemon(false).processNameSuffix("magicv2_state_switch");
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(24,24,24,24);
        TextView title = new TextView(this);
        title.setText("MAGIC V2 - STATE 4 / 8 TEST");
        title.setTextSize(20f);
        TextView info = new TextView(this);
        info.setText("Keep the phone FULLY OPEN. The app will test STATE_CLOSED (4), reset, then STATE_REAR (8), reset. Watch the COVER screen during both tests.\n");
        run = new Button(this); run.setText("RUN STATE 4 / 8 TEST");
        copy = new Button(this); copy.setText("COPY REPORT");
        text = new TextView(this); text.setTextSize(12f); text.setTextIsSelectable(true);
        box.addView(title); box.addView(info); box.addView(run); box.addView(copy); box.addView(text);
        ScrollView sv = new ScrollView(this); sv.addView(box); setContentView(sv);
        run.setOnClickListener(v -> startTest());
        copy.setOnClickListener(v -> {
            ClipboardManager cm=(ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
            cm.setPrimaryClip(ClipData.newPlainText("MagicV2 state switch", report));
            android.widget.Toast.makeText(this,"Report copied",android.widget.Toast.LENGTH_SHORT).show();
        });
        if (Shizuku.pingBinder() && Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED) Shizuku.requestPermission(91);
        text.setText("Shizuku=" + (Shizuku.pingBinder()?"RUNNING":"STOPPED") + " permission=" + (Shizuku.checkSelfPermission()==0?"GRANTED":"NO"));
    }

    private void startTest() {
        if (!Shizuku.pingBinder() || Shizuku.checkSelfPermission()!=0) { text.setText("Shizuku permission required"); return; }
        run.setEnabled(false);
        text.setText("Testing states 4 and 8... keep phone fully open and watch cover screen.\n");
        Shizuku.bindUserService(args, new ServiceConnection() {
            @Override public void onServiceConnected(ComponentName n, IBinder b) {
                new Thread(() -> {
                    String r;
                    try { r=IDisplayToggleService.Stub.asInterface(b).runStateSwitchTest(); }
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
