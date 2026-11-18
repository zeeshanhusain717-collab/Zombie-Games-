package com.zombiez.game

import android.opengl.GLES20
import android.opengl.GLSurfaceView
import android.opengl.Matrix
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.opengles.GL10
import kotlin.math.*
import kotlin.random.Random

// ===================== GAME LOGIC (no OpenGL) =====================
class GameLogic {

    companion object {
        const val WORLD = 140f
        const val PLAYER_R = 0.6f
        const val PLAYER_MAX_HP = 100f
        const val MAG_SIZE = 12
        const val RESERVE_START = 60
        const val RELOAD_TIME = 1.5f
        const val FIRE_DELAY = 0.15f
        const val BULLET_DMG = 25f
        const val PICKUP_DIST = 3f
        const val DROP_FALL_SPEED = 9f
        const val DROP_PARACHUTE_HEIGHT = 18f
        val DROP_GAPS = floatArrayOf(30f, 60f, 90f)
    }

    class Zombie(var x: Float, var z: Float, val big: Boolean) {
        val scale = if (big) 1.35f else 1f
        val maxHp = if (big) 120f else 60f
        var hp = maxHp
        val speed = if (big) 1.6f else 2.4f
        val dmg = if (big) 18f else 10f
        var hitCd = 0f
    }

    class Bullet(var x: Float, var z: Float, val dx: Float, val dz: Float) {
        var life = 1.5f
    }

    class Drop(val x: Float, val z: Float) {
        var y = DROP_PARACHUTE_HEIGHT
        var landed = false
        var looted = false
    }

    val buildings = ArrayList<FloatArray>()   // x, z, width, height, depth
    val zombies = mutableListOf<Zombie>()
    val bullets = mutableListOf<Bullet>()
    val drops = mutableListOf<Drop>()

    var wave = 0
    var spawnLeft = 0
    var spawnTimer = 0f
    var kills = 0
    var playerHp = PLAYER_MAX_HP
    var ammo = MAG_SIZE
    var reserve = RESERVE_START
    var reloadTimer = 0f
    var fireCd = 0f

    var dropIndex = 0
    var dropTimer = DROP_GAPS[0]
    var lootPrev = false

    var px = 0f
    var pz = 0f
    var yaw = 0f
    var pitch = 0.35f
    val moveSpeed = 6f

    var screenW = 1f
    var screenH = 1f

    private val lock = Any()
    // [side, originX, originY, lastX, lastY]; side: 0 move, 1 look, 2 ADS, 3 fire, 4 loot
    private val touches = HashMap<Int, FloatArray>()
    private var moveX = 0f
    private var moveY = 0f
    private var lookDx = 0f
    private var lookDy = 0f

    var inMoveX = 0f
    var inMoveY = 0f
    var inAds = false
    var inFire = false
    var inLoot = false

    fun touchDown(id: Int, x: Float, y: Float) {
        synchronized(lock) {
            val w = screenW
            val h = screenH
            val side = when {
                x < w * 0.4f -> 0f
                y > h * 0.55f && x > w * 0.8f -> 2f
                y > h * 0.55f && x > w * 0.45f -> 3f
                y > h * 0.55f && x > w * 0.25f && x <= w * 0.45f -> 4f
                else -> 1f
            }
            touches[id] = floatArrayOf(side, x, y, x, y)
            if (side == 0f) {
                moveX = 0f
                moveY = 0f
            }
        }
    }

    fun touchMove(id: Int, x: Float, y: Float) {
        synchronized(lock) {
            val t = touches[id] ?: return
            when (t[0]) {
                0f -> {
                    moveX = ((x - t[1]) / 120f).coerceIn(-1f, 1f)
                    moveY = ((y - t[2]) / 120f).coerceIn(-1f, 1f)
                }
                1f -> {
                    lookDx += x - t[3]
                    lookDy += y - t[4]
                }
            }
            t[3] = x
            t[4] = y
        }
    }

    fun touchUp(id: Int) {
        synchronized(lock) {
            val t = touches.remove(id) ?: return
            if (t[0] == 0f) {
                moveX = 0f
                moveY = 0f
            }
        }
    }

