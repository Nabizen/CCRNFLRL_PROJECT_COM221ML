# test_env.py
from traffic_env import TrafficEnv
import time

env = TrafficEnv(render_mode=True)   # enable rendering
obs, _ = env.reset()

for step in range(1000):
    action = env.action_space.sample()   # random action (toggle light or not)
    obs, reward, done, truncated, info = env.step(action)
    time.sleep(0.05)
    if done:
        print("Episode ended:", info)
        break

env.close()
  