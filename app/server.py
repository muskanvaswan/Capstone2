import aiohttp
import asyncio
import uvicorn
import numpy #
from io import BytesIO
from pathlib import Path
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from fast_bert.data_cls import BertDataBunch
from fast_bert.learner_cls import *

export_file_url = "https://www.googleapis.com/drive/v3/files/1KjrRxptv78tXKGYCE-B6EsRJ2e8YkUDm?alt=media&key=AIzaSyCNoRufM9Z-HSsX566HZv-Qj2shWUI7BBs"
export_file_name = 'pytorch_model.bin'

path = Path('app/')

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))


async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)


async def setup_learner():
    await download_file(export_file_url, path / export_file_name)
    try:
        data_bunch = BertDataBunch(path, path,
                                   tokenizer = path,
                                   train_file = None,
                                   val_file = None,
                                   label_file = 'l2.csv',
                                   batch_size_per_gpu = 120,
                                   max_seq_length = 40,
                                   multi_gpu = False,
                                   multi_label = False,
                                   model_type = None)
        model = load_model(data_bunch, path, path / export_file_name, device = "cpu", multi_label = False)
        learn = BertLearner(data_bunch, model, path, metrics = [], output_dir = None, device = 'cpu', logger = None)
        #learn = BertLearner.from_pretrained_model(data_bunch, 
                                            #pretrained_path = path,
                                            #metrics = [],
                                            #device = 'cpu',
                                            #logger = None,
                                            #output_dir = None,
                                            #is_fp16 = False)
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
 text = await request.form()
 preds = learner.predict_batch([text])
 return JSONResponse({'result': str(preds), 'probability': str(probability)})
       
 #  img_data = await request.form()
     
#    img_bytes = await (img_data['file'].read())
 #   img = open_image(BytesIO(img_bytes))
  #  prediction, pred_idx, probs = learn.predict(img)
  #  probability = str(round(float((max(probs)*100).numpy()), 2)) + "%"
  
 


if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
