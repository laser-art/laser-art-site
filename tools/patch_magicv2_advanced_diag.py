from pathlib import Path

root = Path('displaytoggle')

# Keep proven package/application id.

# Manifest: foreground service permissions + controller service.
manifest = root / 'app/src/main/AndroidManifest.xml'
ms = manifest.read_text()
if 'android.permission.FOREGROUND_SERVICE' not in ms:
    ms = ms.replace('<uses-sdk android:minSdkVersion="24" android:targetSdkVersion="34" />', '<uses-sdk android:minSdkVersion="24" android:targetSdkVersion="34" />\n    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />\n    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />\n    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />')
service_xml = '''\n        <service\n            android:name=".HingeControllerService"\n            android:exported="false"\n            android:foregroundServiceType="specialUse">\n            <property android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE" android:value="Magic V2 hinge display controller" />\n        </service>\n'''
if '.HingeControllerService' not in ms:
    ms = ms.replace('    </application>', service_xml + '    </application>')
manifest.write_text(ms)

(root / 'app/src/main/aidl/com/displaytoggle/extreme/IDisplayToggleService.aidl').write_text('''package com.displaytoggle.extreme;\ninterface IDisplayToggleService {\n    int toggleDisplays(int mode, in int[] whitelistDisplayIds);\n    String runCommand(String command);\n}\n''')

svc = root / 'app/src/main/java/com/displaytoggle/extreme/DisplayToggleService.java'
s = svc.read_text()
marker = '    @Override\n    public int toggleDisplays(int mode, int[] whitelistDisplayIds) {'
method = r'''    @Override
    public String runCommand(String command) {
        if (command == null) return "ERROR null command";
        if (!(command.startsWith("cmd device_state state ") || command.equals("cmd device_state state reset") || command.equals("cmd device_state state"))) {
            return "ERROR command not allowed";
        }
        StringBuilder sb = new StringBuilder();
        try {
            Process p = new ProcessBuilder("/system/bin/sh", "-c", command + " 2>&1").redirectErrorStream(true).start();
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

controller = root / 'app/src/main/java/com/displaytoggle/extreme/HingeControllerService.java'
controller.write_text(r'''package com.displaytoggle.extreme;

import android.app.*;
import android.content.*;
import android.hardware.*;
import android.os.*;
import androidx.core.app.NotificationCompat;
import rikka.shizuku.Shizuku;

public class HingeControllerService extends Service implements SensorEventListener {
    public static final String ACTION_STATUS = "com.displaytoggle.extreme.CONTROLLER_STATUS";
    private static final String CH = "magicv2_hinge_controller";
    private SensorManager sm;
    private Sensor hinge;
    private IDisplayToggleService shell;
    private Shizuku.UserServiceArgs args;
    private float last = Float.NaN;
    private float closeAngle = 60f;
    private float openAngle = 165f;
    private int externalState = 4;
    private long maxHoldMs = 2500;
    private boolean forcedExternal = false;
    private boolean forcedInner = false;
    private long forcedAt = 0L;
    private String lastAction = "Idle";

    @Override public void onCreate() {
        super.onCreate();
        createChannel();
        startForeground(7701, notification("Starting…"));
        android.content.SharedPreferences p = getSharedPreferences("magicv2", MODE_PRIVATE);
        closeAngle = p.getFloat("closeAngle", 60f);
        openAngle = p.getFloat("openAngle", 165f);
        externalState = p.getInt("externalState", 4);
        maxHoldMs = p.getLong("holdMs", 2500L);

        sm = (SensorManager)getSystemService(SENSOR_SERVICE);
        hinge = sm.getDefaultSensor(Sensor.TYPE_HINGE_ANGLE, true);
        if (hinge == null) hinge = sm.getDefaultSensor(Sensor.TYPE_HINGE_ANGLE);
        if (hinge != null) sm.registerListener(this, hinge, 8000);

        try {
            args = new Shizuku.UserServiceArgs(new ComponentName(this, DisplayToggleService.class))
                    .daemon(false).processNameSuffix("magicv2_angle_controller");
            Shizuku.bindUserService(args, conn);
        } catch (Throwable e) {
            lastAction = "Shizuku bind error: " + e.getClass().getSimpleName();
            broadcast(Float.NaN, "ERROR");
        }
    }

    private final ServiceConnection conn = new ServiceConnection() {
        @Override public void onServiceConnected(ComponentName n, IBinder b) {
            shell = IDisplayToggleService.Stub.asInterface(b);
            lastAction = "Ready";
            updateNotif("Ready — close " + closeAngle + "°, open " + openAngle + "°");
        }
        @Override public void onServiceDisconnected(ComponentName n) {
            shell = null;
            lastAction = "Shizuku service disconnected";
        }
    };

