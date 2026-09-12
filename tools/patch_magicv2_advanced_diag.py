from pathlib import Path

root = Path('displaytoggle')

# Give this tester a fresh app id so old Shizuku user-service processes from previous
# diagnostic APKs cannot collide with it.
gradle = root / 'app/build.gradle.kts'
gs = gradle.read_text()
gs = gs.replace('applicationId = "com.displaytoggle.extreme"', 'applicationId = "com.magicv2.stateswitchtester"')
gradle.write_text(gs)

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;
interface IDisplayToggleService {
    int toggleDisplays(int mode, in int[] whitelistDisplayIds);
    String runSingleStateTest(int stateId);
}
''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    @Override
    public String runSingleStateTest(int stateId) {
        StringBuilder out = new StringBuilder();
        out.append("MAGIC V2 SINGLE DEVICE-STATE TEST\n\n");
        out.append("Requested state=").append(stateId).append("\n");
        String cur = runShell("cmd device_state state 2>&1");
        out.append("START STATE:\n").append(cur).append('\n');
        if (!cur.contains("identifier=1")) {
            out.append("STOP: phone must be fully open in STATE_FLAT (1).\n");
            return out.toString();
        }
        if (stateId != 4 && stateId != 8) {
            out.append("STOP: only state 4 or 8 is allowed by this tester.\n");
            return out.toString();
        }

        out.append("\n===== APPLY STATE ").append(stateId).append(" =====\n");
        out.append(runShell("cmd device_state state " + stateId + " 2>&1"));
        sleepMs(1200);
        out.append(runShell("cmd device_state state 2>&1"));
        out.append(runShell("dumpsys display 2>&1 | grep -E 'mCurrentLayout=|mDeviceState=|Display State=|mDisplayId=|mState=|mCommittedState=' | head -n 140"));
        out.append(runShell("dumpsys SurfaceFlinger 2>&1 | grep -E 'pacesetterDisplayId|Display 4630946846403687043 \\(active|inactive\\)|Display 4630946324137792644 \\(active|inactive\\)' | head -n 80"));
        out.append("\nHOLDING 4 SECONDS - look at the cover screen now.\n");
        sleepMs(4000);

        out.append("\n===== RESET =====\n");
        out.append(runShell("cmd device_state state reset 2>&1"));
        sleepMs(1200);
        out.append(runShell("cmd device_state state 2>&1"));
        out.append(runShell("dumpsys SurfaceFlinger 2>&1 | grep -E 'pacesetterDisplayId|Display 4630946846403687043 \\(active|inactive\\)|Display 4630946324137792644 \\(active|inactive\\)' | head -n 80"));
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
    private Button test4, test8, copy;
    private Shizuku.UserServiceArgs args;
    private String report = "";

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        args = new Shizuku.UserServiceArgs(new ComponentName(this, DisplayToggleService.class))
                .daemon(false).processNameSuffix("magicv2_state_isolated");
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(24,24,24,24);
        TextView title = new TextView(this);
        title.setText("MAGIC V2 - ISOLATED STATE TESTER");
        title.setTextSize(20f);
        TextView info = new TextView(this);
        info.setText("Phone must stay FULLY OPEN. Nothing runs automatically. Test state 4 first, then state 8 separately. Each test resets automatically after 4 seconds.\n");
        test4 = new Button(this); test4.setText("TEST STATE 4 - CLOSED");
        test8 = new Button(this); test8.setText("TEST STATE 8 - REAR");
        copy = new Button(this); copy.setText("COPY REPORT");
        text = new TextView(this); text.setTextSize(12f); text.setTextIsSelectable(true);
        box.addView(title); box.addView(info); box.addView(test4); box.addView(test8); box.addView(copy); box.addView(text);
        ScrollView sv = new ScrollView(this); sv.addView(box); setContentView(sv);

        test4.setOnClickListener(v -> startTest(4));
        test8.setOnClickListener(v -> startTest(8));
        copy.setOnClickListener(v -> {
            ClipboardManager cm=(ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
            cm.setPrimaryClip(ClipData.newPlainText("MagicV2 isolated state test", report));
            android.widget.Toast.makeText(this,"Report copied",android.widget.Toast.LENGTH_SHORT).show();
        });
        if (Shizuku.pingBinder() && Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED) Shizuku.requestPermission(92);
        text.setText("App launched OK.\nShizuku=" + (Shizuku.pingBinder()?"RUNNING":"STOPPED") + " permission=" + (Shizuku.checkSelfPermission()==0?"GRANTED":"NO"));
    }

    private void startTest(int state) {
        if (!Shizuku.pingBinder() || Shizuku.checkSelfPermission()!=0) {
            text.setText("Shizuku permission required. Open Shizuku and grant this NEW app permission."); return;
        }
        test4.setEnabled(false); test8.setEnabled(false);
        text.setText("Testing state " + state + "... keep phone fully open and look at the cover screen.\n");
        Shizuku.bindUserService(args, new ServiceConnection() {
            @Override public void onServiceConnected(ComponentName n, IBinder b) {
                new Thread(() -> {
                    String r;
                    try { r=IDisplayToggleService.Stub.asInterface(b).runSingleStateTest(state); }
                    catch(Exception e){ r="ERROR: "+e; }
                    final String fr=r;
                    runOnUiThread(() -> { report=fr; text.setText(fr); test4.setEnabled(true); test8.setEnabled(true); });
                }).start();
            }
            @Override public void onServiceDisconnected(ComponentName n) {}
        });
    }
}
''')
