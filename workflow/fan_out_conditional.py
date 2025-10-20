# Copyright (c) Microsoft. All rights reserved.

"""
Conditional Fan-Out/Fan-In Workflow Example

This module demonstrates a workflow pattern combining:

1. **Input Validation (Conditional Edge)**:
   - Checkpoint receives a number as input
   - A conditional edge checks if the number is <= 10
   - If valid: proceeds to fan-out; if invalid: workflow halts silently

2. **Dynamic Fan-Out**:
   - Splitter receives the validated number
   - Creates N worker executors dynamically, where N equals the input number
   - Each worker gets a unique ID (worker_00, worker_01, etc.)
   - All workers receive the same input number and process in parallel

3. **Parallel Processing**:
   - Each worker simulates random work:
     * Sleeps for 100-500ms (simulating I/O or computation)
     * Multiplies the input by a random factor (1-5)
     * Adds random noise (0-10)
   - Workers track their input, output, and processing time

4. **Fan-In Aggregation**:
   - Aggregator collects all worker results
   - Generates a formatted summary table showing:
     * Each worker's ID
     * Input value received
     * Output value produced
     * Processing time taken
     * Total combined output across all workers

5. **Event-Driven Monitoring**:
   - Custom colored events provide real-time visibility:
     * Blue: Checkpoint receipt
     * Cyan: Splitter fan-out initiation
     * Yellow: Worker start/completion with timings
     * Green: Aggregator completion
   - ANSI color codes for enhanced terminal output clarity

Example flows:
- Input 8: Passes validation → 8 workers created → 8 results aggregated
- Input 12: Fails validation (> 10) → Workflow halts
- Input 5: Passes validation → 5 workers created → 5 results aggregated
"""

import asyncio
import random
import time
from typing import Literal

from agent_framework import (
    Executor,
    WorkflowBuilder,
    WorkflowContext,
    WorkflowOutputEvent,
    ExecutorInvokedEvent,
    ExecutorCompletedEvent,
    WorkflowEvent,
    handler,
)
from typing_extensions import Never
from pydantic import BaseModel

# ===========================
# ANSI Color Codes
# ===========================
class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright/Light colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    
    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    
    @staticmethod
    def colored(text: str, color: str) -> str:
        """Apply color to text."""
        return f"{color}{text}{Colors.RESET}"


# ===========================
# Data Models
# ===========================
class WorkerResult(BaseModel):
    """Result from a worker executor."""
    worker_id: str
    input_value: int
    output_value: int
    processing_time: float


class ValidationResult(BaseModel):
    """Result from the validator executor."""
    input_number: int
    is_valid: bool
    reason: str


# ===========================
# Executors
# ===========================
class CheckpointExecutor(Executor):
    """Entry point that receives and passes through the input number."""

    @handler
    async def process(
        self, number: int, ctx: WorkflowContext[int]
    ) -> None:
        """Pass through the number; conditional edge handles the validation."""
        await ctx.add_event(
            _create_info_event(
                f"📋 Checkpoint received: {Colors.colored(str(number), Colors.BRIGHT_BLUE)}"
            )
        )
        await ctx.send_message(number)


class SplitterExecutor(Executor):
    """Splits the input number and dispatches it to multiple workers."""

    @handler
    async def split(
        self, number: int, ctx: WorkflowContext[int]
    ) -> None:
        """Send the number to all worker executors."""
        await ctx.add_event(
            _create_info_event(
                f"📤 Splitting into {Colors.colored(str(number), Colors.BRIGHT_CYAN)} parallel workers..."
            )
        )
        # Send to all workers
        await ctx.send_message(number)


class WorkerExecutor(Executor):
    """Simulates random work processing."""

    @handler
    async def process(
        self, number: int, ctx: WorkflowContext[WorkerResult]
    ) -> None:
        """Simulate work: multiply by a random factor and simulate delay."""
        worker_id = self.id
        start_time = time.time()
        
        # Simulate random processing time (100-500ms)
        await ctx.add_event(
            _create_info_event(
                f"⚙️  Worker {Colors.colored(worker_id, Colors.BRIGHT_YELLOW)} started processing input: {Colors.colored(str(number), Colors.BRIGHT_BLUE)}"
            )
        )
        
        processing_delay = random.uniform(0.1, 0.5)
        await asyncio.sleep(processing_delay)
        
        # Simulate random work: multiply by random factor and add random noise
        output = number * random.randint(1, 5) + random.randint(0, 10)
        
        processing_time = time.time() - start_time
        result = WorkerResult(
            worker_id=worker_id,
            input_value=number,
            output_value=output,
            processing_time=round(processing_time, 3),
        )
        
        await ctx.add_event(
            _create_success_event(
                f"✓ Worker {Colors.colored(worker_id, Colors.BRIGHT_YELLOW)} completed: "
                f"input={Colors.colored(str(number), Colors.BRIGHT_BLUE)}, "
                f"output={Colors.colored(str(output), Colors.BRIGHT_GREEN)}, "
                f"time={Colors.colored(f'{processing_time:.3f}s', Colors.BRIGHT_MAGENTA)}"
            )
        )
        
        await ctx.send_message(result)


