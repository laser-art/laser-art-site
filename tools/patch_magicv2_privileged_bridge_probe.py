from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;\ninterface IDisplayToggleService {\n    int toggleDisplays(int mode, in int[] whitelistDisplayIds);\n    String runPrivilegedBridgeProbe();\n}\n''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    private String shellBridge(String label, String cmd, long timeoutSec) {
        StringBuilder sb = new StringBuilder();
        sb.append("--- ").append(label).append(" ---\n");
        Process p = null;
        java.util.concurrent.ExecutorService ex = java.util.concurrent.Executors.newSingleThreadExecutor();
        try {
            p = new ProcessBuilder("/system/bin/sh", "-c", cmd).redirectErrorStream(true).start();
            final Process fp = p;
            java.util.concurrent.Future<String> reader = ex.submit(() -> {
                StringBuilder out = new StringBuilder();
                try (java.io.BufferedReader r = new java.io.BufferedReader(new java.io.InputStreamReader(fp.getInputStream()))) {
                    String line;
                    while ((line = r.readLine()) != null) out.append(line).append('\n');
                }
                return out.toString();
            });
            boolean done = p.waitFor(timeoutSec, java.util.concurrent.TimeUnit.SECONDS);
            if (!done) {
                p.destroy();
                if (!p.waitFor(500, java.util.concurrent.TimeUnit.MILLISECONDS)) p.destroyForcibly();
                sb.append("[TIMEOUT after ").append(timeoutSec).append("s — scan continued]\n");
            } else {
                sb.append("[exit=").append(p.exitValue()).append("]\n");
            }
            try { sb.append(reader.get(1200, java.util.concurrent.TimeUnit.MILLISECONDS)); }
            catch (Throwable ignored) { sb.append("[partial output unavailable]\n"); }
        } catch (Throwable e) {
            sb.append("ERROR: ").append(e).append('\n');
            try { if (p != null) p.destroyForcibly(); } catch (Throwable ignored) {}
        } finally {
            ex.shutdownNow();
        }
        return sb.toString();
    }

    @Override public String runPrivilegedBridgeProbe() {
        StringBuilder o = new StringBuilder();
        o.append("MAGIC V2 - HONOR PRIVILEGED BRIDGE PROBE v2\n");
        o.append("READ-ONLY. Every stage has a hard timeout, so one Honor command cannot freeze the scan.\n\n");

        o.append("===== STAGE 1/6: PRIVAPP XML =====\n");
        o.append(shellBridge("privapp XML", "grep -B 3 -A 5 -n 'MANAGE_FOLD_SCREEN' /system/etc/permissions/privapp-permissions-system.xml | head -n 350", 5));

        o.append("===== STAGE 2/6: KNOWN HONOR PACKAGES =====\n");
        o.append(shellBridge("targeted holders", "for p in com.hihonor.systemserver com.hihonor.android.remotecontroller com.hihonor.android.upgradeguide; do echo '### '$p; dumpsys package $p 2>/dev/null | grep -Ei -B 3 -A 8 'MANAGE_FOLD_SCREEN|fold|coordination|rear.?display|display.?mode|exported=true' | head -n 220; done", 7));

        o.append("===== STAGE 3/6: PACKAGE RESOLVERS =====\n");
        o.append(shellBridge("resolver hints", "dumpsys package | grep -Ei -B 3 -A 8 'fold[_ -]?screen|fold.?display|coordination.?display|rear.?display|MANAGE_FOLD_SCREEN' | head -n 650", 7));

        o.append("===== STAGE 4/6: EXPORTED COMPONENTS =====\n");
        o.append(shellBridge("exported components", "for p in com.hihonor.systemserver com.hihonor.android.remotecontroller com.hihonor.android.upgradeguide; do echo; echo '### PACKAGE:'$p; dumpsys package $p 2>/dev/null | grep -Ei -B 5 -A 12 'exported=true|fold|coordination|rear.?display|display.?mode|Activity Resolver Table|Service Resolver Table|Receiver Resolver Table' | head -n 320; done", 7));

        o.append("===== STAGE 5/6: APK STRING HINTS =====\n");
        o.append(shellBridge("APK strings", "for p in com.hihonor.systemserver com.hihonor.android.remotecontroller com.hihonor.android.upgradeguide; do echo; echo '### PACKAGE:'$p; for a in $(pm path $p 2>/dev/null | sed 's/^package://'); do echo '-- APK:'$a; strings $a 2>/dev/null | grep -Ei 'setDisplayMode|lockDisplayMode|unlockDisplayMode|fold_screen|MANAGE_FOLD_SCREEN|coordination|rear.?display|fold.?display|display.?mode' | sort -u | head -n 160; done; done", 9));

        o.append("===== STAGE 6/6: SYSTEMSERVER DETAIL =====\n");
        o.append(shellBridge("systemserver detail", "dumpsys package com.hihonor.systemserver | grep -Ei -B 6 -A 16 'exported=true|fold|coordination|rear.?display|display.?mode|intent' | head -n 600", 7));

        o.append("===== DONE =====\n");
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
    private Button run, copy;
    private String report="";

    @Override protected void onCreate(Bundle b){
        super.onCreate(b);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(24,24,24,24);
        TextView title=new TextView(this); title.setText("MAGIC V2 — PRIVILEGED BRIDGE PROBE v2"); title.setTextSize(20f);
        TextView info=new TextView(this); info.setText("Read-only. Each scan stage has a timeout and cannot block forever.\n");
        run=new Button(this); run.setText("RUN SAFE BRIDGE SCAN");
        copy=new Button(this); copy.setText("COPY REPORT");
        text=new TextView(this); text.setTextIsSelectable(true); text.setTextSize(10f); text.setText("Ready.");
        box.addView(title); box.addView(info); box.addView(run); box.addView(copy); box.addView(text);
        ScrollView sv=new ScrollView(this); sv.addView(box); setContentView(sv);
        run.setOnClickListener(v->go());
        copy.setOnClickListener(v->{((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("MagicV2 bridge report",report)); Toast.makeText(this,"Report copied",Toast.LENGTH_SHORT).show();});
    }

    private void go(){
        if(!Shizuku.pingBinder()){text.setText("Shizuku is not running.");return;}
        if(Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED){Shizuku.requestPermission(99);text.setText("Grant Shizuku permission, then press again.");return;}
        run.setEnabled(false); text.setText("Scan running. Maximum roughly 45 seconds. A blocked stage will be killed automatically…");
        Shizuku.UserServiceArgs args=new Shizuku.UserServiceArgs(new ComponentName(this,DisplayToggleService.class)).daemon(false).processNameSuffix("magicv2_bridge_probe_v2");
        Shizuku.bindUserService(args,new ServiceConnection(){
            @Override public void onServiceConnected(ComponentName n,IBinder b){new Thread(()->{String r;try{r=IDisplayToggleService.Stub.asInterface(b).runPrivilegedBridgeProbe();}catch(Throwable e){r="ERROR: "+e;} final String fr=r;runOnUiThread(()->{report=fr;text.setText(fr);run.setEnabled(true);});}).start();}
            @Override public void onServiceDisconnected(ComponentName n){runOnUiThread(()->{text.append("\nService disconnected.");run.setEnabled(true);});}
        });
    }
}
''')
