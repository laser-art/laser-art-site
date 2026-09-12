from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;\ninterface IDisplayToggleService {\n    int toggleDisplays(int mode, in int[] whitelistDisplayIds);\n    String runPrivilegedBridgeStage(int stage);\n}\n''')

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
                    while ((line = r.readLine()) != null) {
                        out.append(line).append('\n');
                        if (out.length() > 180000) { out.append("[OUTPUT TRUNCATED]\n"); break; }
                    }
                }
                return out.toString();
            });
            boolean done = p.waitFor(timeoutSec, java.util.concurrent.TimeUnit.SECONDS);
            if (!done) {
                p.destroy();
                if (!p.waitFor(300, java.util.concurrent.TimeUnit.MILLISECONDS)) p.destroyForcibly();
                sb.append("[TIMEOUT after ").append(timeoutSec).append("s — continued]\n");
            } else {
                sb.append("[exit=").append(p.exitValue()).append("]\n");
            }
            try { sb.append(reader.get(700, java.util.concurrent.TimeUnit.MILLISECONDS)); }
            catch (Throwable ignored) { sb.append("[partial output unavailable]\n"); }
        } catch (Throwable e) {
            sb.append("ERROR: ").append(e).append('\n');
            try { if (p != null) p.destroyForcibly(); } catch (Throwable ignored) {}
        } finally {
            ex.shutdownNow();
        }
        return sb.toString();
    }

    @Override public String runPrivilegedBridgeStage(int stage) {
        switch(stage) {
            case 1:
                return "===== STAGE 1/6: PRIVAPP XML =====\n" + shellBridge("privapp XML", "grep -B 3 -A 5 -n 'MANAGE_FOLD_SCREEN' /system/etc/permissions/privapp-permissions-system.xml | head -n 350", 4);
            case 2:
                return "===== STAGE 2/6: KNOWN HONOR PACKAGES =====\n" + shellBridge("targeted holders", "for p in com.hihonor.systemserver com.hihonor.android.remotecontroller com.hihonor.android.upgradeguide; do echo '### '$p; dumpsys package $p 2>/dev/null | grep -Ei -B 3 -A 8 'MANAGE_FOLD_SCREEN|fold|coordination|rear.?display|display.?mode|exported=true' | head -n 220; done", 5);
            case 3:
                return "===== STAGE 3/6: PACKAGE RESOLVERS =====\n" + shellBridge("resolver hints", "dumpsys package | grep -Ei -B 3 -A 8 'fold[_ -]?screen|fold.?display|coordination.?display|rear.?display|MANAGE_FOLD_SCREEN' | head -n 500", 5);
            case 4:
                return "===== STAGE 4/6: EXPORTED COMPONENTS =====\n" + shellBridge("exported components", "for p in com.hihonor.systemserver com.hihonor.android.remotecontroller com.hihonor.android.upgradeguide; do echo; echo '### PACKAGE:'$p; dumpsys package $p 2>/dev/null | grep -Ei -B 5 -A 12 'exported=true|fold|coordination|rear.?display|display.?mode|Activity Resolver Table|Service Resolver Table|Receiver Resolver Table' | head -n 260; done", 5);
            case 5:
                return "===== STAGE 5/6: APK STRING HINTS =====\n" + shellBridge("APK strings", "for p in com.hihonor.systemserver com.hihonor.android.remotecontroller com.hihonor.android.upgradeguide; do echo; echo '### PACKAGE:'$p; for a in $(pm path $p 2>/dev/null | sed 's/^package://'); do echo '-- APK:'$a; timeout 2 strings $a 2>/dev/null | grep -Ei 'setDisplayMode|lockDisplayMode|unlockDisplayMode|fold_screen|MANAGE_FOLD_SCREEN|coordination|rear.?display|fold.?display|display.?mode' | sort -u | head -n 120; done; done", 6);
            case 6:
                return "===== STAGE 6/6: SYSTEMSERVER DETAIL =====\n" + shellBridge("systemserver detail", "dumpsys package com.hihonor.systemserver | grep -Ei -B 6 -A 16 'exported=true|fold|coordination|rear.?display|display.?mode|intent' | head -n 450", 5);
            default:
                return "Invalid stage: " + stage;
        }
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
    private Shizuku.UserServiceArgs args;

    @Override protected void onCreate(Bundle b){
        super.onCreate(b);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(24,24,24,24);
        TextView title=new TextView(this); title.setText("MAGIC V2 — PRIVILEGED BRIDGE PROBE v3"); title.setTextSize(20f);
        TextView info=new TextView(this); info.setText("Read-only. Visible progress. Every stage has its own hard timeout.\n");
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
        run.setEnabled(false); report="MAGIC V2 - HONOR PRIVILEGED BRIDGE PROBE v3\nREAD-ONLY\n\n"; text.setText(report+"Connecting to Shizuku service…\n");
        args=new Shizuku.UserServiceArgs(new ComponentName(this,DisplayToggleService.class)).daemon(false).processNameSuffix("magicv2_bridge_probe_v3");
        Shizuku.bindUserService(args,new ServiceConnection(){
            @Override public void onServiceConnected(ComponentName n,IBinder b){
                final IDisplayToggleService svc=IDisplayToggleService.Stub.asInterface(b);
                new Thread(()->{
                    for(int i=1;i<=6;i++){
                        final int st=i;
                        runOnUiThread(()->text.append("\n>>> Running stage "+st+"/6…\n"));
                        String r;
                        try { r=svc.runPrivilegedBridgeStage(st); }
                        catch(Throwable e){ r="===== STAGE "+st+"/6 ERROR =====\n"+e+"\n"; }
                        report += r + "\n";
                        final String fr=report;
                        runOnUiThread(()->text.setText(fr+"\n>>> Completed stage "+st+"/6\n"));
                    }
                    report += "===== DONE =====\n";
                    final String fr=report;
                    runOnUiThread(()->{text.setText(fr);run.setEnabled(true);});
                }).start();
            }
            @Override public void onServiceDisconnected(ComponentName n){runOnUiThread(()->{text.append("\nService disconnected. You can copy the partial report.\n");run.setEnabled(true);});}
        });
    }
}
''')
