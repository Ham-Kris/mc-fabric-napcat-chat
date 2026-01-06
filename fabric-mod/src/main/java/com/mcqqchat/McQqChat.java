package com.mcqqchat;

import com.mcqqchat.config.ModConfig;
import com.mcqqchat.network.BridgeClient;
import com.mcqqchat.handler.ChatHandler;
import net.fabricmc.api.DedicatedServerModInitializer;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.message.v1.ServerMessageEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class McQqChat implements DedicatedServerModInitializer {
    public static final String MOD_ID = "mc-qq-chat";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    private static MinecraftServer server;
    private static BridgeClient bridgeClient;
    private static ModConfig config;

    @Override
    public void onInitializeServer() {
        LOGGER.info("MC-QQ Chat Bridge initializing...");

        // 加载配置
        config = ModConfig.load();

        // 创建桥接客户端
        bridgeClient = new BridgeClient(config);

        // 服务器启动事件
        ServerLifecycleEvents.SERVER_STARTED.register(s -> {
            server = s;
            bridgeClient.start();
            bridgeClient.sendSystemMessage("🎮 Minecraft 服务器已启动！");
            LOGGER.info("MC-QQ Chat Bridge started!");
        });

        // 服务器关闭事件
        ServerLifecycleEvents.SERVER_STOPPING.register(s -> {
            bridgeClient.sendSystemMessage("🔌 Minecraft 服务器正在关闭...");
            bridgeClient.stop();
            LOGGER.info("MC-QQ Chat Bridge stopped!");
        });

        // 玩家发送消息事件
        ServerMessageEvents.CHAT_MESSAGE.register((message, sender, params) -> {
            String playerName = sender.getName().getString();
            String content = message.getContent().getString();
            ChatHandler.handleMinecraftMessage(bridgeClient, playerName, content);
        });

        // 玩家加入事件
        ServerPlayConnectionEvents.JOIN.register((handler, sender, s) -> {
            ServerPlayerEntity player = handler.getPlayer();
            String playerName = player.getName().getString();
            bridgeClient.sendSystemMessage("📥 " + playerName + " 加入了服务器");
        });

        // 玩家离开事件
        ServerPlayConnectionEvents.DISCONNECT.register((handler, s) -> {
            ServerPlayerEntity player = handler.getPlayer();
            String playerName = player.getName().getString();
            bridgeClient.sendSystemMessage("📤 " + playerName + " 离开了服务器");
        });

        LOGGER.info("MC-QQ Chat Bridge initialized!");
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
            server.getPlayerManager().broadcast(Text.literal(message), false);
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

