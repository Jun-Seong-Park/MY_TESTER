# MY_TESTER

Firmware for the **All Tester** board, built around an **STM32F401RCT6**
(LQFP-64, Arm Cortex-M4). Powered from a single USB-C input (J101).

This is a personal study project: I use it to learn STM32 development hands-on,
starting from a CubeMX-generated base and modifying the firmware directly to
understand how each peripheral works.

## Overview

- **MCU:** STM32F401RCT6 (Cortex-M4, LQFP-64)
- **Board:** Byrobot All Tester
- **Power:** USB-C only (J101)
- **Base:** STM32CubeMX-generated project (`MY_TESTER.ioc`), CMake build
- **Toolchain:** arm-none-eabi-gcc
- **Debug:** J-Link over SWD (J301)

Board hardware details (pinmap, connectors, peripherals, power) are kept under
[.claude/ref/](.claude/ref/) — start from [.claude/ref/README.md](.claude/ref/README.md).

> Note: pin assignments are not fixed — they change whenever the `.ioc` is
> edited in CubeMX. The current firmware snapshot lives in
> [.claude/ref/current-firmware-config.md](.claude/ref/current-firmware-config.md).
