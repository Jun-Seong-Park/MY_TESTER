> description: MY_TESTER (Byrobot All Tester, STM32F401RCT6) 펌웨어의 현재 설정 스냅샷 — 클럭/주변장치/GPIO/인터럽트/앱 동작/외부 배선을 한 시점의 고정값으로 기록한 문서입니다.
> when to use: 현재 펌웨어가 "지금 어떻게 동작하도록 설정돼 있는가"를 확인할 때(클럭 16MHz 여부, 어떤 핀이 어떤 AF로 mux 됐는지, USART2 echo 동작, J601-CP2102 배선 등). 핀/클럭을 바꾸기 전 baseline 비교용.
> caution: 핀·클럭은 변경 가능 — 이 문서는 한 시점의 스냅샷이며, .ioc/main.c가 바뀌면 더 이상 유효하지 않습니다. LED 색·핀·극성은 고정 사실이 아니므로(외부배선/펌웨어 소관) 기록하지 않습니다 — 실물로 확인하세요.

# 목차

1. 클럭 (SystemClock_Config) — 현재 16MHz (낮음)
2. 활성화된 주변장치 & 설정 (ADC1 / USART2 / GPIO AF mux)
3. 전체 GPIO 테이블 (MX_GPIO_Init)
4. 인터럽트 (NVIC / 핸들러 / RxCplt echo)
5. 현재 앱 동작 (1초 카운터 TX / LED / RX echo)
6. 사용 중인 외부 배선 (J601 → CP2102 → PC)
7. 출처

---

# 1. 클럭 (SystemClock_Config) — 현재 16MHz (낮음)

현재 펌웨어는 **내부 RC 오실레이터(HSI) 16MHz를 SYSCLK으로 그대로 사용**하며, **PLL을 켜지 않습니다**. 즉 STM32F401이 낼 수 있는 최고 클럭(84MHz)의 1/5 수준으로 매우 낮게 동작합니다.

| 항목 | 값 | 근거 |
|---|---|---|
| 오실레이터 | HSI (내부 RC) ON | `OscillatorType = RCC_OSCILLATORTYPE_HSI`, `HSIState = RCC_HSI_ON` (main.c:144-145) |
| HSI 주파수 | 16 MHz | "Internal 16 MHz factory-trimmed RC (HSI)" (STM32F401RCT6.pdf p.1 features) / `RCC.HSI_VALUE=16000000` (MY_TESTER.ioc) |
| PLL | **OFF (사용 안 함)** | `PLL.PLLState = RCC_PLL_NONE` (main.c:147) |
| SYSCLK 소스 | HSI | `SYSCLKSource = RCC_SYSCLKSOURCE_HSI` (main.c:157) |
| **SYSCLK** | **16,000,000 Hz (16 MHz)** | HSI 직결 + PLL_NONE / `RCC.SYSCLKFreq_VALUE=16000000` (MY_TESTER.ioc) |
| AHB 분주 (HCLK) | DIV1 | `AHBCLKDivider = RCC_SYSCLK_DIV1` (main.c:158) |
| **HCLK** | **16,000,000 Hz** | SYSCLK/1 / `RCC.AHBFreq_Value=16000000` (MY_TESTER.ioc) |
| APB1 분주 (PCLK1) | DIV1 | `APB1CLKDivider = RCC_HCLK_DIV1` (main.c:159) |
| **PCLK1** | **16,000,000 Hz** | HCLK/1 / `RCC.APB1Freq_Value=16000000` (MY_TESTER.ioc) |
| APB2 분주 (PCLK2) | DIV1 | `APB2CLKDivider = RCC_HCLK_DIV1` (main.c:160) |
| **PCLK2** | **16,000,000 Hz** | HCLK/1 / `RCC.APB2Freq_Value=16000000` (MY_TESTER.ioc) |
| 전압 스케일 | Scale 2 | `__HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE2)` (main.c:139) |
| Flash latency | 0 wait state | `HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0)` (main.c:162) |

