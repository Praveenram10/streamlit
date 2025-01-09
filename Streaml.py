import streamlit as st
import json
import random
import psutil
import matplotlib.pyplot as plt

# Load instance types
def load_instances():
    with open("r3_instance_types.json", "r") as file:
        return json.load(file)

# Extract system utilization
def get_system_utilization():
    return {
        "vCPUs": psutil.cpu_count(logical=True),
        "memory_GiB": psutil.virtual_memory().total / (1024 ** 3),
        "cpu_utilization": psutil.cpu_percent(interval=1),
        "memory_utilization": psutil.virtual_memory().percent
    }

# Scaling Decision Logic
def suggest_required_resources(current_usage):
    cpu_util = current_usage["cpu_utilization"]
    mem_util = current_usage["memory_utilization"]

    if cpu_util > 85 or mem_util > 85:
        return "Upgrade"
    elif cpu_util < 30 and mem_util < 30:
        return "Downgrade"
    return "Optimal"

# Genetic Algorithm Functions
def fitness(solution, instances, required_vCPUs, required_memory_GiB):
    total_vCPUs, total_memory, total_cost = 0, 0, 0
    for instance, count in solution.items():
        instance_data = next(i for i in instances if i["instance_type"] == instance)
        total_vCPUs += instance_data["vCPUs"] * count
        total_memory += instance_data["memory_GiB"] * count
        total_cost += instance_data["on_demand_hourly_price_usd"] * count
    return 1 / total_cost if total_vCPUs >= required_vCPUs and total_memory >= required_memory_GiB else 0

def generate_solution(instances):
    return {instance["instance_type"]: random.randint(0, 10) for instance in instances}

def crossover(parent1, parent2):
    return {key: parent1[key] if random.random() < 0.5 else parent2[key] for key in parent1.keys()}

def mutate(solution, mutation_rate):
    if random.random() < mutation_rate:
        instance = random.choice(list(solution.keys()))
        solution[instance] = max(0, solution[instance] + random.choice([-1, 1]))
    return solution

def genetic_algorithm(instances, required_vCPUs, required_memory_GiB, pop_size=20, generations=100, mutation_rate=0.1):
    population = [generate_solution(instances) for _ in range(pop_size)]
    for _ in range(generations):
        population.sort(key=lambda x: fitness(x, instances, required_vCPUs, required_memory_GiB), reverse=True)
        new_population = population[:2]
        while len(new_population) < pop_size:
            p1, p2 = random.choices(population[:10], k=2)
            child = mutate(crossover(p1, p2), mutation_rate)
            new_population.append(child)
        population = new_population
    return max(population, key=lambda x: fitness(x, instances, required_vCPUs, required_memory_GiB))

# Streamlit UI
st.title("🚀 Cloud Cost Optimization with Genetic Algorithm")

instances = load_instances()
current_usage = get_system_utilization()
decision = suggest_required_resources(current_usage)

# Determine required vCPUs and Memory based on decision
if decision == "Upgrade":
    required_vCPUs = int(current_usage["vCPUs"] * 1.5)
    required_memory_GiB = int(current_usage["memory_GiB"] * 1.5)
elif decision == "Downgrade":
    required_vCPUs = max(1, int(current_usage["vCPUs"] * 0.7))
    required_memory_GiB = max(1, int(current_usage["memory_GiB"] * 0.7))
else:
    required_vCPUs = current_usage["vCPUs"]
    required_memory_GiB = current_usage["memory_GiB"]

# Sidebar System Info
st.sidebar.header("🔧 System Resources")
st.sidebar.write(f"**Detected vCPUs:** {current_usage['vCPUs']}")
st.sidebar.write(f"**Detected Memory (GiB):** {current_usage['memory_GiB']}")
st.sidebar.write(f"**CPU Utilization:** {current_usage['cpu_utilization']}%")
st.sidebar.write(f"**Memory Utilization:** {current_usage['memory_utilization']}%")
st.sidebar.write(f"**Scaling Decision:** {decision}")

# Line Graph for Utilization vs. Optimal Threshold
fig, ax = plt.subplots(1, 2, figsize=(12, 5))

# Simulated data for visualization
time_steps = list(range(1, 11))  # Simulated 10 time points
cpu_usage_data = [random.uniform(20, 90) for _ in time_steps]
mem_usage_data = [random.uniform(20, 90) for _ in time_steps]
optimal_line = [85] * len(time_steps)  # Optimal upgrade threshold

# CPU Utilization Line Graph
ax[0].plot(time_steps, cpu_usage_data, label="CPU Utilization", color="blue", marker="o")
ax[0].plot(time_steps, optimal_line, label="Optimal Threshold (85%)", color="red", linestyle="dashed")
ax[0].set_title("CPU Utilization Over Time")
ax[0].set_xlabel("Time")
ax[0].set_ylabel("Utilization (%)")
ax[0].legend()

# Memory Utilization Line Graph
ax[1].plot(time_steps, mem_usage_data, label="Memory Utilization", color="green", marker="o")
ax[1].plot(time_steps, optimal_line, label="Optimal Threshold (85%)", color="red", linestyle="dashed")
ax[1].set_title("Memory Utilization Over Time")
ax[1].set_xlabel("Time")
ax[1].set_ylabel("Utilization (%)")
ax[1].legend()

st.pyplot(fig)

# Run Optimization
if st.button("⚡ Optimize Resources"):
    best_solution = genetic_algorithm(instances, required_vCPUs, required_memory_GiB)
    total_cost = sum(
        next(i["on_demand_hourly_price_usd"] for i in instances if i["instance_type"] == instance) * count
        for instance, count in best_solution.items()
    )

    # Display Results
    st.subheader("📊 Optimization Results")
    st.write("**🚀 Scaling Decision:**", decision)
    st.write("**🖥️ Best Instance Combination:**", best_solution)
    st.write("**💰 Total Cost (USD/hour):**", round(total_cost, 2))
