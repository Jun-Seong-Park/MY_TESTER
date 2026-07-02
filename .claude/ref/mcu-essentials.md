> description: STM32F401RC(T6) + Cortex-M4 핵심 사실 모음 — 이 보드(MY_TESTER) 학습 문제를 답하기 위한 RCC clock / GPIO / USART / ADC·SPI·I2C·TIM / EXTI / Cortex-M4 core 요점. 망라식 매뉴얼 덤프가 아니라 board-scoped.
> when to use: STM32F401 클럭 트리·GPIO 레지스터·USART baud·인터럽트(EXTI/NVIC)·SysTick·타이밍 관련 학습 질문에 답할 때, 또는 MY_TESTER 펌웨어가 쓰는 페리페럴 동작을 확인할 때.
> caution: 모든 페이지 번호는 rm0368 Rev 6 / pm0214 Rev 10 의 인쇄 페이지 = PDF 페이지(오프셋 0, footer "N/852"·"N/262"로 확인). "up to 256 priority levels"(pm0214 p13)는 Cortex-M4 일반 사양이고, STM32F4 구현은 상위 4비트(16 레벨)만 — 둘을 혼동하지 말 것.

# 목차
1. RCC 클럭 트리 (HSI/HSE/PLL, SYSCLK·버스 prescaler, timer x2, Flash WS)
2. GPIO 레지스터 (MODER/OTYPER/OSPEEDR/PUPDR/AFRL/AFRH) 와 AF 개념
3. USART (baud 공식, RXNE/TXE/TC/IDLE 플래그·인터럽트, oversampling 16/8)
4. ADC / SPI / I2C / TIM 기본 (이 보드 관련 범위)
5. EXTI (SYSCFG_EXTICR 매핑, edge select, NVIC line grouping)
6. Cortex-M4 코어 (vector table, NVIC priority, SysTick, PRIMASK/BASEPRI, tail-chaining)
7. 이 보드(MY_TESTER) 펌웨어 적용 요약

---

# 1. RCC 클럭 트리

## 1.1 클럭 소스
SYSCLK 를 구동할 수 있는 소스는 3가지: HSI oscillator / HSE oscillator / Main PLL (rm0368 p93).

- **HSI**: 내부 16 MHz RC oscillator. 직접 system clock 으로 쓰거나 PLL input 으로 사용. 리셋 후 기본 system clock 이 HSI (rm0368 p98, p103). 리셋 직후 CPU clock = 16 MHz, Flash 0 WS (rm0368 p46).
- **HSE**: 외부 크리스탈/세라믹 레조네이터 또는 외부 클럭. (이 보드는 HSE 미사용 — 1.7절·main.c:144 참조)
- **LSE**: 32.768 kHz 외부 크리스탈, RTC 용 (rm0368 p98).
- **Main PLL**: HSI 또는 HSE 를 입력으로 받아 SYSCLK(최대 84 MHz)와 USB OTG FS/SDIO 용 48 MHz(PLL48CLK)를 생성 (rm0368 p97).

## 1.2 PLL 공식 (RCC_PLLCFGR, rm0368 p96, p105–107)
```
f(VCO clock)            = f(PLL clock input) × (PLLN / PLLM)
f(PLL general output)   = f(VCO clock) / PLLP      ← SYSCLK 후보
f(USB OTG FS/SDIO/RNG)  = f(VCO clock) / PLLQ
```
제약 (rm0368 p105–107):
| 인자 | 범위 | 제약/권장 |
|---|---|---|
| PLLM | 2 ~ 63 | VCO **입력** 주파수 = PLL input / PLLM 가 1~2 MHz 가 되도록. **2 MHz 권장**(PLL jitter 최소) |
| PLLN | 192 ~ 432 | VCO **출력** 주파수가 192~432 MHz 범위 안에 들도록 |
| PLLP | 2, 4, 6, 8 | SYSCLK 가 84 MHz 초과하지 않도록 (00=2, 01=4, 10=6, 11=8) |
| PLLQ | 2 ~ 15 | USB OTG FS = VCO/PLLQ = 48 MHz 가 되도록 |