- **강조**: 현재 **16MHz로 매우 낮게 동작**합니다. STM32F401은 최대 84MHz까지 가능하므로(STM32F401RCT6.pdf p.1 "frequency up to 84 MHz"), 성능이 필요하면 HSE+PLL 또는 HSI+PLL 재설정이 필요합니다.
- USB(OTG FS는 48MHz 클럭 필요)·정밀 타이밍을 쓰려면 16MHz HSI 단독으로는 부족합니다. 보드엔 HSE 크리스탈(PH0/PH1 OSC_IN/OSC_OUT, 회로도 p.4 `3_MCU`)이 있으나 현재 펌웨어는 PLL_NONE으로 미사용입니다 (main.c:147).
- Flash latency 0 / Voltage Scale 2는 16MHz 저속 동작과 정합합니다(고속이면 wait state·Scale1 필요).

# 2. 활성화된 주변장치 & 설정

`main()`에서 초기화하는 것은 GPIO, ADC1, USART2 세 가지입니다 (main.c:97-99). 나머지 핀들은 **AF(Alternate Function)로 mux만 되어 있고, 해당 주변장치 핸들은 초기화되지 않은** 상태입니다(즉 핀은 SPI/I2C/USB/TIM/USART1 기능으로 배정됐지만 그 IP의 init 코드는 없음).

## 2.1 ADC1

| 항목 | 값 | 근거 |
|---|---|---|
| 인스턴스 | ADC1 | `hadc1.Instance = ADC1` (main.c:188) |
| 변환 채널 | **ADC_CHANNEL_0 (PA0)** | `sConfig.Channel = ADC_CHANNEL_0` (main.c:207), rank 1 (main.c:208) |
| 클럭 prescaler | PCLK2/2 | `ADC_CLOCK_SYNC_PCLK_DIV2` (main.c:189) |
| 해상도 | 12-bit | `ADC_RESOLUTION_12B` (main.c:190) |
| Scan / Continuous / Discont | 모두 DISABLE | main.c:191-193 |
| 트리거 | 소프트웨어 시작 | `ADC_SOFTWARE_START`, edge NONE (main.c:194-195) |
| 데이터 정렬 | Right | `ADC_DATAALIGN_RIGHT` (main.c:196) |
| 변환 개수 | 1 | `NbrOfConversion = 1` (main.c:197) |
| 샘플링 시간 | 3 cycles | `ADC_SAMPLETIME_3CYCLES` (main.c:209) |
| ADC GPIO (analog) | PA0,PA1,PA4,PA5,PA6,PA7 / PC4,PC5 / PB0,PB1 = ANALOG | `HAL_ADC_MspInit` (msp.c:111-125), 채널 매핑 주석 (msp.c:99-110) |

- 참고: ADC1 핸들은 init 되지만, `main()` while 루프에서 ADC 변환을 호출하지는 않습니다 (main.c:112-123 — TX만 수행).

## 2.2 USART2 (현재 유일하게 통신에 쓰이는 UART)

| 항목 | 값 | 근거 |
|---|---|---|
| 인스턴스 | USART2 | `huart2.Instance = USART2` (main.c:235) |
| Baud rate | **115200** | `huart2.Init.BaudRate = 115200` (main.c:236) |
| Word length | 8-bit | `UART_WORDLENGTH_8B` (main.c:237) |
| Stop bits | 1 | `UART_STOPBITS_1` (main.c:238) |
| Parity | None | `UART_PARITY_NONE` (main.c:239) → 종합 **8N1** |
| Mode | **TX_RX (송수신)** | `UART_MODE_TX_RX` (main.c:240) |
| HW flow control | None | `UART_HWCONTROL_NONE` (main.c:241) |
| Oversampling | 16 | `UART_OVERSAMPLING_16` (main.c:242) |
| 핀 | PA2=USART2_TX, PA3=USART2_RX (AF7) | `HAL_UART_MspInit`, `GPIO_AF7_USART2` (msp.c:196-204) |
| Global interrupt | **Enabled** | `HAL_NVIC_EnableIRQ(USART2_IRQn)`, priority(0,0) (msp.c:207-208) |

## 2.3 GPIO AF로만 mux 된 핀들 (해당 IP init 없음)

아래 핀들은 `MX_GPIO_Init`에서 AF 모드로 설정만 되어 있습니다(주변장치 핸들 init 코드는 펌웨어에 없음). 회로도 p.4 `3_MCU`의 네트 라벨과 일치합니다.

