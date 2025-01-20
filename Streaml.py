import streamlit as st
import json

# Load instance types
def load_instances():
    with open("tfamily.json", "r") as file:
        return json.load(file)

# Cost Calculation
def calculate_cost(configuration, instances):
    return sum(
        next(i["on_demand_hourly_price_usd"] for i in instances if i["instance_type"] == instance) * count
        for instance, count in configuration.items()
    )

# Scaling Decision Logic
def scaling_analysis(current_config, avg_utilization, instances):
    current_cost = calculate_cost(current_config, instances)
    
    required_vCPUs = avg_utilization["vCPUs"]
    required_memory = avg_utilization["memory_GiB"]

    # Find all valid configurations meeting the requirements
    valid_configs = [
        instance for instance in instances
        if instance["vCPUs"] >= required_vCPUs and instance["memory_GiB"] >= required_memory
    ]

    if not valid_configs:
        return "Upgrade", {}, 0, current_cost

    # Find the optimal configuration
    optimal_instance = min(valid_configs, key=lambda x: x["on_demand_hourly_price_usd"])
    optimal_config = {optimal_instance["instance_type"]: 1}
    optimal_cost = calculate_cost(optimal_config, instances)

    # Determine scaling decision
    if optimal_cost < current_cost:
        decision = "Downgrade"
    elif optimal_cost > current_cost:
        decision = "Upgrade"
    else:
        decision = "Optimal"

    savings = current_cost - optimal_cost
    return decision, optimal_config, optimal_cost, savings

# Streamlit UI
st.title("🔧 **Cloud Cost Optimization**")

instances = load_instances()

# Input Current Configuration
st.sidebar.header("🛠️ Current Configuration")
current_instance_type = st.sidebar.selectbox("Current Instance Type", [i["instance_type"] for i in instances])
current_instance_count = st.sidebar.number_input("Instance Count", min_value=1, value=1)

current_config = {current_instance_type: current_instance_count}

# Input Utilization Data
st.sidebar.header("📊 Utilization Data (N Days Avg)")
avg_cpu_utilization = st.sidebar.number_input("Avg CPU Utilization (%)", min_value=1, max_value=100, value=65)
avg_memory_utilization = st.sidebar.number_input("Avg Memory Utilization (%)", min_value=1, max_value=100, value=70)

# Retrieve instance details for current configuration
current_instance_details = next(i for i in instances if i["instance_type"] == current_instance_type)
total_vCPUs = current_instance_details["vCPUs"] * current_instance_count
total_memory = current_instance_details["memory_GiB"] * current_instance_count

# Calculate required resources
required_vCPUs = int((avg_cpu_utilization / 100) * total_vCPUs)
required_memory = int((avg_memory_utilization / 100) * total_memory)

# Run Optimization
if st.button("⚡ Optimize Resources"):
    avg_utilization = {"vCPUs": required_vCPUs, "memory_GiB": required_memory}
    
    decision, optimal_config, optimal_cost, savings = scaling_analysis(current_config, avg_utilization, instances)
    
    # Display Results
    st.subheader("📊 Optimization Results")
    st.write(f"**🚀 Scaling Decision:** {decision}")
    st.write(f"**💰 Current Cost (USD/hour):** {calculate_cost(current_config, instances):.2f}")
    st.write(f"**🔍 Optimal Configuration:** {optimal_config}")
    st.write(f"**💰 Optimized Cost (USD/hour):** {optimal_cost:.2f}")
    st.write(f"**📉 Savings:** {savings:.2f} USD/hour")

    if decision == "Downgrade":
        st.success(f"🎉 You can save **${savings:.2f}/hour** by switching to the suggested configuration!")
    elif decision == "Upgrade":
        st.warning(f"⚠️ An upgrade is recommended to meet your requirements, increasing costs by **${-savings:.2f}/hour**.")
    else:
        st.info("✅ Your current configuration is already optimal!")
