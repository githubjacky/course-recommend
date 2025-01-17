import csv
import pandas as pd
import json
import numpy as np
import re
from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger


class DataUtil():
    def __init__(
        self,
        user,
        course,
        course_chapter,
        topic,
        train,
        train_topic,
        valseen,
        valseen_topic,
        testseen,
        testseen_topic,
        valunseen,
        valunseen_topic,
        testunseen,
        testunseen_topic
    ):
        arg = locals().copy()
        arg.pop('self')
        self.df = {
            key: pd.read_csv(val)
            for key, val in arg.items()
        }

        self.user2idx = {
            id: idx
            for (idx, id) in enumerate(self.df['user']['user_id'])
        }
        self.idx2user= {
            idx: id
            for (idx, id) in enumerate(self.df['user']['user_id'])
        }

        self.course2idx = {
            id: idx
            for (idx, id) in enumerate(self.df['course']['course_id'])
        }
        self.idx2course = {
            idx: id
            for (idx, id) in enumerate(self.df['course']['course_id'])
        }

        self.cate = ['train', 'valseen', 'testseen', 'valunseen', 'testunseen']
        self.user_ids = {
            i: [self.user2idx[j] for j in self.df[i]['user_id']]
            for i in self.cate
        }

        subgroup2idx = {
            name: idx
            for name, idx in zip(self.df['topic']['subgroup_name'], self.df['topic']['subgroup_id'])
        }

        course2subgroup = {}
        for (idx, subgroup) in enumerate(self.df['course']['sub_groups']):
            try:
                course2subgroup[idx] = [subgroup2idx[i] for i in subgroup.split(',')]
            except:
                course2subgroup[idx] = [0]
        self.course2subgroup = course2subgroup

        self.gender2idx = {
            'female': 0,
            'male': 1,
            'other':2
        }
        self.int_topic2idx, self.int2idx = self.encode_int_inttopic()

    def encode_int_inttopic(self, cate='train', show_res=False):
        uniq_it_topic = []
        uniq_it = []
        for i in self.user_ids[cate]:
            sample = self.df['user'].iloc[i]
            try:
                it_mix = sample['interests'].split(',')
            except:
                continue
            for j in it_mix:
                it_topic, it = j.split('_')
                if it_topic not in uniq_it_topic:
                    uniq_it_topic.append(it_topic)
                if it not in uniq_it:
                    uniq_it.append(it)
        
        if show_res:
            print(cate, ':')
            print('number of unique interest topic', len(uniq_it_topic))
            print('number of unique interest',len(uniq_it))
        else:
            int_topic2idx = {
                i: idx
                for idx, i in enumerate(uniq_it_topic)
            }
            int2idx = {
                i: idx
                for idx, i in enumerate(uniq_it)
            }
            return int_topic2idx, int2idx

    
    def encode_customer_feature(self, cate, output_dir):
        dump_list = []
        for idx, i in enumerate(self.user_ids[cate]):
            sample = self.df['user'].iloc[i]
            gender = sample['gender']
            if isinstance(gender, float):
                gender = -1
            else:
                gender = self.gender2idx[gender]

            inte = sample['interests']
            if isinstance(inte, float):
                int_topic = [-1]
                interest = [-1]
            else:
                int_topic = [self.int_topic2idx[i.split('_')[0]] for i in inte.split(',')]
                interest = [self.int2idx[i.split('_')[1]] for i in inte.split(',')]
            dump_list.append({
                'user_id': self.idx2user[i],
                'gender': gender,
                'interest_topic': int_topic,
                'interest': interest
            })
    
        json_obj = json.dumps(dump_list, indent=4)
        output_path = output_dir / f'{cate}.json'
        with open(output_path, 'w') as f:
            f.write(json_obj)

    def encode_customer_feature_train(self, cate, output_dir):
        dump_list = []
        for idx, i in enumerate(self.user_ids[cate]):
            sample = self.df['user'].iloc[i]
            gender = sample['gender']
            if isinstance(gender, float):
                gender = -1
            else:
                gender = self.gender2idx[gender]
            inte = sample['interests']
            if isinstance(inte, float):
                int_topic = [-1]
                interest = [-1]
            else:
                int_topic = [self.int_topic2idx[i.split('_')[0]] for i in inte.split(',')]
                interest = [self.int2idx[i.split('_')[1]] for i in inte.split(',')]
            
            course = [self.course2idx[j] for j in self.df[cate].iloc[idx]['course_id'].split(' ')]
            cate_topic = cate + '_topic'
            try:
                topic = [int(j) for j in self.df[cate_topic].iloc[idx]['subgroup'].split(' ')]
            except:
                topic = [self.course2subgroup[j] for j in course]
                topic = [k for j in topic for k in j]
            
            dump_list.append({
                'user_id': self.idx2user[i],
                'gender': gender,
                'interest_topic': int_topic,
                'interest': interest,
                'course': course,
                'topic': topic
            })
        json_obj = json.dumps(dump_list, indent=4)
        output_path = output_dir / f'{cate}.json'
        with open(output_path, 'w') as f:
            f.write(json_obj)

    def output_utils(self, output_dir):
        idx2gender = {
            val: key
            for key, val in self.gender2idx.items()
        }
        idx2gender[-1] = 'nan'

        idx2int_topic = {
            val: key
            for key, val in self.int_topic2idx.items()
        }
        idx2int_topic[-1] = 'nan'

        idx2int = {
            val: key
            for key, val in self.int2idx.items()
        }
        idx2int[-1] = 'nan'

        # course2subgroup
        with open(output_dir / 'course2subgroup.json', 'w') as f:
            f.write(json.dumps(self.course2subgroup, indent=4))
        # idx2course
        with open(output_dir / 'idx2course.json', 'w') as f:
            f.write(json.dumps(self.idx2course, indent=4))
        # idx2gender
        with open(output_dir / 'idx2gender.json', 'w') as f:
            f.write(json.dumps(idx2gender, indent=4))
        # idx2int_topic
        with open(output_dir / 'idx2int_topic.json', 'w') as f:
            f.write(json.dumps(idx2int_topic, indent=4))
        # idx2int
        with open(output_dir / 'idx2int.json', 'w') as f:
            f.write(json.dumps(idx2int, indent=4))

    def safetext(self, x):
        try:
            output = x.strip('\n')
            output = output.strip(' ') 
            output = output.strip('\n')
            output = output.strip('。')
            output += '。'
        except:
            output = ""
        return output

    def cleanhtml(self, raw_html): 
        cleanr = re.compile('<.*?>')
        output = re.sub(cleanr, '', raw_html)
        output = output.strip(' ') 
        output = output.strip('\n')
        output = output.strip('。')
        output += '。'
        return output
        
    def clean(self, ws_res, pos_res):
        clean_doc = []
        for ws_res_i, pos_res_i in zip(ws_res, pos_res):
            clean_sentence = []
            block_pos = set(['Nep', 'Nh', 'Nb'])
            for i, j in zip(ws_res_i, pos_res_i):
                is_noun = j.startswith("N")  # retain noun
                is_not_block_pos = j not in block_pos  # retain some pos
                is_not_one_charactor = not (len(i) == 1)  # kick out one character 
            
                if is_noun and is_not_block_pos and is_not_one_charactor:
                    clean_sentence.append(i)
            clean_doc.append(clean_sentence)

        return clean_doc

    def get_course_feature(self, output_dir):
        self.df['course']['clean_course_name'] = self.df['course']['course_name'].apply(self.safetext)
        self.df['course']['clean_sub_groups'] = self.df['course']['sub_groups'].apply(self.safetext)
        self.df['course']['clean_will_learn'] = self.df['course']['will_learn'].apply(self.safetext)
        self.df['course']['clean_description'] = self.df['course']['description'].apply(self.cleanhtml)
        course_feature = dict()
        for i in range(len(self.df['course'])):
            course_feature[str(i)] = self.df['course'].iloc[i]['clean_course_name'] + self.df['course'].iloc[i]['clean_sub_groups'] + self.df['course'].iloc[i]['clean_will_learn'] + self.df['course'].iloc[i]['clean_description']
        doc = list(course_feature.values())
        ws_driver = CkipWordSegmenter(model="bert-base", device=0)
        pos_driver = CkipPosTagger(model="bert-base", device=0)
        ws_res = ws_driver(doc)
        pos_res = pos_driver(ws_res)
        clean_doc = self.clean(ws_res, pos_res)
        course_feature = {
            str(idx): i
            for idx, i in enumerate(clean_doc)
        }
        with open(f'{output_dir}/course_feature.json', 'w') as f:
                f.write(json.dumps(course_feature))
    