| 기능 | 핀 | AF 매크로 | 근거 (main.c) | 회로도 네트 |
|---|---|---|---|---|
| SPI2 (RF/NRF24L01) | PB13,PB14,PB15 | GPIO_AF5_SPI2 | main.c:308-312 | RF_SCLK/RF_MISO/RF_MOSI (회로도 p.4) |
| SPI1 (LCD) | PB3,PB5 | GPIO_AF5_SPI1 | main.c:378-382 | LCD SPI1 (회로도 p.4) |
| SPI3 (J601 확장) | PC10,PC11,PC12 | GPIO_AF6_SPI3 | main.c:363-367 | SPI3_SCK/MISO/MOSI (회로도 p.7 J601) |
| I2C1 | PB8,PB9 | GPIO_AF4_I2C1 (OD) | main.c:394-398 | I2C1_SCL/SDA (회로도 p.4) |
| I2C3 | PA8,PC9 | GPIO_AF4_I2C3 (OD) | main.c:324-328, 316-320 | I2C3_SCL/SDA (회로도 p.4) |
| USB OTG FS | PA11,PA12 | GPIO_AF10_OTG_FS | main.c:347-351 | USB DM/DP (회로도 p.2 `2_Power`/MUX) |
| TIM1 (CH2, 부저 PWM) | PA9 | GPIO_AF1_TIM1 | main.c:332-336 | BUZZ_PWM (회로도 p.6 LCD/Extra) |
| TIM2 (CH1, LCD 백라이트 PWM) | PA15 | GPIO_AF1_TIM2 | main.c:355-359 | LCD_BK_PWM (회로도 p.6) |
| USART1 (디버그 DBG_M) | PB6(TX),PB7(RX) | GPIO_AF7_USART1 | main.c:386-390 | DBG_M-TX/RX (회로도 p.4 "USART1: Debug") |

# 3. 전체 GPIO 테이블 (MX_GPIO_Init)

`MX_GPIO_Init`에서 GPIOA/B/C/D/H 클럭이 켜집니다 (main.c:266-270). 아래는 명시적으로 설정된 핀 전체입니다. 초기 출력 레벨은 main.c:273-283의 `HAL_GPIO_WritePin(..., GPIO_PIN_RESET)`로 모두 LOW(0)로 초기화됩니다(출력 핀에 한함). AF/입력/아날로그 핀은 초기 레벨 개념이 없어 "-"로 표기.

| 핀 | 모드 | AF | 초기 레벨 | 근거 (main.c:LINE) |
|---|---|---|---|---|
| PC13 | OUTPUT_PP (LED RED) | - | LOW (RESET) | main.c:287-292 (write 273), main.c:103 |
| PC14 | OUTPUT_PP (LED GREEN) | - | LOW (RESET) | main.c:287-292 (write 273) |
| PC0 | OUTPUT_PP | - | LOW (RESET) | main.c:287-292 |
| PC1 | OUTPUT_PP | - | LOW (RESET) | main.c:287-292 |
| PC2 | OUTPUT_PP | - | LOW (RESET) | main.c:287-292 |
| PC3 | OUTPUT_PP | - | LOW (RESET) | main.c:287-292 |
| PC6 | OUTPUT_PP (/RF_CS) | - | LOW (RESET) | main.c:287-292 |
| PC7 | OUTPUT_PP (RF_CE) | - | LOW (RESET) | main.c:287-292 |
| PB10 | OUTPUT_PP (/LCD_CS) | - | LOW (RESET) | main.c:295-299 (write 277) |
| PB4 | OUTPUT_PP (/LCD_RESET) | - | LOW (RESET) | main.c:295-299 (write 277) |
| PA10 | OUTPUT_PP (USB_SEL) | - | LOW (RESET) | main.c:339-344 (write 280) |
| PD2 | OUTPUT_PP (LCD_DAT/CMD) | - | LOW (RESET) | main.c:371-375 (write 283) |
| PB12 | IT_RISING (EXTI12, RF_INT) | - | - (입력) | main.c:302-305 |
| PB13 | AF_PP | AF5_SPI2 | - | main.c:308-313 |
| PB14 | AF_PP | AF5_SPI2 | - | main.c:308-313 |
| PB15 | AF_PP | AF5_SPI2 | - | main.c:308-313 |
| PC9 | AF_OD | AF4_I2C3 | - | main.c:316-321 |
| PA8 | AF_OD | AF4_I2C3 | - | main.c:324-329 |
| PA9 | AF_PP | AF1_TIM1 | - | main.c:332-337 |
| PA11 | AF_PP | AF10_OTG_FS | - | main.c:347-352 |
| PA12 | AF_PP | AF10_OTG_FS | - | main.c:347-352 |
| PA15 | AF_PP | AF1_TIM2 | - | main.c:355-360 |
| PC10 | AF_PP | AF6_SPI3 | - | main.c:363-368 |
| PC11 | AF_PP | AF6_SPI3 | - | main.c:363-368 |
| PC12 | AF_PP | AF6_SPI3 | - | main.c:363-368 |
| PB3 | AF_PP | AF5_SPI1 | - | main.c:378-383 |
| PB5 | AF_PP | AF5_SPI1 | - | main.c:378-383 |
| PB6 | AF_PP | AF7_USART1 | - | main.c:386-391 |
| PB7 | AF_PP | AF7_USART1 | - | main.c:386-391 |
| PB8 | AF_OD | AF4_I2C1 | - | main.c:394-399 |
| PB9 | AF_OD | AF4_I2C1 | - | main.c:394-399 |

