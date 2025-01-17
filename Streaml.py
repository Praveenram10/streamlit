import streamlit as st
import json
import random
import psutil
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

def calculate_cost(configuration, instances):
    return sum(next(i["on_demand_hourly_price_usd"] for i in instances if i["instance_type"] == instance) * count
               for instance, count in configuration.items())
    
def scaling_analysis(current_config, avg_utilization, instances):
    current_cost = calculate_cost(current_config, instances)
    optimal_config = genetic_algorithm(instances, avg_utilization["vCPUs"], avg_utilization["memory_GiB"])
    optimal_cost = calculate_cost(optimal_config, instances)

    savings = current_cost - optimal_cost
    decision = "Optimal"
    if savings > 0:
        decision = "Downgrade"
    elif savings < -10:
        decision = "Upgrade"

    return decision, optimal_config, optimal_cost, savings

st.title("🔧 **Cloud Cost Optimization Using Genetic Algorithm**")

instances = load_instances()

st.sidebar.header("🛠️ Current Configuration")
current_cpu = st.sidebar.number_input("Current vCPUs", min_value=1, value=8)
current_memory = st.sidebar.number_input("Current Memory (GiB)", min_value=1, value=16)
current_instance_family = st.sidebar.text_input("Current Instance Family", "r3.large")

st.sidebar.header("📊 Utilization Data (N Days Avg)")
avg_cpu_utilization = st.sidebar.number_input("Avg CPU Utilization (%)", min_value=1, max_value=100, value=65)
avg_memory_utilization = st.sidebar.number_input("Avg Memory Utilization (%)", min_value=1, max_value=100, value=70)

required_vCPUs = int((avg_cpu_utilization / 100) * current_cpu)
required_memory_GiB = int((avg_memory_utilization / 100) * current_memory)

fig, ax = plt.subplots(1, 2, figsize=(10, 4))

ax[0].bar(["Current", "Required"], [current_cpu, required_vCPUs], color=["blue", "red"])
ax[0].set_title("CPU Utilization")
ax[0].set_ylabel("vCPUs")

ax[1].bar(["Current", "Required"], [current_memory, required_memory_GiB], color=["blue", "red"])
ax[1].set_title("Memory Utilization")
ax[1].set_ylabel("GiB")

st.pyplot(fig)

if st.button("⚡ Optimize Resources"):
    current_config = {current_instance_family: 1}
    avg_utilization = {"vCPUs": required_vCPUs, "memory_GiB": required_memory_GiB}

    decision, optimal_config, optimal_cost, savings = scaling_analysis(current_config, avg_utilization, instances)

    st.subheader("📊 Optimization Results")
    st.write(f"**🚀 Scaling Decision:** {decision}")
    st.write(f"**💰 Current Cost (USD/hour):** {calculate_cost(current_config, instances):.2f}")
    st.write(f"**🔍 Optimal Configuration:** {optimal_config}")
    st.write(f"**💰 Optimized Cost (USD/hour):** {optimal_cost:.2f}")
    st.write(f"**📉 Savings:** {savings:.2f} USD/hour")

    if savings > 0:
        st.success(f"🎉 You can save **${savings:.2f}/hour** by switching to the suggested configuration!")
    elif savings < 0:
        st.warning(f"⚠️ An upgrade is recommended, which will increase costs by **${-savings:.2f}/hour**.")
    else:
        st.info("✅ Your current configuration is already optimal!")

