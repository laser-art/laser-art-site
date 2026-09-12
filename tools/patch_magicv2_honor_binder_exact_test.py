from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;\ninterface IDisplayToggleService {\n    int toggleDisplays(int mode, in int[] whitelistDisplayIds);\n    String diagnoseHonorBinder();\n    String testExactMode4();\n    String restoreExactMode1();\n}\n''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    private String shell2(String cmd) {
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

    private String deep(Throwable t) {
        StringBuilder b = new StringBuilder();
        int i=0;
        while (t != null && i < 8) {
            b.append("#").append(i).append(" ").append(t.getClass().getName()).append(": ").append(t.getMessage()).append('\n');
            if (t instanceof java.lang.reflect.InvocationTargetException) {
                Throwable x=((java.lang.reflect.InvocationTargetException)t).getTargetException();
                if (x != null && x != t) { t=x; i++; continue; }
            }
            Throwable c=t.getCause();
            if (c == null || c == t) break;
            t=c; i++;
        }
        return b.toString();
    }

    private Object invokeHonor(String name, Class<?>[] sig, Object[] args) throws Exception {
        Class<?> c=Class.forName("com.hihonor.android.fsm.HwFoldScreenManagerEx");
        java.lang.reflect.Method m=c.getDeclaredMethod(name,sig);
        m.setAccessible(true);
        return m.invoke(null,args);
    }

    private int tx(String name) throws Exception {
        Class<?> c=Class.forName("com.hihonor.android.fsm.IHwFoldScreenManager$Stub");
        java.lang.reflect.Field f=c.getDeclaredField("TRANSACTION_"+name);
        f.setAccessible(true);
        return f.getInt(null);
    }

    private String snap2(String tag) {
        StringBuilder o=new StringBuilder();
        o.append("\n===== ").append(tag).append(" =====\n");
        try{o.append("Honor getDisplayMode=").append(invokeHonor("getDisplayMode",new Class<?>[]{},new Object[]{})).append('\n');}
        catch(Throwable e){o.append("Honor getDisplayMode ERROR\n").append(deep(e));}
        o.append(shell2("cmd device_state state"));
        o.append(shell2("dumpsys fold_screen"));
        o.append(shell2("dumpsys display | grep -E 'mCurrentLayout=|mDeviceState=|Display State=' | head -n 30"));
        o.append(shell2("dumpsys SurfaceFlinger | grep -E 'pacesetterDisplayId|Display 4630946846403687043 \\(active\\)|Display 4630946324137792644 \\(active\\)|Display 4630946846403687043 \\(inactive\\)|Display 4630946324137792644 \\(inactive\\)|layerFilter=' | head -n 40"));
        return o.toString();
    }

    @Override public String diagnoseHonorBinder() {
        StringBuilder o=new StringBuilder();
        o.append("MAGIC V2 - HONOR EXACT BINDER DIAGNOSTIC\n");
        o.append("READ-ONLY except the wrapper call below, which only attempts known mode 4 and reports the real exception.\n\n");
        String[] names={"getDisplayMode","setDisplayMode","lockDisplayMode","unlockDisplayMode","setRearDisplayState"};
        for(String n:names){try{o.append("TRANSACTION_").append(n).append(" = ").append(tx(n)).append('\n');}catch(Throwable e){o.append("TRANSACTION_").append(n).append(" ERROR: ").append(e).append('\n');}}
        o.append(snap2("BEFORE"));
        try { Object r=invokeHonor("setDisplayMode",new Class<?>[]{int.class},new Object[]{4}); o.append("wrapper setDisplayMode(4) returned ").append(r).append('\n'); }
        catch(Throwable e){o.append("wrapper setDisplayMode(4) FAILED:\n").append(deep(e));}
        return o.toString();
    }

    @Override public String testExactMode4() {
        StringBuilder o=new StringBuilder();
        o.append("HONOR EXACT BINDER MODE 4 TEST\n");
        o.append(snap2("BEFORE"));
        try {
            int code=tx("setDisplayMode");
            o.append("Using discovered TRANSACTION_setDisplayMode=").append(code).append('\n');
            String cmd="service call fold_screen "+code+" i32 4";
            o.append("CALL: ").append(cmd).append('\n').append(shell2(cmd));
        } catch(Throwable e){o.append("Binder call setup ERROR:\n").append(deep(e)); return o.toString();}
        try{Thread.sleep(1200);}catch(Exception ignored){}
        o.append(snap2("AFTER MODE 4"));
        try{Thread.sleep(5000);}catch(Exception ignored){}
        try {
            int code=tx("setDisplayMode");
            o.append("AUTO RESTORE mode 1:\n").append(shell2("service call fold_screen "+code+" i32 1"));
        } catch(Throwable e){o.append("AUTO RESTORE setup ERROR:\n").append(deep(e));}
        try{Thread.sleep(800);}catch(Exception ignored){}
        o.append(snap2("AFTER RESTORE"));
        return o.toString();
    }

    @Override public String restoreExactMode1() {
        StringBuilder o=new StringBuilder();
        try { int code=tx("setDisplayMode"); o.append(shell2("service call fold_screen "+code+" i32 1")); }
        catch(Throwable e){o.append(deep(e));}
        o.append(snap2("RESTORE"));
        return o.toString();
    }

'''
if marker not in s: raise SystemExit('marker not found')
s=s.replace(marker,method+marker)
svc.write_text(s)

activity=root/'app/src/main/java/com/displaytoggle/extreme/MainActivity.java'
activity.write_text(r'''package com.displaytoggle.extreme;

import android.app.Activity;
import android.content.*;
import android.content.pm.PackageManager;
import android.os.*;
import android.widget.*;
import rikka.shizuku.Shizuku;

public class MainActivity extends Activity {
    TextView text; Button diag,test,restore,copy; String report="";
    @Override protected void onCreate(Bundle b){super.onCreate(b);LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(24,24,24,24);
        TextView t=new TextView(this);t.setText("MAGIC V2 — HONOR EXACT BINDER TEST");t.setTextSize(20f);
        TextView i=new TextView(this);i.setText("1) DIAGNOSE reveals the real setDisplayMode(4) error and exact Binder transaction codes. 2) EXACT MODE 4 uses the discovered transaction code directly through the shell service. It restores mode 1 after 5 seconds.\n");
        diag=new Button(this);diag.setText("1 — DIAGNOSE ERROR + TRANSACTION CODES");test=new Button(this);test.setText("2 — TEST EXACT BINDER MODE 4");restore=new Button(this);restore.setText("EMERGENCY RESTORE MODE 1");copy=new Button(this);copy.setText("COPY REPORT");text=new TextView(this);text.setTextSize(11f);text.setTextIsSelectable(true);text.setText("Ready.");
        box.addView(t);box.addView(i);box.addView(diag);box.addView(test);box.addView(restore);box.addView(copy);box.addView(text);ScrollView sv=new ScrollView(this);sv.addView(box);setContentView(sv);
        diag.setOnClickListener(v->go(0));test.setOnClickListener(v->go(1));restore.setOnClickListener(v->go(2));copy.setOnClickListener(v->{((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("MagicV2 exact binder",report));Toast.makeText(this,"Report copied",Toast.LENGTH_SHORT).show();});}
    void go(int which){if(!Shizuku.pingBinder()){text.setText("Shizuku is not running.");return;}if(Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED){Shizuku.requestPermission(101);text.setText("Grant Shizuku permission then press again.");return;}diag.setEnabled(false);test.setEnabled(false);restore.setEnabled(false);text.setText("Running…");
        Shizuku.UserServiceArgs a=new Shizuku.UserServiceArgs(new ComponentName(this,DisplayToggleService.class)).daemon(false).processNameSuffix("magicv2_honor_exact_binder");Shizuku.bindUserService(a,new ServiceConnection(){public void onServiceConnected(ComponentName n,IBinder b){new Thread(()->{String r;try{IDisplayToggleService s=IDisplayToggleService.Stub.asInterface(b);r=which==0?s.diagnoseHonorBinder():(which==1?s.testExactMode4():s.restoreExactMode1());}catch(Throwable e){r="ERROR: "+e;}final String fr=r;runOnUiThread(()->{report=fr;text.setText(fr);diag.setEnabled(true);test.setEnabled(true);restore.setEnabled(true);});}).start();}public void onServiceDisconnected(ComponentName n){runOnUiThread(()->{text.append("\nService disconnected");diag.setEnabled(true);test.setEnabled(true);restore.setEnabled(true);});}});}
}
''')