추가로 MSP에서 설정되는 핀 (MX_GPIO_Init 밖):
| 핀 | 모드 | 근거 |
|---|---|---|
| PA2 / PA3 | AF_PP, AF7_USART2 | msp.c:199-204 |
| PA0,PA1,PA4,PA5,PA6,PA7 | ANALOG (ADC1) | msp.c:111-115 |
| PC4,PC5 | ANALOG (ADC1) | msp.c:117-120 |
| PB0,PB1 | ANALOG (ADC1) | msp.c:122-125 |

- 모든 핀 `Pull = GPIO_NOPULL` (각 InitStruct). 출력 GPIO Speed=LOW, AF 핀 대부분 VERY_HIGH (PA9·PA15만 LOW) — main.c 각 블록 참조.

# 4. 인터럽트 (NVIC / 핸들러 / RxCplt echo)

## 4.1 활성화된 NVIC IRQ

| IRQ | 상태 | priority | 근거 |
|---|---|---|---|
| **USART2_IRQn** | Enabled | (0,0) | `HAL_NVIC_SetPriority(USART2_IRQn, 0, 0)` + `HAL_NVIC_EnableIRQ(USART2_IRQn)` (msp.c:207-208) |
| SysTick | (HAL_Init 기본) | - | `SysTick_Handler` → `HAL_IncTick()` (it.c:188) |

- **주의**: PB12를 EXTI_RISING(RF_INT, EXTI12)으로 설정했지만(main.c:302-305), EXTI15_10 IRQ에 대한 `HAL_NVIC_EnableIRQ`는 펌웨어에 없습니다 — 즉 RF_INT 인터럽트는 NVIC에서 활성화되지 않은 상태입니다(미확인 의도, 현 상태 사실만 기록).

## 4.2 핸들러 (stm32f4xx_it.c)

| 핸들러 | 동작 | 근거 |
|---|---|---|
| `USART2_IRQHandler` | `HAL_UART_IRQHandler(&huart2)` 호출 | it.c:204-213 |
| `SysTick_Handler` | `HAL_IncTick()` | it.c:183-192 |
| `NMI_Handler` | `while(1)` 무한 루프 | it.c:69-79 |
| `HardFault/MemManage/BusFault/UsageFault` | 각각 `while(1)` | it.c:84-139 |
| `huart2` 참조 | `extern UART_HandleTypeDef huart2;` | it.c:58 |

## 4.3 HAL_UART_RxCpltCallback — RX echo 동작

USART2로 PC에서 1바이트가 도착하면 `USART2_IRQHandler` → `HAL_UART_IRQHandler` → `HAL_UART_RxCpltCallback`(main.c:411-418)가 호출됩니다.

- 수신 바이트를 **그대로 다시 송신(echo)** 합니다: `HAL_UART_Transmit(&huart2, &rx_byte, 1, HAL_MAX_DELAY)` (main.c:415).
- 그 후 다음 1바이트 수신을 **재무장(re-arm)**: `HAL_UART_Receive_IT(&huart2, &rx_byte, 1)` (main.c:416).
- 최초 수신 무장은 `main()`에서 한 번: `HAL_UART_Receive_IT(&huart2, &rx_byte, 1)` (main.c:106).
- 버퍼는 1바이트 `volatile uint8_t rx_byte` (main.c:51).

