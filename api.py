from flask import Flask, render_template, request
from flask_ngrok import run_with_ngrok
app = Flask(__name__)
run_with_ngrok(app)

from generator_utils import query_dbpedia, decode
from transformers import BertTokenizer, BertModel, BertConfig
from model import BertSeq2Seq
import torch
import re




def process_sentence(sent):
  sent = sent.strip().replace('< ', '<').replace(' >', '>')
  sent = re.sub(r' ?([!"#$%&\'(’)*+,-./:;=?@\\^_`{|}~]) ?', r'\1', sent)
  sent = sent.replace('attr_close>', 'attr_close >').replace('_attr_open', '_ attr_open')
  sent = sent.replace(' [ ', ' [').replace(' ] ', '] ')
  sent = sent.replace('_obd_', ' _obd_ ').replace('_oba_', ' _oba_ ')
  return sent

def generate_summary(question):
    model_inputs = tokenizer(question, max_length=max_source_length, padding=padding, truncation=True, return_tensors="pt")
    input_ids = model_inputs.input_ids.to('cuda')
    attention_mask = model_inputs.attention_mask.to('cuda')
    pred = None
    with torch.no_grad():
      outputs = model(source_ids=input_ids, source_mask=attention_mask)
      for pred in outputs:
        t=pred[0].cpu().numpy()
        t=list(t)
        if 0 in t:
            t=t[:t.index(0)]
        text = decoder_tokenizer.decode(t, clean_up_tokenization_spaces=True, skip_special_tokens=True)
        pred = process_sentence(text)

    return pred



load_model_path = '../drive/MyDrive/THESIS/BertSeq2seq/Monument/bert2sparql/pytorch_model.bin'
max_source_length = 64
max_target_length = 256
source_lang = 'en'
target_lang = 'sparql'
padding = 'max_length'
num_beams = 10
encoder_model_path = 'bert-base-cased'
decoder_model_path = 'bert-base-cased'

tokenizer = BertTokenizer.from_pretrained(encoder_model_path, do_lower_case=False)
decoder_tokenizer = BertTokenizer.from_pretrained(decoder_model_path, do_lower_case=False)
config = BertConfig.from_pretrained(encoder_model_path)

decoder_config = BertConfig.from_pretrained(decoder_model_path)
encoder = BertModel.from_pretrained(encoder_model_path, config=config)
decoder_config.is_decoder = True
decoder_config.add_cross_attention = True
decoder = BertModel.from_pretrained(
    decoder_model_path,
    config=decoder_config,
)

model = BertSeq2Seq(encoder=encoder, decoder=decoder, config=decoder_config,
                    beam_size=num_beams, max_length=max_target_length,
                    sos_id=decoder_tokenizer.cls_token_id, eos_id=decoder_tokenizer.sep_token_id)
model.load_state_dict(torch.load(load_model_path))
model.to('cuda')
model.eval()

@app.route("/answer", methods=['POST'])
def answer():
    question = request.get_json()['question']
    question = " ".join(question.lower().split())
    sparql_query = generate_summary(question)
    decoded_sparql_query = decode(sparql_query)
    results = query_dbpedia(decoded_sparql_query)
    if 'boolean' in results:
      return {'query': decoded_sparql_query, 'result': results['boolean']}
    else:
      entities = []
      for r in results['results']['bindings']:
        for variable, value in r.items():
          entities.append(value['value'])
      return {'query': decoded_sparql_query, 'result': "</br>".join(entities)}


@app.route("/")
def home():
    return render_template('index.html')
    
app.run()