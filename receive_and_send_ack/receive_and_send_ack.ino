#include "BluetoothSerial.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth not enabled!
#endif

BluetoothSerial SerialBT;

void setup() {
  delay(2000);
  Serial.begin(115200);
  SerialBT.begin("ESP32_BT");
  Serial.println("The device started, you can now pair it using Bluetooth.");
}

void loop() {
  if (SerialBT.available()) {
    String message = SerialBT.readString();
    Serial.println("Received: " + message);


    //if (message == "ON" || message == "OFF") {
      SerialBT.println("ACK_" + message + " FROM ESP:)");  // Acknowledgment message
      Serial.println("Sent ACK for " + message);
    //}
  }
  delay(20);
}
