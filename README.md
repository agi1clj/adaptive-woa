# DAG Task Allocation and Optimization

This repository contains two main Python files located in the `src` directory:

## 1. dag.py

This file (`src/dag.py`) generates a Directed Acyclic Graph (DAG) representing a task allocation architecture. The DAG is created using the NetworkX library, and the resulting graph is visualized using Pyvis. The script randomly assigns attributes to tasks such as type (EdgeTask, FogTask, CloudTask), region, provider, data volume, computational requirements, latency, bandwidth, and energy consumption. The generated DAG is saved as both an interactive HTML visualization (`docs/dag.html`) and a JSON file (`docs/dag_model.json`).

## 2. woa_task_shifting.py

The file (`src/woa_task_shifting.py`) implements a multi-objective optimization problem for task shifting using the Whale Optimization Algorithm (WOA) from the `mealpy` library. The optimization problem considers objectives related to minimizing energy consumption, latency, and data volume. The best solution and fitness information are logged, and various charts depicting the algorithm's performance are saved in the `docs/algo` directory.

### Example of an output for the best sequence of task execution
```
2024/01/25 09:31:42 AM, INFO, __main__: Best solution: {'per_var': [8, 12, 10, 16, 9, 18, 7, 19, 11, 3, 1, 15, 0, 4, 17, 6, 14, 13, 2, 5]} 
2024/01/25 09:31:42 AM, INFO, __main__: Best fitness: 366.1046438740182
```

## Running the Optimization

To execute the task shifting optimization, run the `woa_task_shifting.py` script. The optimized solution, along with fitness information, will be displayed in the console. Additionally, charts illustrating the optimization process will be saved in the `docs/algo` directory.

Please make sure to install the required dependencies using:

```bash
pip install networkx pyvis mealpy numpy
