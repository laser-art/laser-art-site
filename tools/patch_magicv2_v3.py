from pathlib import Path

shader = Path('duo-open/app/src/main/java/com/duoopen/fold/DuoShader.kt')
s = shader.read_text()
s = s.replace('const val PANEL_ON_HINGE = 20f', 'const val PANEL_ON_HINGE = 43f')
shader.write_text(s)

service = Path('duo-open/app/src/main/java/com/duoopen/overlay/FoldOverlayService.kt')
s = service.read_text()

s = s.replace(
    'private var timedResolve = false',
    'private var timedResolve = false\n    private var handoffSnapshot: Bitmap? = null'
)

old = """if (inner != innerPanel) {
            innerPanel = inner
            panelSwitched = true
            if (phase != Phase.IDLE) removeOverlay() // old panel's snapshot is meaningless now
        }"""
new = """if (inner != innerPanel) {
            innerPanel = inner
            panelSwitched = true
            if (phase != Phase.IDLE) removeOverlay()
            val cached = handoffSnapshot
            if (cached != null && !cached.isRecycled) {
                val copy = cached.copy(Bitmap.Config.ARGB_8888, false)
                if (copy != null) {
                    val peak = DuoShader.MAX_TILT * DuoSettings.config.value.intensity.coerceAtMost(1f)
                    show(copy, peak, fadeIn = false, timed = !innerPanel)
                    if (innerPanel) follower?.setTarget(currentTilt())
                    panelSwitched = false
                    restArmed = false
                    return
                }
            }
        }"""
s = s.replace(old, new)

s = s.replace(
    'val tilt = startTilt ?: currentTilt()',
    'val tilt = if (afterSwap) DuoShader.MAX_TILT * DuoSettings.config.value.intensity.coerceAtMost(1f) else (startTilt ?: currentTilt())'
)

marker = '// Closing onto the cover: the hinge HAL goes quiet around 30°, so the'
s = s.replace(marker, '''handoffSnapshot?.recycle()\n        handoffSnapshot = runCatching { bitmap.copy(Bitmap.Config.ARGB_8888, false) }.getOrNull()\n\n        ''' + marker)

s = s.replace(
    'show(bitmap, tilt, fadeIn = afterSwap, timed = timed)',
    'show(bitmap, tilt, fadeIn = false, timed = timed)'
)
s = s.replace('private const val TIMED_RESOLVE_TAU_S = 0.07f', 'private const val TIMED_RESOLVE_TAU_S = 0.14f')
s = s.replace('private const val FADE_IN_MS = 140L', 'private const val FADE_IN_MS = 0L')
s = s.replace('private const val FADE_OUT_FLAT_MS = 120L', 'private const val FADE_OUT_FLAT_MS = 80L')

service.write_text(s)
print('Magic V2 v3 patch applied')