예) HSI 16 MHz → 84 MHz: PLLM=16(→1 MHz VCO입력*), PLLN=336(→336 MHz VCO출력), PLLP=4(→84 MHz). (*권장 2 MHz 면 PLLM=8.)

## 1.3 SYSCLK / 버스 주파수 상한 (rm0368 p95)
| 도메인 | 클럭 | 최대 주파수 |
|---|---|---|
| SYSCLK | system clock | 84 MHz |
| AHB (HCLK) | SYSCLK / AHB prescaler(HPRE) | 84 MHz |
| APB2 (high-speed, PCLK2) | HCLK / APB2 prescaler(PPRE2) | 84 MHz |
| APB1 (low-speed, PCLK1) | HCLK / APB1 prescaler(PPRE1) | **42 MHz** |

- AHB prescaler: 1~512. APB1/APB2 prescaler: 1,2,4,8,16 (RCC_CFGR HPRE/PPRE1/PPRE2).
- SW 가 APB1 ≤ 42 MHz, APB2 ≤ 84 MHz 를 직접 보장해야 함 (rm0368 p107 Caution).

## 1.4 Timer clock ×2 규칙 (rm0368 p95)
TIMxCLK 는 하드웨어가 자동 설정 (TIMPRE 비트 reset 가정, 기본값):
- **APB prescaler = 1** → TIMxCLK = 해당 APB 도메인 주파수 (= HCLK).
- **APB prescaler ≠ 1** → TIMxCLK = 해당 APB 도메인 주파수의 **2배** (TIMxCLK = 2 × PCLKx).

이유: APB 가 분주돼도 타이머는 분주 전 속도를 받아 풀 분해능 유지. (예: SYSCLK=84, APB1=/2=42 MHz 라면 APB1 타이머(TIM2~5) 클럭 = 84 MHz.)

## 1.5 Flash wait-state vs HCLK (rm0368 p46, Table 6 — PNG 확인)
LATENCY 비트(FLASH_ACR)는 HCLK 와 공급전압에 맞게 설정. 전압범위별 WS 경계(MHz):

| WS (CPU cycles) | 2.7–3.6 V | 2.4–2.7 V | 2.1–2.4 V | 1.71–2.1 V |
|---|---|---|---|---|
| 0 WS (1) | 0 < HCLK ≤ 30 | 0 < HCLK ≤ 24 | 0 < HCLK ≤ 18 | 0 < HCLK ≤ 16 |
| 1 WS (2) | 30 < HCLK ≤ 60 | 24 < HCLK ≤ 48 | 18 < HCLK ≤ 36 | 16 < HCLK ≤ 32 |
| 2 WS (3) | 60 < HCLK ≤ 84 | 48 < HCLK ≤ 72 | 36 < HCLK ≤ 54 | 32 < HCLK ≤ 48 |
| 3 WS (4) | — | 72 < HCLK ≤ 84 | 54 < HCLK ≤ 72 | 48 < HCLK ≤ 64 |
| 4 WS (5) | — | — | 72 < HCLK ≤ 84 | 64 < HCLK ≤ 80 |
| 5 WS (6) | — | — | — | 80 < HCLK ≤ 84 |

- 3.3 V 동작(2.7–3.6 V 열) 기준: 84 MHz → **2 WS**.
- VOS[1:0]=0x01 이면 fHCLK_max=60 MHz, VOS[1:0]=0x10 이면 84 MHz (rm0368 p46).
- 리셋 후 16 MHz, 0 WS (rm0368 p46).
- WS 증가 절차: LATENCY 먼저 쓰고 → FLASH_ACR 읽어 반영 확인 → 그 다음 클럭 올림 (rm0368 p46–47).

## 1.6 SysTick 외부 클럭 소스
RCC 는 SysTick 의 외부 클럭으로 **HCLK/8** 을 공급. SysTick 은 이 HCLK/8 또는 Cortex clock(HCLK) 중 선택 가능(STK_CTRL CLKSOURCE) (rm0368 p95; 레지스터는 6절 참조).

---