    fun touchCancel() {
        synchronized(lock) {
            touches.clear()
            moveX = 0f
            moveY = 0f
        }
    }

    fun setScreen(w: Float, h: Float) {
        screenW = w
        screenH = h
    }

    fun update(dt: Float) {
        var look = 0f
        var lookY = 0f
        synchronized(lock) {
            inMoveX = moveX
            inMoveY = moveY
            look = lookDx
            lookY = lookDy
            lookDx = 0f
            lookDy = 0f
            inAds = touches.values.any { it[0] == 2f }
            inFire = touches.values.any { it[0] == 3f }
            inLoot = touches.values.any { it[0] == 4f }
        }

        yaw += look * 0.008f
        pitch = (pitch + lookY * 0.004f).coerceIn(0.1f, 0.9f)

        if (wave == 0) startWave(1)

        val fwdX = sin(yaw)
        val fwdZ = cos(yaw)
        val rgtX = cos(yaw)
        val rgtZ = -sin(yaw)

        if (hypot(inMoveX, inMoveY) > 0.12f) {
            var mx = rgtX * inMoveX + fwdX * (-inMoveY)
            var mz = rgtZ * inMoveX + fwdZ * (-inMoveY)
            val len = hypot(mx, mz)
            if (len > 1f) {
                mx /= len
                mz /= len
            }
            val speed = if (inAds) 3.5f else moveSpeed
            val nx = (px + mx * speed * dt).coerceIn(-WORLD + 2f, WORLD - 2f)
            if (!blocked(nx, pz, PLAYER_R)) px = nx
            val nz = (pz + mz * speed * dt).coerceIn(-WORLD + 2f, WORLD - 2f)
            if (!blocked(px, nz, PLAYER_R)) pz = nz
        }

        if (reloadTimer > 0f) {
            reloadTimer -= dt
            if (reloadTimer <= 0f) {
                val take = min(MAG_SIZE - ammo, reserve)
                ammo += take
                reserve -= take
            }
        } else if (ammo == 0 && reserve > 0) {
            reloadTimer = RELOAD_TIME
        }

        fireCd = max(0f, fireCd - dt)
        if (inFire && fireCd <= 0f && ammo > 0 && reloadTimer <= 0f) {
            ammo--
            fireCd = FIRE_DELAY
            bullets.add(Bullet(px + fwdX, pz + fwdZ, fwdX * 60f, fwdZ * 60f))
        }

        val bIt = bullets.iterator()
        while (bIt.hasNext()) {
            val b = bIt.next()
            b.x += b.dx * dt
            b.z += b.dz * dt
            b.life -= dt
            var hit = blocked(b.x, b.z, 0f)
            if (!hit) {
                val zIt = zombies.iterator()
                while (zIt.hasNext()) {
                    val z = zIt.next()
                    if (hypot(b.x - z.x, b.z - z.z) < 0.7f * z.scale + 0.2f) {
                        z.hp -= BULLET_DMG
                        hit = true
                        if (z.hp <= 0f) {
                            zIt.remove()
                            kills++
                            if (Random.nextFloat() < 0.25f) reserve += 6
                        }
                        break
                    }
                }
            }
            if (hit || b.life <= 0f || abs(b.x) > WORLD || abs(b.z) > WORLD) bIt.remove()
        }

        for (z in zombies) {
            z.hitCd = max(0f, z.hitCd - dt)
            val dx = px - z.x
            val dz = pz - z.z
            val d = hypot(dx, dz)
            if (d > 1.2f * z.scale + PLAYER_R) {
                val nx = z.x + dx / d * z.speed * dt
                val nz = z.z + dz / d * z.speed * dt
                if (!blocked(nx, z.z, 0.5f * z.scale)) z.x = nx
                if (!blocked(z.x, nz, 0.5f * z.scale)) z.z = nz
            } else if (z.hitCd <= 0f) {
                playerHp -= z.dmg
                z.hitCd = 1f
            }
        }

        dropTimer -= dt
        if (dropTimer <= 0f) {
            spawnDrop()
            dropIndex = (dropIndex + 1) % DROP_GAPS.size
            dropTimer = DROP_GAPS[dropIndex]
        }
        for (d in drops) {
            if (d.landed || d.looted) continue
            d.y -= DROP_FALL_SPEED * dt
            if (d.y <= 0f) {
                d.y = 0f
                d.landed = true
            }
        }
        if (inLoot && !lootPrev) {
            for (d in drops) {
                if (d.landed && !d.looted && hypot(px - d.x, pz - d.z) < PICKUP_DIST) {
                    d.looted = true
                    reserve += 30
                    playerHp = min(PLAYER_MAX_HP, playerHp + 40f)
                    break
                }
            }
        }
        lootPrev = inLoot
        drops.removeAll { it.looted }

        if (playerHp <= 0f) {
            playerHp = PLAYER_MAX_HP
            px = 0f
            pz = 0f
        }

        if (spawnLeft > 0) {
            spawnTimer -= dt
            if (spawnTimer <= 0f) {
                spawnZombie()
                spawnLeft--
                spawnTimer = 0.8f
            }
        } else if (zombies.isEmpty()) {
            startWave(wave + 1)
        }
    }

