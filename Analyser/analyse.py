import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("prices_round_0_day_-1.csv", sep=";")

# Check columns
print(df.columns.tolist())
print(df["product"].unique())

# Split products
tomatoes = df[df["product"] == "TOMATOES"]
emeralds = df[df["product"] == "EMERALDS"]

# Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

ax1.plot(tomatoes["timestamp"], tomatoes["mid_price"], color="red")
ax1.set_title("Tomatoes Price Over Time")
ax1.set_ylabel("Price")
ax1.grid(True)

ax2.plot(emeralds["timestamp"], emeralds["mid_price"], color="green")
ax2.set_title("Emeralds Price Over Time")
ax2.set_ylabel("Price")
ax2.grid(True)

plt.tight_layout()
plt.show()