/**
  ******************************************************************************
  * @file    uc1701x.h
  * @brief   JLX12864G-0088 (UC1701X 컨트롤러) 128x64 모노 LCD 드라이버.
  *
  * 결선 (회로도 p.6 / .claude/ref/peripherals.md §2):
  *   SPI1 TX-only : PB3 = SCLK, PB5 = MOSI (2.625 MBit/s)
  *   PB10 = /LCD_CS (active-low), PB4 = /LCD_RESET (active-low)
  *   PD2  = D/C (LOW = command, HIGH = data)
  *   백라이트 = PA15 TIM2_CH1 PWM (드라이버 범위 밖, main 에서 제어)
  *
  * 초기화 시퀀스 출처: JLX12864G-0088 中文说明书 p.14 (curl 확인 2026-07-03),
  * 컨트롤러 명시: 같은 문서 2.2절 "IC 采用 UC1701X".
  ******************************************************************************
  */
#ifndef UC1701X_H
#define UC1701X_H

#include "stm32f4xx_hal.h"

#define UC1701X_CS_PORT    GPIOB
#define UC1701X_CS_PIN     GPIO_PIN_10
#define UC1701X_RST_PORT   GPIOB
#define UC1701X_RST_PIN    GPIO_PIN_4
#define UC1701X_DC_PORT    GPIOD
#define UC1701X_DC_PIN     GPIO_PIN_2

#define UC1701X_WIDTH      128U
#define UC1701X_HEIGHT     64U
#define UC1701X_PAGES      8U    /* 페이지 1개 = 세로 8픽셀 (LSB 가 위) */
#define UC1701X_RAM_COLS   132U  /* 컨트롤러 RAM 폭: 표시 128 + 여분 4 */

#define UC1701X_FONT_W     6U    /* 글리프 5px + 간격 1px */

void uc1701x_init(SPI_HandleTypeDef *hspi);
void uc1701x_clear(void);
void uc1701x_draw_string(uint8_t page, uint8_t x, const char *text);

#endif /* UC1701X_H */
