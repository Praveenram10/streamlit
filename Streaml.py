import streamlit as st
import json
import random
import psutil
import time
import matplotlib.pyplot as plt

# Load instance types
def load_instances():
    with open("r3_instance_types.json", "r") as file:
        return json.load(file)

# Genetic Algorithm functions
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

def scaling_analysis(current_usage, required_resources):
    vCPU_diff = required_resources["vCPUs"] - current_usage["vCPUs"]
    memory_diff = required_resources["memory_GiB"] - current_usage["memory_GiB"]
    if vCPU_diff > 0 or memory_diff > 0:
        return "Upgrade", {"vCPUs": vCPU_diff, "memory_GiB": memory_diff}
    elif vCPU_diff < -10 or memory_diff < -10:
        return "Downgrade", {"vCPUs": vCPU_diff, "memory_GiB": memory_diff}
    return "Optimal", {"vCPUs": vCPU_diff, "memory_GiB": memory_diff}

# Function to get real-time system usage
def get_system_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    total_vCPUs = psutil.cpu_count(logical=True)
    memory_info = psutil.virtual_memory()
    memory_used = memory_info.used / (1024 ** 3)
    total_memory = memory_info.total / (1024 ** 3)
    return {
        "current_vCPUs": int((cpu_usage / 100) * total_vCPUs),
        "current_memory_GiB": round(memory_used, 2),
        "total_vCPUs": total_vCPUs,
        "total_memory_GiB": round(total_memory, 2),
        "cpu_usage_percent": cpu_usage,
        "memory_usage_percent": memory_info.percent,
    }

# Streamlit UI
st.set_page_config(page_title="Cloud Cost Optimization", layout="wide")

st.title("🌩️ Cloud Cost Optimization using Genetic Algorithm")
st.markdown("This application dynamically determines the best cloud instance configuration to optimize costs based on your system's real-time utilization.")

# Get real-time system usage
usage = get_system_usage()

# Layout using columns
col1, col2 = st.columns(2)

# CPU Utilization Graph
with col1:
    st.subheader("🔵 CPU Utilization")
    fig, ax = plt.subplots()
    ax.bar(["Used", "Total"], [usage["current_vCPUs"], usage["total_vCPUs"]], color=["blue", "gray"])
    ax.set_ylabel("vCPUs")
    ax.set_ylim(0, usage["total_vCPUs"])
    st.pyplot(fig)

# Memory Utilization Graph
with col2:
    st.subheader("🟢 Memory Utilization")
    fig, ax = plt.subplots()
    ax.bar(["Used", "Total"], [usage["current_memory_GiB"], usage["total_memory_GiB"]], color=["green", "gray"])
    ax.set_ylabel("Memory (GiB)")
    ax.set_ylim(0, usage["total_memory_GiB"])
    st.pyplot(fig)

# Automatically determine required vCPUs and memory (with a buffer)
buffer_percentage = st.slider("⚙️ Buffer Percentage for Scaling", min_value=10, max_value=50, value=20, step=5)

required_vCPUs = int(usage["current_vCPUs"] * (1 + buffer_percentage / 100))
required_memory_GiB = round(usage["current_memory_GiB"] * (1 + buffer_percentage / 100), 2)

st.subheader("📌 Suggested Cloud Resources")
st.write(f"✅ **Required vCPUs:** {required_vCPUs}")
st.write(f"✅ **Required Memory (GiB):** {required_memory_GiB}")

if st.button("🚀 Run Optimization"):
    instances = load_instances()
    best_solution = genetic_algorithm(instances, required_vCPUs, required_memory_GiB)
    decision, adjustment = scaling_analysis(usage, {"vCPUs": required_vCPUs, "memory_GiB": required_memory_GiB})
    total_cost = sum(
        next(i["on_demand_hourly_price_usd"] for i in instances if i["instance_type"] == instance) * count
        for instance, count in best_solution.items()
    )
    
    st.subheader("📊 Optimization Results")
    st.write("🔹 **Scaling Decision:**", f"**{decision}**")
    st.write("🔹 **Adjustment Needed:**", adjustment)
    st.write("🔹 **Best Instance Combination:**")
    st.json(best_solution)
    st.write(f"💰 **Total Cost (USD/hour):** ${total_cost:.2f}")

