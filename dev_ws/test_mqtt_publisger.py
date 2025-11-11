#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

def publish_event():
    # 使用 MQTT v5 协议
    client = mqtt.Client(protocol=mqtt.MQTTv5)
    client.username_pw_set("zone", "NeverGiveUp")
    
    try:
        client.connect("120.24.79.108", 1883, 60)
        
        message = {
            "timestamp": datetime.utcnow().isoformat(),
            "source_node": "ros_bridge",
            "source_topic": "/event_trigger",
            "data": True,
            "frame_id": "event_frame",
            "bridge_name": "event_trigger_bridge"
        }
        
        result = client.publish(
            "ros2/event_trigger/data", 
            json.dumps(message), 
            qos=1
        )
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print("消息发布成功")
        else:
            print(f"消息发布失败，错误码：{result.rc}")
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    publish_event()
