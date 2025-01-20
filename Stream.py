import streamlit as st
import json
import random
import matplotlib.pyplot as plt

def load_instances():
    with open("tfamily.json", "r") as file:
        return json.load(file)

def fitness(solution, instances, required_vCPUs, required_memory_GiB):
    total_vCPUs, total_memory, total_cost = 0, 0, 0
    for instance, count in solution.items():
        instance_data = next(i for i in instances if i["instance_type"] == instance)
        total_vCPUs += instance_data["vCPUs"] * count
        total_memory += instance_data["memory_GiB"] * count
        total_cost += instance_data["on_demand_hourly_price_usd"] * count

    if total_vCPUs < required_vCPUs or total_memory < required_memory_GiB:
        return 0  

    return (1 / total_cost) * (total_vCPUs / required_vCPUs) * (total_memory / required_memory_GiB)

def generate_solution(instances):
    return {instance["instance_type"]: random.randint(0, 2) for instance in instances} 

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
    best_config = max(population, key=lambda x: fitness(x, instances, required_vCPUs, required_memory_GiB))

    total_vCPUs = sum(next(i["vCPUs"] for i in instances if i["instance_type"] == instance) * count
                      for instance, count in best_config.items())
    total_memory = sum(next(i["memory_GiB"] for i in instances if i["instance_type"] == instance) * count
                       for instance, count in best_config.items())

    if total_vCPUs < required_vCPUs or total_memory < required_memory_GiB:
        return None  

    return best_config

def calculate_cost(configuration, instances):
    return sum(next(i["on_demand_hourly_price_usd"] for i in instances if i["instance_type"] == instance) * count
               for instance, count in configuration.items())

def scaling_analysis(current_config, avg_utilization, instances):
    current_cost = calculate_cost(current_config, instances)
    optimal_config = genetic_algorithm(instances, avg_utilization["vCPUs"], avg_utilization["memory_GiB"])

    if not optimal_config:
        return "Upgrade", None, current_cost, 0  

    optimal_cost = calculate_cost(optimal_config, instances)
    savings = current_cost - optimal_cost

    utilization_threshold = 80  

    if optimal_cost > current_cost:
        decision = "Upgrade"
    elif savings > 5 and avg_utilization["vCPUs"] < utilization_threshold and avg_utilization["memory_GiB"] < utilization_threshold:
        decision = "Downgrade"
    else:
        decision = "Optimal"

    # Filter out instances with 0 quantity
    optimal_config_filtered = {instance: count for instance, count in optimal_config.items() if count > 0}

    return decision, optimal_config_filtered, optimal_cost, savings

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

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(["Current", "Optimized"], [current_cpu, required_vCPUs], marker='o', linestyle='-', label="vCPUs")
ax.plot(["Current", "Optimized"], [current_memory, required_memory_GiB], marker='o', linestyle='-', label="Memory (GiB)")
ax.set_xlabel("Configuration")
ax.set_ylabel("Resources")
ax.set_title("Current vs Optimized Resource Allocation")
ax.legend()
st.pyplot(fig)

if st.button("⚡ Optimize Resources"):
    current_config = {current_instance_family: 1}
    avg_utilization = {"vCPUs": required_vCPUs, "memory_GiB": required_memory_GiB}

    decision, optimal_config, optimal_cost, savings = scaling_analysis(current_config, avg_utilization, instances)

    st.subheader("📊 Optimization Results")
    st.write(f"**🚀 Scaling Decision:** {decision}")
    st.write(f"**💰 Current Cost (USD/hour):** {calculate_cost(current_config, instances):.2f}")
    if optimal_config:
        st.write(f"**🔍 Optimal Configuration:** {optimal_config}")
        st.write(f"**💰 Optimized Cost (USD/hour):** {optimal_cost:.2f}")
        st.write(f"**📉 Savings:** {savings:.2f} USD/hour")

        if decision == "Downgrade":
            st.success(f"🎉 You can save **${savings:.2f}/hour** by switching to the suggested configuration!")
        elif decision == "Upgrade":
            st.warning(f"⚠️ An upgrade is recommended due to high resource utilization.")
        else:
            st.info("✅ Your current configuration is already optimal!")
    else:
        st.error("⚠️ No valid optimization found. Consider upgrading resources.")
