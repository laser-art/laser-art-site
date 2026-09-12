from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;\ninterface IDisplayToggleService {\n    int toggleDisplays(int mode, in int[] whitelistDisplayIds);\n    String copyHnFoldScreen();\n}\n''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    @Override
    public String copyHnFoldScreen() {
        StringBuilder out = new StringBuilder();
        String src = "/system/priv-app/HnSystemServer/HnFoldScreen.apk";
        String dst = "/sdcard/Download/HnFoldScreen.apk";
        String[] commands = new String[] {
            "id",
            "ls -l " + src,
            "mkdir -p /sdcard/Download",
            "rm -f " + dst,
            "cp " + src + " " + dst,
            "chmod 0644 " + dst,
            "ls -lh " + dst,
            "sha256sum " + dst
        };
        for (String cmd : commands) {
            out.append("$ ").append(cmd).append("\n");
            out.append(runShell(cmd)).append("\n");
        }
        if (runShell("test -s " + dst + " && echo OK || echo FAIL").contains("OK")) {
            out.append("SUCCESS\nSaved to: ").append(dst).append("\n");
        } else {
            out.append("FAILED\nThe APK was not copied.\n");
        }
        return out.toString();
    }

    private String runShell(String cmd) {
        StringBuilder sb = new StringBuilder();
        try {
            Process p = new ProcessBuilder("/system/bin/sh", "-c", cmd + " 2>&1").redirectErrorStream(true).start();
            java.io.BufferedReader r = new java.io.BufferedReader(new java.io.InputStreamReader(p.getInputStream()));
            String line;
            while ((line = r.readLine()) != null) sb.append(line).append('\n');
            p.waitFor();
            sb.append("[exit=").append(p.exitValue()).append("]");
        } catch (Throwable e) {
            sb.append("ERROR: ").append(e);
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
import android.content.ComponentName;
import android.content.ServiceConnection;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.IBinder;
import android.widget.*;
import rikka.shizuku.Shizuku;

public class MainActivity extends Activity {
    private TextView status;
    private Button copy;

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(28,28,28,28);

        TextView title = new TextView(this);
        title.setText("MAGIC V2 — HnFoldScreen APK COPIER");
        title.setTextSize(20f);

        TextView info = new TextView(this);
        info.setText("Copies Honor's system HnFoldScreen.apk to Download without modifying the original. Start Shizuku first.\n\nSource:\n/system/priv-app/HnSystemServer/HnFoldScreen.apk\n\nDestination:\nDownload/HnFoldScreen.apk\n");

        copy = new Button(this);
        copy.setText("COPY HnFoldScreen.apk TO DOWNLOAD");
        status = new TextView(this);
        status.setTextIsSelectable(true);
        status.setText("Ready.");

        box.addView(title);
        box.addView(info);
        box.addView(copy);
        box.addView(status);
        ScrollView sv = new ScrollView(this);
        sv.addView(box);
        setContentView(sv);

        copy.setOnClickListener(v -> doCopy());
    }

    private void doCopy() {
        try {
            if (!Shizuku.pingBinder()) {
                status.setText("Shizuku is not running.");
                return;
            }
            if (Shizuku.checkSelfPermission() != PackageManager.PERMISSION_GRANTED) {
                status.setText("Grant Shizuku permission, then press COPY again.");
                Shizuku.requestPermission(98);
                return;
            }
            copy.setEnabled(false);
            status.setText("Copying…");
            Shizuku.UserServiceArgs args = new Shizuku.UserServiceArgs(new ComponentName(this, DisplayToggleService.class))
                    .daemon(false).processNameSuffix("magicv2_apk_copier");
            Shizuku.bindUserService(args, new ServiceConnection() {
                @Override public void onServiceConnected(ComponentName n, IBinder b) {
                    new Thread(() -> {
                        String result;
                        try { result = IDisplayToggleService.Stub.asInterface(b).copyHnFoldScreen(); }
                        catch (Throwable e) { result = "ERROR: " + e; }
                        final String r = result;
                        runOnUiThread(() -> {
                            status.setText(r);
                            copy.setEnabled(true);
                            if (r.contains("SUCCESS")) Toast.makeText(MainActivity.this, "Saved in Download/HnFoldScreen.apk", Toast.LENGTH_LONG).show();
                        });
                    }).start();
                }
                @Override public void onServiceDisconnected(ComponentName n) {
                    runOnUiThread(() -> { status.append("\nService disconnected."); copy.setEnabled(true); });
                }
            });
        } catch (Throwable e) {
            status.setText("START ERROR: " + e);
            copy.setEnabled(true);
        }
    }
}
''')
