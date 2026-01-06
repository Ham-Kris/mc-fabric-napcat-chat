package com.mcqqchat.network;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.mcqqchat.McQqChat;
import com.mcqqchat.config.ModConfig;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class BridgeClient {
    private final ModConfig config;
    private final HttpClient httpClient;
    private final Gson gson;
    private ScheduledExecutorService scheduler;
    private volatile boolean running = false;

    public BridgeClient(ModConfig config) {
        this.config = config;
        this.gson = new Gson();
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    public void start() {
        if (running) return;
        running = true;

        scheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "MC-QQ-Bridge-Poller");
            t.setDaemon(true);
            return t;
        });

        // 定期轮询消息
        scheduler.scheduleAtFixedRate(this::pollMessages, 1000, config.pollInterval, TimeUnit.MILLISECONDS);

        McQqChat.LOGGER.info("Bridge client started, polling every {}ms", config.pollInterval);
    }

    public void stop() {
        running = false;
        if (scheduler != null) {
            scheduler.shutdown();
            try {
                if (!scheduler.awaitTermination(5, TimeUnit.SECONDS)) {
                    scheduler.shutdownNow();
                }
            } catch (InterruptedException e) {
                scheduler.shutdownNow();
            }
        }
        McQqChat.LOGGER.info("Bridge client stopped");
    }

    private void pollMessages() {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(config.backendUrl + "/api/messages/poll"))
                    .header("Authorization", "Bearer " + config.backendToken)
                    .header("Content-Type", "application/json")
                    .GET()
                    .timeout(Duration.ofSeconds(5))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() == 200) {
                JsonObject json = gson.fromJson(response.body(), JsonObject.class);
                JsonArray messages = json.getAsJsonArray("messages");

                if (messages != null) {
                    for (JsonElement element : messages) {
                        JsonObject msg = element.getAsJsonObject();
                        handleIncomingMessage(msg);
                    }
                }
            } else if (response.statusCode() != 204) {
                McQqChat.LOGGER.warn("Poll failed with status: {}", response.statusCode());
            }
        } catch (IOException | InterruptedException e) {
            McQqChat.LOGGER.debug("Poll failed: {}", e.getMessage());
        }
    }

    private void handleIncomingMessage(JsonObject message) {
        String type = message.has("type") ? message.get("type").getAsString() : "chat";
        String nickname = message.has("nickname") ? message.get("nickname").getAsString() : "Unknown";
        String qq = message.has("qq") ? message.get("qq").getAsString() : "0";
        String content = message.has("content") ? message.get("content").getAsString() : "";

        switch (type) {
            case "chat":
                McQqChat.broadcastQqMessage(nickname, qq, content);
                break;
            case "system":
                McQqChat.broadcastSystemMessage(content);
                break;
            case "image":
                String desc = message.has("description") ? message.get("description").getAsString() : "[图片]";
                McQqChat.broadcastQqMessage(nickname, qq, "§d[图片] §7" + desc);
                break;
            case "video":
                String videoDesc = message.has("description") ? message.get("description").getAsString() : "[视频]";
                McQqChat.broadcastQqMessage(nickname, qq, "§c[视频] §7" + videoDesc);
                break;
            case "face":
                String faceName = message.has("face_name") ? message.get("face_name").getAsString() : "表情";
                McQqChat.broadcastQqMessage(nickname, qq, "§e[" + faceName + "]");
                break;
            default:
                McQqChat.broadcastQqMessage(nickname, qq, content);
        }
    }

    /**
     * 发送玩家聊天消息到后端
     */
    public void sendPlayerMessage(String playerName, String message) {
        JsonObject json = new JsonObject();
        json.addProperty("type", "player_chat");
        json.addProperty("player", playerName);
        json.addProperty("message", message);
        sendToBackend("/api/messages/send", json);
    }

    /**
     * 发送系统消息到后端
     */
    public void sendSystemMessage(String message) {
        JsonObject json = new JsonObject();
        json.addProperty("type", "system");
        json.addProperty("message", message);
        sendToBackend("/api/messages/send", json);
    }

    /**
     * 发送玩家加入/离开事件
     */
    public void sendPlayerEvent(String eventType, String playerName) {
        if (!config.syncPlayerJoinLeave) return;

        JsonObject json = new JsonObject();
        json.addProperty("type", eventType);
        json.addProperty("player", playerName);
        sendToBackend("/api/messages/send", json);
    }

    private void sendToBackend(String endpoint, JsonObject data) {
        if (!running) return;

        // 异步发送
        scheduler.submit(() -> {
            try {
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(config.backendUrl + endpoint))
                        .header("Authorization", "Bearer " + config.backendToken)
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(gson.toJson(data)))
                        .timeout(Duration.ofSeconds(5))
                        .build();

                HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

                if (response.statusCode() != 200) {
                    McQqChat.LOGGER.warn("Send failed with status: {} - {}", response.statusCode(), response.body());
                }
            } catch (IOException | InterruptedException e) {
                McQqChat.LOGGER.debug("Send failed: {}", e.getMessage());
            }
        });
    }
}

