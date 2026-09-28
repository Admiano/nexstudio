"""Noun-coverage gate and stateful-object direction."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from editorial_plan_compiler.coverage import NounGate, noun_phrases, paper_key  # noqa: E402
from editorial_plan_compiler.directing import state_kind, tokens, verb_kind  # noqa: E402


def test_paper_key_reads_underscore_keys_and_aliases():
    assert paper_key('soccer_ball') == 'soccer_ball'
    assert paper_key('ball') == 'soccer_ball'
    assert paper_key('seed') == 'seed'
    assert paper_key('zzz-not-a-thing') is None


def test_noun_phrases_stop_at_function_words_and_verbs():
    runs = [r for _d, r in noun_phrases('The seed and the little chick hatched.')]
    assert ['seed'] in runs
    assert any(r[-1] == 'chick' for r in runs)


def test_things_skips_environment_and_parts():
    words = [w for w, _l, _p in NounGate().things('The moon rose over the horizon and the kite flew.')]
    assert 'horizon' not in words
    assert 'kite' in words


@pytest.mark.parametrize('kind,lemma,concept,expect', [
    ('dim', 'blow', 'candle', 'out'),
    ('shine', 'light', 'candle', 'light'),
    ('fill', 'pour', 'cup', 'fill'),
    ('empty', 'drink', 'cup', 'empty'),
    ('unfold', 'open', 'door', 'swing'),
    ('close', 'shut', 'door', 'close'),
    ('melt', 'melt', 'snowman', 'melt'),
    ('hatch', 'hatch', 'ball', 'pop'),
])
def test_state_kind_by_concept_family(kind, lemma, concept, expect):
    assert state_kind(kind, lemma, concept) == expect


@pytest.mark.parametrize('text,kind', [
    ('At last Grandma blew the candle out.', 'dim'),
    ('The kite flew away.', 'fly'),
    ('The pond froze.', 'freeze'),
])
def test_verb_kind_phrasal_and_irregular(text, kind):
    toks = tokens(None, text)
    kinds = [verb_kind(toks, i)[0] for i in range(len(toks))]
    assert kind in kinds
