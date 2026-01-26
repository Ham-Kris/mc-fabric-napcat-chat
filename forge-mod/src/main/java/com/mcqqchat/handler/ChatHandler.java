package com.mcqqchat.handler;

import com.mcqqchat.McQqChat;
import com.mcqqchat.network.BridgeClient;

public class ChatHandler {

    /**
     * 处理Minecraft聊天消息，发送到QQ群
     */
    public static void handleMinecraftMessage(BridgeClient client, String playerName, String message) {
        // 过滤命令
        if (message.startsWith("/")) {
            return;
        }

        // 过滤空消息
        if (message.trim().isEmpty()) {
            return;
        }

        McQqChat.LOGGER.debug("MC -> QQ: {} said: {}", playerName, message);
        client.sendPlayerMessage(playerName, message);
    }
}
