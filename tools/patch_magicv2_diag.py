from pathlib import Path

root = Path('duo-open')

# Calibrate the shader to the observed HONOR hand-off.
shader = root / 'app/src/main/java/com/duoopen/fold/DuoShader.kt'
s = shader.read_text()
s = s.replace('const val PANEL_ON_HINGE = 20f', 'const val PANEL_ON_HINGE = 43f')
shader.write_text(s)

service = root / 'app/src/main/java/com/duoopen/overlay/FoldOverlayService.kt'
s = service.read_text()

# Imports for the diagnostic HUD.
s = s.replace('import android.view.WindowManager\n', 'import android.view.WindowManager\nimport android.widget.TextView\nimport android.graphics.Color\nimport android.text.method.ScrollingMovementMethod\n')

# Diagnostic state fields.
s = s.replace('private var timedResolve = false\n', '''private var timedResolve = false

    // HONOR Magic V2 on-device diagnostic HUD.
    private var diagWm: WindowManager? = null
    private var diagView: TextView? = null
    private var diagLastEvent = "service start"
    private var diagCapture = "none"
    private val diagHistory = ArrayDeque<String>()
''')

# Start HUD on service connect.
s = s.replace('Log.i(TAG, "connected; hinge=${hinge.sensor?.name} inner=$innerPanel")', '''Log.i(TAG, "connected; hinge=${hinge.sensor?.name} inner=$innerPanel")
        diagAdd("connected sensor=${hinge.sensor?.name ?: "NONE"}")
        diagEnsure()
        diagUpdate()
''')

# Remove HUD on destroy.
s = s.replace('removeOverlay()\n        scope.cancel()', 'removeOverlay()\n        diagRemove()\n        scope.cancel()')

# Record hinge values before evaluate.
s = s.replace('private fun onHinge(angle: Float) {\n        lastHingeMoveMs', '''private fun onHinge(angle: Float) {
        diagLastEvent = "hinge %.1f°".format(angle)
        diagAdd(diagLastEvent)
        diagUpdate()
        lastHingeMoveMs''')

# Record display changes at beginning of evaluate.
s = s.replace('private fun evaluate() {\n        if (demoRunning) return', '''private fun evaluate() {
        diagUpdate()
        if (demoRunning) return''')

# Record panel swap.
s = s.replace('Log.i(TAG, "panel swapped (inner=$inner) at hinge=$angle")', '''Log.i(TAG, "panel swapped (inner=$inner) at hinge=$angle")
                diagLastEvent = "PANEL SWAP inner=$inner @ %.1f°".format(angle)
                diagAdd(diagLastEvent)
                diagUpdate()''')

# Record leaving rest.
s = s.replace('Log.i(TAG, "leaving rest (inner=$inner) at hinge=$angle")', '''Log.i(TAG, "leaving rest (inner=$inner) at hinge=$angle")
                diagLastEvent = "leave rest inner=$inner @ %.1f°".format(angle)
                diagAdd(diagLastEvent)
                diagUpdate()''')

# Capture start diagnostics.
s = s.replace('phase = Phase.CAPTURING\n        capture(gen = ++captureGen', '''phase = Phase.CAPTURING
        diagCapture = "request afterSwap=$afterSwap"
        diagAdd("capture request afterSwap=$afterSwap angle=${hinge.lastAngle}")
        diagUpdate()
        capture(gen = ++captureGen''')

# Capture success diagnostics.
s = s.replace('override fun onSuccess(result: ScreenshotResult) {\n                val buffer', '''override fun onSuccess(result: ScreenshotResult) {
                diagCapture = "success attempt=$attempt"
                diagAdd("capture SUCCESS attempt=$attempt angle=${hinge.lastAngle}")
                diagUpdate()
                val buffer''')

# Black capture diagnostics.
s = s.replace('Log.i(TAG, "capture $attempt is black after ${SystemClock.uptimeMillis() - t0}ms; retrying")', '''Log.i(TAG, "capture $attempt is black after ${SystemClock.uptimeMillis() - t0}ms; retrying")
                        diagCapture = "BLACK attempt=$attempt"
                        diagAdd("capture BLACK attempt=$attempt angle=${hinge.lastAngle}")
                        diagUpdate()''')

# Screenshot failure diagnostics.
s = s.replace('Log.w(TAG, "screenshot failed: $errorCode")', '''Log.w(TAG, "screenshot failed: $errorCode")
                diagCapture = "FAIL code=$errorCode"
                diagAdd("capture FAIL code=$errorCode angle=${hinge.lastAngle}")
                diagUpdate()''')

