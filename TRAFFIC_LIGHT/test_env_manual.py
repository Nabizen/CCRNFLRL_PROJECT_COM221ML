# test_env_manual_continuous.py
from traffic_env import TrafficEnv
import time
import pygame

env = TrafficEnv(render_mode=True)
obs, _ = env.reset()
total_reward = 0
action = 0  # default: keep light

print("Controls:")
print("  [SPACE] = switch light")
print("  [Q] = quit")

running = True
while running:
    # Handle keyboard input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
                break
            elif event.key == pygame.K_SPACE:
                action = 1  # switch
            else:
                action = 0  # default keep

    # Step environment every frame
    obs, reward, done, truncated, info = env.step(action)
    total_reward += reward

    # Print rewards occasionally
    if reward != 0:
        print(f"Reward: {reward:.2f} | Total: {total_reward:.2f} | State: {obs}")

    if done:
        print("Episode ended. Resetting...\n")
        obs, _ = env.reset()
        total_reward = 0
        action = 0

    # Continue simulation
    action = 0  # reset to 'keep' each frame
    time.sleep(0.05)

env.close()
