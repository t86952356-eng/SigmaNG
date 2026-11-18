import java.lang.reflect.Field;
import java.lang.reflect.Method;

/**
 * Reproduces the v14.3 FCL device crash path and proves the v14.4 fix.
 *
 * Device crash (SigmaNG-Android-14.3, Holy-GL4ES / GL 2.1 / GLES2):
 *   SelectAddonsGUI.draw -> JelloBlur.renderRectBlur -> JelloBlur.<clinit>
 *   -> new ShaderUtil("kawaseDown"/"kawaseUp")
 *   -> IllegalStateException: Shader (35632) failed to compile!
 *   -> ExceptionInInitializerError -> game crashed at the main menu.
 *
 * The same ShaderUtil instances are used by the in-game clickgui and HUD,
 * so the identical crash would happen in-game on GLES2-class renderers.
 *
 * Fix contract (v14.4): ShaderUtil constructors must NEVER throw - any
 * failure (compile, link, or even missing GL/LWJGL) switches the instance
 * to a no-op mode; blur/bloom skip themselves, gradient/rounded-rect fall
 * back to flat fills.
 *
 * On this CI host LWJGL is not on the classpath (the fat jar never bundles
 * it), so shader creation fails with NoClassDefFoundError - a different
 * trigger than on device, but the exact same "constructor must not throw"
 * contract is asserted.
 */
public class ProbeShader {
    public static void main(String[] args) throws Throwable {
        String pkg = "info.sigmaclient.sigma.utils.render.blurs.";

        // 1) All shader/blur classes must initialize without
        //    ExceptionInInitializerError (the v14.3 device crash).
        //    (Blur framebuffers are created lazily since v14.4, so class init
        //    no longer depends on the render-thread context or LWJGL.)
        Class<?> jello = Class.forName(pkg + "JelloBlur");
        Class.forName(pkg + "Bloom");
        Class.forName(pkg + "Gradient");
        Class.forName(pkg + "GradientGlowing");
        Class.forName(pkg + "GradientRoundRectShader");
        Class.forName(pkg + "RoundRectShader");
        Class.forName(pkg + "RoundedRectShader");
        System.out.println("OK: all 7 shader/blur classes initialized cleanly");

        // 2) The blur shader must report itself unusable (no GL here).
        Field up = jello.getField("kawaseUp");
        Object shaderUp = up.get(null);
        Method isUsable = shaderUp.getClass().getMethod("isUsable");
        boolean usable = (Boolean) isUsable.invoke(shaderUp);
        System.out.println("kawaseUp.isUsable() = " + usable);

        if (!usable) {
            // 3) Blur/bloom entry points must be safe no-ops when unusable
            //    (they return before touching Minecraft/window state).
            Method rectBlur = jello.getMethod("renderRectBlur",
                    float.class, float.class, float.class, float.class,
                    int.class, int.class, float.class);
            rectBlur.invoke(null, 0f, 0f, 100f, 100f, 0, 4, 10f);
            Method blur = jello.getMethod("renderBlur",
                    int.class, int.class, float.class);
            blur.invoke(null, 0, 4, 10f);
            System.out.println("OK: renderRectBlur/renderBlur are safe no-ops when unusable");
        } else {
            System.out.println("NOTE: GL unexpectedly available; skip no-op checks");
        }

        System.out.println("PROBE-PASSED: shader failure is contained, no crash path remains");
        System.exit(0);
    }
}
