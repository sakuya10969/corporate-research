All agents must follow the rules below:

1. **Plan-First Execution**  
   Before performing any action, the agent must generate a clear and explicit plan.  
   The plan must outline the intended steps, the reasoning behind them, and any assumptions.  
   The agent may not execute the task until the plan is fully produced.

2. **Reference to `docs/`**  
   Whenever additional context, specifications, or definitions are required,  
   the agent must consult the relevant materials under the `docs/` directory.  
   Any referenced documents should be explicitly noted in the plan.

3. **Execution After Planning**  
   After producing the plan, the agent proceeds with execution.  
   Execution must follow the planned steps, and any deviations must be justified.
