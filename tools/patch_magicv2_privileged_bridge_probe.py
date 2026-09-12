from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;\ninterface IDisplayToggleService {\n    int toggleDisplays(int mode, in int[] whitelistDisplayIds);\n    String runPrivilegedBridgeProbe();\n}\n''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    private String shellBridge(String cmd) {
        StringBuilder sb = new StringBuilder();
        try {
            Process p = new ProcessBuilder("/system/bin/sh", "-c", cmd).redirectErrorStream(true).start();
            java.io.BufferedReader r = new java.io.BufferedReader(new java.io.InputStreamReader(p.getInputStream()));
            String line;
            while ((line = r.readLine()) != null) sb.append(line).append('\n');
            p.waitFor();
            sb.append("[exit=").append(p.exitValue()).append("]\n");
        } catch (Throwable e) { sb.append("ERROR: ").append(e).append('\n'); }
        return sb.toString();
    }

    @Override public String runPrivilegedBridgeProbe() {
        StringBuilder o = new StringBuilder();
        o.append("MAGIC V2 - HONOR PRIVILEGED BRIDGE PROBE\n");
        o.append("READ-ONLY. Searches system apps already holding MANAGE_FOLD_SCREEN for exported bridges/intents/services.\n\n");

        o.append("===== PRIVAPP XML CONTEXT =====\n");
        o.append(shellBridge("grep -B 3 -A 5 -n 'MANAGE_FOLD_SCREEN' /system/etc/permissions/privapp-permissions-system.xml | head -n 500"));

        o.append("===== SYSTEM PACKAGES HOLDING MANAGE_FOLD_SCREEN =====\n");
        String candidates = shellBridge("for p in $(pm list packages -s | cut -d: -f2); do dumpsys package \"$p\" 2>/dev/null | grep -q 'com.hihonor.permission.MANAGE_FOLD_SCREEN: granted=true' && echo \"$p\"; done");
        o.append(candidates);

        o.append("===== FOLD/COORDINATION COMPONENTS IN PACKAGE MANAGER =====\n");
        o.append(shellBridge("dumpsys package | grep -Ei -B 4 -A 10 'fold[_ -]?screen|fold.?display|coordination.?display|rear.?display|setDisplayMode|lockDisplayMode|MANAGE_FOLD_SCREEN' | head -n 1200"));

        o.append("===== EXPORTED/INTENT HINTS FOR PRIVILEGED HOLDERS =====\n");
        o.append(shellBridge("for p in $(pm list packages -s | cut -d: -f2); do d=$(dumpsys package \"$p\" 2>/dev/null); echo \"$d\" | grep -q 'com.hihonor.permission.MANAGE_FOLD_SCREEN: granted=true' || continue; echo; echo '### PACKAGE:'$p; echo \"$d\" | grep -Ei -B 5 -A 12 'fold|coordination|rear.?display|display.?mode|exported=true|Activity Resolver Table|Service Resolver Table|Receiver Resolver Table' | head -n 280; done"));

        o.append("===== APK STRING HINTS FOR PRIVILEGED HOLDERS =====\n");
        o.append(shellBridge("for p in $(pm list packages -s | cut -d: -f2); do d=$(dumpsys package \"$p\" 2>/dev/null); echo \"$d\" | grep -q 'com.hihonor.permission.MANAGE_FOLD_SCREEN: granted=true' || continue; paths=$(pm path \"$p\" 2>/dev/null | sed 's/^package://'); [ -z \"$paths\" ] && continue; echo; echo '### PACKAGE:'$p; for a in $paths; do echo '-- APK:'$a; strings \"$a\" 2>/dev/null | grep -Ei 'setDisplayMode|lockDisplayMode|unlockDisplayMode|fold_screen|MANAGE_FOLD_SCREEN|coordination|rear.?display|fold.?display|display.?mode' | sort -u | head -n 180; done; done"));

        o.append("===== SYSTEMSERVER EXPORTED COMPONENT HINTS =====\n");
        o.append(shellBridge("dumpsys package com.hihonor.systemserver | grep -Ei -B 6 -A 16 'exported=true|fold|coordination|rear.?display|display.?mode|intent' | head -n 700"));

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
        TextView title=new TextView(this); title.setText("MAGIC V2 — PRIVILEGED BRIDGE PROBE"); title.setTextSize(20f);
        TextView info=new TextView(this); info.setText("Read-only scan for Honor system apps that already hold MANAGE_FOLD_SCREEN and expose a usable Intent/Service bridge. This does not change display mode.\n");
        run=new Button(this); run.setText("RUN BRIDGE PROBE");
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
        run.setEnabled(false); text.setText("Scanning system packages… this can take 1–2 minutes.");
        Shizuku.UserServiceArgs args=new Shizuku.UserServiceArgs(new ComponentName(this,DisplayToggleService.class)).daemon(false).processNameSuffix("magicv2_bridge_probe");
        Shizuku.bindUserService(args,new ServiceConnection(){
            @Override public void onServiceConnected(ComponentName n,IBinder b){new Thread(()->{String r;try{r=IDisplayToggleService.Stub.asInterface(b).runPrivilegedBridgeProbe();}catch(Throwable e){r="ERROR: "+e;} final String fr=r;runOnUiThread(()->{report=fr;text.setText(fr);run.setEnabled(true);});}).start();}
            @Override public void onServiceDisconnected(ComponentName n){runOnUiThread(()->{text.append("\nService disconnected.");run.setEnabled(true);});}
        });
    }
}
''')
