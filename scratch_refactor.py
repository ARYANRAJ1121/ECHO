import re

with open('run_simulation.py', 'r') as file:
    content = file.read()

# Make market_ctx required for all builders
content = re.sub(r'def build_llm_simulation\(n_rounds: int, market_ctx=None\)', 'def build_llm_simulation(n_rounds: int, market_ctx)', content)
content = re.sub(r'def build_rag_simulation\(n_rounds: int, sim_id: int, market_ctx=None\)', 'def build_rag_simulation(n_rounds: int, sim_id: int, market_ctx)', content)
content = re.sub(r'def build_dummy_simulation\(n_rounds: int, market_ctx=None\)', 'def build_dummy_simulation(n_rounds: int, market_ctx)', content)
content = re.sub(r'def build_rl_simulation\(n_rounds: int, market_ctx=None\)', 'def build_rl_simulation(n_rounds: int, market_ctx)', content)
content = re.sub(r'def build_dqn_simulation\(n_rounds: int, market_ctx=None\)', 'def build_dqn_simulation(n_rounds: int, market_ctx)', content)

# Instead of complex regex for removing the if/else blocks, let's just make the fallback blocks unreachable and delete them cleanly.
content = content.replace('if market_ctx:', 'if True:  # Always True now since market_ctx is required')

with open('run_simulation.py', 'w') as file:
    file.write(content)