    private fun spawnDrop() {
        for (attempt in 0 until 20) {
            val x = (Random.nextFloat() * 2f - 1f) * (WORLD - 20f)
            val z = (Random.nextFloat() * 2f - 1f) * (WORLD - 20f)
            if (!blocked(x, z, 1.5f)) {
                drops.add(Drop(x, z))
                return
            }
        }
    }

    private fun startWave(n: Int) {
        wave = n
        spawnLeft = 4 + n * 2
        spawnTimer = 1f
    }

    private fun spawnZombie() {
        for (attempt in 0 until 15) {
            val a = Random.nextFloat() * 2f * PI.toFloat()
            val d = 35f + Random.nextFloat() * 20f
            val x = (px + cos(a) * d).coerceIn(-WORLD + 3f, WORLD - 3f)
            val z = (pz + sin(a) * d).coerceIn(-WORLD + 3f, WORLD - 3f)
            if (!blocked(x, z, 1.2f)) {
                val big = wave >= 3 && Random.nextFloat() < 0.25f
                zombies.add(Zombie(x, z, big))
                return
            }
        }
    }

    fun buildCity() {
        if (buildings.isNotEmpty()) return
        val rng = Random(7)
        var tries = 0
        while (buildings.size < 45 && tries < 800) {
            tries++
            val w = 6f + rng.nextFloat() * 8f
            val d = 6f + rng.nextFloat() * 8f
            val h = 8f + rng.nextFloat() * 22f
            val x = -WORLD + 10f + rng.nextFloat() * (2f * WORLD - 20f)
            val z = -WORLD + 10f + rng.nextFloat() * (2f * WORLD - 20f)
            if (abs(x) < 16f && abs(z) < 16f) continue
            var overlap = false
            for (b in buildings) {
                if (abs(x - b[0]) < (w + b[2]) / 2f + 3f && abs(z - b[1]) < (d + b[4]) / 2f + 3f) {
                    overlap = true
                    break
                }
            }
            if (!overlap) buildings.add(floatArrayOf(x, z, w, h, d))
        }
    }

    fun blocked(x: Float, z: Float, r: Float): Boolean {
        for (b in buildings) {
            if (abs(x - b[0]) < b[2] / 2f + r && abs(z - b[1]) < b[4] / 2f + r) return true
        }
        return false
    }
}

// ===================== OPENGL DRAWING =====================
class GameDraw : GLSurfaceView.Renderer {

    private val logic = GameLogic()
    private var lastTime = 0L

    fun touchDown(id: Int, x: Float, y: Float) = logic.touchDown(id, x, y)
    fun touchMove(id: Int, x: Float, y: Float) = logic.touchMove(id, x, y)
    fun touchUp(id: Int) = logic.touchUp(id)
    fun touchCancel() = logic.touchCancel()

    class Mesh(verts: FloatArray, normals: FloatArray) {
        val count: Int = verts.size / 3
        val pos: FloatBuffer = toBuffer(verts)
        val nor: FloatBuffer = toBuffer(normals)

        private fun toBuffer(a: FloatArray): FloatBuffer {
            val bb = ByteBuffer.allocateDirect(a.size * 4).order(ByteOrder.nativeOrder())
            val fb = bb.asFloatBuffer()
            fb.put(a)
            fb.position(0)
            return fb
        }
    }

