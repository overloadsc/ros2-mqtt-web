#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import paho.mqtt.client as mqtt
import json
import os
from collections import defaultdict
from file_transfer_util import FileTransferUtil

class ZipReceiverNode(Node):
    def __init__(self):
        super().__init__('zip_receiver')
        
        # 参数声明
        self.declare_parameter('mqtt_broker_host', '120.24.79.108')
        self.declare_parameter('mqtt_broker_port', 1883)
        self.declare_parameter('mqtt_username', 'zone')
        self.declare_parameter('mqtt_password', 'NeverGiveUp')
        self.declare_parameter('mqtt_topic', 'ros2/file_transfer/zip')
        self.declare_parameter('output_dir', os.path.expanduser('~/received_files'))
        
        # 获取参数
        self.broker_host = self.get_parameter('mqtt_broker_host').value
        self.broker_port = self.get_parameter('mqtt_broker_port').value
        self.username = self.get_parameter('mqtt_username').value
        self.password = self.get_parameter('mqtt_password').value
        self.mqtt_topic = self.get_parameter('mqtt_topic').value
        self.output_dir = self.get_parameter('output_dir').value
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 文件缓存
        self.file_cache = defaultdict(lambda: {
            'metadata': None,
            'chunks': {}
        })
        
        # MQTT客户端
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(self.username, self.password)
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        
        self.connect_mqtt()
    
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
            self.mqtt_client.subscribe(self.mqtt_topic, qos=1)
            self.get_logger().info(f'MQTT连接成功，已订阅主题: {self.mqtt_topic}')
        else:
            self.get_logger().error(f'MQTT连接失败，错误码: {rc}')
    
    def _on_mqtt_message(self, client, userdata, msg):
        """MQTT消息回调"""
        try:
            data = json.loads(msg.payload.decode('utf-8'))
            msg_type = data.get('type')
            
            if msg_type == 'file_metadata':
                self._handle_metadata(data)
            elif msg_type == 'file_chunk':
                self._handle_chunk(data)
                
        except Exception as e:
            self.get_logger().error(f'处理MQTT消息时出错: {str(e)}')
    
    def _handle_metadata(self, metadata: dict):
        """处理文件元数据"""
        file_name = metadata['file_name']
        self.file_cache[file_name]['metadata'] = metadata
        self.get_logger().info(
            f'收到文件元数据: {file_name}, '
            f'大小: {metadata["file_size"]} 字节, '
            f'总块数: {metadata["total_chunks"]}'
        )
    
    def _handle_chunk(self, chunk_data: dict):
        """处理文件数据块"""
        file_name = chunk_data['file_name']
        chunk_id = chunk_data['chunk_id']
        
        self.file_cache[file_name]['chunks'][chunk_id] = chunk_data
        
        # 检查是否接收完整
        metadata = self.file_cache[file_name]['metadata']
        if metadata and len(self.file_cache[file_name]['chunks']) == metadata['total_chunks']:
            self._save_file(file_name)
    
    def _save_file(self, file_name: str):
        """保存完整的文件"""
        try:
            cache = self.file_cache[file_name]
            metadata = cache['metadata']
            
            # 构建文件信息
            file_info = {
                'file_name': metadata['file_name'],
                'file_size': metadata['file_size'],
                'file_hash': metadata['file_hash'],
                'total_chunks': metadata['total_chunks'],
                'timestamp': metadata['timestamp'],
                'chunks': []
            }
            
            # 收集所有块
            for i in range(metadata['total_chunks']):
                chunk = cache['chunks'][i]
                file_info['chunks'].append({
                    'chunk_id': chunk['chunk_id'],
                    'chunk_size': chunk['chunk_size'],
                    'data': chunk['data']
                })
            
            # 解码和保存文件
            file_path = FileTransferUtil.decode_file(file_info, self.output_dir)
            self.get_logger().info(f'文件接收完成: {file_path}')
            
            # 清理缓存
            del self.file_cache[file_name]
            
        except Exception as e:
            self.get_logger().error(f'保存文件时出错: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    node = ZipReceiverNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()