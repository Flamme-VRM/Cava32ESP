# CavaESP32 - Audio Visualizer Bridge

**CavaESP32** is a Python based audio processing tool that captures your Windows system audio (what you hear), analyzes it in real-time, and sends frequency data to an ESP32 or Arduino microcontroller via USB Serial. This allows you to build physical audio visualizers (e.g., LED strips) that react to music, games, or videos.

## Demo
![Demo](demo.gif)

## Features

*   **System Audio Capture:** Uses `pyaudiowpatch` (WASAPI Loopback) to capture high-quality audio directly from your output device (no microphone needed).
*   **Real-time Processing:** Performs Fast Fourier Transform (FFT) to break audio into frequency bands.
*   **Optimized for Microcontrollers:** Downmixes stereo to mono, calculates average volume for 10 distinct frequency bars, and sends lightweight binary packets.
*   **High Speed:** configured for 1,000,000 baud rate for minimal latency.

## Requirements

### Hardware
*   PC running Windows (for WASAPI Loopback support).
*   ESP32 or Arduino board connected via USB.

### Software
*   Python 3.11+
*   The following Python libraries:
    *   `numpy`
    *   `pyaudiowpatch`
    *   `pyserial`

## Installation

1.  **Clone or Download** this repository.
2.  **Create a Virtual Environment** (optional but recommended):
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install numpy pyserial pyaudiowpatch
    ```

## Configuration & Usage

### 1. Find Your Audio Device ID
Before using the visualizer, you need to tell the script which audio device to listen to (e.g., your headphones or speakers).

1.  Open `cavaESP32.py` in a text editor.
2.  Find the line `DEVICE_INDEX = 13` (or whatever number is there) and change it to:
    ```python
    DEVICE_INDEX = None
    ```
3.  Run the script:
    ```bash
    python cavaESP32.py
    ```
4.  The script will print a list of available WASAPI Loopback devices. Look for the one matching your output device (e.g., "Speakers" or "Headphones"). Note its **ID**.

### 2. Configure the Script
1.  Open `cavaESP32.py` again.
2.  Set `DEVICE_INDEX` to the ID you found in the previous step.
3.  Set `PORT` to the COM port of your microcontroller (e.g., `'COM3'`). You can find this in Windows Device Manager.
4.  (Optional) Adjust other settings if needed:
    *   `BAUD`: Serial baud rate (default: `1000000`). Must match your microcontroller code.
    *   `NUM_BARS`: Number of frequency bars to send (default: `10`).

### 3. Run the Visualizer
Once configured, run the script normally:
```bash
python cavaESP32.py
```
If successful, you will see "Визуализатор работает!" and your microcontroller should start receiving data. Press `Ctrl+C` to stop.

## Serial Protocol
The script sends data to the microcontroller in the following binary format:

*   **Header:** 1 Byte (`'B'` or `0x42`) - Used to sync the start of the packet.
*   **Data:** 10 Bytes - One byte for each frequency bar (values 0-255).

**Total Packet Size:** 11 Bytes.

### Example Arduino/ESP32 Code Snippet (C++)
```cpp
void setup() {
  Serial.begin(1000000); // Must match Python script
}

void loop() {
  if (Serial.available() >= 11) {
    if (Serial.read() == 'B') { // Check header
      uint8_t bars[10];
      Serial.readBytes(bars, 10);
      
      // Now use 'bars' array to control LEDs
      // analogWrite(LED_PIN, bars[0]); 
    }
  }
}
```

## Troubleshooting
*   **"WASAPI not found":** Ensure you are running on Windows.
*   **"Access Denied" or Port Error:** Close any other programs using the COM port (like Arduino IDE Serial Monitor or Cura).
*   **Low/High Sensitivity:** Adjust the divisor in the line `bar_data = [int(np.sum(band) / 500) ...`. Lower value = higher sensitivity.
