from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;\ninterface IDisplayToggleService {\n    int toggleDisplays(int mode, in int[] whitelistDisplayIds);\n    String runPrivilegedBridgeProbeFast();\n}\n''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    private String shellFast(String cmd, long timeoutSec) {
        StringBuilder sb = new StringBuilder();
        try {
            Process p = new ProcessBuilder("/system/bin/sh", "-c", cmd).redirectErrorStream(true).start();
            java.io.BufferedReader r = new java.io.BufferedReader(new java.io.InputStreamReader(p.getInputStream()));
            java.util.concurrent.ExecutorService ex = java.util.concurrent.Executors.newSingleThreadExecutor();
            java.util.concurrent.Future<?> f = ex.submit(() -> {
                try { String line; while ((line = r.readLine()) != null) sb.append(line).append('\n'); } catch (Throwable ignored) {}
            });
            boolean done = p.waitFor(timeoutSec, java.util.concurrent.TimeUnit.SECONDS);
            if (!done) { p.destroyForcibly(); sb.append("[TIMEOUT after ").append(timeoutSec).append("s]\n"); }
            else sb.append("[exit=").append(p.exitValue()).append("]\n");
            try { f.get(1, java.util.concurrent.TimeUnit.SECONDS); } catch(Throwable ignored) { f.cancel(true); }
            ex.shutdownNow();
        } catch (Throwable e) { sb.append("ERROR: ").append(e).append('\n'); }
        return sb.toString();
    }

    @Override public String runPrivilegedBridgeProbeFast() {
        StringBuilder o = new StringBuilder();
        o.append("MAGIC V2 - HONOR PRIVILEGED BRIDGE PROBE FAST\n");
        o.append("READ-ONLY. Optimized scan; each command has a timeout.\n\n");

        o.append("===== PACKAGES GRANTED MANAGE_FOLD_SCREEN (from privapp XML) =====\n");
        String xmlCmd = "awk '\n"
            + "BEGIN{pkg=\"\"} "
            + "/<privapp-permissions package=/{if(match($0,/package=\"[^\"]+\"/)){pkg=substr($0,RSTART+9,RLENGTH-10)}} "
            + "/com.hihonor.permission.MANAGE_FOLD_SCREEN/{if(pkg!=\"\") print pkg}' "
            + "/system/etc/permissions/privapp-permissions-system.xml | sort -u";
        String pkgs = shellFast(xmlCmd, 5);
        o.append(pkgs);

        o.append("===== TARGETED PACKAGE SUMMARIES =====\n");
        String targets = "com.hihonor.systemserver com.android.systemui com.android.settings com.hihonor.android.launcher com.hihonor.associateassistant com.hihonor.android.remotecontroller";
        o.append(shellFast("for p in " + targets + "; do echo '### '$p; pm path $p 2>/dev/null; dumpsys package $p 2>/dev/null | grep -Ei -B 3 -A 8 'MANAGE_FOLD_SCREEN|fold|coordination|rear.?display|display.?mode|exported=true|Service Resolver Table|Receiver Resolver Table|Activity Resolver Table' | head -n 220; done", 12));

        o.append("===== SYSTEMSERVER SERVICES / RECEIVERS / ACTIVITIES =====\n");
        o.append(shellFast("dumpsys package com.hihonor.systemserver 2>/dev/null | grep -Ei -B 5 -A 12 'Service Resolver Table|Receiver Resolver Table|Activity Resolver Table|exported=true|fold|coordination|rear.?display|display.?mode' | head -n 420", 8));

        o.append("===== SYSTEMSERVER APK STRINGS =====\n");
        o.append(shellFast("for a in $(pm path com.hihonor.systemserver 2>/dev/null | sed 's/^package://'); do echo '-- '$a; strings $a 2>/dev/null | grep -Ei 'setDisplayMode|lockDisplayMode|unlockDisplayMode|fold_screen|MANAGE_FOLD_SCREEN|coordination|rear.?display|fold.?display|display.?mode' | sort -u | head -n 220; done", 8));

        o.append("===== EXPLICIT RESOLVE CHECKS =====\n");
        o.append(shellFast("cmd package query-services --brief -a com.hihonor 2>/dev/null | grep -Ei 'fold|coordination|display' | head -n 120; cmd package query-receivers --brief -a com.hihonor 2>/dev/null | grep -Ei 'fold|coordination|display' | head -n 120", 6));
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
        TextView title=new TextView(this); title.setText("MAGIC V2 — FAST PRIVILEGED BRIDGE PROBE"); title.setTextSize(20f);
        TextView info=new TextView(this); info.setText("Optimized read-only scan. No full package scan; commands time out automatically.\n");
        run=new Button(this); run.setText("RUN FAST BRIDGE PROBE");
        copy=new Button(this); copy.setText("COPY REPORT");
        text=new TextView(this); text.setTextIsSelectable(true); text.setTextSize(10f); text.setText("Ready.");
        box.addView(title); box.addView(info); box.addView(run); box.addView(copy); box.addView(text);
        ScrollView sv=new ScrollView(this); sv.addView(box); setContentView(sv);
        run.setOnClickListener(v->go());
        copy.setOnClickListener(v->{((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("MagicV2 fast bridge report",report)); Toast.makeText(this,"Report copied",Toast.LENGTH_SHORT).show();});
    }
    private void go(){
        if(!Shizuku.pingBinder()){text.setText("Shizuku is not running.");return;}
        if(Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED){Shizuku.requestPermission(99);text.setText("Grant Shizuku permission, then press again.");return;}
        run.setEnabled(false); text.setText("Fast scan running… normally under 30 seconds.");
        Shizuku.UserServiceArgs args=new Shizuku.UserServiceArgs(new ComponentName(this,DisplayToggleService.class)).daemon(false).processNameSuffix("magicv2_bridge_fast");
        Shizuku.bindUserService(args,new ServiceConnection(){
            @Override public void onServiceConnected(ComponentName n,IBinder b){new Thread(()->{String r;try{r=IDisplayToggleService.Stub.asInterface(b).runPrivilegedBridgeProbeFast();}catch(Throwable e){r="ERROR: "+e;} final String fr=r;runOnUiThread(()->{report=fr;text.setText(fr);run.setEnabled(true);});}).start();}
            @Override public void onServiceDisconnected(ComponentName n){runOnUiThread(()->{text.append("\nService disconnected.");run.setEnabled(true);});}
        });
    }
}
''')
