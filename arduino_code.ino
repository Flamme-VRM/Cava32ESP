#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>

// Твои пины
#define TFT_CS   5
#define TFT_DC   2
#define TFT_RST  4

Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_RST);

const int numBars = 10; // Количество столбиков
int barWidth = 22;      // Ширина одного столбика
int prevHeights[numBars];

void setup() {
  Serial.begin(1000000); // Скорость 1 Мбит/с для плавности!
  tft.init(240, 280);
  tft.setRotation(0);
  tft.fillScreen(ST77XX_BLACK);
  
  for(int i=0; i<numBars; i++) prevHeights[i] = 0;
}

void loop() {
  if (Serial.available() > 0) {
    // Ждем символ начала пакета
    if (Serial.read() == 'B') {
      for (int i = 0; i < numBars; i++) {
        int height = Serial.read(); // Считываем высоту (0-255)
        height = map(height, 0, 255, 0, 260); // Масштабируем под экран

        // Рисуем только если высота изменилась (оптимизация)
        if (height != prevHeights[i]) {
          // Стираем верхушку старого столбика (черным)
          if (height < prevHeights[i]) {
            tft.fillRect(i * (barWidth + 2), 0, barWidth, 280 - height, ST77XX_BLACK);
          }
          // Рисуем новый столбик (градиент или один цвет)
          uint16_t color = tft.color565(height, 100, 255 - height);
          tft.fillRect(i * (barWidth + 2), 280 - height, barWidth, height, color);
          
          prevHeights[i] = height;
        }
      }
    }
  }
}