# 2. GPIO 레지스터와 AF 개념

각 포트(GPIOA..E,H)는 아래 레지스터로 핀당 설정. y = pin number 0..15.

| 레지스터 | 폭/핀 | 의미 (rm0368 출처) |
|---|---|---|
| **MODER** | 2 bit | 00 Input(reset) / 01 General-purpose output / 10 Alternate function / 11 Analog (p158) |
| **OTYPER** | 1 bit | 0 Push-pull(reset) / 1 Open-drain (p159) |
| **OSPEEDR** | 2 bit | 00 Low / 01 Medium / 10 High / 11 Very high speed (p159) |
| **PUPDR** | 2 bit | 00 No pull / 01 Pull-up / 10 Pull-down / 11 Reserved (p160) |
| **AFRL** | 4 bit ×8 | pin 0~7 의 AF 선택 (AFRL[31:0]) (p149, p151) |
| **AFRH** | 4 bit ×8 | pin 8~15 의 AF 선택 (AFRH[31:0]) (p149, p151) |

## AF (Alternate Function) 개념 (rm0368 p149–150)
- 각 I/O 핀은 16개 AF input(AF0~AF15) 중 하나에 연결되는 multiplexer 를 가짐 → 한 시점에 한 페리페럴만 핀에 연결(충돌 방지).
- 리셋 후 모든 I/O 는 AF0. 페리페럴 AF 는 AF1~AF13 에 매핑. AF15 = Cortex-M4 EVENTOUT.
- 페리페럴 핀 설정 순서: MODER 를 `10`(AF) 로 → OTYPER/PUPDR/OSPEEDR 설정 → AFRL/AFRH 에서 원하는 AFx 선택 (rm0368 p150).
- **ADC** 만 예외: MODER 를 `11`(Analog) 로 설정 (AFR 불필요) (rm0368 p150).
- 어느 AFx 번호가 어느 페리페럴인지의 상세 매핑은 RM 이 아니라 **데이터시트의 "Alternate function mapping" 표** 참조 (rm0368 p150). (이 보드의 실제 AF 번호는 7절 표 참조)

---

# 3. USART

## 3.1 Baud rate 공식 (rm0368 p520, Equation 1)
```
Tx/Rx baud = fCK / ( 8 × (2 − OVER8) × USARTDIV )
```
- OVER8=0 (oversampling ×16) → 분모 = 16 × USARTDIV.
- OVER8=1 (oversampling ×8)  → 분모 = 8 × USARTDIV.
- USARTDIV: USART_BRR 에 fixed-point 로 코딩된 unsigned 값.
  - OVER8=0: 소수부 4 bit (DIV_Fraction[3:0]).
  - OVER8=1: 소수부 3 bit (DIV_Fraction[2:0], bit3 은 0 유지) (rm0368 p520).
- fCK = USART 가 속한 APB 도메인 클럭(PCLK). USART1/6 = APB2(PCLK2), USART2 = APB1(PCLK1).
- 예) USARTDIV=27.75 → DIV_Mantissa=27, DIV_Fraction=12/16=0.75 → BRR=0x1BC (rm0368 p520).

## 3.2 Oversampling 16 vs 8 (rm0368 p521, p507)
- **OVER8=0 (×16)**: 클럭 편차에 대한 receiver tolerance 큼. 최대 속도 fPCLK/16 로 제한.
- **OVER8=1 (×8)**: 더 높은 속도(최대 fPCLK/8) 가능하나 tolerance 감소.
- start bit 검출 시퀀스는 ×16/×8 동일: `1 1 1 0 X 0 X 0 X 0 0 0 0` (rm0368 p507).
- Smartcard/IrDA/LIN 모드에선 OVER8 이 HW 로 0 강제 (rm0368 p507).

