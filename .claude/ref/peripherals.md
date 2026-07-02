> description: All-Tester (NRF24L01P / USB-C) 보드의 온보드 주변장치(RF, LCD, 버튼, LED, 부저, USB)와 각 장치가 사용하는 STM32F401RCT6 핀/버스 매핑.
> when to use: 펌웨어에서 특정 주변장치를 드라이브할 때(SPI/EXTI/TIM/GPIO 설정), 또는 회로도 핀 매핑을 확인할 때 연다.
> caution: 이 회로도에는 LED 부품 자체가 없다(PC13/PC14는 J601로 빠지는 GPIO일 뿐; 색·극성은 펌웨어/외부배선 소관이라 고정 기록 안 함). 디버그 USART1 은 PB6/PB7 이며 PA9/PA10 이 아니다(아래 정정 참고). PB14 의 alt-function 라벨 "SPI2_MOSI" 는 회로도 오타(실제 SPI2_MISO).

# 목차
- [0. 정정 / 주의 사항 (known facts 대비)](#0-정정--주의-사항)
- [1. RF 모듈 — NRF24L01+ (SPI2)](#1-rf-모듈--nrf24l01-spi2)
- [2. LCD (SPI1, transmit-only)](#2-lcd-spi1-transmit-only)
- [3. 버튼 (Buttons)](#3-버튼-buttons)
- [4. LED (PC13/PC14) — 회로도상 LED 부품 없음](#4-led-pc13pc14--회로도상-led-부품-없음)
- [5. 부저 (Buzzer)](#5-부저-buzzer)
- [6. USB 서브시스템 (USB-C device / USB-A host / FSUSB30 mux)](#6-usb-서브시스템)
- [7. J601 확장 헤더 핀맵 (전체)](#7-j601-확장-헤더-핀맵-전체)
- [8. EXTI / 페리페럴 배정 요약 (회로도 6_Extra 박스)](#8-exti--페리페럴-배정-요약)
- [출처](#출처)

# 0. 정정 / 주의 사항

KNOWN FACTS 와 회로도가 어긋난 부분을 회로도 기준으로 정정한다.

| 항목 | known facts | 회로도 실제 | 근거 |
|---|---|---|---|
| 부저 핀/타이머 | "BUZZ_PWM (timer)" 만 명시 | **PA9 = BUZZ_PWM = TIM1_CH2** | 회로도 p.4, 3_MCU (PA9/pin42) |
| USB_SEL 핀 | "GPIO" (핀 미지정) | **PA10 = USB_SEL (GPIO)** | 회로도 p.4, 3_MCU (PA10/pin43) |
| USB OTG FS D+/D- | PA12=D+, PA11=D- | **PA11 = MCU_D- (USB_D-), PA12 = MCU_D+ (USB_D+)** (일치) | 회로도 p.4, 3_MCU (pin44/45) |
| 디버그 UART | "DBG_M-TX=PA9, DBG_M-RX=PA10 (USART1)" | **PB6 = DBG_M-TX = USART1_TX, PB7 = DBG_M-RX = USART1_RX** (PA9/PA10 아님) | 회로도 p.4, 3_MCU (PB6/pin58, PB7/pin59); J301 net 명 DBG_M-TX/RX |
| /LCD_RESET 핀 | "있음" (핀 미지정) | **PB4 = /LCD_RESET** | 회로도 p.4, 3_MCU (PB4/pin56) |
| /LCD_CS 핀 | "있음" (핀 미지정) | **PB10 = /LCD_CS (GPIO)** | 회로도 p.4, 3_MCU (PB10/pin29) |
| 버튼 EXTI 라인 | BTN_RIGHT=EXTI1 등 (개별) | **PC0=EXTI0, PB1=EXTI1, PB2=EXTI2, PC3=EXTI3** (요약 박스 기준) | 회로도 p.7, 6_Extra (EXTI 요약 박스) |
| PB14 alt-func | SPI2_MISO | 라벨이 "SPI2_MOSI" 로 오타 표기됨. net=RF_MISO, NRF MISO(pin5) 연결이므로 기능은 **SPI2_MISO** | 회로도 p.4 라벨 vs p.5 NRF 핀 |

> 주의: PA9 가 BUZZ_PWM 으로 쓰이므로, USART1 의 기본 핀(PA9/PA10)을 디버그로 쓸 수 없다. 그래서 디버그는 USART1 의 대체 핀 PB6/PB7 로 라우팅되어 있다 (회로도 p.4, 3_MCU). USART2(PA2 TX / PA3 RX, AF7)는 별도로 J601 로 노출됨.

---

# 1. RF 모듈 — NRF24L01+ (SPI2)

NRF24L01+ (U401, QFN-20) 가 SPI2 버스 + GPIO(CS/CE) + EXTI(IRQ)로 연결된다 (회로도 p.5, 4_RF).

| 신호 | NRF 핀 | MCU 핀 | MCU 기능 | net 명 |
|---|---|---|---|---|
| SCK | 3 SCK | **PB13** | SPI2_SCK | RF_SCLK |
| MISO | 5 MISO | **PB14** | SPI2_MISO (라벨 오타 "SPI2_MOSI") | RF_MISO |
| MOSI | 4 MOSI | **PB15** | SPI2_MOSI | RF_MOSI |
| CSN (~{CS}) | 2 ~{CS} | **PC6** | GPIO | /RF_CS |
| CE | 1 CE | **PC7** | GPIO | RF_CE |
| IRQ | 6 IRQ | **PB12** | GPIO, **EXTI12** (EXTI10_15 그룹) | RF_INT |

(NRF 핀번호·net 명: 회로도 p.5, 4_RF. MCU 핀: 회로도 p.4, 3_MCU. EXTI12 배정: 회로도 p.7, 6_Extra 요약 박스 "EXTI10_15: RF_INT(PB12)".)

펌웨어 구동: **SPI2 master + GPIO 로 /RF_CS(PC6)·RF_CE(PC7) 제어 + RF_INT(PB12) 에 EXTI(line12, EXTI10_15 IRQn) falling-edge.**

---

# 2. LCD (SPI1, transmit-only)

LCD 모듈 (J501, BR_LCD_128x64_2x6P 커넥터)이 SPI1 송신 전용 + GPIO(CS/RESET/D-C) + 백라이트 PWM 으로 연결된다 (회로도 p.6, 5_LCD_BUZZER).

| 신호 | MCU 핀 | MCU 기능 | net 명 | 비고 |
|---|---|---|---|---|
| SCLK | **PB3** | SPI1_SCK | LCD_SCLK | (PB3 = SWO 겸용) |
| MOSI | **PB5** | SPI1_MOSI | LCD_MOSI | |
| MISO | (없음) | — | — | transmit-only (회로도 p.7 요약: "SPI1: LCD (Transmit only)") |
| CS | **PB10** | GPIO | /LCD_CS | active-low (~{LCD_CS}) |
| RESET | **PB4** | GPIO (alt SPI1_MISO) | /LCD_RESET | active-low (~{LCD_RST}) |
| D/C (data/cmd) | **PD2** | GPIO | LCD_DAT/~{CMD} | LOW=command, HIGH=data |
| Backlight | **PA15** | **TIM2_CH1** | LCD_BK_PWM / LCD_BK_CTRL | PWM 백라이트 |

(MCU 핀·기능: 회로도 p.4, 3_MCU — PB3=LCD_SCLK/SPI1_SCK, PB4=/LCD_RESET, PB5=LCD_MOSI/SPI1_MOSI, PB10=/LCD_CS, PD2=LCD_DAT/~{CMD}, PA15=LCD_BK_PWM/TIM2_CH1. 커넥터 J501 핀: 회로도 p.6, 5_LCD_BUZZER. 백라이트 타이머: 회로도 p.7, 6_Extra "TIM2: LCD_BK_CTRL(PA15/TIM2_CH1)".)

펌웨어 구동: **SPI1 master TX-only + GPIO 로 /LCD_CS(PB10)·/LCD_RESET(PB4)·D/C(PD2) 제어 + TIM2_CH1(PA15) PWM 으로 백라이트 밝기 조절.**

> 참고: 4개 방향 버튼(BTN_LCD-UP/DOWN/LEFT/RIGHT)이 같은 J501 커넥터(pin 3~8)에 있고, 메인 보드 버튼과 동일한 MCU 핀(PC3/PB2/PC0/PB1)으로 묶여 있다 (회로도 p.1 cover 매핑, p.6 J501). 즉 "버튼"과 "LCD 버튼"은 물리적으로 LCD 모듈 위의 같은 입력이다.

---

# 3. 버튼 (Buttons)

4개 방향 버튼. 모두 EXTI 가능한 라인에 배정되어 있다 (STM32 는 전 GPIO 가 EXTI 가능하나, 라인 번호가 충돌하지 않게 배정됨).

| 버튼 | MCU 핀 | EXTI 라인 | ADC 겸용 | net 명 |
|---|---|---|---|---|
| LEFT | **PC0** | **EXTI0** | ADC1_10 | PC0/BTN_LEFT (LB_LEFT) |
| RIGHT | **PB1** | **EXTI1** | ADC1_9 | PB1/BTN_RIGHT (LB_RIGHT) |
| DOWN | **PB2** | **EXTI2** | — | PB2/BTN_DOWN (LB_DOWN) |
| UP | **PC3** | **EXTI3** | ADC1_13 | PC3/BTN_UP (LB_UP) |

(핀·net: 회로도 p.4, 3_MCU 및 p.7, 6_Extra. EXTI 라인 배정: 회로도 p.7, 6_Extra 요약 박스 "EXTI0: BTN_LEFT(PC0) / EXTI1: BTN_RIGHT(PB1) / EXTI2: BTN_DOWN(PB2) / EXTI3: BTN_UP(PC3)".)

네 버튼 모두 **개별 EXTI 라인(0,1,2,3)** 을 쓰므로 라인 충돌 없이 각각 독립 EXTI ISR 로 처리 가능하다. 풀업/풀다운·active level 은 LCD 모듈(J501) 측 회로에 의존 — 본 회로도에는 버튼 스위치 회로가 그려져 있지 않다 (미확인: pull 방향·active level).

펌웨어 구동: **4개 핀 각각 EXTI(line 0/1/2/3) + 각자 IRQ handler**, 또는 폴링.

---

# 4. LED (PC13/PC14) — 회로도상 LED 부품 없음

**회로도 사실(고정):** 7장 회로도 어디에도 LED 부품(D 심볼·직렬저항·RED/GREEN 표기)이 없다. PC13/PC14 는 alt-function·LED 심볼 없이 그냥 GPIO 로 라우팅되어 J601 헤더로 노출된다 — PC13=J601 pin4, PC14=J601 pin3 (회로도 p.4 3_MCU, p.7 6_Extra).

**LED 의 색·핀 매핑·극성은 고정 사실이 아니다(기록 안 함):** "RED=PC13 / GREEN=PC14" 는 펌웨어/외부배선에서 정하는 것이고 언제든 바뀔 수 있다. active-high/active-low 도 외부 LED 배선(공통 애노드/캐소드)에 달려 회로도로는 확정 불가다. 그때그때 실물·펌웨어로 확인할 것.

---

# 5. 부저 (Buzzer)

부저 BZ501 (Buzzer/5.5R/9055) 가 NPN 트랜지스터 로우사이드 스위치로 구동된다 (회로도 p.6, 5_LCD_BUZZER).

| 신호 | MCU 핀 | MCU 기능 | 경로 |
|---|---|---|---|
| BUZZ_PWM | **PA9** | **TIM1_CH2** | PA9 → R502(1K) → Q501(SS8050 NPN, SOT23-3) base → 부저 로우사이드 |

(부저 핀/타이머: 회로도 p.4, 3_MCU "PA9 = BUZZ_PWM = TIM1_CH2". 드라이브 회로: 회로도 p.6, 5_LCD_BUZZER — BUZZ_PWM → R502 1K → Q501 SS8050.)

- 부저(+)는 VBUS/전원에, (-)가 Q501 컬렉터로 들어가는 로우사이드 구동. **PA9 HIGH → Q501 ON → 부저 ON** (즉 회로 레벨에서 active-high 게이팅).

펌웨어 구동: **TIM1_CH2(PA9) PWM 으로 부저 톤 주파수 출력** (NPN 트랜지스터가 전류 버퍼).

---

# 6. USB 서브시스템

USB-C(device/sink) ↔ MCU native USB OTG FS ↔ FSUSB30 mux ↔ USB-A(host). MCU 의 단일 USB OTG FS PHY 가 mux 를 통해 device 포트 또는 host 포트 중 하나로 스위칭된다.

## 6.1 native USB OTG FS (MCU)

| 신호 | MCU 핀 | net | 비고 |
|---|---|---|---|
| USB D- | **PA11** | MCU_D- (USB_D-) | 회로도 p.4, 3_MCU (pin44) |
| USB D+ | **PA12** | MCU_D+ (USB_D+) | 회로도 p.4, 3_MCU (pin45) |
| USB_SEL (mux select) | **PA10** | USB_SEL (GPIO) | 회로도 p.4, 3_MCU (pin43) |

## 6.2 FSUSB30 mux (U101, MSOP-10)

| FSUSB30 핀 | net | 연결 |
|---|---|---|
| 10 VCC | VCC33 | 3.3V |
| 4 D+ (common) | MCU_D+ | ← MCU PA12 |
| 6 D- (common) | MCU_D- | ← MCU PA11 |
| 1 SEL | USB_SEL | ← MCU PA10 (R3 10K pull) |
| 9 ~{OE} | — | output enable (active-low) |
| 2 HSD1+ / 8 HSD1- | DEVICE_D+ / DEVICE_D- | **CH1 = DEVICE = USB-C J101** |
| 3 HSD2+ / 7 HSD2- | HOST_D+ / HOST_D- | **CH2 = HOST = USB-A J102** |
| 5 GND | GND | |

(회로도 p.2, 1_Ext_Connector. mux 진리표 회로도 주기: **"SEL=0 → CH1 (DEVICE)", "SEL=1 → CH2 (HOST)"**.)

## 6.3 USB-C device 경로 (J101)

- J101 = USB-C_16P(1PAD). D+/D-(Dp1 A6 / Dn1 A7 등) → R603/R604 27R → DEVICE_D+/DEVICE_D- → FSUSB30 CH1 (회로도 p.2).
- **CC1(A5)/CC2(B5) 각각 R601/R602 = 5.1K pulldown** → device/sink 역할 확정 (회로도 p.2).
- VBUS(5V) 가 보드 메인 전원원 → U201 ME6217C33 LDO → VCC33 (회로도 p.3, 2_Power: U201 VIN(1)=VBUS, VOUT(5)=VCC33, CE(3) via R201 10K).

## 6.4 USB-A host 경로 (J102)

- J102 = USB-A_Female(1PAD). VBUS(pin1), D-(pin2)=HOST_D-, D+(pin3)=HOST_D+ → FSUSB30 CH2 (회로도 p.2).

펌웨어 구동: **USB_OTG_FS(PA11/PA12) 1개 PHY + PA10(USB_SEL GPIO)로 mux 방향 선택** — LOW(=0)면 USB-C device 로, HIGH(=1)면 USB-A host 로 D+/D- 를 라우팅 (회로도 p.2 진리표).

---

# 7. J601 확장 헤더 핀맵 (전체)

J601 = CON_AllTester26/34 (회로도 p.7, 6_Extra). 홀수 핀은 KNOWN FACTS 와 일치, **짝수 핀을 회로도로 확정**:

| 핀 | net | 핀 | net |
|---|---|---|---|
| 1 | PC15 | 2 | VCC33 |
| 3 | PC14 | 4 | PC13 |
| 5 | VBUS | 6 | VCC33 |
| 7 | PA0 (ADC1_0) | 8 | PB8 (I2C1_SCL) |
| 9 | PA1 (ADC1_1) | 10 | PB9 (I2C1_SDA) |
| 11 | PA2 (ADC1_2 / U2TXD) | 12 | PC0 (ADC1_10) |
| 13 | PA3 (ADC1_3 / U2RXD) | 14 | PC1 (ADC1_11) |
| 15 | PA4 | 16 | PC2 (ADC1_12) |
| 17 | PA5 | 18 | PC3 (ADC1_13) |
| 19 | PA6 (TIM3_CH1) | 20 | PC4 (ADC1_14) |
| 21 | PA7 (TIM3_CH2) | 22 | PC5 (ADC1_15) |
| 23 | PA8 (I2C3_SCL) | 24 | PC9 (I2C3_SDA) |
| 25 | PB0 (ADC1_8) | 26 | PC10 (SPI3_SCK) |
| 27 | PB1 (BTN_RIGHT / ADC1_9) | 28 | PC11 (SPI3_MISO) |
| 29 | GND | 30 | PC12 (SPI3_MOSI) |
| 31 | PB2 (BTN_DOWN) | 32 | PC8 (TIM3_CH3) |
| 33 | GND | 34 | GND |

(회로도 p.7, 6_Extra. 짝수 핀 2~34 회로도로 확인 완료.)

---

# 8. EXTI / 페리페럴 배정 요약

회로도 p.7 (6_Extra) 우하단 요약 박스 원문 (저자 의도 그대로):

```
EXTI0 :     BTN_LEFT(PC0)   ADC1_10      USART1 : Debug
EXTI1 :     BTN_RIGHT(PB1)  ADC1_9
EXTI2 :     BTN_DOWN(PB2)                SPI1 :   LCD (Transmit only)
EXTI3 :     BTN_UP(PC3)     ADC1_13      SPI2 :   RF (NRF24L01P)
EXTI10_15 : RF_INT(PB12)
TIM2 :      LCD_BK_CTRL(PA15/TIM2_CH1)
```

(회로도 p.7, 6_Extra 요약 박스.)

해석:
- **SPI1 = LCD (송신 전용)**, **SPI2 = RF**, **USART1 = Debug**(단, 핀은 PB6/PB7 — §0 정정 참고), **TIM2_CH1 = LCD 백라이트**, **TIM1_CH2 = 부저(PA9)**.
- 버튼 4개는 EXTI0~3, RF IRQ 는 EXTI12(EXTI10_15 그룹).

---

# 출처:
- Byrobot All-Tester (NRF24L01P / USB-C) 회로도: `C:/Users/ALUX/Firmware/MY_TESTER/MY_TESTER/References/Byrobot_All_Tester_NRF24L01P_USB-C_Schematic.pdf` (KiCad E.D.A. 9.0.6, 7페이지 — 시트: 1/7 cover, 2/7 1_Ext_Connector, 3/7 2_Power, 4/7 3_MCU, 5/7 4_RF, 6/7 5_LCD_BUZZER, 7/7 6_Extra). (pdftotext + 페이지 PNG 렌더 확인 2026-06-24)
- 펌웨어: `C:/Users/ALUX/Firmware/MY_TESTER/MY_TESTER/Core/Src/main.c` (LED 주석 main.c:101, GPIO 초기화 main.c:103-104; USART2 = PA2/PA3, MX_GPIO_Init). (확인 2026-06-24)
- MCU: STM32F401RCT6, LQFP64.
