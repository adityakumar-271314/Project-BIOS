# Hardware Integration & Future Roadmap

Project BIOS is currently a **pure software simulation**, but it was designed from the beginning with real-world robotics in mind.

---

## Current State

- Python cognition engine runs on laptop/desktop
- Godot handles physics and rendering
- Communication via lightweight TCP bridge
- Fully deterministic and replayable

This separation makes it easy to replace the simulated body with real hardware later.

---

## Hardware Vision

### Short-term Goal (v0.2 – v0.3)
- Differential drive robot (2 wheels + caster)
- Raspberry Pi 5 or Jetson Nano as onboard computer
- Camera + simple object detection (food/hazard)
- IMU for better odometry

### Medium-term Goal
- ROS 2 integration
- LiDAR or depth camera for better spatial awareness
- Multiple agents / swarm experiments

---

## Design Considerations for Hardware

| Aspect                    | Simulation                  | Hardware Requirement                     |
|--------------------------|-----------------------------|------------------------------------------|
| **Delta Time**           | Fixed physics tick          | Real-time capable (ROS 2)                |
| **Sensors**              | Raycasts + proximity        | Camera / LiDAR / ultrasonic              |
| **Odometry**             | Perfect + landmarks         | Wheel encoders + IMU + visual odometry   |
| **Latency**              | Near zero                   | Must handle network / processing delay   |
| **Power Management**     | Unlimited                   | Critical (energy model becomes real)     |

---

## Suggested Hardware Stack (Budget-friendly)

**Beginner Kit (~₹8,000 – ₹15,000):**
- Raspberry Pi 5
- Pi Camera Module 3
- L298N or TB6612 motor driver
- DC motors + chassis
- MPU6050 IMU
- LiPo battery + power management

**Better Performance:**
- NVIDIA Jetson Orin Nano
- RPLIDAR A1 or similar

---

## Integration Strategy

1. Keep Python brain mostly unchanged (run on robot or offloaded to laptop)
2. Replace Godot sensor input with real sensor readings
3. Send motor commands to motor controllers instead of Godot
4. Gradually improve odometry using real landmarks / visual features

---

## Challenges Ahead

- Sensor noise and uncertainty
- Real-time constraints
- Power and thermal management
- Safety (especially with hazards)
- Bridging simulation → reality gap

---

## Long-term Dream

A small fleet of autonomous agents running Project BIOS, learning from real-world interaction, forming memories, and developing survival strategies in unstructured environments.

---

**Status**: Simulation foundation is solid. Hardware bridge experiments will begin after v0.2.

---