class AggregatorExecutor(Executor):
    """Aggregates results from all workers."""

    @handler
    async def aggregate(
        self, results: list[WorkerResult], ctx: WorkflowContext[Never, str]
    ) -> None:
        """Collect and concatenate results from all workers."""
        await ctx.add_event(
            _create_info_event(
                f"🔄 Fan-in: Aggregating {Colors.colored(str(len(results)), Colors.BRIGHT_CYAN)} worker results..."
            )
        )
        
        # Build output summary
        output_lines = [
            Colors.colored("=" * 80, Colors.BOLD),
            Colors.colored("📊 WORKFLOW RESULTS SUMMARY", Colors.BOLD + Colors.BRIGHT_GREEN),
            Colors.colored("=" * 80, Colors.BOLD),
        ]
        
        total_output = 0
        for result in results:
            output_lines.append(
                f"  {Colors.colored(result.worker_id, Colors.BRIGHT_YELLOW)}: "
                f"input={Colors.colored(str(result.input_value), Colors.BRIGHT_BLUE)} → "
                f"output={Colors.colored(str(result.output_value), Colors.BRIGHT_GREEN)} "
                f"({Colors.colored(f'{result.processing_time}s', Colors.BRIGHT_MAGENTA)})"
            )
            total_output += result.output_value
        
        output_lines.extend([
            Colors.colored("-" * 80, Colors.BOLD),
            f"  Total combined output: {Colors.colored(str(total_output), Colors.BOLD + Colors.BRIGHT_GREEN)}",
            Colors.colored("=" * 80, Colors.BOLD),
        ])
        
        final_output = "\n".join(output_lines)
        
        await ctx.add_event(
            _create_success_event("✓ Aggregation complete. Yielding final output.")
        )
        
        await ctx.yield_output(final_output)


# ===========================
# Custom Event Helper
# ===========================
class CustomInfoEvent(WorkflowEvent):
    """Custom event for informational messages."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
        self.event_type = "info"


class CustomSuccessEvent(WorkflowEvent):
    """Custom event for success messages."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
        self.event_type = "success"


class CustomErrorEvent(WorkflowEvent):
    """Custom event for error messages."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
        self.event_type = "error"


def _create_info_event(message: str) -> CustomInfoEvent:
    """Create an info event."""
    return CustomInfoEvent(message)


def _create_success_event(message: str) -> CustomSuccessEvent:
    """Create a success event."""
    return CustomSuccessEvent(message)


def _create_error_event(message: str) -> CustomErrorEvent:
    """Create an error event."""
    return CustomErrorEvent(message)


# ===========================
# Workflow Builder
# ===========================
def create_conditional_fan_out_workflow(num_workers: int = 5):
    """
    Create a workflow with:
    1. Validator: Checks if input <= 10 (conditional edge)
    2. Splitter: Dispatches to N workers
    3. Workers: Process in parallel (fan-out)
    4. Aggregator: Collects and concatenates results (fan-in)
    """
    # Create executors
    checkpoint = CheckpointExecutor(id="checkpoint")
    splitter = SplitterExecutor(id="splitter")
    
    # Dynamically create workers
    workers = [
        WorkerExecutor(id=f"worker_{i:02d}")
        for i in range(num_workers)
    ]
    
    aggregator = AggregatorExecutor(id="aggregator")
    
    # Build workflow
    builder = WorkflowBuilder()
    
    # Set checkpoint as start
    builder.set_start_executor(checkpoint)
    
    # Conditional edge: only proceed if number <= 10
    builder.add_edge(
        checkpoint,
        splitter,
        condition=lambda msg: isinstance(msg, int) and msg <= 10,
    )
    
    # Fan-out: splitter sends to all workers
    builder.add_fan_out_edges(splitter, workers)
    
    # Fan-in: all workers feed into aggregator
    builder.add_fan_in_edges(workers, aggregator)
    
    workflow = builder.build()
    
    return workflow


# ===========================
# Event Printer with Colors
# ===========================
async def print_event_with_colors(event):
    """Print workflow events with colored output."""
    if isinstance(event, ExecutorInvokedEvent):
        print(
            Colors.colored(
                f"  → Executor invoked: {event.executor_id}",
                Colors.CYAN
            )
        )
    elif isinstance(event, ExecutorCompletedEvent):
        print(
            Colors.colored(
                f"  ← Executor completed: {event.executor_id}",
                Colors.GREEN
            )
        )
    elif isinstance(event, WorkflowOutputEvent):
        print(
            Colors.colored(
                f"✓ Workflow output received:",
                Colors.BOLD + Colors.BRIGHT_GREEN
            )
        )
    elif isinstance(event, CustomInfoEvent):
        print(f"  ℹ️  {event.message}")
    elif isinstance(event, CustomSuccessEvent):
        print(f"  {event.message}")
    elif isinstance(event, CustomErrorEvent):
        print(f"  {event.message}")
    else:
        print(f"  Event: {event}")


# ===========================
# Main Execution
# ===========================
async def main():
    """Run the workflow with colored event output."""
    print(
        Colors.colored(
            "\n" + "=" * 80,
            Colors.BOLD + Colors.BRIGHT_CYAN
        )
    )
    print(
        Colors.colored(
            "CONDITIONAL FAN-OUT/FAN-IN WORKFLOW",
            Colors.BOLD + Colors.BRIGHT_CYAN
        )
    )
    print(
        Colors.colored(
            "=" * 80 + "\n",
            Colors.BOLD + Colors.BRIGHT_CYAN
        )
    )
    
    # Test cases
    test_cases = [8, 12, 5]  # 8 and 5 pass validation, 12 fails
    
    for test_input in test_cases:
        # Create workflow with N workers where N = input number
        workflow = create_conditional_fan_out_workflow(test_input)
        
        print(
            Colors.colored(
                f"\n🚀 Running workflow with input: {test_input}",
                Colors.BOLD + Colors.BRIGHT_YELLOW
            )
        )
        print(
            Colors.colored(
                "-" * 80,
                Colors.BOLD
            )
        )
        
        output: str | None = None
        async for event in workflow.run_stream(test_input):
            await print_event_with_colors(event)
            if isinstance(event, WorkflowOutputEvent):
                output = event.data
        
        if output:
            print("\n" + output)
        
        print()


if __name__ == "__main__":
    asyncio.run(main())
