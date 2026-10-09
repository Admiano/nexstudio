"""Photo evidence rung: rights, ranking, cache, and catalogue failure — all offline."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from editorial_plan_compiler import evidence as ev
from editorial_plan_compiler.evidence import Candidate, CatalogueDown, PhotoEvidence
from editorial_plan_compiler.lexicon import NounLexicon

pytestmark = pytest.mark.skipif(not shutil.which('ffmpeg'), reason='ffmpeg required')


def _cand(title, source='openverse', sid='1', license='CC0 1.0', w=1400, h=1000, url='https://x/a.jpg', subjects=(), year=None):
    return Candidate(source, 'prov', sid, title, 'Someone', license, 'https://creativecommons.org/publicdomain/zero/1.0/',
                     'https://example.org/landing', url, w, h, tuple(subjects), year)


@pytest.fixture(scope='module')
def lexicon():
    lx = NounLexicon()
    if not lx.available:
        pytest.skip('WordNet lexicon not installed')
    return lx


@pytest.fixture
def photo_bytes(tmp_path):
    src = tmp_path / 'src.jpg'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=0x8a5a2b:s=1600x1100',
                    '-frames:v', '1', str(src)], check=True)
    return src.read_bytes()


def test_title_policy_keeps_the_subject_and_refuses_people_records_and_other_things(lexicon):
    pe = PhotoEvidence(root=Path('/nonexistent'), lexicon=lexicon, online=False)
    ok = lambda t, w: pe._score(_cand(t), tuple(w.split())) is not None
    assert ok('File:Almonds02.jpg', 'almond')
    assert ok('File:Roasted coffee beans.jpg', 'bean')
    assert ok('File:Almond nut closeup.jpg', 'almond')        # its own ancestor is description
    assert not ok('File:Bean salad.jpg', 'bean')               # a salad
    assert not ok('File:Coffee machine.jpg', 'coffee')         # a machine
    assert not ok('File:Ralph J. Bean.jpg', 'bean')            # a person
    assert not ok('File:Almond painting 1740.jpg', 'almond')   # artwork
    assert not ok('File:Bean.jpg', 'coffee bean')              # phrase must appear in order
    assert not ok('File:Some very long archival record of many different items in a room.jpg', 'room')
    assert pe._score(_cand('File:Almonds.jpg', w=300, h=200), ('almond',)) is None
    assert pe._score(_cand('File:Almonds.jpg', w=3000, h=600), ('almond',)) is None   # a strip
    assert not ok('File:Bandage Scissors.JPG', 'bandage')      # scissors: a plural-only lemma is still a thing
    assert not ok('File:Marijuana and pipe.jpg', 'pipe')       # one of two named subjects
    assert not ok('File:Dress and legging.jpg', 'dress')
    assert not ok('File:Salt & pepper.jpg', 'salt')
    assert ok('File:Two guitars.jpg', 'guitar') and ok('File:Coffee in a mug.jpg', 'coffee')
    assert not ok('File:Hamam street Old Salt.jpg', 'salt')    # a town: the concept capitalised mid-sentence
    assert not ok('File:Turkey Point beach.jpg', 'turkey')
    assert ok('File:Two Guitars.jpg', 'guitar')                 # Title Case throughout says nothing
    assert ok('File:Sea salt in a bowl.jpg', 'salt')


def test_title_policy_refuses_scenes_damage_credits_and_other_languages(lexicon):
    pe = PhotoEvidence(root=Path('/nonexistent'), lexicon=lexicon, online=False)
    ok = lambda t, w: pe._score(_cand(t), tuple(w.split())) is not None
    assert not ok('File:Kereta Api Bandara.jpg', 'api')            # another language: two words the lexicon lacks
    assert not ok('File:Mohan Tamang checking rocket.jpg', 'rocket')
    assert ok('File:Bus in Újpest.jpg', 'bus')                       # one place name is fine
    assert not ok('File:Diseased apple.jpg', 'apple') and not ok('File:Car crash 1.jpg', 'car')
    assert not ok('File:Flower mirror by Gabriel Bracho.jpg', 'mirror')   # a credited artwork
    assert not ok('File:Apollo 17 Cernan on moon.jpg', 'moon')      # the moon is what he stands on
    assert not ok('File:A waterdrop on umbrella.jpg', 'umbrella')
    assert ok('File:Headphones on a loudspeaker.jpg', 'headphone')
    assert not ok('File:Shoe trees.jpg', 'tree')                   # a compound the lexicon knows as another thing
    assert not ok('File:Hot dog stand.jpg', 'dog')
    assert ok('File:Roasted coffee beans.jpg', 'bean') and ok('File:Hard hat 20111111.jpg', 'hat')
    assert not ok('File:Speaker at Public Meeting in Taunton.jpg', 'speaker')   # a scene with people
    assert not ok('File:Ring, versierd met eenvoudig gedraaid motief, AK-RAK-1978-3.jpg', 'ring')
    assert not ok('File:Ro Server 20250221 Bergen.jpg', 'server')     # a ship called Ro Server
    assert not ok('File:Matatu Speaker 8.jpg', 'speaker') and not ok('File:Procell Batteries.jpg', 'battery')
    assert ok('File:Two Guitars.jpg', 'guitar') and ok('File:Tree 20210106.jpg', 'tree')
    assert not ok('File:Erechtheum Acropolis Athens evening moon.jpg', 'moon')   # a temple with the moon in it
    assert ok('File:6-Pack-Chicken-Eggs.jpg', 'egg') and ok('File:Big motorcycle in Tokyo.jpg', 'motorcycle')
    assert not ok('File:Messy table.jpg', 'table')
    filed = lambda t, w, subs: pe._score(_cand(t, subjects=subs), tuple(w.split())) is not None
    assert not filed('File:Disco dress 1970s.jpg', 'dress', ('Wrap dresses', 'Women wearing blue dresses'))
    assert not filed('File:Stethoscope A.jpg', 'stethoscope', ('Stethoscopes', 'Personality rights warning'))
    assert filed('File:Stethoscope A.jpg', 'stethoscope', ('Stethoscopes',))
    assert not pe._photographable('api') and not pe._photographable('revenue') and pe._photographable('laptop')


def test_archive_prints_are_refused_by_date_and_by_curators(lexicon):
    pe = PhotoEvidence(root=Path('/nonexistent'), lexicon=lexicon, online=False)
    assert pe._score(_cand('File:Salt-packaging.jpg', year=1934), ('salt',)) is None
    assert pe._score(_cand('File:Clay tablet.jpg', year=-2000), ('tablet',)) is None
    assert pe._score(_cand('File:Salt-packaging.jpg', year=2015), ('salt',)) is not None
    assert pe._score(_cand('File:Gosport ferry.jpg', subjects=('Ferries', 'Postcards of Hampshire')), ('ferry',)) is None
    assert pe._score(_cand('File:Gosport ferry.jpg', subjects=('Ferries',)), ('ferry',)) is not None
    assert ev._year('ca. 2000 <a href="x">BC</a>') == -2000 and ev._year('1895-06-01') == 1895 and ev._year('') is None


def test_a_black_and_white_frame_is_not_kept(tmp_path):
    grey, colour = tmp_path / 'grey.jpg', tmp_path / 'colour.jpg'
    for path, c in ((grey, 'gray'), (colour, '0x8a5a2b')):
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', f'color=c={c}:s=800x600',
                        '-frames:v', '1', str(path)], check=True)
    assert ev._is_monochrome(grey) and not ev._is_monochrome(colour)


def test_rank_is_deterministic_and_prefers_a_plain_study(lexicon):
    pe = PhotoEvidence(root=Path('/nonexistent'), lexicon=lexicon, online=False)
    cands = [_cand('File:Almond market street.jpg', sid='a'), _cand('File:Almonds.jpg', sid='b'),
             _cand('File:Almonds.jpg', sid='c'), _cand('File:Almond tree in an orchard field.jpg', sid='d')]
    r1 = pe._rank(list(cands), ('almond',))
    r2 = pe._rank(list(reversed(cands)), ('almond',))
    assert [c.source_id for c in r1] == [c.source_id for c in r2]
    assert r1[0].title == 'File:Almonds.jpg'
    assert sorted(c.source_id for c in r1[:2]) == ['b', 'c'] and [c.source_id for c in r1[2:]] == ['d']   # the market scene is refused


def test_curators_subjects_outrank_a_bare_title_and_refuse_art_and_renders(lexicon):
    pe = PhotoEvidence(root=Path('/nonexistent'), lexicon=lexicon, online=False)
    plain = _cand('File:Pantry cocina.jpg', source='wikimedia_commons', sid='a')                     # nobody filed it
    filed = _cand('File:Residential pantry.jpg', source='wikimedia_commons', sid='b', subjects=('Pantries',))
    render = _cand('File:Pantry 01.jpg', source='wikimedia_commons', sid='c', subjects=('Pantries', '3D renderings'))
    drawn = _cand('File:Pantry shelf.jpg', sid='d', subjects=('kitchen', 'illustration'))
    ranked = pe._rank([plain, filed, render, drawn], ('pantry',))
    assert [c.source_id for c in ranked] == ['b', 'a']
    assert pe._score(filed, ('pantry',)) > pe._score(plain, ('pantry',)) + 1.5
    # Openverse tags carry no housekeeping noise, so an untagged record is not penalised
    assert pe._score(_cand('File:Pantry.jpg'), ('pantry',)) == pe._score(_cand('File:Pantry.jpg', subjects=('food',)), ('pantry',))


def test_commons_categories_keep_the_subject_and_drop_housekeeping(monkeypatch):
    pe = PhotoEvidence(root=Path('/nonexistent'), online=False)
    pages = {'query': {'pages': {'10': {'pageid': 10, 'title': 'File:A.jpg', 'imageinfo': [{
        'mime': 'image/jpeg', 'width': 1200, 'height': 900, 'url': 'u',
        'extmetadata': {'LicenseShortName': {'value': 'CC0'}, 'Categories': {
            'value': 'CC-Zero|Self-published work|All media needing categories as of 2024|Pantries|Kitchens in Spain|'
                     'Files with no machine-readable author|Uploaded with pattypan|Photographs taken on 2020-01-01'}}}]}}}}
    monkeypatch.setattr(ev, '_fetch_json', lambda url: pages)
    (got,) = pe._commons('pantry')
    assert got.subjects == ('Pantries', 'Kitchens in Spain')


def test_openverse_tags_become_subjects(monkeypatch):
    pe = PhotoEvidence(root=Path('/nonexistent'), online=False)
    doc = {'results': [{'id': '1', 'title': 'Almond', 'license': 'cc0', 'url': 'https://x/1.jpg', 'width': 1200, 'height': 900,
                        'tags': [{'name': 'almond'}, {'name': 'nut', 'accuracy': 0.9}, {}]}]}
    monkeypatch.setattr(ev, '_fetch_json', lambda url: doc)
    (got,) = pe._openverse('almond')
    assert got.subjects == ('almond', 'nut')


def test_only_cc0_or_public_domain_candidates_survive_the_catalogue_parsers(monkeypatch):
    pe = PhotoEvidence(root=Path('/nonexistent'), online=False)
    doc = {'results': [
        {'id': '1', 'title': 'Almond', 'license': 'cc0', 'url': 'https://x/1.jpg', 'width': 1200, 'height': 900},
        {'id': '2', 'title': 'Almond', 'license': 'by', 'url': 'https://x/2.jpg', 'width': 1200, 'height': 900},
        {'id': '3', 'title': 'Almond', 'license': 'pdm', 'url': 'https://x/3.png', 'width': 1200, 'height': 900},
        {'id': '4', 'title': 'Almond', 'license': 'pdm', 'url': 'https://x/4.jpg', 'width': 1200, 'height': 900, 'mature': True},
    ]}
    monkeypatch.setattr(ev, '_fetch_json', lambda url: doc)
    got = pe._openverse('almond')
    assert [c.source_id for c in got] == ['1'] and got[0].license == 'CC0 1.0'
    pages = {'query': {'pages': {
        '10': {'pageid': 10, 'title': 'File:A.jpg', 'imageinfo': [{'mime': 'image/jpeg', 'width': 1200, 'height': 900, 'url': 'u',
               'extmetadata': {'LicenseShortName': {'value': 'CC0'}}}]},
        '11': {'pageid': 11, 'title': 'File:B.jpg', 'imageinfo': [{'mime': 'image/jpeg', 'width': 1200, 'height': 900, 'url': 'u',
               'extmetadata': {'LicenseShortName': {'value': 'CC BY-SA 4.0'}}}]},
        '12': {'pageid': 12, 'title': 'File:C.png', 'imageinfo': [{'mime': 'image/png', 'width': 1200, 'height': 900, 'url': 'u',
               'extmetadata': {'LicenseShortName': {'value': 'Public domain'}}}]},
    }}}
    monkeypatch.setattr(ev, '_fetch_json', lambda url: pages)
    got = pe._commons('almond')
    assert [c.source_id for c in got] == ['10']


def test_find_caches_a_normalised_hashed_record_and_answers_offline_afterwards(tmp_path, lexicon, photo_bytes, monkeypatch):
    pe = PhotoEvidence(root=tmp_path / 'ev', lexicon=lexicon, online=True)
    monkeypatch.setattr(pe, '_openverse', lambda q: [_cand('File:Almonds.jpg')])
    monkeypatch.setattr(pe, '_commons', lambda q: [])
    monkeypatch.setattr(ev, '_fetch_bytes', lambda url, limit=0: photo_bytes)
    rec = pe.find('Almonds')
    assert rec is not None and rec.license == 'CC0 1.0' and rec.landing_url.startswith('https://')
    f = tmp_path / 'ev' / rec.file
    assert f.exists() and hashlib.sha256(f.read_bytes()).hexdigest() == rec.sha256
    assert max(rec.width, rec.height) <= ev.MAX_EDGE and rec.width / rec.height == pytest.approx(1600 / 1100, rel=0.01)
    idx = json.loads((tmp_path / 'ev' / ev.INDEX_NAME).read_text())
    assert 'almond' in idx['photos'] and idx['misses'] == {}
    plan = pe.as_plan(rec)
    assert plan['rights'].startswith('CC0 1.0 (openverse:prov') and plan['path'] == str(f)
    # Offline, a fresh instance answers from the cache with the same record.
    off = PhotoEvidence(root=tmp_path / 'ev', lexicon=lexicon, online=False)
    assert off.find('almond') == rec
    assert idx['photos']['almond']['source_size'] == [1400, 1000] and idx['photos']['almond']['subjects'] == []
    # A tampered file is not served: its record is dropped and, offline, nothing stands in.
    f.write_bytes(b'not the photo')
    off2 = PhotoEvidence(root=tmp_path / 'ev', lexicon=lexicon, online=False)
    assert off2.find('almond') is None


def test_a_cached_record_is_re_read_against_the_current_policy(tmp_path, lexicon, photo_bytes, monkeypatch):
    pe = PhotoEvidence(root=tmp_path / 'ev', lexicon=lexicon, online=True)
    monkeypatch.setattr(pe, '_openverse', lambda q: [_cand('File:Almonds.jpg')])
    monkeypatch.setattr(pe, '_commons', lambda q: [])
    monkeypatch.setattr(ev, '_fetch_bytes', lambda url, limit=0: photo_bytes)
    rec = pe.find('almond')
    assert rec is not None
    # The catalogue's facts travel with the record; a rule tightened later retires it offline.
    idx = tmp_path / 'ev' / ev.INDEX_NAME
    doc = json.loads(idx.read_text())
    doc['photos']['almond']['year'] = 1921
    idx.write_text(json.dumps(doc))
    off = PhotoEvidence(root=tmp_path / 'ev', lexicon=lexicon, online=False)
    assert off.find('almond') is None and not (tmp_path / 'ev' / rec.file).exists()
    doc['photos']['almond']['year'] = None
    doc['photos']['almond']['subjects'] = ['Almonds', 'Paintings of fruit']
    idx.write_text(json.dumps(doc))
    assert PhotoEvidence(root=tmp_path / 'ev', lexicon=lexicon, online=False).find('almond') is None
    monkeypatch.setattr(pe, '_openverse', lambda q: [_cand('File:Api.jpg')])
    monkeypatch.setattr(pe, '_photographable', lambda c: True)
    assert pe.find('api') is not None
    assert PhotoEvidence(root=tmp_path / 'ev', lexicon=lexicon, online=False).find('api') is None


def test_a_miss_is_recorded_but_a_catalogue_outage_is_not(tmp_path, lexicon, monkeypatch):
    pe = PhotoEvidence(root=tmp_path / 'ev', lexicon=lexicon, online=True)
    monkeypatch.setattr(pe, '_openverse', lambda q: [])
    monkeypatch.setattr(pe, '_commons', lambda q: [])
    assert pe.find('almond') is None
    assert 'almond' in pe.misses and pe.unavailable == []

    def down(q):
        raise CatalogueDown('429')
    pe2 = PhotoEvidence(root=tmp_path / 'ev2', lexicon=lexicon, online=True)
    monkeypatch.setattr(pe2, '_openverse', down)
    monkeypatch.setattr(pe2, '_commons', down)
    assert pe2.find('almond') is None
    assert pe2.misses == {} and pe2.unavailable and '429' in pe2.unavailable[0]
    # One catalogue answering nothing while the other is down is still not a miss.
    pe3 = PhotoEvidence(root=tmp_path / 'ev3', lexicon=lexicon, online=True)
    monkeypatch.setattr(pe3, '_openverse', down)
    monkeypatch.setattr(pe3, '_commons', lambda q: [])
    assert pe3.find('almond') is None and pe3.misses == {} and pe3.unavailable


def test_only_things_a_camera_can_see_are_searched(tmp_path, lexicon, monkeypatch):
    pe = PhotoEvidence(root=tmp_path / 'ev', lexicon=lexicon, online=True)
    calls = []
    monkeypatch.setattr(pe, '_openverse', lambda q: calls.append(q) or [])
    monkeypatch.setattr(pe, '_commons', lambda q: [])
    for c in ('flavour', 'collision', 'latency', 'happiness'):
        assert pe.find(c) is None
    assert calls == [], calls
    for c in ('nurse', 'farmer', 'doctor'):           # a person's likeness is never evidence
        assert pe.find(c) is None
    assert calls == [], calls
    pe.find('tractor')
    assert calls and calls[0] == 'tractor'