# Timeout diagnostics.
s = s.replace('Log.w(TAG, "capture $attempt timed out; giving up")', '''Log.w(TAG, "capture $attempt timed out; giving up")
                diagCapture = "TIMEOUT attempt=$attempt"
                diagAdd("capture TIMEOUT attempt=$attempt angle=${hinge.lastAngle}")
                diagUpdate()''')

# Show overlay diagnostics.
s = s.replace('Log.i(TAG, "showing ${bitmap.width}x${bitmap.height} at tilt=$tilt (capture ${SystemClock.uptimeMillis() - t0}ms)${if (timed) " timed" else ""}")', '''Log.i(TAG, "showing ${bitmap.width}x${bitmap.height} at tilt=$tilt (capture ${SystemClock.uptimeMillis() - t0}ms)${if (timed) " timed" else ""}")
        diagLastEvent = "SHOW tilt=%.1f inner=$innerPanel timed=$timed".format(tilt)
        diagAdd(diagLastEvent)
        diagUpdate()''')

# Inject diagnostic helper methods before companion object.
marker = '    companion object {\n'
diag = r'''
    private fun diagStateName(state: Int): String = when (state) {
        Display.STATE_ON -> "ON"
        Display.STATE_OFF -> "OFF"
        Display.STATE_DOZE -> "DOZE"
        Display.STATE_DOZE_SUSPEND -> "DOZE_SUSP"
        Display.STATE_VR -> "VR"
        else -> state.toString()
    }

    private fun diagAdd(msg: String) {
        val line = "${SystemClock.uptimeMillis() % 100000}: $msg"
        diagHistory.addLast(line)
        while (diagHistory.size > 10) diagHistory.removeFirst()
    }

    private fun diagEnsure() {
        val display = defaultDisplay() ?: return
        if (diagView != null) return
        val wm = createDisplayContext(display)
            .createWindowContext(WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY, null)
            .getSystemService(WindowManager::class.java)
        val tv = TextView(this).apply {
            setTextColor(Color.WHITE)
            setBackgroundColor(0xCC000000.toInt())
            textSize = 12f
            setPadding(16, 12, 16, 12)
            movementMethod = ScrollingMovementMethod()
        }
        val p = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT,
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            title = "DuoOpenDiag"
        }
        runCatching { wm.addView(tv, p) }.onSuccess {
            diagWm = wm
            diagView = tv
        }
    }

    private fun diagRemove() {
        val v = diagView ?: return
        runCatching { diagWm?.removeViewImmediate(v) }
        diagView = null
        diagWm = null
    }

    private fun diagUpdate() {
        val d = defaultDisplay()
        // Recreate HUD if MagicOS swapped display backing/window context.
        if (diagView == null) diagEnsure()
        val mode = runCatching { d?.mode }.getOrNull()
        val all = if (::displayManager.isInitialized) displayManager.displays.joinToString(" | ") {
            val m = runCatching { it.mode }.getOrNull()
            "id=${it.displayId}:${diagStateName(it.state)} ${m?.physicalWidth}x${m?.physicalHeight} ${it.name}"
        } else "displayManager?"
        val sensor = if (::hinge.isInitialized) hinge.sensor else null
        val angle = if (::hinge.isInitialized) hinge.lastAngle else Float.NaN
        val inner = runCatching { d.isInnerPanel() }.getOrDefault(false)
        val text = buildString {
            appendLine("DUO OPEN — MAGIC V2 DIAGNOSTIC")
            appendLine("angle=${if (angle.isNaN()) "NaN" else "%.1f°".format(angle)}  sensor=${sensor?.name ?: "NONE"}")
            appendLine("sensorType=${sensor?.stringType ?: "-"} wake=${sensor?.isWakeUpSensor ?: false}")
            appendLine("default id=${d?.displayId} state=${d?.let { diagStateName(it.state) }} mode=${mode?.physicalWidth}x${mode?.physicalHeight} inner=$inner")
            appendLine("phase=$phase overlay=${overlay != null} panelSwitched=$panelSwitched restArmed=$restArmed")
            appendLine("capture=$diagCapture")
            appendLine("event=$diagLastEvent")
            appendLine("displays: $all")
            appendLine("--- recent ---")
            diagHistory.forEach { appendLine(it) }
        }
        handler.post { diagView?.text = text }
    }

'''
s = s.replace(marker, diag + marker)

# Make diagnostic HUD less likely to disappear behind effect: keep it recreated after removeOverlay.
s = s.replace('private fun removeOverlay() {\n        phase = Phase.IDLE', 'private fun removeOverlay() {\n        phase = Phase.IDLE\n        diagUpdate()')

service.write_text(s)

# Give diagnostic build a different app label and version for easy identification.
build = root / 'app/build.gradle.kts'
b = build.read_text()
b = b.replace('versionName = "1.0.0"', 'versionName = "1.0.0-magicv2-diag"')
build.write_text(b)
