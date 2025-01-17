import streamlit as st
import json
import random
import matplotlib.pyplot as plt

def load_instances():
    with open("r3_instance_types.json", "r") as file:
        return json.load(file)

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

st.title("Cloud Cost Optimization")
instances = load_instances()

current_vCPUs = st.number_input("Current vCPUs", value=10, step=1)
current_memory_GiB = st.number_input("Current Memory (GiB)", value=127, step=1)
instance_family = st.text_input("Instance Family (e.g., r3, m5)", value="r3")

cpu_utilization = st.number_input("CPU Utilization (%) - N Days Avg", value=70, step=1)
memory_utilization = st.number_input("Memory Utilization (%) - N Days Avg", value=80, step=1)

required_vCPUs = int(current_vCPUs * (cpu_utilization / 100))
required_memory_GiB = int(current_memory_GiB * (memory_utilization / 100))

if st.button("Run Optimization"):
    best_solution = genetic_algorithm(instances, required_vCPUs, required_memory_GiB)
    decision, adjustment = scaling_analysis({"vCPUs": current_vCPUs, "memory_GiB": current_memory_GiB},
                                            {"vCPUs": required_vCPUs, "memory_GiB": required_memory_GiB})
    total_cost = sum(next(i["on_demand_hourly_price_usd"] for i in instances if i["instance_type"] == instance) * count
                     for instance, count in best_solution.items())

    st.subheader("Results")
    st.write("**Scaling Decision:**", decision)
    st.write("**Adjustment Needed:**", adjustment)
    st.write("**Best Instance Combination:**", best_solution)
    st.write("**Total Cost (USD/hour):**", total_cost)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(["Current", "Optimized"], [current_vCPUs, required_vCPUs], marker='o', linestyle='-', label="vCPUs")
    ax.plot(["Current", "Optimized"], [current_memory_GiB, required_memory_GiB], marker='o', linestyle='-', label="Memory (GiB)")
    ax.set_xlabel("Configuration")
    ax.set_ylabel("Resources")
    ax.set_title("Current vs Optimized Resource Allocation")
    ax.legend()
    st.pyplot(fig)
