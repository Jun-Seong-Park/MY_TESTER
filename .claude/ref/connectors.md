> description: All-Tester (NRF24L01P / USB-C) 보드의 외부 커넥터 5종(J101 USB-C, J102 USB-A, J301 SWD/UART 디버그, J501 LCD 모듈, J601 26/34 확장 헤더) 핀-바이-핀 핀아웃과 각 핀의 MCU 핀/기능/net 매핑.
> when to use: 보드에 무언가를 꽂거나(USB-to-TTL, J-Link, LCD, 확장 보드) 케이블·하니스를 만들 때, 또는 커넥터 핀이 어떤 MCU 핀/net 으로 가는지 추적할 때 연다.
> caution: (1) 디버그 UART(J301 7/8번)는 **USART1 = PB6/PB7** 이다. PA9/PA10 이 아니다(아래 §3, §0 정정). (2) 이 보드에는 on-board LED 부품이 없다 — PC13/PC14 는 J601 로 빠지는 GPIO 일 뿐, 극성을 회로도로 확정할 수 없다(§0). (3) 회로도 MCU 시트의 PB14 alt-function 라벨 "SPI2_MOSI" 는 오타로 보인다(실제 SPI2_MISO, §0).

# 목차
- [0. 정정 / 주의 (KNOWN FACTS 대비)](#0-정정--주의-known-facts-대비)
- [1. 커넥터 한눈 요약](#1-커넥터-한눈-요약)
- [2. J101 — USB-C 16P (DEVICE)](#2-j101--usb-c-16p-device)
- [3. J301 — SWD_ARM-8P_PETRONE (디버그 SWD + UART)](#3-j301--swd_arm-8p_petrone-디버그-swd--uart)
- [4. J102 — USB-A Female (HOST)](#4-j102--usb-a-female-host)
- [5. J601 — CON_AllTester26/34 확장 헤더](#5-j601--con_alltester2634-확장-헤더)
- [6. J501 — LCD 모듈 (BR_LCD_128x64_2x6P)](#6-j501--lcd-모듈-br_lcd_128x64_2x6p)
- [7. USB mux(U101) / 전원 흐름 보조 설명](#7-usb-muxu101--전원-흐름-보조-설명)
- [8. 자주 쓰는 연결 요약](#8-자주-쓰는-연결-요약)
- [출처](#출처)

---

## 0. 정정 / 주의 (KNOWN FACTS 대비)

작업 지시에 딸려온 KNOWN FACTS 중 회로도/펌웨어와 **다른** 항목을 먼저 정정합니다(근거 함께).

1. **디버그 UART = USART1 = PB6/PB7 (PA9/PA10 아님).**
   - KNOWN FACTS 는 J301 TXD/RXD net `DBG_M-TX = USART1_TX = PA9`, `DBG_M-RX = USART1_RX = PA10` 이라 했으나, MCU 시트에서 `DBG_M-TX` 는 **PB6(USART1_TX)**, `DBG_M-RX` 는 **PB7(USART1_RX)** 에 연결됩니다 (회로도 p.4, 3_MCU — PB6/PB7 핀 옆 net label).
   - PA9 = **BUZZ_PWM**(TIM1_CH2), PA10 = **USB_SEL**(GPIO) 입니다 (회로도 p.4, 3_MCU).
   - 펌웨어도 일치: PB6/PB7 을 `GPIO_AF7_USART1` 로 설정 (main.c:386-391). PA9 는 `GPIO_AF1_TIM1`(main.c:333-337), PA10 은 일반 출력(main.c:340-345).

2. **on-board LED 부품 없음 — PC13/PC14 극성 회로도로 확정 불가.**
   - 7페이지 전체에 LED/다이오드 부품은 D301(J301 VBAT용 Schottky 1N5819) 하나뿐입니다 (회로도 전수, `D[0-9]+` refdes 검색 결과 D301 only). 저항+LED 네트워크가 없습니다.
   - PC13 은 J601 4번, PC14 는 J601 3번으로만 빠집니다 (회로도 p.7, 6_Extra). 즉 "RED/GREEN LED" 는 J601 에 꽂는 외부 모듈/하니스에 있고, **active-high/active-low 극성은 이 회로도로는 판단 불가** 입니다.
   - 펌웨어 주석은 `LED PC13 RED / PC14 GREEN (SET=on, RESET=off)` (main.c:101) 이지만 이는 펌웨어 가정일 뿐 회로도 근거가 아닙니다.

3. **RF SPI2 핀 라벨 오타(추정).** MCU 시트에서 PB14(RF_MISO) 의 alt-function 텍스트가 `SPI2_MOSI` 로 적혀 있는데, PB15(RF_MOSI)도 `SPI2_MOSI` 라 둘이 겹칩니다. STM32F401 에서 PB14 는 SPI2_MISO 이므로 회로도 라벨 오타로 보입니다 (회로도 p.4, 3_MCU). net 배선 자체(PB13=SCLK, PB14=MISO, PB15=MOSI)는 정상입니다.

---

## 1. 커넥터 한눈 요약

| refdes | 부품명 | 시트(페이지) | 한 줄 용도 |
|---|---|---|---|
| **J101** | USB-C_16P(1PAD) | 1_Ext_Connector (p.2) | 보드 **유일 전원 입력(VBUS 5V)** + USB device 포트. CC1/CC2 5.1k 풀다운으로 sink/device. |
| **J102** | USB-A_Female(1PAD) | 1_Ext_Connector (p.2) | USB **host** 포트. mux(U101) CH2 로 연결, 보드가 host 로 동작 시 다른 USB 장치를 붙임. |
| **J301** | SWD_ARM-8P_PETRONE | 3_MCU (p.4) | **디버그/플래시 커넥터** — SWD(J-Link 등) + 디버그 UART(USART1) + 타깃전압 sense. |
| **J501** | BR_LCD_128x64_2x6P | 5_LCD_BUZZER (p.6) | **LCD 128x64 모듈** 커넥터(SPI1 transmit-only) + LCD 면의 4-way 버튼 입력. |
| **J601** | CON_AllTester26/34 | 6_Extra (p.7) | **확장/테스트 헤더**(2.54mm 2열). ADC/GPIO/I2C/SPI3/UART2/전원을 외부로 노출. |

> J 외 외부 커넥터는 없습니다. NPTH1/2/11/12/13/14 는 비도금 마운팅 홀(non-plated, 전기 연결 없음)입니다 (회로도 p.1 시트맵).

---

## 2. J101 — USB-C 16P (DEVICE)

USB-C 리셉터클(16핀). 보드의 **유일한 전원 입력**이며 USB 2.0 device 데이터 라인을 제공합니다 (회로도 p.2, 1_Ext_Connector).

| 핀(USB-C) | net | 기능 / 연결 | 비고 |
|---|---|---|---|
| A4 / B9 | VBUS | 5V 입력 | FB603(bead) 거쳐 VBUS rail → LDO U201 |
| A9 / B4 | VBUS | 5V 입력 | A4B9/A9B4 동일 VBUS |
| A6 | Dp1 (D+) | R603 27Ω 직렬 → DEVICE_D+ | mux U101 HSD1+(2) |
| A7 | Dn1 (D-) | R604 27Ω 직렬 → DEVICE_D- | mux U101 HSD1-(8) |
| B6 | Dp2 (D+) | A6 와 묶임(리버서블) | |
| B7 | Dn2 (D-) | A7 과 묶임(리버서블) | |
| A5 | CC1 | R601 5.1kΩ → GND | sink/device 풀다운 (UFP) |
| B5 | CC2 | R602 5.1kΩ → GND | sink/device 풀다운 (UFP) |
| A8 | SBU1 | 미연결(NC) | × 표시 |
| B8 | SBU2 | 미연결(NC) | × 표시 |
| A1 / B12 | GND | GND | |
| A12 / B1 | GND | GND | |
| PAD | USB_SHIELD | shield | |

- 전원 경로: J101 VBUS → FB603 bead → **VBUS rail** → LDO **U201 ME6217C33(SOT23-5)** → **VCC33 3.3V** (회로도 p.3, 2_Power). 보드는 USB-C VBUS 로만 전원을 받습니다.
- 데이터: DEVICE_D+/DEVICE_D- 는 mux U101 의 CH1 입력. SEL=0 일 때 MCU(PA12/PA11)와 연결 (회로도 p.2, §7 참조).
- C601/C602 47pF: D+/D- ESD/EMI 필터. R3 10k: mux D+ 풀(보조).

---

## 3. J301 — SWD_ARM-8P_PETRONE (디버그 SWD + UART)

8핀 디버그 커넥터. **SWD(J-Link 등으로 플래시/디버그) + 디버그 UART + 타깃전압 sense + 배터리 sense** 를 한 커넥터에 모았습니다 (회로도 p.4, 3_MCU). 핀 배열은 2열(홀수 좌측 1/3/5/7, 짝수 우측 2/4/6/8).

| 핀 | net | MCU 핀 / 기능 | 분류 | 비고 |
|---|---|---|---|---|
| 1 | VBAT | — | **전원/sense** | D301 1N5819 Schottky 거쳐 들어옴 (역류 방지) |
| 2 | /MCU_RESET (~{RESET}) | NRST | **SWD(reset)** | R301 10k pull-up + C301 100n |
| 3 | SWCLK | PA14 (SWCLK) | **SWD** | clock |
| 4 | SWDIO | PA13 (SWDIO) | **SWD** | data |
| 5 | GND | — | **전원** | |
| 6 | TVDD | VCC33 | **전원/sense** | target reference voltage (3.3V sense) |
| 7 | TXD | **PB6 = USART1_TX** (net DBG_M-TX) | **UART** | 디버그 콘솔 TX |
| 8 | RXD | **PB7 = USART1_RX** (net DBG_M-RX) | **UART** | 디버그 콘솔 RX |

- **J-Link(SWD)**: 핀 2(/RESET), 3(SWCLK), 4(SWDIO), 5(GND), 6(TVDD) 사용 (회로도 p.4, 3_MCU; J301c 심볼).
- **UART**: 핀 7(TXD)/8(RXD)/5(GND). net DBG_M-TX→PB6, DBG_M-RX→PB7 = **USART1**(AF7) (회로도 p.4, 3_MCU; main.c:386-391). KNOWN FACTS 의 PA9/PA10 은 오류 — §0 참조.
- 핀1 VBAT 는 D301(1N5819WS, SOD-323)을 통해 들어와 MCU VBAT 핀으로 갑니다 (회로도 p.4, 3_MCU).

---

## 4. J102 — USB-A Female (HOST)

USB-A 암 커넥터(4핀 + 1PAD). 보드가 **USB host** 로 동작할 때 외부 USB 장치를 붙이는 포트입니다. 데이터는 mux U101 CH2(HOST) 로 들어갑니다 (회로도 p.2, 1_Ext_Connector).

| 핀 | net | 연결 | 비고 |
|---|---|---|---|
| 1 | VBUS | VBUS rail | host 측에 5V 공급 |
| 2 | D- | HOST_D- | mux U101 HSD2-(7) |
| 3 | D+ | HOST_D+ | mux U101 HSD2+(3) |
| 4 | GND | GND | |
| PAD | (shield) | R2 0Ω → GND | shield ground |

- host 데이터(HOST_D+/HOST_D-)는 SEL=1 일 때 MCU(PA12/PA11)와 연결됩니다 (§7).

---

## 5. J601 — CON_AllTester26/34 확장 헤더

2.54mm 2열 핀헤더(최대 34핀). ADC 입력, GPIO, I2C, SPI3, UART2, 전원(VBUS/VCC33/GND) 을 외부로 노출하는 **확장/테스트 헤더**입니다. 홀수=좌열, 짝수=우열 (회로도 p.7, 6_Extra; J601 / J601r 심볼).

### 홀수 핀 (1 ~ 33)

| 핀 | net | MCU 핀 / 기능 | 비고 |
|---|---|---|---|
| 1 | PC15 | PC15 (OSC32_OUT) | GPIO |
| 3 | PC14 | PC14 (OSC32_IN) | GPIO (펌웨어상 "GREEN LED") |
| 5 | VBUS | VBUS rail | 5V |
| 7 | PA0 | PA0 — ADC1_0 / TIM5_CH1 | |
| 9 | PA1 | PA1 — ADC1_1 / TIM5_CH2 | |
| 11 | PA2 | PA2 — ADC1_2 / **U2TXD(USART2_TX)** / TIM5_CH3 / TIM9_CH1 | **USB-to-TTL TX** |
| 13 | PA3 | PA3 — ADC1_3 / **U2RXD(USART2_RX)** / TIM5_CH4 / TIM9_CH2 | **USB-to-TTL RX** |
| 15 | PA4 | PA4 — ADC1_4 | |
| 17 | PA5 | PA5 — ADC1_5 | |
| 19 | PA6 | PA6 — ADC1_6 / TIM3_CH1 | |
| 21 | PA7 | PA7 — ADC1_7 / TIM3_CH2 | |
| 23 | PA8 | PA8 — I2C3_SCL | |
| 25 | PB0 | PB0 — ADC1_8 / TIM3_CH3 | |
| 27 | PB1 | PB1 — ADC1_9 / TIM3_CH4 / **BTN_RIGHT(LB_RIGHT, EXTI1)** | |
| 29 | GND | GND | |
| 31 | PB2 | PB2 — **BTN_DOWN(LB_DOWN)** | |
| 33 | GND | GND | |

### 짝수 핀 (2 ~ 34) — 회로도 확인 완료

| 핀 | net | MCU 핀 / 기능 | 비고 |
|---|---|---|---|
| 2 | VCC33 | 3.3V rail | (AVCC33 로 연결) |
| 4 | PC13 | PC13 (VSSA/VREF- 인접 핀) | GPIO (펌웨어상 "RED LED") |
| 6 | VCC33 | 3.3V rail | |
| 8 | PB8 | PB8 — I2C1_SCL / TIM4_CH3 / TIM10_CH1 | |
| 10 | PB9 | PB9 — I2C1_SDA / TIM4_CH4 / TIM11_CH1 | |
| 12 | PC0 | PC0 — ADC1_10 / **BTN_LEFT(LB_LEFT, EXTI0)** | |
| 14 | PC1 | PC1 — ADC1_11 | |
| 16 | PC2 | PC2 — ADC1_12 | |
| 18 | PC3 | PC3 — ADC1_13 / **BTN_UP(LB_UP)** | |
| 20 | PC4 | PC4 — ADC1_14 | |
| 22 | PC5 | PC5 — ADC1_15 | |
| 24 | PC9 | PC9 — I2C3_SDA / TIM3_CH4 | |
| 26 | PC10 | PC10 — SPI3_SCK | |
| 28 | PC11 | PC11 — SPI3_MISO | |
| 30 | PC12 | PC12 — SPI3_MOSI | |
| 32 | PC8 | PC8 — TIM3_CH3 | |
| 34 | GND | GND | |

- **USB-to-TTL 어댑터용 UART = J601 핀 11(PA2 = USART2_TX) / 핀 13(PA3 = USART2_RX) / GND(핀 29 또는 33).** USART2 는 PA2=TX, PA3=RX, AF7 (회로도 p.7, 6_Extra; main.c:236-244 USART2 115200-8-N-1; hal_msp.c:196-203 AF7). 펌웨어가 실제 활성화한 UART 도 USART2 입니다.
- 버튼 net: BTN_LEFT=PC0(12번), BTN_RIGHT=PB1(27번), BTN_DOWN=PB2(31번), BTN_UP=PC3(18번) (회로도 p.7, 6_Extra; main.c:101 주석/PC0·PC3 출력설정은 별개).
- 헤더 전원 디커플: BC601/BC602 10u, FB601 bead 로 VBUS→VBUS_F (회로도 p.7).

---

## 6. J501 — LCD 모듈 (BR_LCD_128x64_2x6P)

LCD 128x64 모듈 커넥터(2열 6핀 = 12핀). LCD 는 **SPI1 transmit-only** 로 구동하고, LCD 면의 4-way 버튼 입력도 이 커넥터로 들어옵니다 (회로도 p.6, 5_LCD_BUZZER). 좌열 1~6, 우열 7~12.

| 핀 | net | MCU 핀 / 기능 | 비고 |
|---|---|---|---|
| 1 | LCD_BK_CTRL | (백라이트 제어) | LCD backlight |
| 2 | /LCD_RST | PB4 (net /LCD_RESET) | LCD reset, active-low |
| 3 | LCD_DAT/~CMD | PD2 (net LCD_DAT/~{CMD}) | D/C 선택 |
| 4 | BTN_LCD_UP | PC3 (BTN_UP) | 버튼 입력 |
| 5 | BTN_LCD_LEFT | PC0 (BTN_LEFT) | 버튼 입력 |
| 6 | VDD_LCD | VCC33 | LCD 전원 |
| 7 | BTN_LCD_RIGHT | PB1 (BTN_RIGHT) | 버튼 입력 |
| 8 | BTN_LCD_DOWN | PB2 (BTN_DOWN) | 버튼 입력 |
| 9 | LCD_SCLK | PB3 (SPI1_SCK) | SPI clock |
| 10 | /LCD_CS | PB10 (net /LCD_CS, GPIO) | chip select, active-low |
| 11 | LCD_MOSI | PB5 (SPI1_MOSI) | SPI data |
| 12 | GND | GND | |

- LCD backlight PWM 은 **PA15 = TIM2_CH1**(net LCD_BK_PWM) 로 별도 구동 (회로도 p.4, 3_MCU; main.c:355-360 AF1_TIM2). J501 1번 LCD_BK_CTRL 은 이 백라이트 제어 net 입니다.
- SPI1 핀: SCLK=PB3, MOSI=PB5 (회로도 p.4; main.c:378-383 PB3/PB5 = AF5_SPI1). MISO 는 LCD 가 transmit-only 라 미사용.

---

## 7. USB mux(U101) / 전원 흐름 보조 설명

USB 데이터는 **U101 FSUSB30MUX (USB2.0 MUX, MSOP-10)** 가 device/host 를 전환합니다 (회로도 p.2, 1_Ext_Connector).

| U101 핀 | 신호 | 연결 |
|---|---|---|
| 1 | SEL | USB_SEL = **PA10(GPIO)** |
| 4 | D+ | MCU_D+ = **PA12** (USB OTG FS) |
| 6 | D- | MCU_D- = **PA11** (USB OTG FS) |
| 2 | HSD1+ | DEVICE_D+ (→ J101) |
| 8 | HSD1- | DEVICE_D- (→ J101) |
| 3 | HSD2+ | HOST_D+ (→ J102) |
| 7 | HSD2- | HOST_D- (→ J102) |
| 9 | /OE | GND (항상 enable) |
| 10 | VCC | VCC33 |
| 5 | GND | GND |

- **SEL=0 → CH1 = DEVICE = USB-C(J101)**, **SEL=1 → CH2 = HOST = USB-A(J102)** (회로도 p.2 텍스트 라벨). USB_SEL 은 GPIO PA10 (회로도 p.4; main.c:340-345 일반 출력).
- MCU USB 핀 PA11/PA12 는 AF10_OTG_FS (회로도 p.4; main.c:347-353).
- 전원 흐름: J101 VBUS(5V) → FB603 → VBUS → **U201 ME6217C33** LDO → VCC33(3.3V). VCC33 은 다시 AVCC33(FB201/FB202 bead 분리) 로 ADC/RF 아날로그 전원에 공급 (회로도 p.3, 2_Power).

---

## 8. 자주 쓰는 연결 요약

- **USB-to-TTL 시리얼 어댑터를 붙일 때**: **J601 11번(PA2, USART2_TX) ↔ 어댑터 RX**, **J601 13번(PA3, USART2_RX) ↔ 어댑터 TX**, **GND = J601 29 또는 33번**. (펌웨어가 USART2 115200-8-N-1 로 콘솔 출력 — main.c:120-121.)
- **J-Link / SWD 디버거를 붙일 때**: **J301** 사용 — 2(/RESET), 3(SWCLK), 4(SWDIO), 5(GND), 6(TVDD=3.3V sense). 디버그 UART 도 같은 커넥터 7(TXD=PB6)/8(RXD=PB7=USART1).
- **전원**: USB-C(J101)만으로 켜짐. J102/J601 의 VBUS 는 출력(5V passthrough)이며 입력 전원으로 쓰지 않음.

---

## 출처
- Byrobot_All_Tester_NRF24L01P_USB-C_Schematic.pdf (KiCad E.D.A. 9.0.6, 7 sheets), 경로: `MY_TESTER/References/Byrobot_All_Tester_NRF24L01P_USB-C_Schematic.pdf` — pdftotext/pdftoppm 로 추출·렌더 후 확인 (2026-06-24)
  - p.1 시트맵, p.2 1_Ext_Connector(J101/J102/U101), p.3 2_Power(U201), p.4 3_MCU(STM32F401RCT6 LQFP-64, J301), p.6 5_LCD_BUZZER(J501), p.7 6_Extra(J601)
- 펌웨어: `MY_TESTER/Core/Src/main.c`, `MY_TESTER/Core/Src/stm32f4xx_hal_msp.c` (AF/peripheral muxing 교차검증, 2026-06-24)
