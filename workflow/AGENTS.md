
# 🧩 Agent Framework – Workflows Overview

### 🔹 Executors

Fundamental building blocks that process messages.

* Receive typed messages → produce output messages & events
* Inherit from `Executor` class
* Have:

  * Unique `id`
  * `@handler`-decorated methods to handle messages

#### Example (class-based)

```python
from agent_framework import Executor, WorkflowContext, handler

class UpperCase(Executor):

    @handler
    async def to_upper_case(self, text: str, ctx: WorkflowContext[str]) -> None:
        """Convert input to uppercase and forward it."""
        await ctx.send_message(text.upper())
```

#### Example (function-based)

```python
from agent_framework import WorkflowContext, executor

@executor(id="upper_case_executor")
async def upper_case(text: str, ctx: WorkflowContext[str]) -> None:
    await ctx.send_message(text.upper())
```

* Multiple handlers can exist in one executor (based on input types)

---

### 🔹 WorkflowContext

Provides interaction between handlers and the workflow.

* `ctx.send_message()` → sends to next executor
* `ctx.yield_output()` → yields workflow output (to caller)

---

### 🔹 Edges

Define how messages flow between executors.

Types:

* **Direct edges**
* **Conditional edges**
* **Switch-case edges**
* **Fan-out edges**
* **Fan-in edges**

#### Direct edge

```python
from agent_framework import WorkflowBuilder

builder = WorkflowBuilder()
builder.add_edge(source_executor, target_executor)
builder.set_start_executor(source_executor)
workflow = builder.build()
```

#### Conditional edge

```python
builder.add_edge(
    spam_detector,
    email_processor,
    condition=lambda r: isinstance(r, SpamResult) and not r.is_spam
)
builder.add_edge(
    spam_detector,
    spam_handler,
    condition=lambda r: isinstance(r, SpamResult) and r.is_spam
)
```

#### Switch-case edges

```python
from agent_framework import Case, Default, WorkflowBuilder

builder.add_switch_case_edge_group(
    router_executor,
    [
        Case(condition=lambda msg: msg.priority < Priority.NORMAL, target=executor_a),
        Case(condition=lambda msg: msg.priority < Priority.HIGH, target=executor_b),
        Default(target=executor_c),
    ],
)
```

#### Fan-out edges

```python
builder.add_fan_out_edges(splitter_executor, [worker1, worker2, worker3])
```

**Custom selection:**

```python
builder.add_fan_out_edges(
    splitter_executor,
    [worker1, worker2, worker3],
    selection_func=lambda msg, target_ids: (
        [0] if msg.priority == Priority.HIGH else [1, 2]
    )
)
```

#### Fan-in edge

```python
builder.add_fan_in_edge([worker1, worker2, worker3], aggregator_executor)
```

---

### 🔹 Workflows

Tie everything together using `WorkflowBuilder`.

```python
from agent_framework import WorkflowBuilder

processor = DataProcessor()
validator = Validator()
formatter = Formatter()

builder = WorkflowBuilder()
builder.set_start_executor(processor)
builder.add_edge(processor, validator)
builder.add_edge(validator, formatter)
workflow = builder.build()
```

---

### 🔹 Execution

Run workflows synchronously or via stream.

**Streaming (async events):**

```python
from agent_framework import WorkflowCompletedEvent

async for event in workflow.run_stream(input_message):
    if isinstance(event, WorkflowCompletedEvent):
        print(f"Workflow completed: {event.data}")
```

**Non-streaming:**

```python
events = await workflow.run(input_message)
print(events.get_completed_event())
```

---

### 🔹 Execution Model: Pregel

* Origin: Google (also used in AutoGen)
* Each executor = vertex (node) in a graph
* Nodes exchange messages via edges
* Runs in **supersteps**:

  1. Nodes read messages from last round
  2. Perform work
  3. Send messages for next round
  4. Wait for all nodes → repeat until no messages left

---

### 🔹 Events

Capture runtime info when streaming workflows.

Common events:

```python
from agent_framework import (
    ExecutorInvokeEvent,
    ExecutorCompleteEvent,
    WorkflowOutputEvent,
    WorkflowErrorEvent,
)

async for event in workflow.run_stream(input_message):
    match event:
        case ExecutorInvokeEvent() as e:
            print(f"Starting {e.executor_id}")
        case ExecutorCompleteEvent() as e:
            print(f"Completed {e.executor_id}: {e.data}")
        case WorkflowOutputEvent() as e:
            print(f"Output: {e.data}")
        case WorkflowErrorEvent() as e:
            print(f"Error: {e.exception}")
```

---

### 🔹 Custom Events

```python
from agent_framework import handler, Executor, WorkflowContext, WorkflowEvent

class CustomEvent(WorkflowEvent):
    def __init__(self, message: str):
        super().__init__(message)

class CustomExecutor(Executor):
    @handler
    async def handle(self, message: str, ctx: WorkflowContext[str]) -> None:
        await ctx.add_event(CustomEvent(f"Processing message: {message}"))
```

---

Would you like me to add a **visual diagram (Mermaid)** summarizing the data flow (executors → edges → workflow)? It makes it clearer for documentation or slide decks.
