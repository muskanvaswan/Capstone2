import aiohttp
import asyncio
import uvicorn
import numpy #
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from fast_bert.data_cls import BertDataBunch
from fast_bert.learner_cls import BertLearner
from fast_bert.metrics import accuracy

export_file_url = "https://www.googleapis.com/drive/v3/files/1-00f28mlffM2uPJVJDY94K1aOy9LfJw1?alt=media&key=AIzaSyArebv-g7_CgQUjKftzGkgeHhtHivaR4TA"
export_file_name = 'pytorch_model.bin'

classes = ['Jacob Elordi or Noah',
 'Joel Courtney or Lee',
 'Joey King or Elle',
 'Maise Richardson-sellers or Chloe',
 'Meganne Young or Rachel',
 'Molly Ringwald known or Sara Flynn',
 'Taylor Zakhar Perez or Marco']

path = Path(__file__).parent

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
                           model_type = 'bert') 
        
        learn = BertLearner.from_pretrained_model(data_bunch, 
                                            pretrained_path = path,
                                            metrics = [],
                                            device = 'cpu',
                                            logger = None,
                                            output_dir = None,
                                            is_fp16 = False)
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
  #  img_data = await request.form()
     
#    img_bytes = await (img_data['file'].read())
 #   img = open_image(BytesIO(img_bytes))
  #  prediction, pred_idx, probs = learn.predict(img)
  #  probability = str(round(float((max(probs)*100).numpy()), 2)) + "%"
  
    return JSONResponse({'result': str(preds), 'probability': str(probability)})
 


if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