    private val VERTEX_SHADER = """
        attribute vec3 aPos;
        attribute vec3 aNor;
        uniform mat4 uMVP;
        varying vec3 vN;
        void main() {
            vN = aNor;
            gl_Position = uMVP * vec4(aPos, 1.0);
        }
    """.trimIndent()

    private val FRAGMENT_SHADER = """
        precision mediump float;
        uniform vec3 uColor;
        varying vec3 vN;
        void main() {
            float l = max(dot(normalize(vN), normalize(vec3(0.4, 1.0, 0.3))), 0.0);
            float shade = 0.35 + 0.65 * l;
            gl_FragColor = vec4(uColor * shade, 1.0);
        }
    """.trimIndent()

    private val proj = FloatArray(16)
    private val view = FloatArray(16)
    private val ortho = FloatArray(16)
    private val model = FloatArray(16)
    private val tmp = FloatArray(16)
    private val mvp = FloatArray(16)

    private var program = 0
    private var aPos = 0
    private var aNor = 0
    private var uMVP = 0
    private var uColor = 0
    private var aspect = 1f

    private lateinit var cube: Mesh
    private lateinit var plane: Mesh

    private val buildingColors = arrayOf(
        floatArrayOf(0.55f, 0.45f, 0.35f),
        floatArrayOf(0.45f, 0.5f, 0.6f),
        floatArrayOf(0.6f, 0.4f, 0.4f),
        floatArrayOf(0.5f, 0.55f, 0.45f)
    )

    private val DIGIT_MASKS = intArrayOf(
        0b111101101101111, 0b010110010010111, 0b111001111100111,
        0b111001111001111, 0b101101111001001, 0b111100111001111,
        0b111100111101111, 0b111001001001001, 0b111101111101111,
        0b111101111001111
    )

    private var camX = 0f
    private var camY = 0f
    private var camZ = 0f
    private var camInit = false

    override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
        GLES20.glClearColor(0.55f, 0.8f, 1f, 1f)
        GLES20.glEnable(GLES20.GL_DEPTH_TEST)

        val vs = compileShader(GLES20.GL_VERTEX_SHADER, VERTEX_SHADER)
        val fs = compileShader(GLES20.GL_FRAGMENT_SHADER, FRAGMENT_SHADER)
        program = GLES20.glCreateProgram()
        GLES20.glAttachShader(program, vs)
        GLES20.glAttachShader(program, fs)
        GLES20.glLinkProgram(program)

        aPos = GLES20.glGetAttribLocation(program, "aPos")
        aNor = GLES20.glGetAttribLocation(program, "aNor")
        uMVP = GLES20.glGetUniformLocation(program, "uMVP")
        uColor = GLES20.glGetUniformLocation(program, "uColor")

        cube = buildCube()
        plane = buildPlane()
        camInit = false