    @Override public void onSensorChanged(SensorEvent e) {
        float a = e.values[0];
        if (Float.isNaN(last)) { last = a; broadcast(a, "IDLE"); return; }
        float d = a - last;
        String dir = d < -0.25f ? "CLOSING" : (d > 0.25f ? "OPENING" : "STABLE");
        long now = SystemClock.elapsedRealtime();

        if (!forcedExternal && !forcedInner && d < -0.25f && last > closeAngle && a <= closeAngle) {
            forceState(externalState, "External @ " + Math.round(a) + "°");
            forcedExternal = true; forcedAt = now;
        } else if (!forcedExternal && !forcedInner && d > 0.25f && last < openAngle && a >= openAngle) {
            forceState(1, "Inner @ " + Math.round(a) + "°");
            forcedInner = true; forcedAt = now;
        }

        if (forcedExternal) {
            if (a <= 35f || d > 0.8f || now - forcedAt >= maxHoldMs) resetState("Reset external");
        }
        if (forcedInner) {
            if (a >= 178f || d < -0.8f || now - forcedAt >= maxHoldMs) resetState("Reset inner");
        }

        last = a;
        broadcast(a, dir);
    }

    private synchronized void forceState(int state, String action) {
        lastAction = action;
        runAsync("cmd device_state state " + state);
        updateNotif(action);
    }

    private synchronized void resetState(String action) {
        if (!forcedExternal && !forcedInner) return;
        forcedExternal = false; forcedInner = false;
        lastAction = action;
        runAsync("cmd device_state state reset");
        updateNotif(action);
    }

    private void runAsync(String cmd) {
        IDisplayToggleService s = shell;
        if (s == null) { lastAction = "Shizuku not ready"; return; }
        new Thread(() -> { try { s.runCommand(cmd); } catch (Throwable ignored) {} }).start();
    }

    private void broadcast(float angle, String dir) {
        Intent i = new Intent(ACTION_STATUS);
        i.setPackage(getPackageName());
        i.putExtra("angle", angle);
        i.putExtra("dir", dir);
        i.putExtra("action", lastAction);
        sendBroadcast(i);
    }

    private void createChannel() {
        NotificationManager nm = getSystemService(NotificationManager.class);
        nm.createNotificationChannel(new NotificationChannel(CH, "Magic V2 hinge controller", NotificationManager.IMPORTANCE_LOW));
    }

    private Notification notification(String txt) {
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(this, 1, open, PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        return new NotificationCompat.Builder(this, CH).setSmallIcon(android.R.drawable.ic_menu_rotate).setContentTitle("Magic V2 angle controller").setContentText(txt).setContentIntent(pi).setOngoing(true).build();
    }
    private void updateNotif(String txt) { getSystemService(NotificationManager.class).notify(7701, notification(txt)); }

    @Override public void onDestroy() {
        if (sm != null) sm.unregisterListener(this);
        if (shell != null) { try { shell.runCommand("cmd device_state state reset"); } catch (Throwable ignored) {} }
        try { if (args != null) Shizuku.unbindUserService(args, conn, true); } catch (Throwable ignored) {}
        super.onDestroy();
    }

    @Override public void onAccuracyChanged(Sensor s, int a) {}
    @Override public IBinder onBind(Intent i) { return null; }
}
''')

activity = root / 'app/src/main/java/com/displaytoggle/extreme/MainActivity.java'
activity.write_text(r'''package com.displaytoggle.extreme;

import android.app.Activity;
import android.content.*;
import android.content.pm.PackageManager;
import android.hardware.*;
import android.os.Bundle;
import android.widget.*;
import rikka.shizuku.Shizuku;

public class MainActivity extends Activity implements SensorEventListener {
    private EditText closeEt, openEt, holdEt;
    private Spinner stateSp;
    private TextView status;
    private SensorManager sm;
    private Sensor hinge;

    private final BroadcastReceiver receiver = new BroadcastReceiver() {
        @Override public void onReceive(Context c, Intent i) {
            float a = i.getFloatExtra("angle", Float.NaN);
            String d = i.getStringExtra("dir");
            String act = i.getStringExtra("action");
            status.setText("Controller ON\nAngle: " + (Float.isNaN(a)?"?":String.format(java.util.Locale.US,"%.1f°",a)) + "\nDirection: " + d + "\nLast action: " + act);
        }
    };

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout box = new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(24,24,24,24);
        TextView title = new TextView(this); title.setText("MAGIC V2 — ANGLE CONTROLLER"); title.setTextSize(21f);
        TextView help = new TextView(this); help.setText("Switch screens before Honor's native thresholds. Defaults: external at 60°, internal at 165°. Start Shizuku first.");
        closeEt = field("60"); openEt = field("165"); holdEt = field("2500");
        stateSp = new Spinner(this); stateSp.setAdapter(new ArrayAdapter<String>(this, android.R.layout.simple_spinner_dropdown_item, new String[]{"STATE_CLOSED (4)","STATE_REAR (8)"}));
        Button start = new Button(this); start.setText("START CONTROLLER");
        Button stop = new Button(this); stop.setText("STOP + RESET");
        Button testExt = new Button(this); testExt.setText("TEST EXTERNAL NOW");
        Button testIn = new Button(this); testIn.setText("TEST INTERNAL NOW");
        status = new TextView(this); status.setTextSize(15f);

