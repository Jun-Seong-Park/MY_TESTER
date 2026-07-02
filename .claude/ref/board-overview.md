> description: Byrobot All Tester 보드의 최상위 개요 — 보드 정체, 주요 서브시스템, MCU 핵심 스펙, 블록 다이어그램, 개발자용 헤더(J301/J601), 전원 구조.
> when to use: 이 보드로 STM32 개발을 처음 시작하거나, 전체 구조를 한눈에 파악하고 어느 상세 ref 파일로 가야 할지 정할 때 가장 먼저 연다.
> caution: LED(PC13/PC14) 극성은 회로도에 LED 부품 심볼이 없어 미확인이다. 디버그 UART는 USART1(PB6/PB7)이며, USART2(PA2/PA3)와 혼동하지 말 것.

# 목차
1. 보드 정체와 주요 서브시스템
2. MCU 핵심 스펙
3. 블록 다이어그램 (한눈에)
4. 개발자용 헤더 (J301 디버그+UART, J601 확장)
5. 전원 구조 (USB-C 단일 전원)
6. 상세 ref 파일 안내

---

# 1. 보드 정체와 주요 서브시스템

Byrobot All Tester 는 STM32F401RCT6 를 중심으로 한 **NRF24L01P 무선 테스터 보드**다 (회로도 파일명 `Byrobot_All_Tester_NRF24L01P_USB-C_Schematic.pdf`, KiCad EDA 9.0.6, 7시트). 회로도는 6개 기능 시트로 나뉜다: 1_Ext_Connector, 2_Power, 3_MCU, 4_RF, 5_LCD_BUZZER, 6_Extra(회로도 p.7, Id 7/7).

| 서브시스템 | 부품 / 핵심 | MCU 인터페이스 | 근거 |
|---|---|---|---|
| MCU | STM32F401RCT6, LQFP-64 (U301) | — | 회로도 p.4, 3_MCU |
| RF | NRF24L01+ / QFN-20 (U401), 온보드 2.4G 안테나 | SPI2 + GPIO | 회로도 p.5, 4_RF |
| LCD | BR_LCD_128x64_2x6P (J501), 128×64 모노 | SPI1 (송신 전용) | 회로도 p.6, 5_LCD_BUZZER |
| 버튼 | LEFT/RIGHT/DOWN/UP 4개 (EXTI) | GPIO/EXTI | 회로도 p.7, 6_Extra |
| LED | PC13(RED) / PC14(GREEN) — 부품 심볼 미발견 | GPIO 출력 | 펌웨어 main.c:101, 극성 미확인 |
| 부저 | BZ501 Buzzer/5.5R/9055, NPN(SS8050) 드라이브 | TIM PWM (BUZZ_PWM) | 회로도 p.6, 5_LCD_BUZZER |
| USB | USB-C 디바이스(J101) + USB-A 호스트(J102), MUX로 전환 | USB OTG FS (PA11/PA12) | 회로도 p.2, 1_Ext_Connector |
| 확장 | J601 CON_AllTester26/34 | 다수 GPIO/ADC/SPI3/I2C | 회로도 p.7, 6_Extra |

USB 경로 핵심: USB-C(J101)와 USB-A(J102)가 **U101 FSUSB30MUX(MSOP-10)** 한 개로 다중화되어, MCU 의 단일 USB OTG FS(PA12=D+, PA11=D-)에 연결된다. `USB_SEL`(PA10, GPIO)로 두 포트 중 하나를 선택한다: SEL=0 → CH1(DEVICE=USB-C), SEL=1 → CH2(HOST=USB-A) (회로도 p.2, 1_Ext_Connector).

# 2. MCU 핵심 스펙

| 항목 | 값 | 근거 |
|---|---|---|
| 부품번호 / 패키지 | STM32F401RCT6 / LQFP-64 (10×10 mm) | 회로도 p.4 ("STM32F401RCT6/LQFP-64"); stm32f401rc.pdf p.1 |
| 코어 | Arm Cortex-M4 + FPU (105 DMIPS) | stm32f401rc.pdf p.1 |
| Flash | 256 Kbyte | stm32f401rc.pdf p.1 device summary ("C = 256 Kbytes of Flash memory") |
| SRAM | 64 Kbyte | stm32f401rc.pdf p.1 ("Up to 64 Kbytes of SRAM") |
| 최대 클럭 | 84 MHz | stm32f401rc.pdf p.1 ("frequency up to 84 MHz") |

