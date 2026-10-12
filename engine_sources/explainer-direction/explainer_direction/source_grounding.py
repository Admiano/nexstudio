"""Independent, conservative development preflight for proposed meaning facts.

Entailment is a rejection signal, not factual certification: NLI alone can
confidently accept unsupported causal or storage claims.
"""

from __future__ import annotations

import re
from typing import Any

from .contracts import ScoreError

MODEL = "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli"
REVISION = "b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7"


class LocalEntailment:
    def __init__(self):
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError("local meaning preflight needs torch, transformers and sentencepiece") from exc
        torch.set_num_threads(2)
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            MODEL, revision=REVISION, use_safetensors=True,
        ).eval()
        self.identity = {"model": MODEL, "revision": REVISION, "authority": "DEVELOPMENT_PREFLIGHT_ONLY"}

    def __call__(self, premise: str, hypothesis: str) -> dict[str, float]:
        encoded = self.tokenizer(premise, hypothesis, truncation=False, return_tensors="pt")
        if encoded["input_ids"].shape[1] > self.model.config.max_position_embeddings:
            raise ScoreError("source exceeds local fact checker's context; do not truncate claims", "$.meaning")
        with self.torch.inference_mode():
            probabilities = self.torch.softmax(self.model(**encoded).logits[0], dim=-1).tolist()
        return {self.model.config.id2label[index]: float(value)
                for index, value in enumerate(probabilities)}


def _statement(fact: dict[str, Any], entities: dict[str, dict[str, Any]], *,
               via: bool = False, process: bool = False) -> str:
    source, target = (entities[fact[key]]["label"].lower() for key in ("from", "to"))
    kind = fact["kind"]
    if kind == "flows_to":
        carrier = entities[fact["carrier"]]["label"].lower()
        phrase = f"{carrier} moves from {source} to {target}"
        if via and "via" in fact:
            phrase += f" via {entities[fact['via']]['label'].lower()}"
        if process and "process" in fact:
            phrase += f" during {entities[fact['process']]['label'].lower()}"
        return phrase + "."
    if kind in ("above", "below", "left_of", "right_of"):
        return f"{source} is physically {kind.replace('_', ' ')} {target}."
    return f"{source} {kind.replace('_', ' ')} {target}."


def joint_process_label(claim):
    verbs = r"(?:creates?|produces?|causes?|generates?)"
    if len(re.findall(r"\b" + verbs + r"\b", claim, re.I)) != 1:
        return None
    match = re.match(
        r"^\s*(?:(?:the|this|these|both)\s+)?(?P<subject>"
        r"[\w'-]+(?:\s+[\w'-]+){0,6}\s+and\s+[\w'-]+(?:\s+[\w'-]+){0,6})"
        r"\s+" + verbs + r"\b", claim, re.I,
    )
    if match is None:
        return None
    return re.sub(r"\s+(?:together|jointly)$", "", match["subject"], flags=re.I)


def _split_joint_process(claim, entity):
    if entity["kind"] != "process" or re.search(r"\band\b", entity["label"], re.I):
        return False
    subject = joint_process_label(claim)
    if subject is None:
        return False
    ignored = {"a", "an", "the", "this", "these", "of", "in", "to", "from", "by"}
    label = set(re.findall(r"[\w'-]+", entity["label"].casefold())) - ignored
    parts = re.split(r"\s+and\s+", subject.casefold())
    return bool(label) and any(set(part.split()) - ignored <= label for part in parts)


def check_source_facts(graph: dict[str, Any], evidence: list[dict[str, Any]], judge: Any) -> None:
    """Veto unsupported atomic facts before the model's coverage review.

    An uncertain verdict is an actionable scoped fact repair, not a license to
    rewrite other accepted facts or switch to a fixture.
    """
    entities = {entity["id"]: entity for entity in graph["entities"]}
    claims = {record["id"]: record["claim"] for record in evidence}
    for index, fact in enumerate(graph["facts"]):
        path = f"$.meaning.facts[{index}]"
        citations = set(fact["evidence_ids"])
        if fact["kind"] in ("above", "below", "left_of", "right_of"):
            for endpoint in ("from", "to"):
                citations.update(entities[fact[endpoint]]["evidence_ids"])
        premise = " ".join(claims[record["id"]] for record in evidence if record["id"] in citations)
        if (fact["kind"] in ("causes", "produces") and len(citations) == 1
                and _split_joint_process(premise, entities[fact["from"]])):
            raise ScoreError(
                f"source preflight cannot support {fact['id']}: the source names a joint process; "
                "one constituent is not the complete stated cause", path,
            )
        if fact["kind"] == "causes":
            if not re.search(r"\b(?:caus(?:e|es|ed)|triggers?|leads?\s+to|results?\s+in|induces?"
                             r"|changes?|affects?|influences?|drives?|forces?)\b",
                             premise, re.I):
                raise ScoreError(
                    f"source preflight cannot support {fact['id']}: static orientation or sequence "
                    "is not source-stated causation", path,
                )
        if fact["kind"] == "stores":
            if not re.search(r"\b(?:stor(?:e|es|ed|ing)|holds?|retains?|keeps?)\b", premise, re.I):
                raise ScoreError(
                    f"source preflight cannot support {fact['id']}: influence is not source-stated storage", path,
                )
        if fact["kind"] == "contains" and entities[fact["to"]]["kind"] == "energy":
            if not re.search(r"\b(?:contain(?:s|ed)?|holds?|inside|within)\b", premise, re.I):
                raise ScoreError("stored energy is not evidence of physical containment", path)
        hypothesis = _statement(fact, entities)
        for annotation in (None, "process", "via"):
            if annotation is not None and annotation not in fact:
                continue
            if annotation == "process":
                hypothesis = _statement(fact, entities, process=True)
            elif annotation == "via":
                hypothesis = _statement(fact, entities, via=True, process="process" in fact)
            premises = [claims[cid] for cid in fact["evidence_ids"]] if fact["kind"] == "aligns_with" else [premise]
            for cited_premise in premises:
                scores = judge(cited_premise, hypothesis)
                if scores.get("entailment", 0) <= max(scores.get("neutral", 0),
                                                       scores.get("contradiction", 0)):
                    suffix = f".{annotation}" if annotation is not None else ""
                    raise ScoreError(
                        f"source preflight cannot support {fact['id']}{suffix}: {hypothesis} "
                        f"(entailment {scores.get('entailment', 0):.3f}; "
                        f"neutral {scores.get('neutral', 0):.3f}; "
                        f"contradiction {scores.get('contradiction', 0):.3f}). "
                        f"Repair or remove only this unsupported fact or annotation.",
                        path,
                    )
