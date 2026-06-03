# 06-f — LLMs in the Loop

A large language model (GPT-4o, Claude, Gemini, Llama 3) used as a
**planner or task decomposer**, **not** as a motor controller.

The LLM translates "tidy the table" into a sequence of perception +
motion primitives your robot already knows how to execute.

## Common use cases

- **Long-horizon natural-language tasks** — "make me a coffee", "pack
  this order".
- **Orchestrating a library of pretested skills** the robot already
  has.
- **Operator interfaces** — a human types or speaks; the LLM emits
  the plan.
- **Failure recovery** — the LLM re-plans when a perception or motion
  step returns an error.
- **Generating new skills as code** at design time (not run time).

You **don't** want an LLM when:

- The task is one fixed sequence. Hard-code it.
- Latency under 100 ms matters. LLMs are too slow.
- Reliability matters and you can't constrain the output. LLMs
  hallucinate.

## Frameworks / libraries / methods

### LLM choice

| Model | Best for |
|-------|----------|
| **GPT-4o, GPT-4.1, o-series (OpenAI)** | Strong tool-use, JSON-mode output. |
| **Claude (Sonnet, Opus)** (Anthropic) | Long context, careful reasoning. |
| **Gemini 2.x** (Google) | Multimodal vision input. |
| **Llama 3.x, Qwen 2.x, Mistral** | Local / on-prem deployment. |

### Patterns for grounding the LLM

The LLM doesn't know your robot. You bridge the two with one of:

- **Code-as-Policies (Google)** — the LLM writes Python that calls
  your perception and motion APIs. The "callable surface" of the
  robot becomes the LLM's vocabulary.
- **SayCan (Google)** — the LLM proposes actions; an "affordance"
  model scores how feasible each is on the current robot.
- **Inner Monologue** — the LLM re-plans based on textual feedback
  ("the gripper is empty"; "the cup is now in hand").
- **ProgPrompt** — pseudo-code prompting; LLM emits structured
  programs.
- **ReAct (general LLM pattern)** — interleave reasoning steps and
  tool calls.

### Frameworks that wrap this up

- **LangChain, LlamaIndex** — generic LLM tooling. Heavy, but you
  can pull just the pieces you need.
- **OpenAI Function Calling / Anthropic Tool Use** — native
  structured tool calls; usually simpler than a framework.
- **ROS-LLM bridges** — community packages exposing ROS 2 services
  as LLM tools (e.g. `rosa`, `rosgpt`).

### Speech / multimodal frontends

- **Whisper, Whisper-large-v3** — speech-to-text for voice prompts.
- **GPT-4o, Gemini, Claude Sonnet** — vision-language input directly.
- **VAD + interruption handling** — Silero VAD, LiveKit Agents.

### Local-LLM serving

- **vLLM** — the production default for serving open-weight LLMs on
  a local GPU.
- **llama.cpp, Ollama** — easy, lightweight serving.
- **ExLlamaV2, MLC-LLM** — quantised, fast inference for edge boxes.

## How to pick

1. **One human operator, voice or chat input?** → GPT-4o or Claude
   Sonnet + Function Calling, with your robot's perception and
   motion skills as tools.
2. **On-prem / air-gapped factory?** → Llama 3 or Qwen, served via
   vLLM on a local GPU.
3. **Heavy vision-grounded planning?** → Gemini 2.x for multimodal
   input.
4. **Research on grounding patterns?** → Code-as-Policies + SayCan +
   Inner Monologue, mix-and-match.

## Where it runs

- **Cloud APIs** — easiest, fastest to set up, monthly bill.
- **Local vLLM on a workstation** — Llama 3 70B or smaller; needed
  for air-gapped factories.
- **Jetson Orin (small models)** — Llama 3 8B at INT4 is viable for
  outer-loop planning.

LLMs in the **outer loop** at ≥1 s cadence. Never in the inner
control loop. Pair them with a fast lower layer (MoveIt, a VLA, a
scripted skill library).

## Common mistakes

1. **LLM in the inner loop.** A 2 s round-trip to the cloud is fine
   for "what should I do next"; it's fatal for "stop the gripper
   now."
2. **Unconstrained outputs.** Always use Function Calling / JSON mode
   so the LLM's output is parseable.
3. **No verifier.** The LLM proposes a wrong plan; nobody checks.
   Always validate the plan against feasibility before executing.
4. **Cloud LLM in a regulated environment.** Data-residency policies
   forbid it. Use a local model or check policy first.
5. **No timeout / retry policy.** Network blips break the loop. Cache
   recent plans and have a fallback skill.

## What's next

Every model so far depends on a dataset and a pretrained checkpoint.
Where do those come from?

→ Next: [06-g-datasets-and-pretraining.md](06-g-datasets-and-pretraining.md)

← Back to: [Layer 3, AI overview](06-ai-and-foundation-models.md)
