# Copyright (c) 2020 Mobvoi Inc. (authors: Binbin Zhang, Xiaoyu Chen, Di Wu)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import copy
import logging
import sys
import os
import torch
import yaml
from torch.utils.data import DataLoader
from wenet.dataset.dataset import Dataset
from wenet.transformer.asr_model import init_asr_model
from wenet.utils.checkpoint import load_checkpoint
from wenet.utils.file_utils import read_symbol_table, read_non_lang_symbols
from wenet.utils.config import override_config

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]

class Recognize():
    def __init__(self, ):
        self.root_path = rootPath
        self.batch_size = 1
        self.beam_size = 10
        self.bpe_model = None
        self.checkpoint = self.root_path+'/model/20210815_unified_conformer_exp/final.pt'
        self.config = self.root_path+'/model/20210815_unified_conformer_exp/train.yaml'
        self.ctc_weight = 0.5
        self.data_type = 'raw'
        self.decoding_chunk_size = -1
        self.dict = self.root_path+'/model/20210815_unified_conformer_exp/words.txt'
        self.gpu = -1
        self.mode = 'attention_rescoring'
        self.non_lang_syms = None
        self.num_decoding_left_chunks = -1
        self.override_config = []
        self.penalty = 0.0
        self.result_file = 'online_text'
        self.reverse_weight = 0.0
        self.simulate_streaming = False,
        self.test_data = ''
        
        self.use_cuda = self.gpu >= 0 and torch.cuda.is_available()
        
        self.device = torch.device('cuda' if False else 'cpu')
        self.load_configs()  # 加载配置
        self.test_data_conf()
        self.loadmodel()  # 加载模型
    
    def load_configs(self):
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s')
        os.environ['CUDA_VISIBLE_DEVICES'] = str(self.gpu)
        
        if self.mode in ['ctc_prefix_beam_search', 'attention_rescoring'
                              ] and self.batch_size > 1:
            logging.fatal(
                'decoding mode {} must be running with batch_size == 1'.format(
                    self.mode))
            sys.exit(1)
        with open(self.config, 'r') as fin:
            self.configs = yaml.load(fin, Loader=yaml.FullLoader)
        if len(self.override_config) > 0:
            self.configs = override_config(self.configs, self.override_config)
        # 加载词典
        self.symbol_table = read_symbol_table(self.dict)
    
    def loadmodel(self):
        # Init asr model from configs
        model = init_asr_model(self.configs)
        
        # Load dict
        self.char_dict = {v: k for k, v in self.symbol_table.items()}
        self.eos = len(self.char_dict) - 1
        
        load_checkpoint(model, self.checkpoint)
        self.model = model.to(self.device)
        self.model.eval()
    
    def test_data_conf(self):
        '''
        测试数据配置
        '''
        self.test_conf = copy.deepcopy(self.configs['dataset_conf'])
        self.test_conf['filter_conf']['max_length'] = 102400
        self.test_conf['filter_conf']['min_length'] = 0
        self.test_conf['filter_conf']['token_max_length'] = 102400
        self.test_conf['filter_conf']['token_min_length'] = 0
        self.test_conf['filter_conf']['max_output_input_ratio'] = 102400
        self.test_conf['filter_conf']['min_output_input_ratio'] = 0
        self.test_conf['speed_perturb'] = False
        self.test_conf['spec_aug'] = False
        self.test_conf['shuffle'] = False
        self.test_conf['sort'] = False
        if 'fbank_conf' in self.test_conf:
            self.test_conf['fbank_conf']['dither'] = 0.0
        elif 'mfcc_conf' in self.test_conf:
            self.test_conf['mfcc_conf']['dither'] = 0.0
        self.test_conf['batch_conf']['batch_type'] = "static"
        self.test_conf['batch_conf']['batch_size'] = self.batch_size
        self.non_lang_syms = read_non_lang_symbols(self.non_lang_syms)
    
    def get_test_data_loader(self,path):
        self.test_data=path
        test_dataset = Dataset(self.data_type,
                               self.test_data,
                               self.symbol_table,
                               self.test_conf,
                               self.bpe_model,
                               self.non_lang_syms,
                               partition=False)
        return DataLoader(test_dataset, batch_size=None, num_workers=0)
    
    def create_data_list(self,path):
        file_name = path.split("/")[-1].split(".")[0]
        filepath = "/home/asr/data/aizimu_online/decoder/datalist/"+file_name
        if not os.path.exists(filepath):
            with open(filepath,'w',encoding="utf-8") as file:
                file.write('{"key":"%s","wav":"/home/asr/data/aizimu_online/cache/%s.wav","txt":""}'%(file_name,file_name))
        return filepath

    def get_recognize(self , path):
        path = self.create_data_list(path) 
        test_data_loader = self.get_test_data_loader(path)
        with torch.no_grad():
            for batch_idx, batch in enumerate(test_data_loader):
                keys, feats, target, feats_lengths, target_lengths = batch
                feats = feats.to(self.device)
                feats_lengths = feats_lengths.to(self.device)
                assert (feats.size(0) == 1)
                if self.mode == 'attention':
                    hyps, _ = self.model.recognize(
                        feats,
                        feats_lengths,
                        beam_size=self.beam_size,
                        decoding_chunk_size=self.decoding_chunk_size,
                        num_decoding_left_chunks=self.num_decoding_left_chunks,
                        simulate_streaming=self.simulate_streaming)
                    hyps = [hyp.tolist() for hyp in hyps]
                elif self.mode == 'ctc_greedy_search':
                    hyps, _ = self.model.ctc_greedy_search(
                        feats,
                        feats_lengths,
                        decoding_chunk_size=self.decoding_chunk_size,
                        num_decoding_left_chunks=self.num_decoding_left_chunks,
                        simulate_streaming=self.simulate_streaming)
                # ctc_prefix_beam_search and attention_rescoring only return one
                # result in List[int], change it to List[List[int]] for compatible
                # with other batch decoding mode
                elif self.mode == 'ctc_prefix_beam_search':
                    assert (feats.size(0) == 1)
                    hyp, _ = self.model.ctc_prefix_beam_search(
                        feats,
                        feats_lengths,
                        self.beam_size,
                        decoding_chunk_size=self.decoding_chunk_size,
                        num_decoding_left_chunks=self.num_decoding_left_chunks,
                        simulate_streaming=self.simulate_streaming)
                    hyps = [hyp]
                elif self.mode == 'attention_rescoring':
                    assert (feats.size(0) == 1)
                    hyp, _ = self.model.attention_rescoring(
                        feats,
                        feats_lengths,
                        self.beam_size,
                        decoding_chunk_size=self.decoding_chunk_size,
                        num_decoding_left_chunks=self.num_decoding_left_chunks,
                        ctc_weight=self.ctc_weight,
                        simulate_streaming=self.simulate_streaming,
                        reverse_weight=self.reverse_weight)
                    hyps = [hyp]
                
                content = ''
                for w in hyps[0]:
                    if w == self.eos:
                        break
                    content += self.char_dict[w]
                return content

if __name__ == '__main__':
    # 加载模型
    recog = Recognize()
    result1 = recog.get_recognize("../cache/temp.wav")
    print(result1)
        
            