from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;
interface IDisplayToggleService {
    int toggleDisplays(int mode, in int[] whitelistDisplayIds);
    String runDualScreenTest();
}
''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    @Override
    public String runDualScreenTest() {
        final long INNER_PHYS = 4630946846403687043L;
        final long OUTER_PHYS = 4630946324137792644L;
        StringBuilder out = new StringBuilder();
        out.append("MAGIC V2 SAFE DUAL-SCREEN TEST\n\n");
        out.append("Known physical panels:\n");
        out.append("INNER = ").append(INNER_PHYS).append(" port 131 / HWC 0\n");
        out.append("OUTER = ").append(OUTER_PHYS).append(" port 132 / HWC 3\n\n");

        String before = runShell("dumpsys display | grep -E 'mCurrentLayout=|DisplayDeviceInfo|state (ON|OFF)|mDisplayId=|mDeviceState=' | head -n 80");
        out.append("===== BEFORE =====\n").append(before).append('\n');

        String current = runShell("cmd display get-displays");
        boolean open = current.contains("real 2156 x 2344");
        boolean closed = current.contains("real 1060 x 2376");
        out.append("Detected logical screen: ").append(open ? "OPEN/INNER" : (closed ? "CLOSED/OUTER" : "UNKNOWN")).append("\n\n");

        if (!open) {
            out.append("STOP: Open the phone fully before running this test.\n");
            out.append("This protects the currently visible cover display from being touched.\n");
            return out.toString();
        }

        out.append("===== TEST 1: cmd display enable-display 1 =====\n");
        out.append(runShell("cmd display enable-display 1 2>&1"));
        sleepMs(1800);
        String afterCmd = runShell("dumpsys display | grep -E 'DisplayDeviceInfo|mDisplayId=|mState=|mCommittedState=|mCurrentLayout=' | head -n 100");
        out.append(afterCmd).append('\n');
        boolean cmdSuccess = afterCmd.contains("mDisplayId=1") && afterCmd.contains("mState=ON");
        out.append("TEST1_RESULT=").append(cmdSuccess ? "POSSIBLE_SUCCESS" : "NO_CONFIRMED_ON").append("\n\n");

        if (!cmdSuccess) {
            out.append("===== TEST 2: direct SurfaceControl power ON outer physical panel =====\n");
            out.append(setPhysicalPower(OUTER_PHYS, 2));
            sleepMs(1800);
            String sf = runShell("dumpsys SurfaceFlinger | grep -E 'Display 4630946324137792644|active\\)|inactive\\)|pacesetterDisplayId' | head -n 40");
            out.append(sf).append('\n');
            out.append("TEST2 sent physical power mode ON to OUTER.\n\n");
        }

        out.append("Holding test state for 5 seconds so you can look at the cover screen...\n");
        sleepMs(5000);

        out.append("\n===== RESTORE =====\n");
        out.append(runShell("cmd display power-reset 1 2>&1"));
        out.append(setPhysicalPower(OUTER_PHYS, 0));
        sleepMs(1000);
        out.append(runShell("dumpsys display | grep -E 'mCurrentLayout=|DisplayDeviceInfo|mDisplayId=|mState=|mCommittedState=' | head -n 100"));

        out.append("\n===== HONOR FOLD SERVICE (READ ONLY) =====\n");
        out.append(runShell("dumpsys fold_screen 2>&1 | head -n 220"));
        out.append("\n===== FOLD SETTINGS =====\n");
        out.append(runShell("settings list global | grep -E 'hn_fold|FoldScreen'"));
        return out.toString();
    }

    private String setPhysicalPower(long physicalId, int mode) {
        StringBuilder sb = new StringBuilder();
        try {
            Class<?> classLoaderFactoryClass = Class.forName("com.android.internal.os.ClassLoaderFactory");
            java.lang.reflect.Method createClassLoader = classLoaderFactoryClass.getDeclaredMethod(
                    "createClassLoader", String.class, String.class, String.class,
                    ClassLoader.class, int.class, boolean.class, String.class);
            ClassLoader cl = (ClassLoader) createClassLoader.invoke(null,
                    "/system/framework/services.jar", null, null,
                    ClassLoader.getSystemClassLoader(), 0, true, null);
            Class<?> displayControlClass = cl.loadClass("com.android.server.display.DisplayControl");
            java.lang.reflect.Method loadLib = Runtime.class.getDeclaredMethod("loadLibrary0", Class.class, String.class);
            loadLib.setAccessible(true);
            try { loadLib.invoke(Runtime.getRuntime(), displayControlClass, "android_servers"); } catch (Throwable ignored) {}
            java.lang.reflect.Method getToken = displayControlClass.getMethod("getPhysicalDisplayToken", long.class);
            android.os.IBinder token = (android.os.IBinder) getToken.invoke(null, physicalId);
            if (token == null) return "Physical token is NULL for " + physicalId + "\n";
            Class<?> sc = Class.forName("android.view.SurfaceControl");
            java.lang.reflect.Method set = sc.getMethod("setDisplayPowerMode", android.os.IBinder.class, int.class);
            set.invoke(null, token, mode);
            return "SurfaceControl setDisplayPowerMode(" + physicalId + ", " + mode + ") OK\n";
        } catch (Throwable e) {
            return "SurfaceControl ERROR: " + e + "\n";
        }
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
                if (chars > 50000) { sb.append("[truncated]\n"); break; }
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
                .daemon(false).processNameSuffix("magicv2_dual_test");

        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(24,24,24,24);
        TextView title = new TextView(this);
        title.setText("MAGIC V2 - DUAL SCREEN TEST");
        title.setTextSize(20f);
        TextView info = new TextView(this);
        info.setText("IMPORTANT: open the phone fully before the test.\nThe app will try to wake ONLY the inactive cover panel for 5 seconds, then restore the normal state automatically.\n");
        run = new Button(this); run.setText("RUN SAFE TEST CHAIN");
        copy = new Button(this); copy.setText("COPY REPORT");
        text = new TextView(this); text.setTextSize(12f); text.setTextIsSelectable(true);
        box.addView(title); box.addView(info); box.addView(run); box.addView(copy); box.addView(text);
        ScrollView sv = new ScrollView(this); sv.addView(box); setContentView(sv);

        run.setOnClickListener(v -> startTest());
        copy.setOnClickListener(v -> {
            ClipboardManager cm=(ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
            cm.setPrimaryClip(ClipData.newPlainText("MagicV2 dual display report", report));
            android.widget.Toast.makeText(this,"Report copied",android.widget.Toast.LENGTH_SHORT).show();
        });
        if (Shizuku.pingBinder() && Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED) Shizuku.requestPermission(88);
        text.setText("Shizuku=" + (Shizuku.pingBinder()?"RUNNING":"STOPPED") + " permission=" + (Shizuku.checkSelfPermission()==0?"GRANTED":"NO"));
    }

    private void startTest() {
        if (!Shizuku.pingBinder() || Shizuku.checkSelfPermission()!=0) {
            text.setText("Shizuku permission required"); return;
        }
        run.setEnabled(false);
        text.setText("Testing... Keep the phone FULLY OPEN. Watch the cover screen during the next 10 seconds.\n");
        Shizuku.bindUserService(args, new ServiceConnection() {
            @Override public void onServiceConnected(ComponentName n, IBinder b) {
                new Thread(() -> {
                    String r;
                    try { r=IDisplayToggleService.Stub.asInterface(b).runDualScreenTest(); }
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
