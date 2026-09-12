from pathlib import Path

root = Path('displaytoggle')

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;\ninterface IDisplayToggleService {\n    int toggleDisplays(int mode, in int[] whitelistDisplayIds);\n    String runReflectProbe();\n}\n''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    @Override
    public String runReflectProbe() {
        StringBuilder out = new StringBuilder();
        out.append("MAGIC V2 - HONOR FSM REFLECTION PROBE\n");
        out.append("READ-ONLY: no setters are invoked.\n\n");
        String[] classes = new String[] {
            "com.hihonor.android.fsm.HwFoldScreenManager",
            "com.hihonor.android.fsm.HwFoldScreenManagerEx",
            "com.hihonor.android.fsm.IHwFoldScreenManager"
        };
        for (String cn : classes) {
            out.append("===== ").append(cn).append(" =====\n");
            try {
                Class<?> c = Class.forName(cn);
                out.append("Class loaded: ").append(c).append("\n");
                out.append("-- declared fields --\n");
                java.lang.reflect.Field[] fs = c.getDeclaredFields();
                java.util.Arrays.sort(fs, java.util.Comparator.comparing(java.lang.reflect.Field::getName));
                for (java.lang.reflect.Field f : fs) {
                    out.append(java.lang.reflect.Modifier.toString(f.getModifiers())).append(" ")
                       .append(f.getType().getTypeName()).append(" ").append(f.getName());
                    try {
                        if (java.lang.reflect.Modifier.isStatic(f.getModifiers())) {
                            f.setAccessible(true);
                            Object v = f.get(null);
                            out.append(" = ").append(String.valueOf(v));
                        }
                    } catch (Throwable t) { out.append(" = <inaccessible:").append(t.getClass().getSimpleName()).append(">"); }
                    out.append("\n");
                }
                out.append("-- declared methods --\n");
                java.lang.reflect.Method[] ms = c.getDeclaredMethods();
                java.util.Arrays.sort(ms, java.util.Comparator.comparing(java.lang.reflect.Method::getName));
                for (java.lang.reflect.Method m : ms) {
                    out.append(java.lang.reflect.Modifier.toString(m.getModifiers())).append(" ")
                       .append(m.getReturnType().getTypeName()).append(" ")
                       .append(m.getName()).append("(");
                    Class<?>[] ps = m.getParameterTypes();
                    for (int i=0;i<ps.length;i++) { if(i>0) out.append(", "); out.append(ps[i].getTypeName()); }
                    out.append(")\n");
                }
            } catch (Throwable e) {
                out.append("ERROR: ").append(e).append("\n");
            }
            out.append("\n");
        }
        out.append("===== CURRENT VALUES =====\n");
        try {
            Class<?> ex = Class.forName("com.hihonor.android.fsm.HwFoldScreenManagerEx");
            java.lang.reflect.Method getMode = ex.getDeclaredMethod("getDisplayMode");
            getMode.setAccessible(true);
            out.append("HwFoldScreenManagerEx.getDisplayMode() = ").append(String.valueOf(getMode.invoke(null))).append("\n");
        } catch(Throwable e) { out.append("getDisplayMode error: ").append(e).append("\n"); }
        try {
            Class<?> ex = Class.forName("com.hihonor.android.fsm.HwFoldScreenManagerEx");
            java.lang.reflect.Method getState = ex.getDeclaredMethod("getFoldableState");
            getState.setAccessible(true);
            out.append("HwFoldScreenManagerEx.getFoldableState() = ").append(String.valueOf(getState.invoke(null))).append("\n");
        } catch(Throwable e) { out.append("getFoldableState error: ").append(e).append("\n"); }
        return out.toString();
    }

'''
if marker not in s:
    raise SystemExit('service marker not found')
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
    private String report = "";
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout box = new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(24,24,24,24);
        TextView title = new TextView(this); title.setText("MAGIC V2 — HONOR FSM REFLECTION PROBE"); title.setTextSize(20f);
        TextView info = new TextView(this); info.setText("Read-only. Lists Honor fold-manager methods and constants without invoking setters.\n");
        Button run = new Button(this); run.setText("RUN REFLECTION PROBE");
        Button copy = new Button(this); copy.setText("COPY REPORT");
        text = new TextView(this); text.setTextSize(11f); text.setTextIsSelectable(true); text.setText("Ready.");
        box.addView(title); box.addView(info); box.addView(run); box.addView(copy); box.addView(text);
        ScrollView sv = new ScrollView(this); sv.addView(box); setContentView(sv);
        run.setOnClickListener(v -> {
            if(!Shizuku.pingBinder()){ text.setText("Shizuku is not running."); return; }
            if(Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED){ Shizuku.requestPermission(98); text.setText("Grant Shizuku permission, then press RUN again."); return; }
            text.setText("Running…"); run.setEnabled(false);
            Shizuku.UserServiceArgs args = new Shizuku.UserServiceArgs(new ComponentName(this, DisplayToggleService.class)).daemon(false).processNameSuffix("magicv2_honor_reflect");
            Shizuku.bindUserService(args, new ServiceConnection(){
                @Override public void onServiceConnected(ComponentName n, IBinder bnd){
                    new Thread(() -> {
                        String r;
                        try { r = IDisplayToggleService.Stub.asInterface(bnd).runReflectProbe(); }
                        catch(Throwable e){ r = "ERROR: "+e; }
                        final String fr=r;
                        runOnUiThread(() -> { report=fr; text.setText(fr); run.setEnabled(true); });
                    }).start();
                }
                @Override public void onServiceDisconnected(ComponentName n){ runOnUiThread(() -> run.setEnabled(true)); }
            });
        });
        copy.setOnClickListener(v -> {
            ClipboardManager cm=(ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
            cm.setPrimaryClip(ClipData.newPlainText("MagicV2 Honor FSM reflection", report));
            Toast.makeText(this,"Report copied",Toast.LENGTH_SHORT).show();
        });
    }
}
''')
