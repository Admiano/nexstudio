import importlib.util,json,os,tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class WorkerTests(unittest.TestCase):
    def test_versioned_finish_profile_cannot_inherit_baseline_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);blender=base/'blender';blender.touch()
            source=base/'source';(source/'scenes').mkdir(parents=True);(source/'scenes/BASE_V58.blend').touch()
            with patch.dict(os.environ,{'BLENDER_BIN':str(blender),'CAST_SOURCE_DIR':str(source),'CAST_QUALITY_PILOT':'0','CAST_FINISH_UPGRADE':'0','CAST_GARMENT_STRUCTURE_PILOT':'0'}):
                spec=importlib.util.spec_from_file_location('cast_worker_profile',ROOT/'scripts/cast-preview-worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
                config={'sourceVersion':worker.SOURCE_VERSION,'renderVersion':worker.RENDER_VERSION,'frame':27,'resolutionPercentage':50,'framing':'upper-thigh','env':{k:'' for k in worker.ENV_KEYS}}
                config['env'].update(CAST_CHARACTER='female',CAST_FACE='0')
                job=base/('b'*64);job.mkdir();(job/'request.json').write_text(json.dumps({'config':config}))
                def finish(command,**kwargs):
                    for flag in ('CAST_QUALITY_PILOT','CAST_FINISH_UPGRADE','CAST_GARMENT_STRUCTURE_PILOT'):
                        self.assertEqual(kwargs['env'][flag],'1')
                    (job/'render.png').write_bytes(b'versioned-render')
                    return SimpleNamespace(returncode=0)
                with patch.object(worker.subprocess,'run',side_effect=finish):worker.render(job)
                self.assertEqual((job/'preview.png').read_bytes(),b'versioned-render')
                self.assertEqual(json.loads((job/'status.json').read_text())['status'],'ready')
                self.assertIn(worker.RENDER_VERSION,(ROOT/'src/studio-v2/cast/render-config.ts').read_text())
                config['env']['CAST_FINISH_UPGRADE']='0'
                with self.assertRaises(ValueError):worker.validate(config)
    def test_failure_and_lock_release(self):
        with tempfile.TemporaryDirectory() as cache:
            os.environ['CAST_PREVIEW_CACHE_DIR']=cache;os.environ['BLENDER_BIN']=str(Path(cache)/'missing-blender')
            spec=importlib.util.spec_from_file_location('cast_worker',ROOT/'scripts/cast-preview-worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
            job=Path(cache)/('a'*64);job.mkdir();config={'sourceVersion':worker.SOURCE_VERSION,'renderVersion':worker.RENDER_VERSION,'frame':27,'resolutionPercentage':50,'framing':'upper-thigh','env':{k:'' for k in worker.ENV_KEYS}};config['env'].update(CAST_CHARACTER='female',CAST_FACE='0');(job/'request.json').write_text(json.dumps({'config':config}))
            first=worker.take_lock();self.assertIsNone(worker.take_lock());first.close();worker.drain();self.assertEqual(json.loads((job/'status.json').read_text())['error'],'BLENDER_RUNTIME_MISSING');self.assertFalse((job/'preview.png').exists());reopened=worker.take_lock();self.assertIsNotNone(reopened);reopened.close()
            config['env']['CAST_CHARACTER']='female; touch stolen'
            with self.assertRaises(ValueError):worker.validate(config)
            config['env']['CAST_CHARACTER']='female';config['sourceVersion']='other-source'
            with self.assertRaises(ValueError):worker.validate(config)
if __name__=='__main__':unittest.main()
