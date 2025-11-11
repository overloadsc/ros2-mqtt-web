# 2025.7.16
    完成ROS-MQTT-WEB的链路打通

# 2025.7.17
    完成ROS-MQTT的模块化重构
    完成多话题监控页面设计

# 2025.7.22
    完成图片远程落盘Demo设计

# 2025.7.23
    完成图传Demo页面设计

# 2025.7.24
    完成GPS地图显示页面设计
    完成初始页面设计

# 2025.8.22
    完成相关文档编写
    测试成功打通本地-公网MQTT服务器-网页通信全链路

# ROS2 MQTT Bridge Node

一个功能完整的ROS2-MQTT桥接系统，支持多话题桥接和大文件传输。

## 功能特性

### 1. 多话题桥接
- **ROS to MQTT**: 订阅ROS话题，将消息发布到MQTT
- **MQTT to ROS**: 订阅MQTT主题，将消息发布到ROS话题
- 支持灵活的数据字段提取
- 可配置的QoS级别和消息保留策略

### 2. ZIP文件传输
- **分块传输**: 大文件自动分块（默认1MB/块）
- **Base64编码**: 二进制数据安全传输
- **完整性校验**: MD5哈希验证
- **断点续传**: 支持消息重传机制
- **双向传输**: 支持发送和接收

## 项目结构

```
dev_ws/
├── src/
│   └── ros_mqtt_bridge_node/
│       ├── ros_mqtt_bridge_node/
│       │   ├── zip_sender.py          # ZIP文件发送端
│       │   ├── zip_receiver.py        # ZIP文件接收端
│       │   ├── file_transfer_util.py  # 文件传输工具类
│       │   ├── bridge_node.py         # 多话题桥接主节点
│       │   └── __init__.py
│       ├── config/
│       │   ├── multi_bridge_config.yaml    # 多话题桥接配置
│       │   └── zip_sender_config.yaml      # ZIP发送端配置
│       ├── launch/
│       │   └── bridge_launch.py
│       └── package.xml
```

## 安装依赖

```bash
# 系统依赖
sudo apt-get install python3-paho-mqtt python3-pyyaml

# Python包
pip install paho-mqtt pyyaml
```

## 配置说明

### 多话题桥接配置 (`multi_bridge_config.yaml`)

```yaml
mqtt_global:
  broker_host: "120.24.79.108"
  broker_port: 1883
  username: "zone"
  password: "NeverGiveUp"

bridges:
  - name: "hello_world_bridge"
    description: "Hello World消息桥接"
    enabled: true
    ros_config:
      topic: "/hello_world"
      message_type: "std_msgs/String"
      data_field: "data"
      queue_size: 10
    mqtt_config:
      topic_name: "hello_world"
      topic_suffix: "data"
      qos: 0
      retain: false
```

### ZIP发送端配置 (`zip_sender_config.yaml`)

```yaml
zip_sender:
  mqtt:
    broker_host: "120.24.79.108"
    broker_port: 1883
    username: "zone"
    password: "NeverGiveUp"
    topic: "ros2/file_transfer/zip"
    qos: 1
  
  file:
    zip_file_path: "~/Downloads/example.zip"
```

## 使用方法

### 1. 启动多话题桥接

```bash
cd dev_ws
colcon build
source install/setup.bash

# 运行桥接节点
ros2 run ros_mqtt_bridge_node bridge_node
```

### 2. 发送ZIP文件

```bash
# 编辑配置文件指定要发送的ZIP文件
# config/zip_sender_config.yaml

# 运行发送端
ros2 run ros_mqtt_bridge_node zip_sender
```

### 3. 接收ZIP文件

```bash
# 运行接收端
ros2 run ros_mqtt_bridge_node zip_receiver

# 文件保存在 ~/received_files/
```

## ZIP文件传输工作流程

### 发送端流程

1. 读取ZIP文件
2. 计算MD5哈希值
3. 按1MB分块编码为Base64
4. 生成元数据消息
5. 逐块发送到MQTT

### 接收端流程

1. 订阅MQTT主题
2. 接收元数据（文件名、大小、总块数）
3. 缓存接收到的数据块
4. 块齐全后触发保存
5. Base64解码并按顺序重组
6. 验证MD5哈希
7. 保存到输出目录

### 消息格式

**元数据消息**:
```json
{
  "type": "file_metadata",
  "file_name": "example.zip",
  "file_size": 1048576,
  "file_hash": "d41d8cd98f00b204e9800998ecf8427e",
  "total_chunks": 1,
  "timestamp": 1699684613
}
```

**数据块消息**:
```json
{
  "type": "file_chunk",
  "file_name": "example.zip",
  "chunk_id": 0,
  "chunk_size": 1048576,
  "total_chunks": 1,
  "data": "UEsDBAoA..."
}
```

## 关键特性说明

### 分块传输优势
- ✅ 支持任意大小的文件
- ✅ MQTT消息大小限制内安全传输
- ✅ 提高传输稳定性
- ✅ 支持断点续传

### 完整性校验
- ✅ MD5哈希值验证
- ✅ 自动检测传输错误
- ✅ 校验失败自动清理

### 灵活配置
- ✅ 可配置的分块大小
- ✅ 可配置的QoS级别
- ✅ 可配置的MQTT连接参数
- ✅ 可配置的输出目录

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| mqtt_broker_host | string | 120.24.79.108 | MQTT服务器地址 |
| mqtt_broker_port | int | 1883 | MQTT服务器端口 |
| mqtt_username | string | zone | MQTT用户名 |
| mqtt_password | string | NeverGiveUp | MQTT密码 |
| mqtt_topic | string | ros2/file_transfer/zip | MQTT主题 |
| output_dir | string | ~/received_files | 接收文件保存目录 |

## 故障排查

### 文件发送失败

- ✗ 检查文件是否存在
- ✗ 检查文件是否为.zip格式
- ✗ 检查MQTT连接状态

### 文件接收不完整

- ✗ 检查MQTT消息是否丢失（建议使用QoS=1）
- ✗ 查看日志中的块接收进度
- ✗ 检查网络稳定性

### 哈希校验失败

- ✗ 检查网络传输是否中断
- ✗ 检查Base64编解码是否正确
- ✗ 重新发送文件

## 日志输出

接收端日志示例：
```
[INFO] MQTT连接成功，已订阅主题: ros2/file_transfer/zip
[INFO] 收到文件元数据: example.zip, 大小: 1048576 字节, 总块数: 1
[INFO] 文件接收完成: ~/received_files/example.zip
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