        box.addView(title); box.addView(help);
        box.addView(label("Closing switch angle (°)")); box.addView(closeEt);
        box.addView(label("Opening switch angle (°)")); box.addView(openEt);
        box.addView(label("Maximum forced-state hold (ms)")); box.addView(holdEt);
        box.addView(label("External state")); box.addView(stateSp);
        box.addView(start); box.addView(stop); box.addView(testExt); box.addView(testIn); box.addView(status);
        ScrollView sv = new ScrollView(this); sv.addView(box); setContentView(sv);

        android.content.SharedPreferences p = getSharedPreferences("magicv2", MODE_PRIVATE);
        closeEt.setText(String.valueOf(p.getFloat("closeAngle",60f))); openEt.setText(String.valueOf(p.getFloat("openAngle",165f))); holdEt.setText(String.valueOf(p.getLong("holdMs",2500)));
        stateSp.setSelection(p.getInt("externalState",4)==8?1:0);

        start.setOnClickListener(v -> startController());
        stop.setOnClickListener(v -> { stopService(new Intent(this,HingeControllerService.class)); status.setText("Controller stopped. Device state reset requested."); });
        testExt.setOnClickListener(v -> oneShot(stateSp.getSelectedItemPosition()==1?8:4));
        testIn.setOnClickListener(v -> oneShot(1));

        sm=(SensorManager)getSystemService(SENSOR_SERVICE); hinge=sm.getDefaultSensor(Sensor.TYPE_HINGE_ANGLE,true); if(hinge==null) hinge=sm.getDefaultSensor(Sensor.TYPE_HINGE_ANGLE);
    }

    private TextView label(String s){ TextView t=new TextView(this); t.setText(s); t.setTextSize(15f); return t; }
    private EditText field(String s){ EditText e=new EditText(this); e.setInputType(android.text.InputType.TYPE_CLASS_NUMBER|android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL); e.setText(s); return e; }

    private void startController(){
        if(!Shizuku.pingBinder()){ status.setText("Shizuku is not running."); return; }
        if(Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED){ Shizuku.requestPermission(95); status.setText("Grant Shizuku permission, then press START again."); return; }
        try{
            float ca=Float.parseFloat(closeEt.getText().toString()); float oa=Float.parseFloat(openEt.getText().toString()); long hm=Long.parseLong(holdEt.getText().toString());
            if(ca<40||ca>120||oa<130||oa>179||oa<=ca){ status.setText("Invalid angles. Suggested: close 50–80°, open 155–175°."); return; }
            int es=stateSp.getSelectedItemPosition()==1?8:4;
            getSharedPreferences("magicv2",MODE_PRIVATE).edit().putFloat("closeAngle",ca).putFloat("openAngle",oa).putLong("holdMs",hm).putInt("externalState",es).apply();
            Intent i=new Intent(this,HingeControllerService.class); if(android.os.Build.VERSION.SDK_INT>=26) startForegroundService(i); else startService(i);
            status.setText("Starting controller…");
        }catch(Throwable e){ status.setText("Settings error: "+e); }
    }

    private void oneShot(int state){
        if(!Shizuku.pingBinder()||Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED){ status.setText("Shizuku permission required."); return; }
        Shizuku.UserServiceArgs args=new Shizuku.UserServiceArgs(new ComponentName(this,DisplayToggleService.class)).daemon(false).processNameSuffix("magicv2_manual");
        Shizuku.bindUserService(args,new ServiceConnection(){ public void onServiceConnected(ComponentName n,android.os.IBinder b){ IDisplayToggleService s=IDisplayToggleService.Stub.asInterface(b); new Thread(()->{try{s.runCommand("cmd device_state state "+state); Thread.sleep(1800); s.runCommand("cmd device_state state reset");}catch(Throwable ignored){} runOnUiThread(()->status.setText("Manual state "+state+" test complete + reset."));}).start(); } public void onServiceDisconnected(ComponentName n){} });
    }

    @Override protected void onResume(){ super.onResume(); registerReceiver(receiver,new IntentFilter(HingeControllerService.ACTION_STATUS), Context.RECEIVER_NOT_EXPORTED); if(hinge!=null) sm.registerListener(this,hinge,SensorManager.SENSOR_DELAY_NORMAL); }
    @Override protected void onPause(){ super.onPause(); try{unregisterReceiver(receiver);}catch(Throwable ignored){} if(sm!=null)sm.unregisterListener(this); }
    @Override public void onSensorChanged(SensorEvent e){ if(status.getText().toString().startsWith("Controller ON"))return; status.setText("Live hinge angle: "+String.format(java.util.Locale.US,"%.1f°",e.values[0])+"\nController not reporting yet."); }
    @Override public void onAccuracyChanged(Sensor s,int a){}
}
''')
