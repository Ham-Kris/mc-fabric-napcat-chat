package com.mcqqchat.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.mcqqchat.McQqChat;
import net.fabricmc.loader.api.FabricLoader;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class ModConfig {
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private static final String CONFIG_FILE = "mc-qq-chat.json";

    // FastAPI 后端配置
    public String backendUrl = "http://localhost:8765";
    public String backendToken = "your-secret-token";

    // 消息同步配置
    public boolean syncPlayerJoinLeave = true;
    public boolean syncDeathMessages = true;
    public boolean syncAchievements = true;

    // 轮询间隔（毫秒）
    public int pollInterval = 1000;

    // 消息格式
    public String mcToQqFormat = "[MC] {player}: {message}";
    public String qqToMcFormat = "§b[QQ] §e{nickname}§7({qq})§f: {message}";

    public static ModConfig load() {
        Path configPath = FabricLoader.getInstance().getConfigDir().resolve(CONFIG_FILE);

        if (Files.exists(configPath)) {
            try {
                String json = Files.readString(configPath);
                ModConfig config = GSON.fromJson(json, ModConfig.class);
                McQqChat.LOGGER.info("Config loaded from {}", configPath);
                return config;
            } catch (IOException e) {
                McQqChat.LOGGER.error("Failed to load config", e);
            }
        }

        // 创建默认配置
        ModConfig config = new ModConfig();
        config.save();
        return config;
    }

    public void save() {
        Path configPath = FabricLoader.getInstance().getConfigDir().resolve(CONFIG_FILE);

        try {
            Files.writeString(configPath, GSON.toJson(this));
            McQqChat.LOGGER.info("Config saved to {}", configPath);
        } catch (IOException e) {
            McQqChat.LOGGER.error("Failed to save config", e);
        }
    }
}

