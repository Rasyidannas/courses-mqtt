from command import *
import paho.mqtt.client as mqtt
import os.path
import time
import json

certificates_path = "./python_certificates"
ca_certificate = os.path.join(certificates_path, "ca.crt")
client_certificate = os.path.join(certificates_path, "device001.crt")
client_key = os.path.join(certificates_path, "device001.key")

mqtt_server_host = "192.168.8.129"
mqtt_server_port = 8883
mqtt_keepalive = 60

drone_name = "drone01"
commands_topic = f"commands/{drone_name}"
processed_commands_topic = f"processedcommands/{drone_name}"


class LoopControl:
    is_last_command_processed = False

    @staticmethod
    def on_connect(client, userdata, flags, rc):
        print("Connect result:", mqtt.connack_string(rc))
        client.subscribe(processed_commands_topic)

    @staticmethod
    def on_message(client, userdata, msg):
        if msg.topic == processed_commands_topic:
            payload_string = msg.payload.decode('utf-8')
            print(payload_string)

            if CMD_LAND_IN_SAFE_PLACE in payload_string:
                LoopControl.is_last_command_processed = True

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        print("Subscribed with QoS:", granted_qos[0])

    @staticmethod
    def publish_command(client, command_name, key="", value=""):
        if key:
            command_message = json.dumps({
                COMMAND_KEY: command_name,
                key: value
            })
        else:
            command_message = json.dumps({
                COMMAND_KEY: command_name
            })

        return client.publish(commands_topic, command_message, qos=2)


if __name__ == "__main__":
    client = mqtt.Client(protocol=mqtt.MQTTv311)

    client.on_connect = LoopControl.on_connect
    client.on_subscribe = LoopControl.on_subscribe
    client.on_message = LoopControl.on_message

    client.tls_set(
        ca_certs=ca_certificate,
        certfile=client_certificate,
        keyfile=client_key
    )

    client.connect(mqtt_server_host, mqtt_server_port, mqtt_keepalive)

    client.loop_start()
    time.sleep(1)  # wait for connection

    LoopControl.publish_command(client, CMD_TAKE_OFF)
    LoopControl.publish_command(client, CMD_MOVE_UP)
    LoopControl.publish_command(client, CMD_ROTATE_LEFT, KEY_DEGREES, 90)
    LoopControl.publish_command(client, CMD_ROTATE_LEFT, KEY_DEGREES, 45)
    LoopControl.publish_command(client, CMD_ROTATE_LEFT, KEY_DEGREES, 45)
    LoopControl.publish_command(client, CMD_LAND_IN_SAFE_PLACE)

    while not LoopControl.is_last_command_processed:
        time.sleep(1)

    client.disconnect()
    client.loop_stop()