        logic.buildCity()
        lastTime = System.nanoTime()
    }

    override fun onSurfaceChanged(gl: GL10?, width: Int, height: Int) {
        GLES20.glViewport(0, 0, width, height)
        logic.setScreen(width.toFloat(), height.toFloat())
        aspect = width.toFloat() / height.toFloat()
    }

    override fun onDrawFrame(gl: GL10?) {
        val now = System.nanoTime()
        val dt = ((now - lastTime) / 1_000_000_000f).coerceIn(0f, 0.05f)
        lastTime = now

        logic.update(dt)
        render(dt)
    }

    private fun render(dt: Float) {
        val g = logic
        updateCamera(g, dt)

        Matrix.perspectiveM(proj, 0, if (g.inAds) 45f else 60f, aspect, 0.1f, 400f)
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
        GLES20.glUseProgram(program)

        val groundSize = GameLogic.WORLD * 2f + 40f
        drawPart(plane, 0f, 0f, 0f, 0f, 0f, 0f, 0f, groundSize, 1f, groundSize, 0.25f, 0.55f, 0.25f)

        val pal = buildingColors[max(0, g.wave - 1) % buildingColors.size]
        for (b in g.buildings) {
            drawPart(cube, b[0], 0f, b[1], 0f, 0f, b[3] / 2f, 0f, b[2], b[3], b[4], pal[0], pal[1], pal[2])
        }

        val rot = Math.toDegrees(g.yaw.toDouble()).toFloat()
        drawPart(cube, g.px, 0f, g.pz, rot, 0f, 0.6f, 0f, 0.8f, 1.2f, 0.6f, 0.2f, 0.4f, 0.9f)
        drawPart(cube, g.px, 0f, g.pz, rot, 0f, 1.5f, 0f, 0.5f, 0.5f, 0.5f, 0.9f, 0.75f, 0.6f)
        drawPart(cube, g.px, 0f, g.pz, rot, 0f, 1.0f, 0.9f, 0.18f, 0.18f, 1.0f, 0.15f, 0.15f, 0.15f)

        for (z in g.zombies) {
            val ang = Math.toDegrees(atan2((g.px - z.x).toDouble(), (g.pz - z.z).toDouble())).toFloat()
            val s = z.scale
            val bodyR = if (z.big) 0.35f else 0.2f
            val bodyG = if (z.big) 0.5f else 0.6f
            drawPart(cube, z.x, 0f, z.z, ang, 0f, 0.55f * s, 0f, 0.7f * s, 1.1f * s, 0.5f * s, bodyR, bodyG, 0.2f)
            drawPart(cube, z.x, 0f, z.z, ang, 0f, 1.4f * s, 0f, 0.6f * s, 0.6f * s, 0.6f * s, 0.25f, 0.6f, 0.25f)
            drawPart(cube, z.x, 0f, z.z, ang, 0.15f * s, 1.45f * s, 0.31f * s, 0.12f * s, 0.12f * s, 0.05f * s, 1f, 0.1f, 0.1f)
            drawPart(cube, z.x, 0f, z.z, ang, -0.15f * s, 1.45f * s, 0.31f * s, 0.12f * s, 0.12f * s, 0.05f * s, 1f, 0.1f, 0.1f)
        }

        for (d in g.drops) {
            if (d.looted) continue
            if (!d.landed) {
                drawPart(cube, d.x, d.y + 2.4f, d.z, 0f, 0f, 0f, 0f, 2.4f, 0.4f, 2.4f, 0.2f, 0.8f, 0.3f)
            }
            drawPart(cube, d.x, d.y, d.z, 0f, 0f, 0.5f, 0f, 1.2f, 1.0f, 1.2f, 0.45f, 0.35f, 0.15f)
        }

        for (b in g.bullets) {
            drawPart(cube, b.x, 1.2f, b.z, 0f, 0f, 0f, 0f, 0.12f, 0.12f, 0.5f, 1f, 0.9f, 0.2f)
        }

        drawHud(g)
    }

    private fun updateCamera(g: GameLogic, dt: Float) {
        val fwdX = sin(g.yaw)
        val fwdZ = cos(g.yaw)
        val rgtX = cos(g.yaw)
        val rgtZ = -sin(g.yaw)

        val dist = if (g.inAds) 4.5f else 9f
        val shoulder = if (g.inAds) 0.9f else 1.6f
        val desX = g.px - fwdX * dist * cos(g.pitch) + rgtX * shoulder
        val desY = 1.2f + dist * sin(g.pitch)
        val desZ = g.pz - fwdZ * dist * cos(g.pitch) + rgtZ * shoulder

        if (!camInit) {
            camX = desX
            camY = desY
            camZ = desZ
            camInit = true
        }
        val k = 1f - exp(-dt * 12f)
        camX += (desX - camX) * k
        camY += (desY - camY) * k
        camZ += (desZ - camZ) * k

        val tgtX = g.px + fwdX * 5f + rgtX * shoulder * 0.6f
        val tgtZ = g.pz + fwdZ * 5f + rgtZ * shoulder * 0.6f
        Matrix.setLookAtM(view, 0, camX, camY, camZ, tgtX, 1.2f, tgtZ, 0f, 1f, 0f)
    }

    private fun drawHud(g: GameLogic) {
        val w = g.screenW
        val h = g.screenH
        GLES20.glDisable(GLES20.GL_DEPTH_TEST)
        Matrix.orthoM(ortho, 0, 0f, w, h, 0f, -1f, 1f)
        GLES20.glUseProgram(program)

        drawRect2D(w * 0.03f, h * 0.03f, w * 0.3f, h * 0.035f, 0.2f, 0.2f, 0.2f)
        val hpRatio = (g.playerHp / GameLogic.PLAYER_MAX_HP).coerceIn(0f, 1f)
        drawRect2D(w * 0.03f, h * 0.03f, w * 0.3f * hpRatio, h * 0.035f, 0.2f, 0.85f, 0.25f)
        drawNumber(g.playerHp.toInt(), w * 0.34f, h * 0.03f, h * 0.035f, 1f, 1f, 1f)

        drawRect2D(w * 0.03f, h * 0.085f, w * 0.3f * g.ammo / GameLogic.MAG_SIZE.toFloat(), h * 0.03f, 1f, 0.85f, 0.2f)
        drawNumber(g.ammo, w * 0.34f, h * 0.085f, h * 0.03f, 1f, 0.85f, 0.2f)
        drawNumber(g.reserve, w * 0.34f + h * 0.12f, h * 0.085f, h * 0.03f, 1f, 1f, 1f)

        drawNumber(g.wave, w * 0.03f, h * 0.14f, h * 0.03f, 0.8f, 0.9f, 1f)
        drawNumber(g.dropTimer.toInt(), w * 0.2f, h * 0.14f, h * 0.03f, 0.9f, 0.7f, 1f)

        drawRect2D(w * 0.05f, h * 0.7f, w * 0.15f, h * 0.22f, 0.3f, 0.4f, 0.3f)
        drawRect2D(w * 0.27f, h * 0.7f, w * 0.15f, h * 0.22f, if (g.inLoot) 1f else 0.2f, if (g.inLoot) 0.8f else 0.5f, if (g.inLoot) 1f else 0.5f)
        drawRect2D(w * 0.6f, h * 0.7f, w * 0.15f, h * 0.22f, if (g.inFire) 1f else 0.6f, if (g.inFire) 0.3f else 0.15f, 0.15f)
        drawRect2D(w * 0.85f, h * 0.7f, w * 0.12f, h * 0.22f, if (g.inAds) 0.3f else 0.15f, if (g.inAds) 0.5f else 0.25f, if (g.inAds) 1f else 0.5f)

        GLES20.glEnable(GLES20.GL_DEPTH_TEST)
    }

    private fun drawNumber(value: Int, x: Float, y: Float, size: Float, r: Float, g: Float, b: Float) {
        val text = max(0, value).toString()
        val digitW = size * 0.6f
        val gap = size * 0.2f
        var cx = x
        for (ch in text) {
            drawDigit(ch - '0', cx, y, digitW, size, r, g, b)
            cx += digitW + gap
        }
    }

    private fun drawDigit(d: Int, x: Float, y: Float, dw: Float, dh: Float, r: Float, g: Float, b: Float) {
        if (d !in 0..9) return
        val mask = DIGIT_MASKS[d]
        val px3 = dw / 3f
        val py5 = dh / 5f
        for (row in 0 until 5) {
            for (col in 0 until 3) {
                val bit = 14 - (row * 3 + col)
                if ((mask shr bit) and 1 == 1) {
                    drawRect2D(x + col * px3, y + row * py5, px3 * 0.9f, py5 * 0.9f, r, g, b)
                }
            }
        }
    }

    private fun drawRect2D(x: Float, y: Float, rw: Float, rh: Float, r: Float, g: Float, b: Float) {
        Matrix.setIdentityM(model, 0)
        Matrix.translateM(model, 0, x + rw / 2f, y + rh / 2f, 0f)
        Matrix.scaleM(model, 0, rw, rh, 0.01f)
        Matrix.multiplyMM(mvp, 0, ortho, 0, model, 0)
        GLES20.glUniformMatrix4fv(uMVP, 1, false, mvp, 0)
        GLES20.glUniform3f(uColor, r, g, b)
        bindAndDraw(cube)
    }

    private fun drawPart(
        mesh: Mesh,
        bx: Float, by: Float, bz: Float, rotY: Float,
        lx: Float, ly: Float, lz: Float,
        sx: Float, sy: Float, sz: Float,
        r: Float, g: Float, b: Float
    ) {
        Matrix.setIdentityM(model, 0)
        Matrix.translateM(model, 0, bx, by, bz)
        Matrix.rotateM(model, 0, rotY, 0f, 1f, 0f)
        Matrix.translateM(model, 0, lx, ly, lz)
        Matrix.scaleM(model, 0, sx, sy, sz)

        Matrix.multiplyMM(tmp, 0, view, 0, model, 0)
        Matrix.multiplyMM(mvp, 0, proj, 0, tmp, 0)
        GLES20.glUniformMatrix4fv(uMVP, 1, false, mvp, 0)
        GLES20.glUniform3f(uColor, r, g, b)
        bindAndDraw(mesh)
    }

    private fun bindAndDraw(mesh: Mesh) {
        GLES20.glEnableVertexAttribArray(aPos)
        GLES20.glVertexAttribPointer(aPos, 3, GLES20.GL_FLOAT, false, 0, mesh.pos)
        GLES20.glEnableVertexAttribArray(aNor)
        GLES20.glVertexAttribPointer(aNor, 3, GLES20.GL_FLOAT, false, 0, mesh.nor)
        GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, mesh.count)
    }

    private fun compileShader(type: Int, src: String): Int {
        val s = GLES20.glCreateShader(type)
        GLES20.glShaderSource(s, src)
        GLES20.glCompileShader(s)
        return s
    }

    private fun buildCube(): Mesh {
        val normals = arrayOf(
            floatArrayOf(1f, 0f, 0f), floatArrayOf(-1f, 0f, 0f),
            floatArrayOf(0f, 1f, 0f), floatArrayOf(0f, -1f, 0f),
            floatArrayOf(0f, 0f, 1f), floatArrayOf(0f, 0f, -1f)
        )
        val axesU = arrayOf(
            floatArrayOf(0f, 1f, 0f), floatArrayOf(0f, 1f, 0f),
            floatArrayOf(1f, 0f, 0f), floatArrayOf(1f, 0f, 0f),
            floatArrayOf(1f, 0f, 0f), floatArrayOf(1f, 0f, 0f)
        )
        val axesV = arrayOf(
            floatArrayOf(0f, 0f, 1f), floatArrayOf(0f, 0f, 1f),
            floatArrayOf(0f, 0f, 1f), floatArrayOf(0f, 0f, 1f),
            floatArrayOf(0f, 1f, 0f), floatArrayOf(0f, 1f, 0f)
        )
        val corners = arrayOf(
            floatArrayOf(-1f, -1f), floatArrayOf(1f, -1f),
            floatArrayOf(1f, 1f), floatArrayOf(-1f, 1f)
        )
        val order = intArrayOf(0, 1, 2, 0, 2, 3)

        val pos = ArrayList<Float>()
        val nor = ArrayList<Float>()
        for (f in 0 until 6) {
            val n = normals[f]
            val u = axesU[f]
            val v = axesV[f]
            for (k in order) {
                val s1 = corners[k][0] * 0.5f
                val s2 = corners[k][1] * 0.5f
                pos.add(n[0] * 0.5f + u[0] * s1 + v[0] * s2)
                pos.add(n[1] * 0.5f + u[1] * s1 + v[1] * s2)
                pos.add(n[2] * 0.5f + u[2] * s1 + v[2] * s2)
                nor.add(n[0]); nor.add(n[1]); nor.add(n[2])
            }
        }
        return Mesh(pos.toFloatArray(), nor.toFloatArray())
    }

    private fun buildPlane(): Mesh {
        val pos = floatArrayOf(
            -0.5f, 0f, -0.5f,
             0.5f, 0f, -0.5f,
             0.5f, 0f,  0.5f,
            -0.5f, 0f, -0.5f,
             0.5f, 0f,  0.5f,
            -0.5f, 0f,  0.5f
        )
        val nor = FloatArray(18)
        for (i in 0 until 6) {
            nor[i * 3] = 0f
            nor[i * 3 + 1] = 1f
            nor[i * 3 + 2] = 0f
        }
        return Mesh(pos, nor)
    }
}
