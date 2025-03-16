# OpenWeather MCP Server

这是一个简单的天气预报 MCP (Model Control Protocol) 服务器，提供全球天气预报和当前天气状况查询功能。

## Claude Desktop使用效果

以下是Claude Desktop使用MCP天气服务的效果截图：

![Claude Desktop使用MCP天气服务](image.png)

## 特点

- 无需单独的配置文件，API密钥可以直接通过环境变量或参数传递
- 支持查询全球任何地点的天气状况
- 提供当前天气和未来预报
- 带有详细的天气信息，包括温度、湿度、风速等
- 支持不同时区的天气数据

## 安装要求

```
pip install mcp-server requests pydantic
```

## 使用方法

### 1. 获取OpenWeatherMap API密钥

访问 [OpenWeatherMap](https://openweathermap.org/) 并注册一个账号获取API密钥。

### 2. 运行服务器

有两种方式提供API密钥：

#### 方式1：通过环境变量

```bash
# 设置环境变量
export OPENWEATHER_API_KEY="你的API密钥"  # Linux/Mac
set OPENWEATHER_API_KEY=你的API密钥  # Windows

# 运行服务器
python weather_mcp_server.py
```

#### 方式2：在工具调用时提供

不设置环境变量，直接运行：

```bash
python weather_mcp_server.py
```

在调用工具时，需要提供`api_key`参数。

### 3. 在MCP客户端配置中使用

在支持MCP的客户端配置中添加以下配置：

```json
{
  "weather_forecast": {
    "command": "python",
    "args": [
      "/完整路径/weather_mcp_server.py"
    ],
    "env": {
      "OPENWEATHER_API_KEY": "你的OpenWeatherMap密钥在这里"
    },
    "disabled": false,
    "autoApprove": ["get_weather", "get_current_weather"]
  }
}
```

### 4. 可用的工具

#### get_weather

获取指定地点的当前天气和未来预报。

参数:
- `location`: 地点名称，例如："Beijing"、"New York"、"Tokyo"
- `api_key`: OpenWeatherMap API密钥（可选，如未提供将从环境变量读取）
- `timezone_offset`: 时区偏移量（小时），如北京为8，纽约为-4。默认为0（UTC时间）

#### get_current_weather

获取指定地点的当前天气。

参数:
- `location`: 地点名称，例如："Beijing"、"New York"、"Tokyo"
- `api_key`: OpenWeatherMap API密钥（可选，如未提供将从环境变量读取）
- `timezone_offset`: 时区偏移量（小时），如北京为8，纽约为-4。默认为0（UTC时间）

## 使用示例

AI助手调用示例：

```
用户: 北京现在天气怎么样？

AI: 让我为您查询北京的当前天气。
[调用get_current_weather("Beijing", timezone_offset=8)]

北京当前天气：23°C，晴，湿度45%，风速2.1m/s。
```

## 故障排除

如果遇到"未提供API密钥"错误，请确保：
1. 在环境变量中设置了OPENWEATHER_API_KEY，或
2. 在调用工具时提供了api_key参数

如果地点名称不正确，可能会收到"地点未找到"错误，请尝试使用更准确的城市名称或添加国家代码，例如："Beijing,CN"或"Paris,FR"。 