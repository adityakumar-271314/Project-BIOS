# Theoretical Framework

## 1. Non-Linear Urgency
In biological systems, drives are not linear. Hunger doesn't bother an organism until it reaches a critical threshold. We model this using an inverted Sigmoid function for the Goal Stack Manager (GSM):

$$U(s) = \frac{100}{1 + e^{-k(s - x_0)}}$$

This ensures the agent maintains "calm" behavior until a survival threshold is crossed, at which point the drive score explodes, overriding curiosity.

## 2. Nociceptive Bias
"Pain" is treated as a systemic disruptor. High levels of damage to the `Integrity` variable increase the `Stress` hormone, which creates a competitive weight against exploration, forcing the agent into `HIDE` or `REST` states.