## 3.3 USART_SR 상태 플래그 & 인터럽트 (rm0368 p549)
| 플래그 | set 조건 | clear 방법 | 인터럽트 enable 비트 (CR1) |
|---|---|---|---|
| **TXE** | TDR→shift register 로 전송됨(TDR 비었음) | USART_DR 에 write | TXEIE |
| **TC** | 프레임 전송 완료 + TXE=1 | SR read 후 DR write (또는 0 write) | TCIE |
| **RXNE** | shift→RDR(USART_DR) 로 수신됨 | USART_DR read (또는 0 write) | RXNEIE |
| **IDLE** | idle line 검출 | SR read 후 DR read | IDLEIE |
| ORE(overrun) | RXNE=1 인데 다음 워드 도착 | SR read 후 DR read | RXNEIE |

- 모든 USART 인터럽트는 NVIC 상 **USART 인스턴스당 단일 글로벌 벡터**(예: USART2_IRQHandler)로 묶임 — 핸들러에서 SR 플래그로 원인 판별 (rm0368 p547; 이 보드 stm32f4xx_it.c:204).

---

# 4. ADC / SPI / I2C / TIM 기본 (이 보드 범위)

## 4.1 ADC (rm0368 p213–214)
- **12-bit successive approximation** ADC. resolution 12/10/8/6 bit 설정 가능.
- 최대 19 multiplexed channel (외부 16 + 내부 2 + VBAT). 변환 모드: single / continuous / scan / discontinuous.
- 결과는 left/right-aligned 16-bit data register 에 저장. 채널별 sampling time 프로그래머블.
- 인터럽트: EOC(end of conversion), JEOC(injected), analog watchdog, overrun.
- 외부 트리거(regular/injected) + polarity 설정 가능. DMA 지원.
- 공급: 2.4~3.6 V full speed (1.8 V 까지 저속). 입력범위 VREF− ≤ VIN ≤ VREF+.
- (이 보드: ADC1 채널0, 12-bit, software trigger, 3-cycle sampling — main.c:188–209)

## 4.2 SPI (rm0368 p559–560)
- half/full-duplex 동기 직렬. master(SCK 공급)/slave/multimaster.
- **8-bit 또는 16-bit** 프레임. master baud prescaler 8단계, 최대 **fPCLK/2**.
- CPOL/CPHA(클럭 polarity·phase) 프로그래머블. MSB/LSB-first 선택. NSS HW/SW 관리.
- Tx/Rx 플래그(TXE/RXNE) + 인터럽트, BSY 플래그, MODF/OVR/CRCERR 에러 플래그. HW CRC. 1-byte Tx/Rx 버퍼 + DMA.

## 4.3 I2C (rm0368 p474–476)
- Standard mode ≤ 100 kHz, Fast mode ≤ 400 kHz (최대 1 MHz 까지 가능).
- 7-bit / 10-bit 주소, dual addressing, General Call. master/slave, multimaster(arbitration).
- 데이터는 8-bit byte, MSB first. SDA(data) / SCL(clock) 2선.
- 인터럽트 벡터 2개(event / error). ACK enable/disable. SMBus/PMBus 호환, HW PEC.
- (이 보드: I2C1=PB8/PB9 AF4, I2C3=PA8/PC9 AF4, open-drain — main.c:393–399, 315–329)

## 4.4 TIM 기본
**General-purpose TIM2~TIM5** (rm0368 p316):
- 16-bit(TIM3,TIM4) 또는 **32-bit(TIM2,TIM5)** auto-reload counter, up/down/up-down.
- 16-bit 프로그래머블 prescaler(PSC, on-the-fly 변경 가능).
- input capture / output compare / PWM(edge·center-aligned) / one-pulse / encoder·hall.
- 인터럽트·DMA: update(overflow/underflow/init), trigger, capture, compare.
- 핵심 레지스터: TIMx_CNT(카운터), TIMx_PSC(prescaler), TIMx_ARR(auto-reload).

**Advanced-control TIM1** (rm0368 p243–245):
- 16-bit up/down/up-down auto-reload + 16-bit prescaler.
- GP 타이머 기능 + **complementary output + 프로그래머블 dead-time**, **repetition counter**, **break input** (모터 제어용).
- (이 보드: TIM1_CH=PA9 AF1, TIM2_CH=PA15 AF1 — main.c:331–337, 354–360)

---

# 5. EXTI (External interrupt/event controller)

