from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;\ninterface IDisplayToggleService {\n    int toggleDisplays(int mode, in int[] whitelistDisplayIds);\n    String testHonorCoordination();\n    String restoreHonorFull();\n}\n''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    private String shell(String cmd) {
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

    private Object invokeStatic(String method, Class<?>[] sig, Object[] args) throws Exception {
        Class<?> c = Class.forName("com.hihonor.android.fsm.HwFoldScreenManagerEx");
        java.lang.reflect.Method m = c.getDeclaredMethod(method, sig);
        m.setAccessible(true);
        return m.invoke(null, args);
    }

    private String snapshot(String tag) {
        StringBuilder o = new StringBuilder();
        o.append("\n===== ").append(tag).append(" =====\n");
        try { o.append("getDisplayMode=").append(invokeStatic("getDisplayMode", new Class<?>[]{}, new Object[]{})).append('\n'); }
        catch(Throwable e){ o.append("getDisplayMode ERROR: ").append(e).append('\n'); }
        o.append(shell("cmd device_state state"));
        o.append(shell("dumpsys fold_screen"));
        o.append(shell("dumpsys display | grep -E 'mCurrentLayout=|mDeviceState=|Display State=|uniqueId=\\\"local:4630946846403687043|uniqueId=\\\"local:4630946324137792644' | head -n 80"));
        o.append(shell("dumpsys SurfaceFlinger | grep -E 'pacesetterDisplayId|Display 4630946846403687043 \\(active\\)|Display 4630946324137792644 \\(active\\)|Display 4630946846403687043 \\(inactive\\)|Display 4630946324137792644 \\(inactive\\)|layerFilter=' | head -n 80"));
        return o.toString();
    }

    @Override public String testHonorCoordination() {
        StringBuilder o = new StringBuilder();
        o.append("HONOR COORDINATION MODE TEST\n");
        o.append("Known API: HwFoldScreenManagerEx.setDisplayMode(4)\n");
        o.append(snapshot("BEFORE"));
        try {
            Object ret = invokeStatic("setDisplayMode", new Class<?>[]{int.class}, new Object[]{4});
            o.append("\nsetDisplayMode(4) returned: ").append(ret).append('\n');
        } catch(Throwable e) { o.append("\nsetDisplayMode(4) ERROR: ").append(e).append('\n'); return o.toString(); }
        try { Thread.sleep(1200); } catch(Exception ignored) {}
        o.append(snapshot("AFTER MODE 4"));
        // Hold coordination long enough for visual observation, then restore safely.
        try { Thread.sleep(5000); } catch(Exception ignored) {}
        try {
            Object ret = invokeStatic("setDisplayMode", new Class<?>[]{int.class}, new Object[]{1});
            o.append("\nAUTO RESTORE setDisplayMode(1) returned: ").append(ret).append('\n');
        } catch(Throwable e) { o.append("\nAUTO RESTORE ERROR: ").append(e).append('\n'); }
        try { Thread.sleep(800); } catch(Exception ignored) {}
        o.append(snapshot("AFTER RESTORE"));
        return o.toString();
    }

    @Override public String restoreHonorFull() {
        StringBuilder o = new StringBuilder();
        try { o.append("setDisplayMode(1) returned: ").append(invokeStatic("setDisplayMode", new Class<?>[]{int.class}, new Object[]{1})).append('\n'); }
        catch(Throwable e){ o.append("ERROR: ").append(e).append('\n'); }
        o.append(snapshot("RESTORE"));
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
    private Button test, restore, copy;
    private String report="";

    @Override protected void onCreate(Bundle b){
        super.onCreate(b);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(24,24,24,24);
        TextView title=new TextView(this); title.setText("MAGIC V2 — HONOR COORDINATION TEST"); title.setTextSize(20f);
        TextView info=new TextView(this); info.setText("Tests the documented Honor API DISPLAY_MODE_COORDINATION = 4. It automatically restores DISPLAY_MODE_FULL = 1 after about 5 seconds. Watch both physical screens during the test.\n");
        test=new Button(this); test.setText("TEST COORDINATION MODE 4");
        restore=new Button(this); restore.setText("EMERGENCY RESTORE FULL MODE 1");
        copy=new Button(this); copy.setText("COPY REPORT");
        text=new TextView(this); text.setTextIsSelectable(true); text.setTextSize(11f); text.setText("Ready.");
        box.addView(title); box.addView(info); box.addView(test); box.addView(restore); box.addView(copy); box.addView(text);
        ScrollView sv=new ScrollView(this); sv.addView(box); setContentView(sv);
        test.setOnClickListener(v->run(false)); restore.setOnClickListener(v->run(true));
        copy.setOnClickListener(v->{((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("MagicV2 coordination report",report)); Toast.makeText(this,"Report copied",Toast.LENGTH_SHORT).show();});
    }

    private void run(boolean doRestore){
        if(!Shizuku.pingBinder()){text.setText("Shizuku is not running.");return;}
        if(Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED){Shizuku.requestPermission(99);text.setText("Grant Shizuku permission, then press again.");return;}
        test.setEnabled(false); restore.setEnabled(false); text.setText(doRestore?"Restoring…":"Testing mode 4… watch BOTH screens for the next 5 seconds.");
        Shizuku.UserServiceArgs args=new Shizuku.UserServiceArgs(new ComponentName(this,DisplayToggleService.class)).daemon(false).processNameSuffix("magicv2_honor_coordination");
        Shizuku.bindUserService(args,new ServiceConnection(){
            @Override public void onServiceConnected(ComponentName n,IBinder b){new Thread(()->{String r;try{IDisplayToggleService s=IDisplayToggleService.Stub.asInterface(b);r=doRestore?s.restoreHonorFull():s.testHonorCoordination();}catch(Throwable e){r="ERROR: "+e;} final String fr=r;runOnUiThread(()->{report=fr;text.setText(fr);test.setEnabled(true);restore.setEnabled(true);});}).start();}
            @Override public void onServiceDisconnected(ComponentName n){runOnUiThread(()->{text.append("\nService disconnected.");test.setEnabled(true);restore.setEnabled(true);});}
        });
    }
}
''')
