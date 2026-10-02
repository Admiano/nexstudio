import importlib.util,json,os,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class WorkerTests(unittest.TestCase):
    def test_failure_and_lock_release(self):
        with tempfile.TemporaryDirectory() as cache:
            os.environ['CAST_PREVIEW_CACHE_DIR']=cache;os.environ['BLENDER_BIN']=str(Path(cache)/'missing-blender')
            spec=importlib.util.spec_from_file_location('cast_worker',ROOT/'scripts/cast-preview-worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
            job=Path(cache)/('a'*64);job.mkdir();config={'sourceVersion':worker.SOURCE_VERSION,'renderVersion':worker.RENDER_VERSION,'frame':27,'resolutionPercentage':50,'env':{k:'' for k in worker.ENV_KEYS}};config['env'].update(CAST_CHARACTER='female',CAST_FACE='0');(job/'request.json').write_text(json.dumps({'config':config}))
            first=worker.take_lock();self.assertIsNone(worker.take_lock());first.close();worker.drain();self.assertEqual(json.loads((job/'status.json').read_text())['error'],'BLENDER_RUNTIME_MISSING');self.assertFalse((job/'preview.png').exists());reopened=worker.take_lock();self.assertIsNotNone(reopened);reopened.close()
            config['env']['CAST_CHARACTER']='female; touch stolen'
            with self.assertRaises(ValueError):worker.validate(config)
            config['env']['CAST_CHARACTER']='female';config['sourceVersion']='other-source'
            with self.assertRaises(ValueError):worker.validate(config)
if __name__=='__main__':unittest.main()