## 5.1 구조 (rm0368 p202, p205)
- 최대 **23개 edge detector** (line 0~22). 각 라인 독립적으로 type(interrupt/event)·trigger(rising/falling/both)·mask 설정.
- 절차: trigger 레지스터(RTSR/FTSR)에 원하는 edge 설정 → IMR 에 해당 비트 `1` → 선택 edge 발생 시 interrupt request + PR(pending) 비트 set → PR 에 `1` write 로 clear (rm0368 p207–208).

## 5.2 핀 → EXTI line 매핑 (SYSCFG_EXTICR1~4, rm0368 p142–143)
GPIO 핀 x 는 **EXTI line x** 에 연결됨 (PA0/PB0/... 모두 line0 을 공유 → 그중 하나를 EXTICR 로 선택).
EXTICRn 의 EXTIx[3:0] 값으로 어느 포트를 line x 에 연결할지 선택:

| EXTICR | 담당 line/pin x | EXTIx[3:0] 인코딩 |
|---|---|---|
| EXTICR1 | x = 0~3 | 0000=PA[x] 0001=PB[x] 0010=PC[x] 0011=PD[x] 0100=PE[x] 0111=PH[x] |
| EXTICR2 | x = 4~7 | (동일) |
| EXTICR3 | x = 8~11 | (동일) |
| EXTICR4 | x = 12~15 | (동일) |

예) 이 보드 PB12(EXTI 입력): EXTICR4 의 EXTI12[3:0] = `0001`(PB), line12 사용.

## 5.3 Edge select (rm0368 p210)
- **EXTI_RTSR** TRx: 1 = rising trigger enable (line x).
- **EXTI_FTSR** TRx: 1 = falling trigger enable (line x).
- 같은 라인에 RTSR·FTSR 둘 다 set 하면 both-edge 트리거.

## 5.4 NVIC line grouping (rm0368 p202–203, 벡터 테이블)
| EXTI line | NVIC 벡터 |
|---|---|
| line 0 | EXTI0 (전용) |
| line 1 | EXTI1 (전용) |
| line 2 | EXTI2 (전용) |
| line 3 | EXTI3 (전용) |
| line 4 | EXTI4 (전용) |
| line 5~9 | **EXTI9_5** (공유 1개 벡터) |
| line 10~15 | **EXTI15_10** (공유 1개 벡터) |
| line 16 | PVD, line 17 RTC alarm, line 18 USB OTG FS wakeup, line 21 RTC tamper, line 22 RTC wakeup (각 전용) |

- line0~4 는 각자 전용 IRQ. line5~9 은 한 핸들러(EXTI9_5), line10~15 도 한 핸들러(EXTI15_10) → 공유 핸들러에서 EXTI_PR 로 어느 라인인지 판별.
- 예) 이 보드 PB12 → line12 → **EXTI15_10_IRQHandler** 그룹.

---

# 6. Cortex-M4 코어 (pm0214)

## 6.1 Vector table (pm0214 p40)
- 벡터 테이블 = 초기 SP(stack pointer) 값 + 모든 exception handler 시작주소(exception vector) 배열.
- 시스템 리셋 시 주소 **0x00000000** 에 고정. VTOR(Vector Table Offset Register)로 0x00000080~0x3FFFFF80 범위 재배치 가능 (pm0214 p227).
- 각 벡터 LSB 는 1 (Thumb code 표시).
- 순서: SP_main, Reset, NMI, HardFault, ... SysTick, 그 뒤 IRQ0~ (외부 인터럽트).

