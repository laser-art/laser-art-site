from pathlib import Path
import runpy

runpy.run_path('tools/patch_magicv2_advanced_diag.py', run_name='__main__')

controller = Path('displaytoggle/app/src/main/java/com/displaytoggle/extreme/HingeControllerService.java')
s = controller.read_text()
s = s.replace(
    'if (!forcedExternal && !forcedInner && d < -0.25f && last > closeAngle && a <= closeAngle) {',
    'if (!forcedExternal && !forcedInner && last > closeAngle && a <= closeAngle) {'
)
s = s.replace(
    'if (!forcedExternal && !forcedInner && d > 0.25f && last < openAngle && a >= openAngle) {',
    'if (!forcedExternal && !forcedInner && last < openAngle && a >= openAngle) {'
)
s = s.replace(
    'String dir = d < -0.25f ? "CLOSING" : (d > 0.25f ? "OPENING" : "STABLE");',
    'String dir = d < -0.02f ? "CLOSING" : (d > 0.02f ? "OPENING" : "STABLE");'
)
s = s.replace('Magic V2 angle controller V2', 'Magic V2 angle controller V3')
controller.write_text(s)

activity = Path('displaytoggle/app/src/main/java/com/displaytoggle/extreme/MainActivity.java')
a = activity.read_text()
a = a.replace('MAGIC V2 — ANGLE CONTROLLER V2', 'MAGIC V2 — ANGLE CONTROLLER V3')
a = a.replace('Starting controller V2…', 'Starting controller V3…')
activity.write_text(a)
