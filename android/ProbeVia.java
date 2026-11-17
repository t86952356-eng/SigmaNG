import java.lang.reflect.Method;

/**
 * Reproduces the exact FCL device crash path with ONLY the fat client jar on
 * the classpath (same as FCL: -cp lwjgl.jar:launcher.jar:SigmaNG-Android.jar).
 *
 * Device crash (SigmaNG-Android-14.2):
 *   SigmaNG.initClient -> ViaLoader.load -> ViaMCP.create -> ViaMCP.<init>
 *   -> ViaLoadingBaseBuilder.build -> ViaLoadingBase.<init> -> initPlatform
 *   -> ViaVersionPlatformImpl.<init> -> VLBViaConfig/Config -> snakeyaml Yaml
 *   -> NoClassDefFoundError: org/yaml/snakeyaml/constructor/BaseConstructor
 *
 * Expected with the fix: prints PROBE-PASSED and exits 0.
 */
public class ProbeVia {
    public static void main(String[] args) throws Throwable {
        Class<?> loader = Class.forName(
            "info.sigmaclient.sigma.sigma5.jelloportal.vialoader.ViaLoader");
        Method load = loader.getMethod("load");
        long t0 = System.currentTimeMillis();
        load.invoke(null);
        System.out.println("PROBE-PASSED: ViaLoader.load() completed in "
            + (System.currentTimeMillis() - t0) + " ms");
        System.out.println("  -> ViaVersion platform initialized, snakeyaml resolved from the fat jar");
        System.exit(0);
    }
}