참고(현재 펌웨어): 클럭 소스가 HSI, PLL=NONE 이라 현재 SYSCLK 은 16 MHz 로 동작한다 (최대 84 MHz 미사용). 전압 스케일 SCALE2 (main.c:140, 145-148). 상세는 current-firmware-config.md 참조.

# 3. 블록 다이어그램 (한눈에)

근거: 각 연결은 아래 섹션 4·5 및 회로도 시트별 인용과 동일.

```
                    USB-C J101 (device/sink)   USB-A J102 (host)
                          |  DEVICE_D+/-             |  HOST_D+/-
                          +-----------+   +----------+
                                      |   |
                                 +----v---v----+  USB_SEL = PA10 (GPIO)
                                 | U101        |<--- SEL=0->USB-C / SEL=1->USB-A
                                 | FSUSB30MUX  |     (회로도 p.2)
                                 +------+------+
                                        | MCU_D+/MCU_D-
                                        v
   J301 (SWD+UART)           PA12/PA11 = USB OTG FS
   SWDIO=PA13 SWCLK=PA14 ----+         |
   UART USART1: PB6=TX PB7=RX|   +-----+--------------------------------+
   /MCU_RESET, TVDD=VCC33 ---+-->|        STM32F401RCT6  (U301, LQFP64) |
                                 |                                      |
   RF  NRF24L01+ (U401) <--------+ SPI2: PB13 SCLK / PB14 MISO / PB15 MOSI
        IRQ=PB12(EXTI12)         | GPIO: PC6=/RF_CS  PC7=RF_CE          |
                                 |                                      |
   LCD 128x64 (J501)  <----------+ SPI1(송신): PB3 SCLK / PB5 MOSI       |
        /LCD_CS=PB10 /LCD_RST=PB4 | LCD_BK_PWM = PA15 (TIM2_CH1)         |
                                 |                                      |
   Buzzer BZ501 <----------------+ BUZZ_PWM = PA9 (TIM1_CH2) -> NPN     |
   Buttons: PC0=LEFT PB1=RIGHT --+ PB2=DOWN PC3=UP  (EXTI0/1/2/3)       |
   LEDs:    PC13=RED PC14=GREEN -+ (GPIO 출력, 극성 미확인)              |
                                 |                                      |
   J601 확장 헤더 <--------------+ PA0..PA8, PB0..PB2,PB8/9, PC0..PC15  |
        (ADC1, SPI3, I2C1/3 등)  | + VBUS/VCC33/GND                     |
                                 +--------------------------------------+
                                        ^ VCC33 (3.3V)
                                        |
   Power: USB-C VBUS 5V --> U201 ME6217C33 (LDO, SOT23-5) --> VCC33
          (USB-C 가 유일한 전원, 회로도 p.3)
```

# 4. 개발자용 헤더

## J301 — SWD 디버그 + 디버그 UART (SWD_ARM-8P_PETRONE)

ST-Link/J-Link 로 플래시·디버그하고, 동시에 디버그 시리얼을 뽑는 8핀 헤더다 (회로도 p.4, 3_MCU).

| 핀 | 신호 | 연결 / 의미 | 근거 |
|---|---|---|---|
| 1 | VBAT | D301(1N5819WS 쇼트키) 경유 | 회로도 p.4 |
| 2 | /MCU_RESET | ~{RESET}, R301 10K 풀업 | 회로도 p.4 |
| 3 | SWCLK | SWCLK = PA14 | 회로도 p.4 |
| 4 | SWDIO | SWDIO = PA13 | 회로도 p.4 |
| 5 | GND | — | 회로도 p.4 |
| 6 | TVDD | VCC33 (타깃 전압 센스) | 회로도 p.4 |
| 7 | TXD | 넷 DBG_M-TX = **USART1_TX = PB6** | 회로도 p.4 |
| 8 | RXD | 넷 DBG_M-RX = **USART1_RX = PB7** | 회로도 p.4 |

주의: 디버그 UART 는 **USART1(PB6/PB7, AF7)** 이다. KNOWN FACTS 의 "PA9/PA10" 은 잘못된 것으로, 회로도(mcu_r-4.png)에서 PA9=BUZZ_PWM(TIM1_CH2), PA10=USB_SEL(GPIO) 로 확인됨. 한편 펌웨어가 실제로 여는 시리얼은 별개의 USART2(PA2=TX, PA3=RX, AF7)다 (main.c:236, J601로 노출). 상세 connectors.md / peripherals.md 참조.

## J601 — 확장 헤더 (CON_AllTester26/34)

GPIO·ADC·SPI3·I2C 를 외부로 뽑는 26/34핀 헤더. 홀수=좌측열, 짝수=우측열 (회로도 p.7, 6_Extra; j601-7.png / j601r-7.png).

