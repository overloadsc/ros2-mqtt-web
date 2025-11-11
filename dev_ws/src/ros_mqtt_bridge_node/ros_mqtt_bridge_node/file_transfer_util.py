#!/usr/bin/env python3
import base64
import os
import json
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path

class FileTransferUtil:
    """文件传输工具类"""
    
    CHUNK_SIZE = 1048576  # 1MB分块大小
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """计算文件MD5哈希值"""
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    @staticmethod
    def encode_file(file_path: str, chunk_size: int = CHUNK_SIZE) -> Dict[str, Any]:
        """将ZIP文件编码为Base64字符串，支持分块"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not file_path.endswith('.zip'):
            raise ValueError(f"仅支持.zip文件，当前文件: {file_path}")
            
        file_stat = os.stat(file_path)
        file_info = {
            "file_name": os.path.basename(file_path),
            "file_size": file_stat.st_size,
            "file_hash": FileTransferUtil.calculate_file_hash(file_path),
            "chunks": [],
            "timestamp": int(file_stat.st_mtime)
        }
        
        with open(file_path, 'rb') as file:
            chunk_id = 0
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                    
                chunk_data = {
                    "chunk_id": chunk_id,
                    "chunk_size": len(chunk),
                    "data": base64.b64encode(chunk).decode('utf-8')
                }
                file_info["chunks"].append(chunk_data)
                chunk_id += 1
                
        file_info["total_chunks"] = len(file_info["chunks"])
        return file_info
    
    @staticmethod
    def decode_file(file_info: Dict[str, Any], output_dir: str) -> str:
        """将Base64编码的文件数据解码并保存"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        file_path = os.path.join(output_dir, file_info["file_name"])
        
        # 按块重组文件
        with open(file_path, 'wb') as file:
            sorted_chunks = sorted(file_info["chunks"], key=lambda x: x["chunk_id"])
            for chunk in sorted_chunks:
                data = base64.b64decode(chunk["data"])
                file.write(data)
        
        # 验证文件哈希值
        calculated_hash = FileTransferUtil.calculate_file_hash(file_path)
        if calculated_hash != file_info.get("file_hash"):
            os.remove(file_path)
            raise ValueError(f"文件校验失败: 期望{file_info.get('file_hash')}，实际{calculated_hash}")
        
        return file_path
    
    @staticmethod
    def split_file_info(file_info: Dict[str, Any], max_payload_size: int = 262144) -> list:
        """将文件信息分割为多个MQTT消息（每条消息限制为256KB）"""
        messages = []
        chunks = file_info.pop("chunks")
        
        # 第一条消息：元数据
        metadata_msg = {
            "type": "file_metadata",
            "file_name": file_info["file_name"],
            "file_size": file_info["file_size"],
            "file_hash": file_info["file_hash"],
            "total_chunks": file_info["total_chunks"],
            "timestamp": file_info["timestamp"]
        }
        messages.append(metadata_msg)
        
        # 后续消息：数据块
        for chunk in chunks:
            chunk_msg = {
                "type": "file_chunk",
                "file_name": file_info["file_name"],
                "chunk_id": chunk["chunk_id"],
                "chunk_size": chunk["chunk_size"],
                "total_chunks": file_info["total_chunks"],
                "data": chunk["data"]
            }
            messages.append(chunk_msg)
        
        return messages