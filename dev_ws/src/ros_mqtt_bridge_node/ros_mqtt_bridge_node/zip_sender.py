#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import json
import paho.mqtt.client as mqtt
import time
import os
import yaml
from pathlib import Path
from file_transfer_util import FileTransferUtil

class ZipSenderNode(Node):
    def __init__(self):
        super().__init__('zip_sender')
        
        # 加载配置文件
        config_path = Path(__file__).parent.parent / 'config' / 'zip_sender_config.yaml'
        self.config = self._load_config(config_path)
        
        # 从配置文件获取参数
        mqtt_config = self.config['zip_sender']['mqtt']
        file_config = self.config['zip_sender']['file']
        
        self.broker_host = mqtt_config['broker_host']
        self.broker_port = mqtt_config['broker_port']
        self.username = mqtt_config['username']
        self.password = mqtt_config['password']
        self.mqtt_topic = mqtt_config['topic']
        self.mqtt_qos = mqtt_config['qos']
        
        self.zip_file_path = os.path.expanduser(file_config['zip_file_path'])
        
        self.get_logger().info(f'从配置文件加载参数: {config_path}')
        self.get_logger().info(f'MQTT服务器: {self.broker_host}:{self.broker_port}')
        self.get_logger().info(f'待发送文件: {self.zip_file_path}')
        
        # MQTT客户端
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(self.username, self.password)
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
        self.mqtt_client.on_publish = self._on_mqtt_publish
        
        self.is_connected = False
        self.connect_mqtt()
        
        # 创建定时器用于发送文件
        self.timer = self.create_timer(1.0, self._send_zip_file)
        self.file_sent = False
    
    def _load_config(self, config_path: Path) -> dict:
        """加载YAML配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            self.get_logger().error(f'配置文件不存在: {config_path}')
            raise
        except yaml.YAMLError as e:
            self.get_logger().error(f'YAML解析错误: {str(e)}')
            raise
        
    def connect_mqtt(self):
        """连接MQTT服务器"""
        try:
            self.mqtt_client.connect(self.broker_host, self.broker_port, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            self.get_logger().error(f'连接MQTT失败: {str(e)}')
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            self.is_connected = True
            self.get_logger().info('MQTT连接成功')
        else:
            self.get_logger().error(f'MQTT连接失败，错误码: {rc}')
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT断开连接回调"""
        self.is_connected = False
        self.get_logger().warn(f'MQTT连接已断开，错误码: {rc}')
    
    def _on_mqtt_publish(self, client, userdata, mid):
        """MQTT发布回调"""
        self.get_logger().debug(f'消息已发布，消息ID: {mid}')
    
    def _send_zip_file(self):
        """发送ZIP文件"""
        if self.file_sent or not self.is_connected:
            return
        
        try:
            # 检查文件是否存在
            if not os.path.exists(self.zip_file_path):
                self.get_logger().warn(f'ZIP文件不存在: {self.zip_file_path}')
                self.file_sent = True
                return
            
            self.get_logger().info(f'开始发送文件: {self.zip_file_path}')
            
            # 编码文件
            file_info = FileTransferUtil.encode_file(self.zip_file_path)
            
            # 分割消息
            messages = FileTransferUtil.split_file_info(file_info)
            
            # 发送每条消息
            for i, msg in enumerate(messages):
                result = self.mqtt_client.publish(
                    self.mqtt_topic,
                    json.dumps(msg),
                    qos=self.mqtt_qos
                )
                
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    self.get_logger().error(f'消息 {i} 发布失败，错误码: {result.rc}')
                else:
                    self.get_logger().info(f'消息 {i}/{len(messages)} 已发布')
                
                time.sleep(0.1)  # 避免消息拥堵
            
            self.get_logger().info(f'文件发送完成: {self.zip_file_path}')
            self.file_sent = True
            
        except Exception as e:
            self.get_logger().error(f'发送文件时出错: {str(e)}')
            self.file_sent = True

def main(args=None):
    rclpy.init(args=args)
    node = ZipSenderNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()