| 핀(홀) | 신호 | 핀(짝) | 신호 |
|---|---|---|---|
| 1 | PC15 | 2 | VCC33 |
| 3 | PC14 | 4 | PC13 |
| 5 | VBUS | 6 | VCC33 |
| 7 | PA0 (ADC1_0) | 8 | PB8 (I2C1_SCL) |
| 9 | PA1 (ADC1_1) | 10 | PB9 (I2C1_SDA) |
| 11 | PA2 (ADC1_2/U2TXD) | 12 | PC0 (BTN_LEFT/ADC1_10) |
| 13 | PA3 (ADC1_3/U2RXD) | 14 | PC1 (ADC1_11) |
| 15 | PA4 | 16 | PC2 (ADC1_12) |
| 17 | PA5 | 18 | PC3 (BTN_UP/ADC1_13) |
| 19 | PA6 | 20 | PC4 (ADC1_14) |
| 21 | PA7 | 22 | PC5 (ADC1_15) |
| 23 | PA8 (I2C3_SCL) | 24 | PC9 (I2C3_SDA) |
| 25 | PB0 | 26 | PC10 (SPI3_SCK) |
| 27 | PB1 (BTN_RIGHT) | 28 | PC11 (SPI3_MISO) |
| 29 | GND | 30 | PC12 (SPI3_MOSI) |
| 31 | PB2 (BTN_DOWN) | 32 | PC8 (TIM3_CH3) |
| 33 | GND | 34 | GND |

짝수열(2~34)은 회로도 우측열(j601r-7.png)에서 확인됨. 핀 5의 VBUS 와 핀 2/6의 VCC33 으로 외부 보드 급전도 가능하다 (회로도 p.7).

# 5. 전원 구조 — USB-C 단일 전원

이 보드의 유일한 전원은 USB-C(J101)의 VBUS 5V 다 (회로도 p.2, 1_Ext_Connector / p.3, 2_Power).

```
USB-C J101 VBUS(5V) --> [FB601 BEAD 180Ω] --> VBUS_F --> U201 ME6217C33(LDO, SOT23-5) --> VCC33(3.3V)
                                                          BC601/BC602 10uF 디커플링 (회로도 p.7)
```

- USB-C 의 CC1/CC2 에 각각 5.1K 풀다운 → 보드는 USB **디바이스(sink)** 로 동작, 호스트로부터 VBUS 5V 를 받는다 (회로도 p.2).
- VBUS → **U201 ME6217C33 (SOT23-5 LDO)** → VCC33(3.3V): MCU·RF·LCD 등 로직 전원 (회로도 p.3, 2_Power).
- VBUS(5V) 자체는 부저 하이사이드(BZ501, R501 10R 경유)에도 직접 쓰인다 (회로도 p.6).
- USB-A(J102) 의 VBUS 는 호스트 모드에서 외부 디바이스로 나가는 출력 경로이며, 보드를 급전하지 않는다 (회로도 p.2). 별도 배럴잭·배터리 입력은 회로도에 없다 → **USB-C 가 유일한 전원 소스**.

# 6. 상세 ref 파일 안내

이 문서는 진입 개요다. 세부는 아래로:

- 전체 핀 맵 (MCU 핀 ↔ 넷 ↔ AF) → pinmap.md
- 커넥터 핀아웃 상세 (J101/J102/J301/J501/J601) → connectors.md
- 페리페럴 동작 (SPI1/SPI2/USART1/USART2/ADC/TIM/I2C, RF·LCD·부저) → peripherals.md
- 전원 트리·LDO·디커플링 상세 → power.md
- STM32F401RC 데이터시트/레퍼런스 매뉴얼 핵심 발췌 → mcu-essentials.md
- 현재 펌웨어(.ioc/main.c) 설정 (클럭·핀·AF) → current-firmware-config.md

# 출처:
- Byrobot_All_Tester_NRF24L01P_USB-C_Schematic.pdf (KiCad EDA 9.0.6, 7시트) — 회로도 p.2(1_Ext_Connector), p.3(2_Power), p.4(3_MCU), p.5(4_RF), p.6(5_LCD_BUZZER), p.7(6_Extra). (취득 2026-06-24)
- stm32f401rc.pdf (STM32F401xB/STM32F401xC datasheet, STMicroelectronics) — p.1 device summary. (취득 2026-06-24)
- 펌웨어 Core/Src/main.c (MY_TESTER 프로젝트). (취득 2026-06-24)
