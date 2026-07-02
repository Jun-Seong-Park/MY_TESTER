> description: STM32F401RCT6 (LQFP64) 보드 핀맵 — 회로도 net / datasheet AF / 현재 펌웨어(main.c) muxing 을 한 표로 통합한 중앙 레퍼런스
> when to use: 핀 기능을 바꾸거나(타이머/SPI/I2C/UART 추가), 회로도 의도와 펌웨어 설정이 맞는지 확인하거나, 확장 헤더(J601)·디버그(J301)·USB mux 배선을 추적할 때
> caution: 이 보드에는 on-board LED 회로가 없습니다(회로도 전 7페이지에 LED 부품 0개). PC13/PC14 "RED/GREEN" 은 펌웨어 주석일 뿐이며 LED 는 J601 확장 헤더로 외부에 다는 구조라 active-high/low 극성은 회로도로 확인 불가입니다. 또한 SPI1/2/3·I2C1/3·USART1·TIM1/2·USB 는 핀 mux 만 되어 있고 main.c 에서 peripheral init 이 안 된 것이 많습니다(아래 표 비고 참조).

# 목차
- [1. 요약 (핵심 결론)](#1-요약-핵심-결론)
- [2. 전원 / 클럭 / 시스템 핀](#2-전원--클럭--시스템-핀)
- [3. Port A 핀맵](#3-port-a-핀맵)
- [4. Port B 핀맵](#4-port-b-핀맵)
- [5. Port C 핀맵](#5-port-c-핀맵)
- [6. Port H 핀맵](#6-port-h-핀맵)
- [7. 커넥터 핀아웃](#7-커넥터-핀아웃)
  - [7.1 J301 SWD/디버그 8핀](#71-j301-swd디버그-8핀)
  - [7.2 J601 확장 헤더 (26/34핀)](#72-j601-확장-헤더-2634핀)
  - [7.3 USB 경로 (J101/J102/U101 mux)](#73-usb-경로-j101j102u101-mux)
- [8. 펌웨어 vs 회로도 불일치 / 주의점](#8-펌웨어-vs-회로도-불일치--주의점)
- [출처](#출처)

---

# 1. 요약 (핵심 결론)

- MCU = STM32F401RCT6, LQFP-64 (회로도 p.4, 3_MCU; 부품 라벨 "STM32F401RCT6/LQFP-64").
- 전원: USB-C J101 VBUS 5V → LDO U201 ME6217C33(SOT23-5) → VCC33 3.3V (회로도 p.3, 2_Power). AVCC33 은 VCC33 에서 ferrite bead FB201 로 분리 (회로도 p.3).
- main.c 가 **실제로 init 하는 peripheral 은 ADC1, USART2, GPIO 뿐** 입니다 (main.c:97-99). SPI1/SPI2/SPI3·I2C1/I2C3·USART1·TIM1/TIM2·USB OTG 는 `MX_GPIO_Init()` 에서 핀 mux(AF) 만 설정되고 peripheral 초기화 코드가 없습니다.
- **KNOWN FACTS 정정**: "회로도가 J301 TXD/RXD 를 PA9/PA10(USART1)에 연결" 은 **사실이 아닙니다.** 회로도(p.4)에서 디버그 UART net(DBG_M-TX/DBG_M-RX → J301 7/8번)은 **PB6/PB7(USART1)** 에 직접 배선돼 있고, PA9 = BUZZ_PWM(TIM1_CH2), PA10 = USB_SEL(GPIO) 입니다. 펌웨어도 USART1 을 PB6/PB7(AF7)에 두므로 디버그 UART 는 **회로도와 펌웨어가 일치**합니다 (회로도 p.4 / main.c:385-391). 자세한 건 §8.

---

# 2. 전원 / 클럭 / 시스템 핀

| Pin | Port/Pin | 보드 net (schematic) | 사용 가능 AF/기능 (datasheet) | 현재 펌웨어 설정 (main.c) | 비고 |
|---|---|---|---|---|---|
| 1  | VBAT | VCC33 | Backup supply | (HW) | VCC33 에 직결 (회로도 p.4) |
| 5  | PH0 / OSC_IN | (Y301 16MHz 결정자) | OSC_IN | 미사용(HSI) | Y301 16MHz/3225 크리스탈 연결 (회로도 p.4). 단, 펌웨어는 **HSI** 사용 (PLL_NONE, main.c:144-147) — 외부 OSC 미사용 |
| 6  | PH1 / OSC_OUT | (Y301 16MHz 결정자) | OSC_OUT | 미사용(HSI) | 동상 (회로도 p.4) |
| 12 | VSSA / VREF- | GND | Analog GND | (HW) | (회로도 p.4) |
| 13 | VDDA / VREF+ | VCC33(AVCC33 계열) | Analog supply | (HW) | (회로도 p.4) |
| 19/32/48/64 | VDD | VCC33 | Digital supply | (HW) | 디커플 BC301~BC306 100n (회로도 p.4) |
| 18/31/47/63 | VSS | GND | GND | (HW) | (회로도 p.4) |
| 30 | VCAP1 | (C304 2.2u) | Reg cap | (HW) | LDO 내부 레귤레이터 캡 C304 2.2u/16V (회로도 p.4) |
| 7  | NRST | /MCU_RESET | NRST (weak pull-up 내장) | (HW) | R301 10K pull-up + C301 100n, J301 2번으로 (회로도 p.4) |
| 60 | PB2 / BOOT0 핀(주의) | — | BOOT0 / PB2 | — | **주의**: 회로도 p.4 에서 pin60 라벨이 BOOT0 로 보이나 PB2 도 BOOT1 기능과 겹쳐 표기됨. PB2 자체는 §4 참조 (미확인: pin60 의 net 단독 확인 필요) |

> 클럭 참고: main.c:144-165 는 HSI(16MHz) 직접, PLL 없음, AHB/APB1/APB2 = SYSCLK(=16MHz), FLASH_LATENCY_0, 전압 스케일2. 즉 SYSCLK = 16MHz (main.c:139, 157-162).

---

# 3. Port A 핀맵

datasheet AF 출처 = Table 9 "Alternate function mapping" (stm32f401rc.pdf p.44, Port A). 회로도 net 출처 = p.4(3_MCU).

| Pin | Port/Pin | 보드 net (schematic) | 사용 가능 AF/기능 (datasheet Table 9 p.44) | 현재 펌웨어 설정 (main.c) | 비고 |
|---|---|---|---|---|---|
| 14 | PA0 | PA0 (J601 7번, ADC1_0) | AF1 TIM2_CH1/TIM2_ETR, AF2 TIM5_CH1, AF7 USART2_CTS | **미설정**(reset 후 floating input) | 확장 헤더로 노출. ADC1_IN0 (회로도 p.4, p.7) |
| 15 | PA1 | PA1 (J601 9번, ADC1_1) | AF1 TIM2_CH2, AF2 TIM5_CH2, AF7 USART2_RTS | 미설정 | ADC1_IN1 (회로도 p.4, p.7) |
| 16 | PA2 | PA2 (J601 11번, ADC1_2 / U2TXD) | AF1 TIM2_CH3, AF2 TIM5_CH3, AF3 TIM9_CH1, **AF7 USART2_TX** | 미설정 (USART2 는 init되나 GPIO mux 코드 없음) | **주의**: USART2 는 main.c:225-251 에서 init 되지만 `MX_GPIO_Init()` 에 PA2/PA3 AF 설정 줄이 없음. HAL_UART_MspInit (stm32f4xx_hal_msp.c) 에서 mux 하는 구조일 가능성. ADC1_IN2 와 겸용 (회로도 p.4, p.7) |
| 17 | PA3 | PA3 (J601 13번, ADC1_3 / U2RXD) | AF1 TIM2_CH4, AF2 TIM5_CH4, AF3 TIM9_CH2, **AF7 USART2_RX** | 미설정 (위와 동일) | USART2_RX = PC↔보드 통신 RX. ADC1_IN3 (회로도 p.4, p.7) |
| 20 | PA4 | PA4 (J601 15번, ADC1_4) | AF5 SPI1_NSS/SPI3_NSS/I2S3_WS, AF6 SPI2_NSS, AF7 USART2_CK | 미설정 | ADC1_IN4 (회로도 p.4, p.7) |
| 21 | PA5 | PA5 (J601 17번, ADC1_5) | AF1 TIM2_CH1/ETR, AF5 SPI1_SCK | 미설정 | ADC1_IN5 (회로도 p.4, p.7) |
| 22 | PA6 | PA6 (J601 19번, ADC1_6) | AF1 TIM1_BKIN, AF2 TIM3_CH1, AF5 SPI1_MISO, AF3 TIM13_CH1 | 미설정 | ADC1_IN6 (회로도 p.4, p.7) |
| 23 | PA7 | PA7 (J601 21번, ADC1_7) | AF1 TIM1_CH1N, AF2 TIM3_CH2, AF5 SPI1_MOSI | 미설정 | ADC1_IN7 (회로도 p.4, p.7) |
| 41 | PA8 | PA8 (J601 23번, I2C3_SCL) | AF0 MCO_1, AF1 TIM1_CH1, **AF4 I2C3_SCL**, AF7 USART1_CK | **AF4_I2C3** (`GPIO_MODE_AF_OD`, main.c:323-329) | I2C3_SCL. open-drain. 단 **I2C3 peripheral init 없음**(§8). 확장 헤더로 노출 (회로도 p.4, p.7) |
| 42 | PA9 | **BUZZ_PWM** | AF1 **TIM1_CH2**, AF4 I2C3_SMBA, AF7 USART1_TX, AF10 OTG_FS_VBUS | **AF1_TIM1** (`GPIO_MODE_AF_PP`, main.c:331-337) | 부저 PWM 출력. **TIM1 init 없음**(§8) → mux 만 됨. KNOWN FACTS 의 "PA9=USART1_TX" 는 회로도상 아님 (회로도 p.4) |
| 43 | PA10 | **USB_SEL** | AF1 TIM1_CH3, AF7 USART1_RX, AF10 OTG_FS_ID | **GPIO Output** (`GPIO_MODE_OUTPUT_PP`, main.c:339-344; 초기값 RESET=0, main.c:280) | USB mux U101 SEL 핀 구동. 0=DEVICE(J101), 1=HOST(J102) (회로도 p.2). 회로도 net 은 GPIO 의도이고 펌웨어도 GPIO → 일치 |
| 44 | PA11 | MCU_D- | AF10 OTG_FS_DM, AF1 TIM1_CH4 | **AF10_OTG_FS** (`GPIO_MODE_AF_PP`, main.c:346-352) | USB OTG FS D-. U101 mux 의 공통 D- 로 (회로도 p.2, p.4). **USB stack init 없음**(§8) |
| 45 | PA12 | MCU_D+ | AF10 OTG_FS_DP, AF1 TIM1_ETR | **AF10_OTG_FS** (main.c:346-352) | USB OTG FS D+ (회로도 p.2, p.4). USB stack init 없음 |
| 46 | PA13 | SWDIO | AF0 JTMS-SWDIO | (HW 디버그) | SWD 데이터, J301 4번 (회로도 p.4) |
| 49 | PA14 | SWCLK | AF0 JTCK-SWCLK | (HW 디버그) | SWD 클럭, J301 3번 (회로도 p.4) |
| 50 | PA15 | **LCD_BK_PWM** | AF0 JTDI, AF1 **TIM2_CH1**/TIM2_ETR, AF5 SPI1_NSS, AF6 SPI3_NSS/I2S3_WS | **AF1_TIM2** (`GPIO_MODE_AF_PP`, main.c:354-360) | LCD 백라이트 PWM (TIM2_CH1). **TIM2 init 없음**(§8) → mux 만 됨 (회로도 p.4) |

---

# 4. Port B 핀맵

datasheet AF 출처 = Table 9 (stm32f401rc.pdf p.45, Port B). 회로도 net 출처 = p.4.

| Pin | Port/Pin | 보드 net (schematic) | 사용 가능 AF/기능 (datasheet Table 9 p.45) | 현재 펌웨어 설정 (main.c) | 비고 |
|---|---|---|---|---|---|
| 26 | PB0 | PB0 (J601 25번, ADC1_8) | AF1 TIM1_CH2N, AF2 TIM3_CH3, AF5 SPI… | 미설정 | ADC1_IN8, 확장 헤더 노출 (회로도 p.4, p.7) |
| 27 | PB1 | **PB1/BTN_RIGHT** (J601 27번, ADC1_9) | AF1 TIM1_CH3N, AF2 TIM3_CH4 | 미설정 | BTN_RIGHT, EXTI1(BTN_RIGHT). ADC1_IN9 (회로도 p.4, p.7 legend "EXTI1") |
| 28 | PB2 | **PB2/BTN_DOWN** (J601 31번) | (BOOT1 겸용; AF 거의 없음) | 미설정 | BTN_DOWN, EXTI2. BOOT1/PB2 표기 (회로도 p.4, p.7 legend "EXTI2") |
| 55 | PB3 | **LCD_SCLK** | AF1 TIM2_CH2, **AF5 SPI1_SCK**, AF6 SPI3_SCK/I2S3_CK | **AF5_SPI1** (`GPIO_MODE_AF_PP` VERY_HIGH, main.c:377-383) | LCD SPI1 클럭. SPI1=LCD(전송 전용) (회로도 p.4, p.7 legend). **SPI1 peripheral init 없음**(§8) |
| 56 | PB4 | **/LCD_RESET** | AF2 TIM3_CH1, AF5 SPI1_MISO, AF6 SPI3_MISO | **GPIO Output** (`GPIO_MODE_OUTPUT_PP`, main.c:294-299; 초기 RESET=0, main.c:277) | LCD 리셋(active-low). GPIO 로 직접 구동 (회로도 p.4) |
| 57 | PB5 | **LCD_MOSI** | AF2 TIM3_CH2, **AF5 SPI1_MOSI**, AF6 SPI3_MOSI/I2S3_SD | **AF5_SPI1** (main.c:377-383) | LCD SPI1 데이터(MOSI). SPI1 init 없음(§8) (회로도 p.4) |
| 58 | PB6 | **DBG_M-TX** | AF2 TIM4_CH1, **AF7 USART1_TX**, AF4 I2C1_SCL | **AF7_USART1** (main.c:385-391) | **디버그 UART TX** → J301 7번(TXD). USART1=Debug (회로도 p.4, p.7 legend). **USART1 peripheral init 없음**(§8) — 펌웨어가 실제 쓰는 콘솔은 USART2(PA2/PA3) |
| 59 | PB7 | **DBG_M-RX** | AF2 TIM4_CH2, **AF7 USART1_RX**, AF4 I2C1_SDA | **AF7_USART1** (main.c:385-391) | 디버그 UART RX → J301 8번(RXD) (회로도 p.4) |
| 61 | PB8 | PB8 (J601 8번, I2C1_SCL) | AF2 TIM4_CH1, AF3 TIM10_CH1, **AF4 I2C1_SCL** | **AF4_I2C1** (`GPIO_MODE_AF_OD`, main.c:393-399) | I2C1_SCL, 확장 헤더 노출. **I2C1 init 없음**(§8) (회로도 p.4, p.7) |
| 62 | PB9 | PB9 (J601 10번, I2C1_SDA) | AF2 TIM4_CH2, AF3 TIM11_CH1, **AF4 I2C1_SDA** | **AF4_I2C1** (main.c:393-399) | I2C1_SDA (회로도 p.4, p.7) |
| 29 | PB10 | **/LCD_CS** | AF1 TIM2_CH3, AF4 I2C2_SCL, AF5 SPI2_SCK | **GPIO Output** (`GPIO_MODE_OUTPUT_PP`, main.c:294-299; 초기 RESET=0, main.c:277) | LCD chip-select(active-low), GPIO 로 직접 구동 (회로도 p.4) |
| 33 | PB12 | **RF_INT** | AF5 SPI2_NSS/I2S2_WS, AF6 TIM1_BKIN | **EXTI Rising** (`GPIO_MODE_IT_RISING`, main.c:301-305) | NRF24L01+ IRQ 입력. EXTI10_15(RF_INT). 회로도 function 표기 "EXTI12" (회로도 p.4, p.7 legend) |
| 34 | PB13 | **RF_SCLK** | **AF5 SPI2_SCK**/I2S2_CK | **AF5_SPI2** (`GPIO_MODE_AF_PP` VERY_HIGH, main.c:307-313) | RF SPI2 클럭. **회로도 function 주석은 "SPI2_SCLK"** (회로도 p.4). SPI2=RF (p.7 legend). **SPI2 init 없음**(§8) |
| 35 | PB14 | **RF_MISO** | **AF5 SPI2_MISO**/I2S2ext_SD | **AF5_SPI2** (main.c:307-313) | RF SPI2 MISO. **주의**: 회로도 function 주석이 "SPI2_MOSI" 로 잘못 적혀 있음(net 이름은 RF_MISO 가 맞고 NRF MISO 핀에 연결) — 회로도 주석 오기 (회로도 p.4, p.5) |
| 36 | PB15 | **RF_MOSI** | **AF5 SPI2_MOSI**/I2S2_SD | **AF5_SPI2** (main.c:307-313) | RF SPI2 MOSI (회로도 p.4, p.5) |

---

# 5. Port C 핀맵

datasheet AF 출처 = Table 9 (stm32f401rc.pdf p.46, Port C). 회로도 net 출처 = p.4.

| Pin | Port/Pin | 보드 net (schematic) | 사용 가능 AF/기능 (datasheet Table 9 p.46) | 현재 펌웨어 설정 (main.c) | 비고 |
|---|---|---|---|---|---|
| 8  | PC0 | **PC0/BTN_LEFT** (J601 12번, ADC1_10) | (AF 거의 없음; ADC1_IN10) | **GPIO Output** (`GPIO_MODE_OUTPUT_PP`, main.c:285-292) | **불일치 후보**: 회로도/legend 상 BTN_LEFT(버튼=입력, EXTI0)인데 펌웨어는 **출력**으로 설정 (§8) (회로도 p.4, p.7 legend "EXTI0: BTN_LEFT(PC0)") |
| 9  | PC1 | PC1 (J601 14번, ADC1_11) | ADC1_IN11 | **GPIO Output** (main.c:285-292) | 확장 헤더 노출 (회로도 p.4, p.7) |
| 10 | PC2 | PC2 (J601 16번, ADC1_12) | AF5 SPI2_MISO, ADC1_IN12 | **GPIO Output** (main.c:285-292) | (회로도 p.4, p.7) |
| 11 | PC3 | **PC3/BTN_UP** (J601 18번, ADC1_13) | AF5 SPI2_MOSI/I2S2_SD, ADC1_IN13 | **GPIO Output** (main.c:285-292) | **불일치 후보**: BTN_UP(버튼=입력, EXTI3)인데 펌웨어는 출력 (§8) (회로도 p.4, p.7 legend "EXTI3: BTN_UP(PC3)") |
| 24 | PC4 | PC4 (J601 20번, ADC1_14) | ADC1_IN14 | 미설정 | 확장 헤더 노출 (회로도 p.4, p.7) |
| 25 | PC5 | PC5 (J601 22번, ADC1_15) | ADC1_IN15 | 미설정 | (회로도 p.4, p.7) |
| 37 | PC6 | **/RF_CS** | AF2 TIM3_CH1, AF8 USART6_TX, AF6 SDIO, AF5 I2S2_MCK | **GPIO Output** (`GPIO_MODE_OUTPUT_PP`, main.c:285-292; 초기 RESET=0, main.c:273-274) | NRF24L01+ chip-select(active-low). GPIO 로 직접 구동 (회로도 p.4, function 표기 "GPIO") |
| 38 | PC7 | **RF_CE** | AF2 TIM3_CH2, AF8 USART6_RX, AF6 SDIO | **GPIO Output** (main.c:285-292; 초기 RESET=0) | NRF24L01+ chip-enable. GPIO (회로도 p.4) |
| 39 | PC8 | PC8 (J601 32번, GPIO) | AF2 TIM3_CH3, AF8 USART6_CK, AF6 SDIO | 미설정 | 확장 헤더 노출, function 표기 "GPIO" (회로도 p.4, p.7) |
| 40 | PC9 | PC9 (J601 24번, I2C3_SDA) | AF2 TIM3_CH4, **AF4 I2C3_SDA**, AF6 SDIO | **AF4_I2C3** (`GPIO_MODE_AF_OD`, main.c:315-321) | I2C3_SDA (PA8=SCL 과 페어). **I2C3 init 없음**(§8) (회로도 p.4, p.7) |
| 51 | PC10 | PC10 (J601 26번, SPI3_SCK) | **AF6 SPI3_SCK**/I2S3_CK, AF8 USART6_TX | **AF6_SPI3** (`GPIO_MODE_AF_PP` VERY_HIGH, main.c:362-368) | SPI3_SCK, 확장 헤더 노출. **SPI3 init 없음**(§8) (회로도 p.4, p.7) |
| 52 | PC11 | PC11 (J601 28번, SPI3_MISO) | **AF6 SPI3_MISO**, AF8 USART6_RX | **AF6_SPI3** (main.c:362-368) | SPI3_MISO (회로도 p.4, p.7) |
| 53 | PC12 | PC12 (J601 30번, SPI3_MOSI) | **AF6 SPI3_MOSI**/I2S3_SD | **AF6_SPI3** (main.c:362-368) | SPI3_MOSI (회로도 p.4, p.7) |
| 2  | PC13 | PC13 (J601 4번) | (AF 없음 — Table 9 에서 EVENT_OUT 만, p.46) | **GPIO Output** (main.c:285-292; 초기 RESET=0, main.c:103) | 펌웨어 주석상 "RED LED"(SET=on/RESET=off, main.c:101-103). **on-board LED 회로 없음** — J601 4번으로 외부 출력 (§8). 극성 미확인 (회로도 p.4, p.7) |
| 3  | PC14 | PC14 (J601 3번) | OSC32_IN 겸용 / AF 없음 | **GPIO Output** (main.c:285-292) | 펌웨어 주석상 "GREEN LED". 위와 동일하게 on-board LED 없음, J601 3번 외부 출력 (회로도 p.4, p.7) |
| 4  | PC15 | PC15 (J601 1번) | OSC32_OUT 겸용 / AF 없음 | **미설정** | 확장 헤더 J601 1번으로만 노출 (회로도 p.4, p.7) |

> 참고: ADC1 은 main.c:173-218 에서 init 되며 **rank1 채널 = ADC_CHANNEL_0 (=PA0) 하나만** 설정 (main.c:207). 나머지 ADC 핀(PA1~PA7, PB0/PB1, PC0~PC5)은 ADC mux 미설정.

---

# 6. Port H 핀맵

| Pin | Port/Pin | 보드 net (schematic) | 사용 가능 AF/기능 (datasheet) | 현재 펌웨어 설정 (main.c) | 비고 |
|---|---|---|---|---|---|
| 5 | PH0 / OSC_IN | Y301 16MHz | OSC_IN (HSE) | 미사용 (HSI) | Y301 16MHz/3225 + C302/C303 18p (회로도 p.4). 펌웨어 HSI 라 외부 OSC 미사용 (main.c:144-147) |
| 6 | PH1 / OSC_OUT | Y301 16MHz | OSC_OUT (HSE) | 미사용 (HSI) | 동상 (회로도 p.4) |

> GPIOH 클럭은 main.c:267 에서 enable 되지만 PH0/PH1 은 GPIO 로 mux 되지 않음. (LQFP64 의 Port H 는 PH0/PH1 만 존재)

---

# 7. 커넥터 핀아웃

## 7.1 J301 SWD/디버그 8핀

부품명 SWD_ARM-8P_PETRONE (회로도 p.4, 3_MCU).

| J301 핀 | 신호 | 연결처 | 비고 |
|---|---|---|---|
| 1 | VBAT | D301(1N5819 schottky) 경유 | 타겟 배터리 전압 (회로도 p.4) |
| 2 | /MCU_RESET (RESET, active-low) | MCU NRST(pin7) | R301 10K pull-up + C301 100n (회로도 p.4) |
| 3 | SWCLK | PA14 (pin49) | (회로도 p.4) |
| 4 | SWDIO | PA13 (pin46) | (회로도 p.4) |
| 5 | GND | GND | (회로도 p.4) |
| 6 | TVDD | VCC33 | 타겟 전압 sense (회로도 p.4) |
| 7 | TXD | net DBG_M-TX → **PB6 (USART1_TX)** | KNOWN FACTS 는 PA9 라 했으나 회로도상 **PB6** (회로도 p.4) |
| 8 | RXD | net DBG_M-RX → **PB7 (USART1_RX)** | 회로도상 **PB7** (회로도 p.4) |

## 7.2 J601 확장 헤더 (26/34핀)

부품명 CON_AllTester26/34 (회로도 p.7, 6_Extra). 홀수=좌열, 짝수=우열. (전 핀 회로도 p.7 직접 확인)

| 핀 | net | 핀 | net |
|---|---|---|---|
| 1  | PC15 | 2  | VCC33 |
| 3  | PC14 | 4  | PC13 |
| 5  | VBUS | 6  | VCC33 |
| 7  | PA0 (ADC1_0/TIM5_CH1) | 8  | PB8 (TIM10_CH1/TIM4_CH3/I2C1_SCL) |
| 9  | PA1 (ADC1_1/TIM5_CH2) | 10 | PB9 (TIM11_CH1/TIM4_CH4/I2C1_SDA) |
| 11 | PA2 (ADC1_2/U2TXD/TIM5_CH3/TIM9_CH1) | 12 | PC0 (LB_LEFT/ADC1_10) |
| 13 | PA3 (ADC1_3/U2RXD/TIM5_CH4/TIM9_CH2) | 14 | PC1 (ADC1_11) |
| 15 | PA4 (ADC1_4) | 16 | PC2 (ADC1_12) |
| 17 | PA5 (ADC1_5) | 18 | PC3 (LB_UP/ADC1_13) |
| 19 | PA6 (ADC1_6/TIM3_CH1) | 20 | PC4 (ADC1_14) |
| 21 | PA7 (ADC1_7/TIM3_CH2) | 22 | PC5 (ADC1_15) |
| 23 | PA8 (I2C3_SCL) | 24 | PC9 (TIM3_CH4/I2C3_SDA) |
| 25 | PB0 (ADC1_8/TIM3_CH3) | 26 | PC10 (SPI3_SCK) |
| 27 | PB1 (ADC1_9/TIM3_CH4/LB_RIGHT) | 28 | PC11 (SPI3_MISO) |
| 29 | GND | 30 | PC12 (SPI3_MOSI) |
| 31 | PB2 (LB_DOWN) | 32 | PC8 (TIM3_CH3) |
| 33 | GND | 34 | GND |

> p.7 우하단 legend (회로도 p.7): EXTI0=BTN_LEFT(PC0,ADC1_10) / EXTI1=BTN_RIGHT(PB1,ADC1_9) / EXTI2=BTN_DOWN(PB2) / EXTI3=BTN_UP(PC3,ADC1_13) / EXTI10_15=RF_INT(PB12) / TIM2=LCD_BK_CTRL(PA15/TIM2_CH1) / USART1=Debug / SPI1=LCD(Transmit only) / SPI2=RF(NRF24L01P).

## 7.3 USB 경로 (J101/J102/U101 mux)

USB mux U101 = **FSUSB30MUX (MSOP-10)** (회로도 p.2; KNOWN FACTS 의 SOT 추정과 달리 MSOP-10).

| 요소 | 내용 | 비고 |
|---|---|---|
| J101 USB-C (16P) | VBUS, CC1/CC2 각각 5.1K(R601/R602) pull-down | USB device/sink 확정 (회로도 p.2) |
| J101 데이터 | Dp1/Dn1 → R603/R604 (27Ω 직렬) → DEVICE_D+/D- | (회로도 p.2) |
| U101 공통 | D+(pin4)=MCU_D+(PA12), D-(pin6)=MCU_D-(PA11) | OTG FS (회로도 p.2, p.4) |
| U101 SEL | SEL(pin1)=USB_SEL(PA10), R3 10K | SEL=0→CH1(DEVICE,J101), SEL=1→CH2(HOST,J102) (회로도 p.2) |
| U101 CH1/CH2 | HSD1±=DEVICE(J101), HSD2±=HOST(J102 USB-A) | (회로도 p.2) |
| J102 USB-A Female | HOST 포트 | (회로도 p.2) |

---

# 8. 펌웨어 vs 회로도 불일치 / 주의점

근거: 회로도 p.4(3_MCU), p.7 legend; main.c MX_GPIO_Init().

1. **KNOWN FACTS 가정 정정 — J301 디버그 UART 는 PA9/PA10 이 아니라 PB6/PB7**: 회로도(p.4)에서 DBG_M-TX/DBG_M-RX net 은 PB6/PB7(USART1)에 직접 배선. PA9=BUZZ_PWM(TIM1_CH2), PA10=USB_SEL(GPIO). 펌웨어도 USART1 을 PB6/PB7(AF7, main.c:385-391)에 두므로 **이 부분은 회로도-펌웨어 일치** (KNOWN FACTS 의 "PA9=TIM1_CH2, PA10=GPIO, USART1=PB6/PB7" 도 결국 회로도와 동일).

2. **BTN_LEFT(PC0) / BTN_UP(PC3) 가 입력이 아니라 출력으로 설정됨 (실질적 불일치)**: 회로도 net 과 p.7 legend 는 이 둘을 버튼 입력(EXTI0/EXTI3)으로 의도(회로도 p.4, p.7). 그러나 펌웨어는 PC0~PC3 을 PC13/PC14/PC6/PC7 과 묶어 `GPIO_MODE_OUTPUT_PP` 로 설정(main.c:285-292). → 버튼으로 읽으려면 입력+EXTI 로 바꿔야 함. (BTN_RIGHT=PB1, BTN_DOWN=PB2 는 펌웨어에서 아예 미설정.)

3. **peripheral init 누락 (mux 만 됨)**: 다음은 핀 AF mux 만 설정되고 main.c 에 peripheral 초기화가 없음 —
   - SPI1(PB3/PB5, LCD), SPI2(PB13/14/15, RF), SPI3(PC10/11/12) — init 함수 없음.
   - I2C1(PB8/9), I2C3(PA8/PC9) — init 함수 없음.
   - USART1(PB6/7, 디버그) — init 함수 없음. **실제 콘솔은 USART2(PA2/PA3)** (main.c:99, 225-251).
   - TIM1(PA9 BUZZ_PWM), TIM2(PA15 LCD_BK_PWM) — init 없음 → 부저/백라이트 PWM 미동작.
   - USB OTG FS(PA11/12) — USB device stack init 없음.
   → 즉 현재 펌웨어는 사실상 **GPIO + ADC1(채널0=PA0) + USART2 echo loop**(main.c:411-418) 데모만 동작.

4. **on-board LED 없음 / 극성 미확인**: 회로도 전 7페이지에 LED 부품 0개(grep 결과). PC13("RED")/PC14("GREEN")는 펌웨어 주석(main.c:101)일 뿐이며 회로 net 은 J601 4번/3번으로 빠져 외부에 달도록 됨(회로도 p.4, p.7). active-high/low 극성은 **회로도로 확인 불가(미확인)**. main.c:101 주석은 "SET=on/RESET=off" 라고 active-high 를 가정.

5. **PB13/PB14 회로도 function 주석 오기**: p.4 에서 PB13 주석 "SPI2_SCLK", PB14 주석 "SPI2_MOSI", PB15 주석 "SPI2_MOSI" 로 PB14/PB15 가 둘 다 MOSI 로 적혀 있음. 실제 net 이름(RF_SCLK/RF_MISO/RF_MOSI)과 NRF24L01+ 핀(SCK/MISO/MOSI, 회로도 p.5)으로 보면 **PB14=MISO, PB15=MOSI** 가 맞음. datasheet Table 9(p.45)도 PB14=SPI2_MISO, PB15=SPI2_MOSI. → 회로도 주석 오기.

6. **PA2/PA3(USART2) AF mux 가 MX_GPIO_Init 에 없음**: USART2 는 init 되지만(main.c:225-251) `MX_GPIO_Init()` 안에 PA2/PA3 AF 설정 줄이 없음. CubeMX 생성 코드라면 `HAL_UART_MspInit()`(stm32f4xx_hal_msp.c)에서 mux 할 가능성이 높음 — 이 파일은 본 문서 범위 밖이라 **미확인**. (확인하려면 stm32f4xx_hal_msp.c 의 HAL_UART_MspInit 참조.)

---

# 출처:
- 회로도: `MY_TESTER/References/Byrobot_All_Tester_NRF24L01P_USB-C_Schematic.pdf` (KiCad 9.0.6, 7페이지/A3·A4; sheets: p.2 1_Ext_Connector, p.3 2_Power, p.4 3_MCU, p.5 4_RF, p.6 5_LCD_BUZZER, p.7 6_Extra/J601) — 직접 확인 2026-06-24
- Datasheet: `MY_TESTER/References/stm32f401rc.pdf` (DS9716 Rev 11, STM32F401xB/STM32F401xC) — Table 8 pin definitions(p.37~), Table 9 Alternate function mapping(p.44 Port A / p.45 Port B / p.46 Port C) — 직접 확인 2026-06-24
- 펌웨어: `MY_TESTER/Core/Src/main.c` — 직접 확인 2026-06-24
