"""Exercise the real direction pipeline; supplies inputs, never authored scenes."""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path("/home/ubuntu/repos/nexstudio/engine_sources/explainer-direction")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from explainer_direction.authoring import LocalOpenAIProvider, task_system_prompt  # noqa: E402
from explainer_direction.audio import KokoroLocalTTS  # noqa: E402
from explainer_direction.source_grounding import LocalEntailment  # noqa: E402
from make_film import run_pipeline  # noqa: E402


class LoggedLocalProvider(LocalOpenAIProvider):
    def __init__(self, path, model, replay=None, replay_through=None,
                 base_url="http://127.0.0.1:8788/v1", creative_model=None, creative_base_url=None):
        super().__init__(base_url, model,
                         timeout=3600, max_tokens=8000)
        self.directory = Path(path)
        self.directory.mkdir(exist_ok=False)
        self.counter = 0
        self.replay = Path(replay) if replay else None
        self.replay_through = replay_through
        self.creative = (LocalOpenAIProvider(creative_base_url, creative_model,
                                            timeout=3600, max_tokens=3000)
                         if creative_model is not None else None)
        if self.creative is not None:
            self.directory.joinpath("model-policy.json").write_text(json.dumps({
                "primary": self.identity,
                "creative": {**self.creative.identity,
                             "inference_source": json.loads((self.directory.parent / "live_context.json").read_text())["inference_source"]},
                "policy": "Primary authors meaning and concepts; delegate authors outline, scenes and choreography. Explicit local development routing, same contracts and source vetoes. No fixture or automatic fallback.",
            }, indent=2))

    def complete(self, task, request):
        actual = request.get("original_task", task) if task == "repair" else task
        backend = (self.creative if self.creative is not None and actual not in (
            "plan_meaning_entities", "plan_meaning_relations", "review_meaning",
            "plan_strategies", "select_strategy",
        ) else self)
        self.counter += 1
        prefix = self.directory / f"{self.counter:02d}-{task}"
        prefix.with_suffix(".request.json").write_text(json.dumps(request, indent=2))
        print(f"AUTHOR {self.counter}: {task}", flush=True)
        started = time.monotonic()
        try:
            replay_prefix = self.replay / prefix.name if self.replay else None
            if self.replay_through is not None and self.counter > self.replay_through:
                replay_prefix = None
            replay_response = replay_prefix.with_suffix(".response.json") if replay_prefix else None
            if replay_prefix is not None and replay_response is not None and replay_response.exists():
                old_request = json.loads(replay_prefix.with_suffix(".request.json").read_text())
                old_transport = json.loads(replay_prefix.with_suffix(".transport.json").read_text())
                transported = deepcopy(request)
                schema = transported.pop("response_schema")
                transported.pop("score_schema", None)
                transported = {"response_schema": schema, **transported}
                recorded_task = json.loads(old_transport["messages"][-1]["content"])
                recorded_input = deepcopy(recorded_task["request"])
                recorded_input.pop("response_schema")
                current_input = deepcopy(transported)
                current_input.pop("response_schema")
                if (old_request != request or old_transport["model"] != backend.model
                        or old_transport["messages"][0]["content"] != task_system_prompt(task, request)
                        or old_transport["max_tokens"] != backend.max_tokens
                        or old_transport["temperature"] != .35
                        or recorded_task["task"] != task or recorded_input != current_input
                        or (old_transport["response_format"]["type"] == "json_schema"
                            and old_transport["response_format"]["json_schema"]["schema"] != schema)):
                    raise ValueError("cached inference does not match exact request and model")
                response = json.loads(replay_response.read_text())
                self.last_request_id = None
                self.last_request_payload = old_transport
                prefix.with_suffix(".cache.json").write_text(json.dumps({
                    "recorded_response": str(replay_response),
                    "sha256": hashlib.sha256(replay_response.read_bytes()).hexdigest(),
                    "scope": "previous model-authored decision for identical task/request/model, revalidated now; no author-edited scene",
                    "original_response_format": old_transport["response_format"]["type"],
                    "same_system_prompt": old_transport["messages"][0]["content"] == task_system_prompt(task, request),
                    "original_system_prompt_sha256": hashlib.sha256(old_transport["messages"][0]["content"].encode()).hexdigest(),
                    "current_system_prompt_sha256": hashlib.sha256(task_system_prompt(task, request).encode()).hexdigest(),
                }, indent=2))
            else:
                response = (super().complete(task, request) if backend is self
                            else backend.complete(task, request))
                if backend is not self:
                    self.last_request_id = backend.last_request_id
                    self.last_request_payload = deepcopy(backend.last_request_payload)
        except Exception as exc:
            prefix.with_suffix(".error.json").write_text(json.dumps({
                "error": str(exc), "seconds": time.monotonic() - started
            }, indent=2))
            raise
        prefix.with_suffix(".response.json").write_text(json.dumps(response, indent=2))
        prefix.with_suffix(".transport.json").write_text(json.dumps(self.last_request_payload, indent=2))
        prefix.with_suffix(".meta.json").write_text(json.dumps({
            "provider": backend.identity, "request_id": self.last_request_id,
            "seconds": time.monotonic() - started,
        }, indent=2))
        print(f"AUTHOR {self.counter}: complete in {time.monotonic()-started:.1f}s", flush=True)
        return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="pumped-short-v1")
    parser.add_argument("--model", default="qwen3-4b-instruct-2507")
    parser.add_argument("--base-url", default="http://127.0.0.1:8788/v1")
    parser.add_argument("--creative-model")
    parser.add_argument("--creative-base-url")
    parser.add_argument("--film-id")
    parser.add_argument("--replay-dir")
    parser.add_argument("--replay-through", type=int)
    parser.add_argument("--concept-first", action="store_true")
    parser.add_argument("--compact", action="store_true",
                        help="Source-bound compact direction; lower mechanics after measured Liam voice")
    parser.add_argument("--source-quote-narration", action="store_true",
                        help="Speak the supplied evidence sentences in explicit compact development preflight")
    parser.add_argument("--context", default="live_context.json")
    parser.add_argument("--evidence", default="pumped_evidence.json")
    parser.add_argument("--family", default="ocean")
    parser.add_argument("--brief", default=(
        "Explain how pumped storage works as a water battery. Show electricity "
        "moving water uphill during charging, then water moving downhill through "
        "a turbine to generate electricity during discharge. Use only supplied "
        "Department of Energy evidence. Produce an original short, rich graphical "
        "explainer, not a static card deck. Target twenty seconds of narration."
    ))
    parser.add_argument("--proof", choices=["short", "full"], default="short")
    parser.add_argument("--max-repairs", type=int, default=2)
    args = parser.parse_args()
    if bool(args.creative_model) != bool(args.creative_base_url):
        parser.error("--creative-model and --creative-base-url must be supplied together")
    os.environ["OMP_NUM_THREADS"] = "4"
    os.environ["MKL_NUM_THREADS"] = "4"
    base = Path("/home/ubuntu/vid_study/explainer_direction")
    manifest = run_pipeline(
        output=base / args.name,
        brief=args.brief,
        evidence=json.loads((base / args.evidence).read_text()),
        family=args.family,
        context=json.loads((base / args.context).read_text()),
        film_id=args.film_id or args.name.replace("-", "_"),
        aspects=["16:9", "9:16", "1:1"],
        provider=LoggedLocalProvider(base / f"{args.name}-requests", args.model, args.replay_dir,
                                     args.replay_through, base_url=args.base_url,
                                     creative_model=args.creative_model, creative_base_url=args.creative_base_url),
        voice_provider=KokoroLocalTTS(json.loads((base / "kokoro_liam.json").read_text())),
        fps=30, workers=2, proof=args.proof, staged=not args.compact, compact=args.compact,
        concept_first=args.concept_first, source_quote_narration=args.source_quote_narration,
        max_repairs=args.max_repairs, source_judge=LocalEntailment(),
    )
    print(json.dumps({"status": manifest["status"], "manifest": str(base / args.name / "manifest.json")}), flush=True)


if __name__ == "__main__":
    main()
