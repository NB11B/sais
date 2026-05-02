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

void sendHello() {
    // Discovery format:
    // HELLO,node_id,firmware_version,hardware_family,capability1|capability2,battery_mv,rssi_dbm
    char hello[128];
    int rssi = WiFi.RSSI();
    // In a real build, we'd measure battery. For bench test, assume 4100mV.
    snprintf(hello, sizeof(hello), 
        "HELLO,%s,0.1.0,esp32-soil-node,soil.moisture.vwc|soil.temperature,4100,%d",
        node_id, rssi
    );
    
    Serial.printf("Boot Discovery: %s\n", hello);
    udp.beginPacket(udpAddress, udpPort);
    udp.write((uint8_t*)hello, strlen(hello));
    udp.endPacket();
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n--- SAIS Soil Moisture Node (Provisioning Aware) ---");
    
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

    // Send discovery packet once on boot
    sendHello();
}

void loop() {
    // Read sensor every 10 seconds (throttle for bench test)
    if (millis() - lastMsgMs > 10000) {
        lastMsgMs = millis();
        
        // 1. Read Analog Value
        int rawVal = analogRead(sensorPin);
        
        // 2. Normalize to VWC (0.0 - 0.5 range for demo)
        float vwc = (rawVal / 4095.0) * 0.5; 
        
        // 3. Build SAIS UDP Packet
        char packet[128];
        snprintf(packet, sizeof(packet), 
            "%s,soil.moisture.vwc,%.2f,m3/m3,SoilPhysics,%s,%s,%d",
            node_id, vwc, field_id, zone_id, depth_cm
        );
        
        // 4. Send Packet
        Serial.printf("Telemetry: %s\n", packet);
        udp.beginPacket(udpAddress, udpPort);
        udp.write((uint8_t*)packet, strlen(packet));
        udp.endPacket();
    }
    
    // Maintain connection
    if (WiFi.status() != WL_CONNECTED) {
        ESP.restart();
    }
}
