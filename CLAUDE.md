# MY_TESTER — Byrobot All Tester (STM32F401RCT6)

STM32F401RCT6(LQFP-64, Cortex-M4) 기반 Byrobot All Tester 보드입니다. 전원은 USB-C(J101) 단일 입력입니다.
STM32 개발을 익히기 위한 스터디 보드로, 펌웨어는 CubeMX 생성 베이스에서 직접 손대며 학습합니다.

## 상세 보드 지식 위치

보드 하드웨어/펌웨어 상세(핀맵·커넥터·전원·페리페럴 등)는 `.claude/ref/` 에 분리해 두었습니다.
보드 관련 질문을 받으면 먼저 `.claude/ref/README.md` 의 라우팅을 보고 아래 중 해당 문서를 읽으세요.

- 핀이 무엇에 연결됐나 / 어떤 AF 가능한가 -> `.claude/ref/pinmap.md`
- 커넥터 핀배치 (J101/J102/J301/J501/J601) -> `.claude/ref/connectors.md`
- RF / LCD / 버튼 / LED / 부저 / USB 결선 -> `.claude/ref/peripherals.md`
- 전원 (USB-C, LDO, VCC33/AVCC33, VBAT) -> `.claude/ref/power.md`
- STM32 클럭 / 인터럽트 / 타이머 / GPIO 개념 -> `.claude/ref/mcu-essentials.md`
- 지금 펌웨어가 어떻게 설정돼 있나 -> `.claude/ref/current-firmware-config.md`
- 보드 전체 개요 -> `.claude/ref/board-overview.md`

## 현재 설정 한눈에 (스냅샷)

- 클럭: **16 MHz (HSI 내부 RC 직결, PLL 미사용)** — 최대 84 MHz 대비 저속.
- UART 콘솔: **USART2**, J601 pin11(PA2=TX) / pin13(PA3=RX) / pin33(GND) → CP2102 USB-to-TTL → PC, **115200 8N1**.
- 디버그: **J-Link → J301 SWD 커넥터**.
- 전원: **USB-C 단독**.

## 주의

핀 배정은 고정이 아닙니다 — CubeMX(.ioc)로 언제든 바뀝니다. 위 "현재 설정"과 각 ref 문서의 펌웨어 항목은 한 시점의 스냅샷이며, 현재 펌웨어 설정의 기준 스냅샷은 `.claude/ref/current-firmware-config.md` 입니다. 핀/클럭을 바꿨다면 그 문서와 대조 후 갱신하세요.
