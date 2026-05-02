#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>

// --- Configuration ---
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Dashboard Machine IP and Bridge Port
const char* udpAddress = "192.168.1.XXX"; // Update with your dashboard IP
const int udpPort = 5001;

// Metadata for SAIS
const char* node_id = "soil-node-north";
const char* field_id = "field-a";
const char* zone_id = "zone-a1";
const int depth_cm = 10;

// Hardware Pins
const int sensorPin = 34; // Analog input (ADC1_CH6)

// --- Globals ---
WiFiUDP udp;
unsigned long lastMsgMs = 0;

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n--- SAIS Soil Moisture Node ---");
    
    // Connect to Wi-Fi
    Serial.printf("Connecting to %s ", ssid);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nCONNECTED!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
}

void loop() {
    // Read sensor every 5 seconds
    if (millis() - lastMsgMs > 5000) {
        lastMsgMs = millis();
        
        // 1. Read Analog Value
        int rawVal = analogRead(sensorPin);
        
        // 2. Normalize to VWC (0.0 - 0.5 range for demo)
        // Adjust these values based on your specific sensor calibration
        float vwc = (rawVal / 4095.0) * 0.5; 
        
        // 3. Build SAIS UDP Packet (8-field format)
        // node_id,measurement_id,value,unit,layer,field_id,zone_id,depth_cm
        char packet[128];
        snprintf(packet, sizeof(packet), 
            "%s,soil.moisture.vwc,%.2f,m3/m3,SoilPhysics,%s,%s,%d",
            node_id, vwc, field_id, zone_id, depth_cm
        );
        
        // 4. Send Packet
        Serial.printf("Sending: %s\n", packet);
        udp.beginPacket(udpAddress, udpPort);
        udp.write((uint8_t*)packet, strlen(packet));
        udp.endPacket();
        
        Serial.println("Packet sent.");
    }
    
    // Maintain connection
    if (WiFi.status() != WL_CONNECTED) {
        ESP.restart();
    }
}
