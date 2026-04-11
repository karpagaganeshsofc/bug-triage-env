#!/usr/bin/env python3
"""
Baseline inference for the Bug Triage environment.

The LLM agent follows a multi-step investigation workflow:
  1. Sees a brief bug description
  2. Decides whether to investigate (logs/related/reporter) or triage
  3. Gathers information until confident, then submits classification

Uses mandatory [START] / [STEP] / [END] stdout markers.
Uses WebSocket (via openenv GenericEnvClient) for stateful multi-step episodes.
"""

import asyncio
import json
import os
import sys
import time

from openai import OpenAI
from openenv import GenericEnvClient

# ── Defaults ──────────────────────────────────────────────────────────
DEFAULT_ENV_URL = "https://karpagaganeshs-bug-triage-env.hf.space"

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
ENV_URL = os.getenv("ENV_URL", DEFAULT_ENV_URL)

llm_client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

# ── Prompt templates ──────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert software engineer triaging bug reports.

For each bug, you can:
1. INVESTIGATE to gather more information (costs budget)
2. TRIAGE to submit your classification

Investigation targets: "logs" (stack traces), "related" (similar past bugs), "reporter" (extra details from the reporter).

Be strategic: investigate only when uncertain. Wasted investigations lower your score.

You MUST respond with a valid JSON object. No other text."""

INVESTIGATE_OR_TRIAGE_PROMPT = """Bug {bug_index}/{bugs_total} — Task: {task_name}
Title: {title}
Description: {description}
Component: {component}
Reporter: {reporter_role}
Frequency: {frequency}

{investigation_info}

Budget: {budget_used}/{budget_total} investigations used.
Available investigations: {available}

{task_specific}

Decide: investigate for more info, or triage now?

If investigating, respond:
{{"action_type": "investigate", "investigate_target": "<logs|related|reporter>"}}

If triaging, respond:
{triage_format}"""

EASY_TRIAGE_FORMAT = '{"action_type": "triage", "bug_type": "<ui|backend|security>"}'
MEDIUM_TRIAGE_FORMAT = '{"action_type": "triage", "bug_type": "<ui|backend|security>", "severity": "<low|medium|high|critical>"}'
HARD_TRIAGE_FORMAT = '{"action_type": "triage", "bug_type": "<ui|backend|security>", "severity": "<low|medium|high|critical>", "fix_suggestion": "<concise fix recommendation>"}'

TASK_INSTRUCTIONS = {
    "easy": "EASY task: Classify bug_type only (ui/backend/security). Full info is shown — no investigation needed. Submit triage immediately.",
    "medium": "MEDIUM task: Classify bug_type AND severity. Investigate if uncertain, but be efficient — fewer investigations = higher score.",
    "hard": "HARD task: Classify bug_type, severity, AND provide a fix suggestion. Budget is very tight — investigate only the most informative targets.",
}

TRIAGE_FORMATS = {
    "easy": EASY_TRIAGE_FORMAT,
    "medium": MEDIUM_TRIAGE_FORMAT,
    "hard": HARD_TRIAGE_FORMAT,
}


# ── Helpers ───────────────────────────────────────────────────────────

def call_llm(messages: list, temperature: float = 0.2, retries: int = 3) -> str:
    """Call the LLM and return its text response, with retries for transient errors."""
    for attempt in range(retries):
        try:
            resp = llm_client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=temperature,
                max_tokens=300,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            if attempt < retries - 1 and ("429" in str(e) or "402" in str(e) or "503" in str(e)):
                wait = 2 ** (attempt + 1)
                print(f"[STEP] LLM rate limited, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


def parse_action(text: str) -> dict:
    """Extract a JSON action from LLM output, tolerating markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        raise


def build_investigation_info(investigations: list) -> str:
    """Format previously revealed investigation results."""
    if not investigations:
        return "No investigations done yet."
    lines = ["Previously investigated:"]
    for inv in investigations:
        target = inv.get("target", inv.get("investigate_target", "?"))
        content = inv.get("content", "")
        lines.append(f"  [{target.upper()}]: {content}")
    return "\n".join(lines)


def extract_obs(result) -> dict:
    """Extract observation dict from a StepResult."""
    obs = result.observation
    if hasattr(obs, "model_dump"):
        return obs.model_dump()
    if isinstance(obs, dict):
        return obs
    return dict(obs) if obs else {}


