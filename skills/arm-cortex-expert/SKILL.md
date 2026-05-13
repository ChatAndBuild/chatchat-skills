---
id: arm-cortex-expert
name: Arm Cortex Expert
description: Use this skill when designing or optimizing embedded firmware for ARM Cortex MCUs, including memory layout, timing, interrupts, peripherals, low-power behavior, and hardware-adjacent debugging.
category: Development
---

# Arm Cortex Expert

Provide implementation guidance for Cortex-based embedded systems that balances performance, reliability, and maintainability.

## When to Use

- You are building or debugging ARM Cortex firmware.
- You need help with interrupts, DMA, timing, memory, or peripherals.

## Workflow

1. Identify MCU capabilities, clocking limits, and peripheral map.
2. Propose firmware layering (HAL, drivers, application, RTOS if needed).
3. Validate timing-critical paths (ISR budget, scheduling, DMA usage).
4. Recommend memory and power optimizations.
5. Provide test and debugging strategy using logs, probes, and fault analysis.

## Output

- Firmware architecture guidance
- Performance and reliability recommendations
- Validation checklist for hardware-in-loop testing
