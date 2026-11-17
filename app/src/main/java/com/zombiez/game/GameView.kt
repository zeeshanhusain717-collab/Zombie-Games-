package com.zombiez.game

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.view.MotionEvent
import android.view.SurfaceHolder
import android.view.SurfaceView
import kotlin.math.*
import kotlin.random.Random

class GameView(context: Context) : SurfaceView(context), Runnable, SurfaceHolder.Callback {
    private var thread: Thread? = null
    private var isPlaying = false
    private lateinit var canvas: Canvas
    private val paint = Paint()

    private var screenWidth = 1280f
    private var screenHeight = 720f

    // Game States: 0: Menu, 1: Base Camp Hub, 3: Gameplay, 4: Game Over, 5: Victory
    private var gameState = 0

    // Economy & Erangel Survival Stats
    private var playerCoins = 1000
    private var currentDay = 1
    private var maxDays = 60
    private var dailyTargetZombies = 15
    private var zombiesKilledToday = 0

    // Player ("Rocky") Stats
    private var playerX = 1500f
    private var playerY = 1500f
    private var playerHp = 200f
    private var maxPlayerHp = 200f
    private var playerSpeed = 5.5f
    private var playerAngle = 0f

    // Joystick
    private var joyActive = false
    private var joyX = 180f
    private var joyY = 540f
    private var joyKnobX = 180f
    private var joyKnobY = 540f
    private val joyRadius = 75f

    // Erangel Zombies & Zone
    private class Zombie(var x: Float, var y: Float, val type: Int) {
        var hp: Float = if (type == 1) 100f else if (type == 2) 150f else 300f
        val maxHp: Float = hp
        val speed: Float = if (type == 1) 2.2f else if (type == 2) 3.5f else 1.5f
        val radius: Float = if (type == 3) 28f else 18f
    }
    private val zombies = mutableListOf<Zombie>()
    private var zoneRadius = 1600f

    init {
        holder.addCallback(this)
        isFocusable = true
    }

    override fun surfaceCreated(holder: SurfaceHolder) {
        isPlaying = true
        thread = Thread(this)
        thread?.start()
    }

    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {
        screenWidth = width.toFloat()
        screenHeight = height.toFloat()
        joyY = screenHeight - 160f
        joyX = 180f
        joyKnobX = joyX
        joyKnobY = joyY
    }

    override fun surfaceDestroyed(holder: SurfaceHolder) {
        isPlaying = false
        try {
            thread?.join()
        } catch (e: InterruptedException) {
            e.printStackTrace()
        }
    }

    fun resume() {
        isPlaying = true
        thread = Thread(this)
        thread?.start()
    }

    fun pause() {
        isPlaying = false
        try {
            thread?.join()
        } catch (e: InterruptedException) {
            e.printStackTrace()
        }
    }

    private fun startBattle() {
        gameState = 3
        playerX = 1500f
        playerY = 1500f
        playerHp = maxPlayerHp
        zoneRadius = 1600f
        zombies.clear()
        for (i in 0 until 30) {
            val zx = Random.nextFloat() * 2800f + 100f
            val zy = Random.nextFloat() * 2800f + 100f
            val zType = Random.nextInt(1, 4)
            zombies.add(Zombie(zx, zy, zType))
        }
    }

