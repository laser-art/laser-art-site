from pathlib import Path

root = Path('displaytoggle')
manifest = root / 'app/src/main/AndroidManifest.xml'
s = manifest.read_text()
insert = '''\n    <uses-permission android:name="com.hihonor.permission.MANAGE_FOLD_SCREEN"/>\n    <uses-permission android:name="com.huawei.permission.MANAGE_FOLD_SCREEN"/>\n    <uses-permission android:name="android.permission.MANAGE_FOLD_SCREEN"/>\n'''
if '<application' in s and 'MANAGE_FOLD_SCREEN' not in s:
    s = s.replace('<application', insert + '\n    <application', 1)
manifest.write_text(s)

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;\ninterface IDisplayToggleService {\n    int toggleDisplays(int mode, in int[] whitelistDisplayIds);\n    String runFoldPermissionProbe();\n    String tryFoldPermissionGrant();\n}\n''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    private String shellOut(String cmd) {
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

    @Override public String runFoldPermissionProbe() {
        StringBuilder o = new StringBuilder();
        o.append("MAGIC V2 - MANAGE_FOLD_SCREEN PERMISSION PROBE\nREAD-ONLY\n\n");
        o.append("===== id =====\n").append(shellOut("id"));
        o.append("===== permission definitions =====\n").append(shellOut("dumpsys package permissions | grep -i -B 8 -A 16 'MANAGE_FOLD_SCREEN'"));
        o.append("===== pm list permissions =====\n").append(shellOut("pm list permissions -f 2>&1 | grep -i -B 4 -A 8 'MANAGE_FOLD_SCREEN'"));
        o.append("===== packages requesting/holding permission =====\n").append(shellOut("dumpsys package packages 2>/dev/null | grep -i -B 5 -A 12 'MANAGE_FOLD_SCREEN' | head -n 260"));
        o.append("===== our package =====\n").append(shellOut("dumpsys package com.displaytoggle.extreme | grep -i -E -B 4 -A 10 'MANAGE_FOLD_SCREEN|requested permissions|install permissions|runtime permissions' | head -n 180"));
        o.append("===== Honor systemserver =====\n").append(shellOut("dumpsys package com.hihonor.systemserver | grep -i -E -B 4 -A 12 'MANAGE_FOLD_SCREEN|grantedPermissions|requested permissions' | head -n 220"));
        o.append("===== permission XML references =====\n").append(shellOut("grep -R -n -i 'MANAGE_FOLD_SCREEN' /system/etc/permissions /system_ext/etc/permissions /product/etc/permissions /vendor/etc/permissions 2>/dev/null | head -n 100"));
        return o.toString();
    }

    @Override public String tryFoldPermissionGrant() {
        StringBuilder o = new StringBuilder();
        o.append("MAGIC V2 - PM GRANT TEST\nThis only attempts to grant the permission to this test app.\n\n");
        String[] perms = new String[]{
            "com.hihonor.permission.MANAGE_FOLD_SCREEN",
            "com.huawei.permission.MANAGE_FOLD_SCREEN",
            "android.permission.MANAGE_FOLD_SCREEN"
        };
        for (String p : perms) {
            o.append("===== TRY ").append(p).append(" =====\n");
            o.append(shellOut("pm grant com.displaytoggle.extreme " + p + " 2>&1"));
            o.append(shellOut("dumpsys package com.displaytoggle.extreme | grep -i -E -A 2 -B 2 '" + p + "|MANAGE_FOLD_SCREEN' | head -n 80"));
        }
        o.append("===== final permission check via wrapper =====\n");
        try {
            Class<?> c = Class.forName("com.hihonor.android.fsm.HwFoldScreenManagerEx");
            java.lang.reflect.Method m = c.getDeclaredMethod("setDisplayMode", int.class);
            m.setAccessible(true);
            Object r = m.invoke(null, 1);
            o.append("setDisplayMode(1) returned: ").append(r).append('\n');
        } catch (Throwable e) {
            Throwable x=e; int i=0;
            while(x!=null && i<8){ o.append("#").append(i).append(' ').append(x.getClass().getName()).append(": ").append(x.getMessage()).append('\n'); x=x.getCause(); i++; }
        }
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
    private TextView text; private String report=""; private Button probe, grant, copy;
    @Override protected void onCreate(Bundle b){
        super.onCreate(b);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(24,24,24,24);
        TextView title=new TextView(this); title.setText("MAGIC V2 — FOLD PERMISSION PROBE"); title.setTextSize(20f);
        TextView info=new TextView(this); info.setText("1) Run the read-only probe first. 2) TRY PM GRANT only attempts to grant MANAGE_FOLD_SCREEN to this app and reports why it succeeds or fails.\n");
        probe=new Button(this); probe.setText("1 — RUN PERMISSION PROBE");
        grant=new Button(this); grant.setText("2 — TRY PM GRANT");
        copy=new Button(this); copy.setText("COPY REPORT");
        text=new TextView(this); text.setTextIsSelectable(true); text.setTextSize(11f); text.setText("Ready.");
        box.addView(title); box.addView(info); box.addView(probe); box.addView(grant); box.addView(copy); box.addView(text);
        ScrollView sv=new ScrollView(this); sv.addView(box); setContentView(sv);
        probe.setOnClickListener(v->run(false)); grant.setOnClickListener(v->run(true));
        copy.setOnClickListener(v->{((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("MagicV2 permission report",report));Toast.makeText(this,"Report copied",Toast.LENGTH_SHORT).show();});
    }
    private void run(boolean doGrant){
        if(!Shizuku.pingBinder()){text.setText("Shizuku is not running.");return;}
        if(Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED){Shizuku.requestPermission(99);text.setText("Grant Shizuku permission, then press again.");return;}
        probe.setEnabled(false);grant.setEnabled(false);text.setText(doGrant?"Trying pm grant…":"Reading permission data…");
        Shizuku.UserServiceArgs args=new Shizuku.UserServiceArgs(new ComponentName(this,DisplayToggleService.class)).daemon(false).processNameSuffix("magicv2_fold_perm");
        Shizuku.bindUserService(args,new ServiceConnection(){
            @Override public void onServiceConnected(ComponentName n,IBinder b){new Thread(()->{String r;try{IDisplayToggleService s=IDisplayToggleService.Stub.asInterface(b);r=doGrant?s.tryFoldPermissionGrant():s.runFoldPermissionProbe();}catch(Throwable e){r="ERROR: "+e;}final String fr=r;runOnUiThread(()->{report=fr;text.setText(fr);probe.setEnabled(true);grant.setEnabled(true);});}).start();}
            @Override public void onServiceDisconnected(ComponentName n){runOnUiThread(()->{text.append("\nService disconnected.");probe.setEnabled(true);grant.setEnabled(true);});}
        });
    }
}
''')
