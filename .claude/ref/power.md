> description: All-Tester (NRF24L01P / USB-C) 보드의 전원 트리 — USB-C VBUS 입력부터 LDO(VCC33), 아날로그 필터 레일(AVCC33), VBAT 경로, USB-A 호스트 VBUS 출력, J601 헤더 전원까지의 전체 분배 구조.
> when to use: "왜 전원이 안 들어오나", "어느 레일이 죽었나"를 추적하거나, J-Link/SWD 연결 시 보드가 켜지지 않는 원인을 디버깅할 때, 또는 새 측정 포인트의 공급 전압(VCC33 vs AVCC33 vs VBUS)을 확인할 때 연다.
> caution: 이 보드의 유일한 전원은 USB-C(J101) VBUS 5V 다. J-Link/J301 의 TVDD 는 타깃 전압을 "감지만" 할 뿐 보드에 전력을 공급하지 않는다 — USB-C 를 빼면 보드 전체가 죽는다. MCU 의 VDDA/VREF+(pin13)·VBAT(pin1)·VDD 는 회로도상 모두 같은 VCC33 노드에 직결돼 있고(아날로그 필터 레일 AVCC33 이 아님), AVCC33 은 RF 모듈·J601 헤더 전용이다.

# 목차
- [1. 전원 입력 (USB-C J101 VBUS 5V — 유일 전원)](#1-전원-입력)
- [2. 페라이트 비드 (입력·레일 필터)](#2-페라이트-비드)
- [3. 3.3V LDO — U201 ME6217C33](#3-33v-ldo--u201-me6217c33)
- [4. VCC33 / AVCC33 레일 (아날로그 필터)](#4-vcc33--avcc33-레일)
- [5. VBAT 경로 (D301 schottky)](#5-vbat-경로-d301-schottky)
- [6. USB-A 호스트 VBUS 출력 경로](#6-usb-a-호스트-vbus-출력-경로)
- [7. USB-C CC 풀다운 — 보드는 USB sink/device](#7-usb-c-cc-풀다운--보드는-usb-sinkdevice)
- [8. 전원 트리 다이어그램 (텍스트)](#8-전원-트리-다이어그램)
- [9. 디버깅 함의 — J-Link TVDD 는 전원이 아니다](#9-디버깅-함의--j-link-tvdd-는-전원이-아니다)
- [출처](#출처)

# 1. 전원 입력

보드의 **유일한 전원은 USB-C 커넥터 J101 의 VBUS 5V** 다 (회로도 p.2, 1_Ext_Connector). J101 의 VBUS 핀(A4/B9, A9/B4)이 VBUS 넷으로 들어오며, 다른 입력(배터리 커넥터, 별도 DC 잭)은 회로도 어디에도 없다.

- 따라서 **USB-C 케이블을 뽑으면 VBUS 가 끊기고 보드 전체(LDO·MCU·RF·LCD)가 즉시 전원 차단**된다 (회로도 p.2/p.3, VBUS → U201 만이 유일한 3.3V 생성 경로).
- 입력 벌크 커패시터: BC101 10u, BC103 10u, BC102/BC104/BC105 1u 가 VBUS 에 병렬 (회로도 p.2, 1_Ext_Connector). 전원 사이드의 BC201 10u 도 VBUS 에 추가 (회로도 p.3, 2_Power).

# 2. 페라이트 비드

모든 비드는 BEAD/180/2A/C1608 (180Ω@100MHz, 2A, 1608 패키지) 동일 품번이다.

| 비드 | 위치 | 역할 | 근거 |
|---|---|---|---|
| FB602, FB603 | J101 VBUS 입력 | USB-C VBUS 라인 필터 (커넥터 직후) | 회로도 p.2, 1_Ext_Connector |
| FB201 | VCC33 → AVCC33 | 디지털 3.3V 에서 아날로그 3.3V 레일 분리 (HF 격리) | 회로도 p.3, 2_Power |
| FB202 | GND ↔ GND | 두 GND 도메인 간 그라운드 스티칭 비드 (전원 레일 아님 — 양단 모두 GND 심볼) | 회로도 p.3, 2_Power |
| FB601 | VBUS → VBUS_F | J601 헤더로 나가는 필터된 VBUS 생성 | 회로도 p.7, 6_Extra |

주의: **FB202 는 전원 비드가 아니라 GND 분리/스티칭 비드**다 — 양단이 모두 GND 심볼에 묶여 있다 (회로도 p.3, 2_Power, `_pwr_fb2-3.png` 확인).

# 3. 3.3V LDO — U201 ME6217C33

3.3V 생성은 U201 ME6217C33 (SOT23-5, 고정 3.3V LDO) 단일 소자가 담당한다 (회로도 p.3, 2_Power).

| 핀 | 이름 | 연결 | 근거 |
|---|---|---|---|
| 1 | VIN | VBUS (5V 입력) | 회로도 p.3, 2_Power |
| 5 | VOUT | VCC33 (3.3V 출력) | 회로도 p.3, 2_Power |
| 3 | CE | R201 10K 로 VIN(=VBUS) 에 풀업 → 상시 enable | 회로도 p.3, 2_Power |
| 2 | VSS | GND | 회로도 p.3, 2_Power |
| 4 | NC | 미연결 | 회로도 p.3, 2_Power |

- 핵심 경로: **VBUS(VIN, pin1) → VOUT(pin5) → VCC33** (회로도 p.3, 2_Power).
- CE(enable)는 R201 10K 를 통해 VBUS 로 풀업돼 있어 VBUS 가 살아있는 한 항상 켜진다 — 별도 enable GPIO 가 없다 (회로도 p.3, 2_Power, `_pwr-3.png`).
- 출력 디커플: BC202 10u 가 VCC33 에 병렬 (회로도 p.3, 2_Power).

# 4. VCC33 / AVCC33 레일 (아날로그 필터)

- **VCC33 (디지털 3.3V)**: LDO 출력 메인 레일. MCU 의 VDD 4핀(19/32/48/64), VBAT(pin1), **VDDA/VREF+(pin13)** 이 모두 이 VCC33 노드에 직결된다 (회로도 p.4, 3_MCU, `_mcu_pwrpins-4.png` 에서 네 개 VDD + VBAT + VDDA 가 한 VCC33 스텁에 합류 확인). 즉 STM32 의 아날로그 공급(VDDA)은 필터 레일이 아니라 VCC33 직결이다.
- **AVCC33 (아날로그 3.3V)**: VCC33 에서 FB201 비드를 거쳐 만들어지는 노이즈 격리 레일 (회로도 p.3, 2_Power). DC 적으로는 VCC33 과 사실상 동전위(비드는 DC 저항 ≈ 0).
- AVCC33 의 실제 소비처:
  - **RF 모듈 NRF24L01+ (U401)** 의 공급 (회로도 p.5, 4_RF — AVCC33 → VDD_PA 로컬 노드, 디커플 BC401/BC402/BC403 1u).
  - **J601 확장 헤더** 로 노출 (회로도 p.7, 6_Extra — 디커플 BC602 10u). J601 에서 AVCC33 노드는 VCC33(헤더 pin2/pin6)과 같은 노드에 묶여 있다 (`_tmp_img/j601_top-7.png` 확인 — pin2·pin6 VCC33 과 AVCC33 스텁이 한 정션).

요약: AVCC33 은 "MCU 아날로그용"이 아니라 **RF + 확장 헤더용 필터 레일**이다. STM32 자체의 VDDA 는 VCC33 직결.

# 5. VBAT 경로 (D301 schottky)

VBAT(백업 도메인)은 별도 배터리 없이 VBUS 에서 schottky 다이오드로 공급된다.

- **D301 = 1N5819WS (1A, SOD-323)**, 애노드 = pin2 = VBUS 측, 캐소드(바) = pin1 = J301 헤더의 VBAT 측 (회로도 p.4, 3_MCU, `d301-4.png`). 전류 방향: **VBUS → D301 → VBAT(J301 pin1)**.
- 단, MCU 의 VBAT(U301 pin1)은 §4 대로 VCC33 에 직결돼 있으므로(회로도 p.4, 3_MCU), STM32 의 백업 도메인은 평상시 VCC33 으로 공급된다. D301 schottky 는 J301 헤더 pin1(VBAT)로 가는 별도 경로다.

# 6. USB-A 호스트 VBUS 출력 경로

보드가 USB 호스트로 동작할 때(FSUSB30 mux SEL=1, CH2=HOST), USB-A 커넥터 J102 의 VBUS 핀(pin1)으로 5V 를 내보낸다.

- J102 VBUS(pin1) ← VBUS 넷 (회로도 p.2, 1_Ext_Connector, `_j102-2.png`).
- J102 PAD/GND(pin4) 측에 R2 0Ω(R1608) 이 GND 로 연결 (쉴드/패드 옵션 점퍼) (회로도 p.2, 1_Ext_Connector).
- 즉 **입력 VBUS 가 그대로 USB-A 호스트 포트의 VBUS 출력으로 패스스루**된다 (전용 부스트/스위치 없음) — 보드 자체가 USB-C 로 받은 5V 를 USB-A 다운스트림으로 전달.
- 데이터 라인 mux: U101 FSUSB30MUX (MSOP-10) 가 MCU 의 D+/D-(PA12/PA11) 를 SEL 에 따라 CH1(DEVICE, USB-C J101) 또는 CH2(HOST, USB-A J102) 로 라우팅 (회로도 p.2, 1_Ext_Connector — `SEL=0 -> CH1 (DEVICE)`, `SEL=1 -> CH2 (HOST)`). SEL 은 USB_SEL GPIO.

# 7. USB-C CC 풀다운 — 보드는 USB sink/device

- J101 의 CC1, CC2 각각에 **5.1K 풀다운(R601, R602)** 이 GND 로 연결돼 있다 (회로도 p.2, 1_Ext_Connector, `p2lo-2.png`).
- USB Type-C 규격상 CC 핀의 5.1kΩ 풀다운(Rd)은 **sink/device** 를 의미한다 → 이 보드는 USB-C 포트에서 전력을 "받는" 쪽(sink)이며 전원을 공급하지 않는다.
- 이는 §1(VBUS 가 유일 입력)과 일치: 보드는 USB-C 로 5V 를 받아 동작한다.

# 8. 전원 트리 다이어그램

```
USB-C J101 VBUS 5V  ── (유일 전원; 빼면 전체 다운)
   │  (CC1/CC2: 5.1k Rd → sink/device, 회로도 p.2)
   ├─ FB602 / FB603 (BEAD 180/2A)  ── 입력 필터
   │
   ├─► VBUS 넷
   │     ├─ 벌크: BC101 10u, BC103 10u, BC102/104/105 1u (p.2) + BC201 10u (p.3)
   │     │
   │     ├─► U201 ME6217C33 (SOT23-5) LDO
   │     │      VIN(1)=VBUS   CE(3)=R201 10K↑VBUS(상시 on)   VSS(2)=GND
   │     │      └─► VOUT(5) ── VCC33 (3.3V 메인)  [BC202 10u 디커플, p.3]
   │     │            │
   │     │            ├─► STM32F401RCT6 (U301): VDD 19/32/48/64 + VBAT(1) + VDDA/VREF+(13)  ← 모두 VCC33 직결 (p.4)
   │     │            ├─► LCD VDD_LCD (p.6)
   │     │            ├─► J301 TVDD(pin6) ── 전압 감지만 (전원 아님)  ★ §9
   │     │            ├─► J601 헤더 VCC33 (pin2, pin6) (p.7)
   │     │            │
   │     │            └─► FB201 (BEAD 180/2A) ──► AVCC33 (아날로그 3.3V)
   │     │                   ├─► RF NRF24L01+ (U401) VDD (p.5)  [BC401/402/403 1u]
   │     │                   └─► J601 헤더 AVCC33 (p.7)  [BC602 10u]
   │     │
   │     ├─► D301 1N5819WS schottky (VBUS→) ──► J301 pin1 VBAT (p.4)
   │     │
   │     └─► USB-A 호스트 J102 VBUS(pin1) 패스스루 (host 모드 출력, p.2)
   │
   └─ GND 도메인: FB202 (BEAD) = GND↔GND 스티칭 (전원 아님, p.3)
```

# 9. 디버깅 함의 — J-Link TVDD 는 전원이 아니다

J301 (SWD_ARM-8P_PETRONE) 의 핀 중 전원 관련은 다음 둘뿐이다 (회로도 p.4, 3_MCU, `d301-4.png`):

| J301 핀 | 넷 | 의미 |
|---|---|---|
| 1 | VBAT (D301 schottky 경유 VBUS) | 백업 도메인 핀 |
| 6 | TVDD = VCC33 | **타깃 전압 감지(sense) 전용** |

- J-Link 의 TVDD(VTref)는 **타깃의 I/O 전압을 측정해 SWD 신호 레벨을 맞추는 입력**일 뿐, 타깃에 전류를 공급하지 않는다 (J301 pin6 가 VCC33 에 연결돼 있어 J-Link 가 "3.3V 타깃"임을 감지).
- 따라서 **J-Link 만 꽂고 USB-C 를 빼면 보드는 켜지지 않는다** — VCC33 을 만드는 유일한 소스는 U201 LDO 이고, 그 입력 VBUS 는 USB-C 에서만 온다 (§1, §3).
- 디버깅 시 항상 **USB-C 전원을 먼저 연결**한 뒤 SWD 를 연결할 것. "J-Link 연결했는데 코어가 안 깨어난다 / TVDD 0V 로 보인다" 는 거의 대부분 USB-C 미연결(=VCC33 미생성)이 원인이다.

# 출처

- Byrobot_All_Tester_NRF24L01P_USB-C_Schematic.pdf (KiCad E.D.A. 9.0.6, 7 sheets) — 경로 `C:/Users/ALUX/Firmware/MY_TESTER/MY_TESTER/References/`. 인용 sheet: p.2 1_Ext_Connector, p.3 2_Power, p.4 3_MCU, p.5 4_RF, p.6 5_LCD, p.7 6_Extra.
- 회로도 렌더 PNG (검증에 사용): `_pwr-3.png`, `_pwr_fb-3.png`, `_pwr_fb2-3.png`, `d301-4.png`, `_mcu_pwrpins-4.png`, `_mcu_vdda-4.png`, `_mcu_vbat-4.png`, `_j102-2.png`, `p2lo-2.png`, `j601-7.png`, `j601r-7.png`, `_tmp_img/j601_top-7.png` (모두 `C:/Users/ALUX/Firmware/MY_TESTER/`).
- 취득/검증일: 2026-06-24.
