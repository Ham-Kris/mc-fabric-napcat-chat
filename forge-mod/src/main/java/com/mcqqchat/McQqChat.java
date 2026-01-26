package com.mcqqchat;

import com.mcqqchat.config.ModConfig;
import com.mcqqchat.handler.ChatHandler;
import com.mcqqchat.network.BridgeClient;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.ServerChatEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Mod(McQqChat.MOD_ID)
public class McQqChat {
    public static final String MOD_ID = "mcqqchat";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    private static MinecraftServer server;
    private static BridgeClient bridgeClient;
    private static ModConfig config;

    public McQqChat() {
        LOGGER.info("MC-QQ Chat Bridge initializing...");

        // 加载配置
        config = ModConfig.load();

        // 创建桥接客户端
        bridgeClient = new BridgeClient(config);

        // 注册事件监听器
        MinecraftForge.EVENT_BUS.register(this);

        LOGGER.info("MC-QQ Chat Bridge initialized!");
    }

    @SubscribeEvent
    public void onServerStarted(ServerStartedEvent event) {
        server = event.getServer();
        bridgeClient.start();
        
        // 延迟发送启动消息，确保 bridge 完全初始化
        new Thread(() -> {
            try {
                Thread.sleep(2000); // 等待2秒
                bridgeClient.sendSystemMessage("🎮 Minecraft 服务器已启动！");
            } catch (InterruptedException e) {
                LOGGER.error("Failed to send startup message", e);
            }
        }).start();
        
        LOGGER.info("MC-QQ Chat Bridge started!");
    }

    @SubscribeEvent
    public void onServerStopping(ServerStoppingEvent event) {
        bridgeClient.sendSystemMessage("🔌 Minecraft 服务器正在关闭...");
        bridgeClient.stop();
        LOGGER.info("MC-QQ Chat Bridge stopped!");
    }

    @SubscribeEvent
    public void onServerChat(ServerChatEvent event) {
        ServerPlayer player = event.getPlayer();
        String playerName = player.getName().getString();
        String content = event.getRawText();
        ChatHandler.handleMinecraftMessage(bridgeClient, playerName, content);
    }

    @SubscribeEvent
    public void onPlayerJoin(PlayerEvent.PlayerLoggedInEvent event) {
        if (event.getEntity() instanceof ServerPlayer player) {
            String playerName = player.getName().getString();
            bridgeClient.sendPlayerEvent("player_join", playerName);
        }
    }

    @SubscribeEvent
    public void onPlayerLeave(PlayerEvent.PlayerLoggedOutEvent event) {
        if (event.getEntity() instanceof ServerPlayer player) {
            String playerName = player.getName().getString();
            bridgeClient.sendPlayerEvent("player_leave", playerName);
        }
    }

    public static MinecraftServer getServer() {
        return server;
    }

    public static BridgeClient getBridgeClient() {
        return bridgeClient;
    }

    public static ModConfig getConfig() {
        return config;
    }

    /**
     * 向所有在线玩家广播消息
     */
    public static void broadcastToPlayers(String message) {
        if (server != null) {
            server.getPlayerList().broadcastSystemMessage(Component.literal(message), false);
        }
    }

    /**
     * 向所有在线玩家广播格式化的QQ消息
     */
    public static void broadcastQqMessage(String nickname, String qq, String content) {
        String formatted = String.format("§b[QQ] §e%s§7(%s)§f: %s", nickname, qq, content);
        broadcastToPlayers(formatted);
    }

    /**
     * 广播系统消息
     */
    public static void broadcastSystemMessage(String message) {
        String formatted = "§6[QQ系统] §f" + message;
        broadcastToPlayers(formatted);
    }
}
