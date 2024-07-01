import os
import yaml
from glob import glob as lsdir

import nbformat as nbf
from chatify import Chatify
from tqdm import tqdm

import numpy as np
import pickle

from langchain.prompts import PromptTemplate
from gptcache import Cache
from gptcache.processor.pre import get_prompt
from gptcache.manager import get_data_manager
from gptcache.similarity_evaluation.exact_match import ExactMatchEvaluation

source_repo = os.environ.get("SOURCE_REPO", "NeuroAI_Course")
mod_repo = os.environ.get("MOD_REPO", "chatify_NeuroAI_Course")
CACHE = False


def get_tutorial_notebooks(basedir):
    return lsdir(os.path.join(basedir, 'tutorials', '*', 'student', '*Tutorial*.ipynb'))


def chatified(fname):
    notebook = nbf.read(fname, nbf.NO_CONVERT)
    header_cell = notebook['cells'][0]
    return mod_repo in header_cell['source']


def get_text(fname):
    with open(os.path.join(os.getcwd(), 'ci', 'chatify', fname), 'r') as f:
        return ''.join(f.readlines())


def inject_chatify(fname):
    notebook = nbf.read(fname, nbf.NO_CONVERT)
    new_notebook = notebook.copy()

    # update header cell
    header_cell = new_notebook['cells'][0]
    header_cell['source'] = header_cell['source'].replace(source_repo, mod_repo)

    # insert background cell
    background_cell = nbf.v4.new_markdown_cell(source=get_text('background.md'), metadata={'execution': {}})
    del background_cell['id']

    # create davos cell
    davos_cell = nbf.v4.new_code_cell(source=get_text('install_davos.py'), metadata={'cellView': 'form', 'execution': {}})
    del davos_cell['id']

    # create chatify cell
    chatify_cell = nbf.v4.new_code_cell(source=get_text('install_and_load_chatify.py'), metadata={'cellView': 'form', 'execution': {}})
    del chatify_cell['id']

    idx = 0
    for cell in new_notebook['cells']:
        idx += 1
        if cell['cell_type'] == 'markdown':
            if '# Setup' in cell['source']:
                break

    if idx == len(new_notebook['cells']) - 1:
        return

    try:
        if chatified(fname):
            new_notebook.cells[0] = header_cell
            new_notebook.cells[idx] = background_cell
            new_notebook.cells[idx + 1] = davos_cell
            new_notebook.cells[idx + 2] = chatify_cell
        else:
            new_notebook.cells.insert(idx, background_cell)
            new_notebook.cells.insert(idx + 1, davos_cell)
            new_notebook.cells.insert(idx + 2, chatify_cell)
    except IndexError:
        raise ValueError(f"Notebook Missing Setup Header: {fname}, index: {idx}")

    # Write the file
    nbf.write(
        new_notebook,
        fname,
        version=nbf.NO_CONVERT,
    )


def compress_code(text):
    return '\n'.join([line.strip() for line in text.split('\n') if len(line.strip()) > 0])


def get_code_cells(fname):
    notebook = nbf.read(fname, nbf.NO_CONVERT)
    return [compress_code(cell['source']) for cell in notebook['cells'] if cell['cell_type'] == 'code']


def convert_pickle_file_to_cache(pickle_file, config):
    cache_db_version = config['cache_config']['cache_db_version']
    file_name = f'NMA_2023_v{cache_db_version}.cache'

    # Remove file before creating a new one
    if os.path.exists(file_name):
        os.remove(file_name)
    
    llm_cache = Cache()
    llm_cache.set_openai_key()
    data_manager = get_data_manager(data_path=file_name)
    
    llm_cache.init(
        pre_embedding_func=get_prompt,
        data_manager=data_manager,
        similarity_evaluation=ExactMatchEvaluation(),
    )
    
    chatify = Chatify()
    prompts = chatify._read_prompt_dir()['tutor']
    
    with open(pickle_file, 'rb') as f:
        cache = pickle.load(f)
        
    for key, value in cache.items():
        for prompt_name, prompt in prompts.items():
            prompt = PromptTemplate(
                template=prompt['content'],
                input_variables=prompt['input_variables'],
            )
            question = prompt.format(text=compress_code(key))
            try:
                answer = value[prompt_name]
                data_manager.save(question, answer, embedding_data=question)
            except KeyError:
                pass


tutorials = get_tutorial_notebooks(os.getcwd())
tutor = Chatify()
prompts = tutor._read_prompt_dir()['tutor']
code_cells = []
failed_queries = []

for notebook in tqdm(tutorials):
    inject_chatify(notebook)
    code_cells.extend(get_code_cells(notebook))


if CACHE:
    savefile = os.path.join(os.getcwd(), 'chatify', 'cache.pkl')
    failed_queries_file = os.path.join(os.getcwd(), 'chatify', 'failed_queries.pkl')

    if os.path.exists(savefile):
        with open(savefile, 'rb') as f:
            cache = pickle.load(f)
    else:
        cache = {}
    
    failed_queries = []

    tmpfile = os.path.join(os.getcwd(), 'chatify', 'tmp.pkl')
    for cell in tqdm(np.unique(code_cells)):
        if cell not in cache:
            cache[cell] = {}
        
        for name, content in prompts.items():
            if name not in cache[cell] or len(cache[cell][name]) == 0:
                try:
                    cache[cell][name] = tutor._cache(cell, content)

                    with open(tmpfile, 'wb') as f:
                        pickle.dump(cache, f)
                    
                    if cache[cell][name] is None or len(cache[cell][name]) == 0:
                        failed_queries.append((cell, name, 'null response'))
                        print('Response failed for cell (null response):\n', cell)
                except:
                    failed_queries.append((cell, name, 'exception raised'))
                    print('Response failed for cell (exception raised):\n', cell)

    with open(savefile, 'wb') as f:
        pickle.dump(cache, f)
    
    with open(failed_queries_file, 'wb') as f:
        pickle.dump(failed_queries, f)

    if os.path.exists(tmpfile):
        os.remove(tmpfile)

    # build cache
    config = yaml.load(open('config.yaml', 'r'), Loader=yaml.SafeLoader)
    convert_pickle_file_to_cache(savefile, config)