## 6.2 NVIC 우선순위 (pm0214 p41, p215, p229)
- exception 마다 우선순위 존재. **값이 작을수록 우선순위 높음** (pm0214 p41).
- **Reset / HardFault / NMI** 는 고정 음수 우선순위(가장 높음, 구성 불가). 나머지는 configurable.
- **STM32F4 는 우선순위 상위 4비트만 구현 → configurable 값 0~15 (16 레벨)** (pm0214 p41; PRI_N[7:4], Table 51 p229). (pm0214 p13 의 "up to 256 levels" 는 Cortex-M4 일반 사양 — STM32F4 실제 구현 아님.)
- **Preempt(group) vs Sub priority** (pm0214 p41): IPR 우선순위 필드를 상위(group priority) + 하위(subpriority)로 분할.
  - preemption 판정엔 **group priority 만** 사용 (group 이 높으면 실행 중 핸들러를 선점).
  - 같은 group priority 의 pending 들 간 순서는 subpriority 로 결정. group·sub 둘 다 같으면 **가장 낮은 IRQ 번호** 먼저.
  - 실행 중 핸들러와 **같은** 우선순위 exception 은 선점 못 함(pending 으로만 표시).
- **AIRCR PRIGROUP** (pm0214 p228–229, Table 51): group/sub 분할점(binary point) 지정. AIRCR 쓰려면 VECTKEY 에 0x5FA write 필수(아니면 무시).

| PRIGROUP[2:0] | Binary point (PRI_N[7:4]) | Group bits | Sub bits | Group priorities | Sub priorities |
|---|---|---|---|---|---|
| 0b0xx | 0bxxxx | [7:4] | 없음 | 16 | 1 |
| 0b100 | 0bxxx.y | [7:5] | [4] | 8 | 2 |
| 0b101 | 0bxx.yy | [7:6] | [5:4] | 4 | 4 |
| 0b110 | 0bx.yyy | [7] | [6:4] | 2 | 8 |
| 0b111 | 0b.yyyy | 없음 | [7:4] | 1 | 16 |

(x = group bit, y = subpriority bit. pm0214 p229 Table 51.)

## 6.3 SysTick (pm0214 p246–248)
- **24-bit down-counter** (System timer). reload 값에서 0 까지 카운트다운 → 다음 클럭에 STK_LOAD 값으로 wrap → 다시 카운트다운.
- 레지스터: STK_CTRL(제어/상태), STK_LOAD(reload 값, RELOAD[23:0]), STK_VAL(현재값), STK_CALIB.
- **STK_CTRL** 비트: ENABLE(bit0, 카운터 enable) / TICKINT(bit1, 0→0 도달 시 SysTick exception 발생) / CLKSOURCE(bit2, 0=AHB/8, 1=processor clock(AHB)) / COUNTFLAG(bit16, 0 도달 시 set, read 로 clear).
- **RELOAD 계산**: N 클럭 주기마다 1회 인터럽트 → RELOAD = N−1 (예: 100 펄스마다 → 99). 범위 0x000001~0xFFFFFF (pm0214 p248).
- **HAL 1 ms tick 구성** (board 적용): HAL 은 SysTick exception 을 1 ms 주기로 설정하여 `SysTick_Handler` → `HAL_IncTick()` 으로 uwTick 을 증가시킴 (이 보드 stm32f4xx_it.c:183–192). `HAL_GetTick()` 은 이 uwTick 을 반환, `HAL_Delay(ms)` 는 uwTick 이 ms 만큼 증가할 때까지 busy-wait. 
  - 1 ms RELOAD = (SysTick clock / 1000) − 1. 이 보드는 HSI 16 MHz·HCLK=16 MHz·CLKSOURCE=processor clock 이므로 RELOAD = 16000 − 1 = 15999. (clock 근거 main.c:144–165)

## 6.4 인터럽트 마스킹 (pm0214 p24–25)
- **PRIMASK** (1 bit): 1 = configurable priority 를 가진 **모든** exception 활성화 차단(NMI·HardFault 제외). `__disable_irq()`/`__enable_irq()` 가 이 비트 조작. (이 보드 Error_Handler 에서 `__disable_irq()` — main.c:430)
- **FAULTMASK** (1 bit): 1 = NMI 제외 **모든** exception 차단(HardFault 포함).
- **BASEPRI** (BASEPRI[7:4]): nonzero 로 설정하면 그 값보다 **같거나 낮은** 우선순위(= 값이 같거나 큰) exception 을 차단. 0x00 = no effect. → 특정 임계 이하만 막는 선택적 마스킹.
- 접근: MSR/MRS 또는 CPS 명령 (CMSIS: `__set_PRIMASK` 등).

