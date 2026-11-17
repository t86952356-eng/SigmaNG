package info.sigmaclient.sigma;

import com.jagrosh.discordipc.IPCClient;
import com.jagrosh.discordipc.IPCListener;
import com.jagrosh.discordipc.entities.RichPresence;
import com.jagrosh.discordipc.exceptions.NoDiscordClientException;
import info.sigmaclient.sigma.premium.PremiumManager;
import info.sigmaclient.sigma.sigma5.SelfDestructManager;
import org.apache.logging.log4j.Logger;

import java.time.OffsetDateTime;
import java.util.Date;

import static info.sigmaclient.sigma.SigmaNG.getClientVersion;

public class DiscordRPC {
    public static OffsetDateTime time;
    private static final Logger LOGGER = org.apache.logging.log4j.LogManager.getLogger();
    public static void load() {
        // Android (FCL/Pojav) port: Discord IPC relies on junixsocket natives that do not
        // exist on Android (bionic). Loading them throws UnsatisfiedLinkError (an Error,
        // previously uncaught) during startup. Disable entirely on the Android build.
        if (Boolean.getBoolean("sigma.android")) {
            LOGGER.info("[Android] Discord RPC is disabled on this build");
            return;
        }
        IPCClient client = new IPCClient(1278269202863624277L);
        time = OffsetDateTime.now();
        client.setListener(new IPCListener() {
            @Override
            public void onReady(IPCClient client) {
                update(client);
                new Thread(() -> {
                    while (true) {
                        if(SelfDestructManager.destruct){
                            client.close();
                            return;
                        }
                        update(client);
                        try {
                            Thread.sleep(2000);
                        } catch (InterruptedException ignored) {
                        }
                    }
                });
            }
        });
        try {
            client.connect();
        } catch (NoDiscordClientException e) {
            LOGGER.warn("No discord client");
        } catch (Throwable t){
            // Catch Throwable: junixsocket/JNA native loading failures surface as
            // UnsatisfiedLinkError (java.lang.Error), not Exception.
            LOGGER.warn("No discord client! #2 ({}), {}", t.getClass().getSimpleName(), String.valueOf(t.getMessage()));
        }
    }
    static int state = 0;
    private static void update(IPCClient client) {
        state ++;
        String rr = "SigmaNG 1.16.5 b" + SigmaNG.getClientVersion();
        RichPresence.Builder builder = new RichPresence.Builder();
        builder.setDetails(rr)
                .setStartTimestamp(time)
                .setLargeImage("https://assets.lumodev.xyz/sigma1.png", "WTF?! Isn`t this program dead?");
        builder.setState("Dev Editing...");
        if(PremiumManager.isPremium){
            builder.setSmallImage("https://assets.lumodev.xyz/download.png", "Premium");
        }
        client.sendRichPresence(builder.build());
    }

    static void stop() {
    }
}