    override fun run() {
        var lastTime = System.nanoTime()
        val fps = 60
        val targetTime = 1000000000L / fps

        while (isPlaying) {
            val now = System.nanoTime()
            val dt = (now - lastTime) / 1000000000.0f
            lastTime = now

            if (holder.surface.isValid) {
                canvas = holder.lockCanvas()
                synchronized(holder) {
                    update()
                    drawGame(canvas)
                }
                holder.unlockCanvasAndPost(canvas)
            }

            val elapsed = System.nanoTime() - now
            val waitTime = (targetTime - elapsed) / 1000000L
            if (waitTime > 0) {
                try {
                    Thread.sleep(waitTime)
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        }
    }

    private fun update() {
        if (gameState == 3) {
            if (joyActive) {
                val dx = joyKnobX - joyX
                val dy = joyKnobY - joyY
                val dist = hypot(dx, dy)
                if (dist > 5f) {
                    playerAngle = atan2(dy, dx)
                    playerX += (dx / dist) * playerSpeed
                    playerY += (dy / dist) * playerSpeed
                    playerX = playerX.coerceIn(100f, 2900f)
                    playerY = playerY.coerceIn(100f, 2900f)
                }
            }

            for (z in zombies) {
                val zdx = playerX - z.x
                val zdy = playerY - z.y
                val zDist = hypot(zdx, zdy)
                if (zDist > 20f) {
                    z.x += (zdx / zDist) * z.speed
                    z.y += (zdy / zDist) * z.speed
                } else {
                    playerHp -= 0.6f
                    if (playerHp <= 0) gameState = 4
                }
            }

            if (zoneRadius > 400f) zoneRadius -= 0.15f
            if (hypot(playerX - 1500f, playerY - 1500f) > zoneRadius) {
                playerHp -= 0.3f
                if (playerHp <= 0) gameState = 4
            }

            if (zombies.isEmpty()) {
                gameState = 5
            }
        }
    }

    private fun drawGame(canvas: Canvas) {
        // Erangel Grass Map Background
        canvas.drawColor(Color.rgb(45, 120, 45))

        val camX = playerX - screenWidth / 2f
        val camY = playerY - screenHeight / 2f

        canvas.save()
        canvas.translate(-camX, -camY)

        // Draw Pochinki Houses (Landmarks)
        paint.color = Color.rgb(100, 70, 50)
        canvas.drawRect(1300f, 1300f, 1700f, 1700f, paint)
        paint.color = Color.rgb(180, 50, 50)
        canvas.drawRect(1350f, 1350f, 1650f, 1650f, paint)

        // Toxic Blue Zone Circle
        paint.style = Paint.Style.STROKE
        paint.strokeWidth = 8f
        paint.color = Color.rgb(30, 100, 255)
        canvas.drawCircle(1500f, 1500f, zoneRadius, paint)
        paint.style = Paint.Style.FILL

        // Draw Zombies
        for (z in zombies) {
            paint.color = if (z.type == 1) Color.rgb(60, 160, 60) else if (z.type == 2) Color.rgb(180, 100, 40) else Color.rgb(140, 20, 140)
            canvas.drawCircle(z.x, z.y, z.radius, paint)
            // HP Bar
            paint.color = Color.RED
            canvas.drawRect(z.x - 20f, z.y - z.radius - 10f, z.x + 20f, z.y - z.radius - 6f, paint)
            paint.color = Color.YELLOW
            val fill = (z.hp / z.maxHp) * 40f
            canvas.drawRect(z.x - 20f, z.y - z.radius - 10f, z.x - 20f + fill, z.y - z.radius - 6f, paint)
        }

        // Draw Player ("Rocky")
        paint.color = Color.rgb(40, 90, 220)
        canvas.drawCircle(playerX, playerY, 22f, paint)
        paint.color = Color.WHITE
        canvas.drawCircle(playerX, playerY, 22f, paint.apply { style = Paint.Style.STROKE; strokeWidth = 3f })
        paint.style = Paint.Style.FILL

        canvas.restore()

        // UI & HUD Overlays
        when (gameState) {
            0 -> {
                canvas.drawColor(Color.rgb(20, 20, 25))
                paint.textSize = 42f
                paint.color = Color.rgb(235, 130, 20)
                canvas.drawText("ZOMBIE Z: ERANGEL MOBILE ELITE", screenWidth / 2 - 380f, 180f, paint)

                paint.color = Color.rgb(210, 50, 50)
                canvas.drawRect(screenWidth / 2 - 160f, 320f, screenWidth / 2 + 160f, 410f, paint)
                paint.color = Color.WHITE
                paint.textSize = 32f
                canvas.drawText("START SURVIVAL", screenWidth / 2 - 130f, 375f, paint)
            }
            3 -> {
                // Joystick
                paint.color = Color.argb(100, 255, 255, 255)
                canvas.drawCircle(joyX, joyY, joyRadius, paint)
                paint.color = Color.rgb(0, 210, 210)
                canvas.drawCircle(joyKnobX, joyKnobY, 30f, paint)

                // Fire Button
                paint.color = Color.rgb(210, 50, 50)
                canvas.drawCircle(screenWidth - 150f, screenHeight - 150f, 75f, paint)
                paint.color = Color.WHITE
                paint.textSize = 28f
                canvas.drawText("FIRE", screenWidth - 180f, screenHeight - 140f, paint)

                // HUD Stats
                paint.textSize = 26f
                paint.color = Color.YELLOW
                canvas.drawText("HP: ${playerHp.toInt()} | Zombies: ${zombies.size} | Coins: $playerCoins🪙", 40f, 50f, paint)
            }
            4 -> {
                canvas.drawColor(Color.BLACK)
                paint.textSize = 45f
                paint.color = Color.RED
                canvas.drawText("YOU DIED IN THE ERANGEL FOG...", screenWidth / 2 - 330f, screenHeight / 2 - 30f, paint)
                paint.textSize = 26f
                paint.color = Color.WHITE
                canvas.drawText("Tap anywhere to retry", screenWidth / 2 - 130f, screenHeight / 2 + 40f, paint)
            }
            5 -> {
                canvas.drawColor(Color.BLACK)
                paint.textSize = 45f
                paint.color = Color.GREEN
                canvas.drawText("ERANGEL DAY SURVIVED!", screenWidth / 2 - 220f, screenHeight / 2 - 30f, paint)
                paint.textSize = 26f
                paint.color = Color.WHITE
                canvas.drawText("Tap to continue", screenWidth / 2 - 100f, screenHeight / 2 + 40f, paint)
            }
        }
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        val x = event.x
        val y = event.y

        when (event.action) {
            MotionEvent.ACTION_DOWN -> {
                when (gameState) {
                    0 -> startBattle()
                    3 -> {
                        if (hypot(x - (screenWidth - 150f), y - (screenHeight - 150f)) <= 75f) {
                            if (zombies.isNotEmpty()) {
                                var nearest = zombies[0]
                                var minDist = hypot(playerX - nearest.x, playerY - nearest.y)
                                for (z in zombies) {
                                    val d = hypot(playerX - z.x, playerY - z.y)
                                    if (d < minDist) {
                                        minDist = d
                                        nearest = z
                                    }
                                }
                                if (minDist < 600f) {
                                    nearest.hp -= 50f
                                    if (nearest.hp <= 0) {
                                        zombies.remove(nearest)
                                        playerCoins += 20
                                    }
                                }
                            }
                        } else if (hypot(x - joyX, y - joyY) <= joyRadius + 50f) {
                            joyActive = true
                            joyKnobX = x
                            joyKnobY = y
                        }
                    }
                    4, 5 -> gameState = 0
                }
            }
            MotionEvent.ACTION_MOVE -> {
                if (joyActive) {
                    val dx = x - joyX
                    val dy = y - joyY
                    val dist = hypot(dx, dy)
                    if (dist > joyRadius) {
                        joyKnobX = joyX + (dx / dist) * joyRadius
                        joyKnobY = joyY + (dy / dist) * joyRadius
                    } else {
                        joyKnobX = x
                        joyKnobY = y
                    }
                }
            }
            MotionEvent.ACTION_UP -> {
                joyActive = false
                joyKnobX = joyX
                joyKnobY = joyY
            }
        }
        return true
    }
}