## 6.5 Tail-chaining / Late-arriving (pm0214 p43–44)
- **Tail-chaining**: exception handler 종료 시 entry 요건을 만족하는 pending exception 이 있으면 **stack pop 을 생략**하고 바로 새 handler 로 전이 → 연속 ISR 간 오버헤드 대폭 감소.
- **Late-arriving**: 이전 exception 의 state saving(stacking) 도중 더 높은 우선순위 exception 이 오면 그쪽으로 전환(저장 state 는 동일하므로 stacking 은 중단 없이 계속). 원래 handler 첫 명령이 execute stage 진입 전까지 수용 가능; 복귀 시엔 일반 tail-chaining 규칙 적용.
- stack frame: 8 워드(tail-chained/late-arriving 가 아닐 때만 push) (pm0214 p43).

---

# 7. 이 보드(MY_TESTER) 펌웨어 적용 요약

CubeMX 생성 펌웨어(STM32F401RCT6) 기준 — 위 사실들이 실제 어떻게 적용됐는지:

| 항목 | 설정 | 근거 |
|---|---|---|
| Clock | **HSI 직접 SYSCLK = 16 MHz** (PLL 미사용), HPRE=/1, PPRE1=/1, PPRE2=/1, **Flash 0 WS**, VOS scale2 | main.c:144–165, 138–139 |
| → 의미 | 16 MHz 라 PLL 불필요·0 WS 면 충분(rm0368 p46), APB1=APB2=16 MHz | — |
| GPIO LED | PC13(red), PC14(green) push-pull output | main.c:101–103, 287–292 |
| EXTI | **PB12 rising-edge 인터럽트** (GPIO_MODE_IT_RISING) → line12 → EXTI15_10 그룹 | main.c:302–305 |
| USART2 | 115200, 8N1, oversampling **16**, TX/RX, IT 수신(RXNE) | main.c:235–243, 106 |
| USART2 ISR | USART2_IRQHandler → HAL_UART_IRQHandler → RxCpltCallback(echo) | stm32f4xx_it.c:204, main.c:411–418 |
| ADC1 | 채널0(PA0), 12-bit, right-align, software trigger, 3-cycle sampling | main.c:188–211 |
| SPI | SPI1=PB3/PB5(AF5), SPI2=PB13/14/15(AF5), SPI3=PC10/11/12(AF6) | main.c:307–313, 362–383 |
| I2C | I2C1=PB8/PB9(AF4 OD), I2C3=PA8/PC9(AF4 OD) | main.c:315–329, 393–399 |
| TIM | TIM1_CH=PA9(AF1), TIM2_CH=PA15(AF1) | main.c:331–337, 354–360 |
| USB | OTG_FS=PA11/PA12(AF10) | main.c:346–352 |
| SysTick | HAL 1 ms tick → HAL_IncTick(); HAL_Delay(1000) 메인 루프 | stm32f4xx_it.c:188, main.c:122 |

(주의: 회로도(References/Byrobot_All_Tester_NRF24L01P_USB-C_Schematic.pdf) 상의 각 핀 실제 연결처는 본 문서 범위 밖 — 별도 회로도 문서 참조. 위 표는 펌웨어 핀 할당만 정리.)

---

# 출처:
- rm0368 Rev 6 — "RM0368 STM32F401xB/C and STM32F401xD/E advanced Arm-based 32-bit MCUs reference manual", STMicroelectronics. (References/rm0368-stm32f401xbc-and-stm32f401xde-advanced-armbased-32bit-mcus-stmicroelectronics.pdf) — pdftotext/pdftoppm 직접 추출 확인 2026-06-24
- pm0214 Rev 10 — "PM0214 STM32 Cortex-M4 MCUs and MPUs programming manual", STMicroelectronics. (References/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf) — 직접 추출 확인 2026-06-24
- 펌웨어 — MY_TESTER/Core/Src/main.c, MY_TESTER/Core/Src/stm32f4xx_it.c (CubeMX 생성, 직접 read 2026-06-24)