# 5. 현재 앱 동작

## 5.1 메인 while 루프 — 1초 카운터 TX

`main()` 무한 루프(main.c:112-123)는 1초마다 정수 카운터를 USART2로 ASCII 송신합니다.

- `static uint32_t count = 0` 부터 시작 (main.c:117).
- `sprintf(msg, "%lu\r\n", count)` → `"0\r\n"`, `"1\r\n"`, ... (main.c:119).
- `HAL_UART_Transmit(&huart2, msg, len, HAL_MAX_DELAY)` 블로킹 송신 (main.c:120).
- `count++` 후 `HAL_Delay(1000)` (main.c:121-122).
- 주의: HAL_Delay는 SysTick 기준. 현재 16MHz라도 SysTick은 동작하므로 1초 간격은 유지됩니다.

## 5.2 LED 상태

- 초기화 시 `HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET)` 1회 실행 (main.c:103). PC13/PC14는 MX_GPIO_Init에서도 LOW로 초기화됩니다 (main.c:273).
- 코드 주석은 "red off (always)" / "RED OFF, GREEN blink"로 적혀 있습니다 (main.c:101-103).
- **주의 (극성·동작은 고정 사실 아님)**: `GPIO_PIN_RESET`이 LED 켜짐인지 꺼짐인지는 외부 LED 배선(공통 애노드/캐소드)에 달려 있고 회로도로 확정되지 않으며, 핀 매핑도 바뀔 수 있습니다 — 여기 고정 기록하지 않습니다. 실물로 관측해 확인하세요. 한편 코드 주석은 "GREEN blink"라 하지만 현재 루프에는 LED 토글 코드가 없어 **실제로 깜빡이지 않습니다**(PC14는 init 후 그대로). 이건 코드 사실입니다.

## 5.3 인터럽트 RX echo

- 위 4.3절과 동일: PC가 USART2로 보낸 문자를 그대로 되돌려 보냅니다 (main.c:415).

# 6. 사용 중인 외부 배선 (주어진 정보, 파일에 없음)

UART 통신 경로 (현재 PC와 통신하는 실제 배선):

| MCU 핀 | 신호 | J601 핀 | → CP2102 | → PC |
|---|---|---|---|---|
| PA2 | USART2_TX | **J601 pin 11** | CP2102 RXD | USB |
| PA3 | USART2_RX | **J601 pin 13** | CP2102 TXD | USB |
| GND | GND | **J601 pin 33** | CP2102 GND | USB |

- J601 핀 번호 확인: pin 11 = PA2(USART2_TX), pin 13 = PA3(USART2_RX), pin 33 = GND (회로도 p.7 `6_Extra`/J601, `j601-7.png` 렌더 확인). pin 29도 GND이므로 GND는 pin 29/33 둘 다 사용 가능.
- CP2102 USB-to-TTL 변환기를 거쳐 PC에 연결, **115200 8N1** (main.c:236-242 설정과 일치).
- 디버그: **J-Link → J301 SWD 커넥터** (회로도 p.4 `3_MCU` 영역, CLAUDE.md 빌드/디버그 환경).
- 전원: **USB-C** (회로도 p.2 `2_Power`).

# 7. 출처:

- 펌웨어: `MY_TESTER/Core/Src/main.c`, `stm32f4xx_it.c`, `stm32f4xx_hal_msp.c` / `MY_TESTER/MY_TESTER.ioc`
- 회로도: `MY_TESTER/References/Byrobot_All_Tester_NRF24L01P_USB-C_Schematic.pdf` (7페이지, KiCad). 렌더 PNG: `j601-7.png`(p.7), `mcu_pc-4.png`·`chk_pb-4.png`(p.4)
- 데이터시트: `Datasheet/STM32F401RCT6.pdf` (HSI 16MHz / max 84MHz, p.1 features)
- 프로젝트 메모: `MY_TESTER/CLAUDE.md` (LED 극성·커넥터 매핑 진술)
- 취득/작성일: 2026-06-24