async def run_episode(env_url: str, task: str, seed: int | None = None) -> float:
    """Run one full episode over WebSocket and return the final score."""
    ws_url = env_url.replace("https://", "wss://").replace("http://", "ws://")

    env_client = GenericEnvClient(base_url=ws_url)
    async with env_client:
        # Reset
        kwargs = {"task": task}
        if seed is not None:
            kwargs["seed"] = seed
        result = await env_client.reset(**kwargs)
        obs = extract_obs(result)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        step_count = 0
        final_reward = 0.0
        episode_done = result.done if hasattr(result, "done") else False
        all_rewards = []

        while not episode_done:
            bug = obs.get("bug_report") or {}
            investigations = obs.get("investigations_done", [])
            available = obs.get("available_investigations", [])
            task_name = obs.get("task_name", task)
            bug_index = obs.get("current_bug_index", 0)
            bugs_total = obs.get("bugs_total", 0)
            budget_used = obs.get("investigations_used", 0)
            budget_total = obs.get("investigation_budget", 0)

            investigation_info = build_investigation_info(investigations)
            available_str = ", ".join(available) if available else "none (budget exhausted or all revealed)"

            user_prompt = INVESTIGATE_OR_TRIAGE_PROMPT.format(
                bug_index=bug_index,
                bugs_total=bugs_total,
                task_name=task_name,
                title=bug.get("title", "") if isinstance(bug, dict) else getattr(bug, "title", ""),
                description=bug.get("brief_description", "") if isinstance(bug, dict) else getattr(bug, "brief_description", ""),
                component=bug.get("affected_component", "") if isinstance(bug, dict) else getattr(bug, "affected_component", ""),
                reporter_role=bug.get("reporter_role", "") if isinstance(bug, dict) else getattr(bug, "reporter_role", ""),
                frequency=bug.get("frequency", "") if isinstance(bug, dict) else getattr(bug, "frequency", ""),
                investigation_info=investigation_info,
                budget_used=budget_used,
                budget_total=budget_total,
                available=available_str,
                task_specific=TASK_INSTRUCTIONS.get(task_name, ""),
                triage_format=TRIAGE_FORMATS.get(task_name, HARD_TRIAGE_FORMAT),
            )

            step_messages = messages + [{"role": "user", "content": user_prompt}]
            llm_response = call_llm(step_messages)

            try:
                action = parse_action(llm_response)
            except (json.JSONDecodeError, ValueError):
                action = {
                    "action_type": "triage",
                    "bug_type": "backend",
                    "severity": "medium",
                    "fix_suggestion": "Review the component for issues.",
                }

            if "action_type" not in action:
                action["action_type"] = "triage"

            error_str = "null"
            try:
                result = await env_client.step(action)
                obs = extract_obs(result)
                final_reward = result.reward if result.reward is not None else final_reward
                episode_done = result.done if hasattr(result, "done") else obs.get("done", False)
            except Exception as e:
                error_str = str(e)
                episode_done = False

            step_count += 1
            step_reward = float(obs.get("step_score", 0.0)) if error_str == "null" else 0.0
            all_rewards.append(step_reward)
            done_str = "true" if episode_done else "false"

            # Build action summary
            act_type = action.get("action_type", "unknown")
            if act_type == "investigate":
                act_summary = f"investigate {action.get('investigate_target', '?')}"
            else:
                parts = [action.get("bug_type", ""), action.get("severity", "")]
                act_summary = f"triage {' '.join(p for p in parts if p)}"

            print(f"[STEP] step={step_count} action={act_summary} reward={step_reward:.2f} done={done_str} error={error_str}")

            if step_count > 60:
                print("[STEP] step={} action=safety_stop reward=0.00 done=true error=null".format(step_count + 1))
                break

    final_reward = min(max(final_reward, 0.0), 1.0)
    all_rewards_str = ",".join(f"{r:.2f}" for r in all_rewards)
    return final_reward, step_count, all_rewards_str


# ── Main ──────────────────────────────────────────────────────────────

def main():
    tasks = ["easy", "medium", "hard"]

    for task in tasks:
        print(f"[START] task={task} env=bug_triage model={MODEL_NAME}")
        try:
            score, steps, rewards_str = asyncio.run(run_episode(ENV_URL, task, seed=42))
            print(f"[END] success=true steps={steps} rewards={rewards_str}")
        except Exception as e:
            print(f"[END] success=false steps=0 rewards=0.00 error={e}")


if __name__ == "__main__":
    main()
