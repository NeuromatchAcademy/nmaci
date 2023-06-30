import os
import sys
import yaml
from jinja2 import Template
import traceback
import json
from bs4 import BeautifulSoup

REPO = os.environ.get("NMA_REPO", "course-content-dl")
ARG = sys.argv[1]

def main():
    with open('tutorials/materials.yml') as fh:
        materials = yaml.load(fh, Loader=yaml.FullLoader)

    # Make the dictionary that contains the chapters
    toc = {}
    for m in materials:
        if m['category'] not in toc.keys():
            toc[m['category']] = {'part': m['category'], 'chapters': []}
    # Add the project booklet
    toc['Project Booklet'] = {'part': 'Project Booklet', 'chapters': []}

    art_file_list = os.listdir('tutorials/Art/')

    for m in materials:
        directory = f"{m['day']}_{''.join(m['name'].split())}"

        # Make temporary chapter title file
        with open(f"tutorials/{directory}/chapter_title.md",
                  "w+") as title_file:
            title_page = f"# {m['name']}"
            art_file = [fname for fname in art_file_list if m['day'] in fname]
            if len(art_file) == 1:
                artist = art_file[0].split('-')[1].split('.')[0]
                artist = artist.replace('_', ' ')
                title_page += f"\n\n ````{{div}} full-width \n <img src='../Art/{art_file[0]}' alt='art relevant to chapter contents' width='100%'> \n```` \n\n*Artwork by {artist}*"
            title_file.write(title_page)

        chapter = {'file': f"tutorials/{directory}/chapter_title.md",
                   'title': f"{m['name']} ({m['day']})",
                   'sections': []}
        print(m['day'])
        part = m['category']
        directory = f"tutorials/{m['day']}_{''.join(m['name'].split())}"

        # Make list of notebook sections
        notebook_list = []
        notebook_list += [f"{directory}/{ARG}/{m['day']}_Tutorial{i + 1}.ipynb" for i in range(m['tutorials'])]
        notebook_list += [f"{directory}/{ARG}/{m['day']}_BonusLecture.ipynb"] if os.path.exists(f"{directory}/{m['day']}_BonusLecture.ipynb") else []

        # Add and process all notebooks
        for notebook_file_path in notebook_list:
            chapter['sections'].append({'file': notebook_file_path})
            pre_process_notebook(notebook_file_path)

        # Add further reading page
        # chapter['sections'].append({'file': f"{directory}/further_reading.md"})

        # Add chapter
        toc[part]['chapters'].append(chapter)

    # Project chapter -- under construction
    part = 'Project Booklet'
    toc[part]['chapters'].append({'file': 'projects/README.md', 'title': 'Introduction'})
    toc[part]['chapters'].append({'file': 'projects/docs/project_guidance.md'})

    with open('projects/project_materials.yml') as fh:
        project_materials = yaml.load(fh, Loader=yaml.FullLoader)

    # Add modelling steps
    category = 'modelingsteps'
    this_section = {'file': f'projects/{category}/intro.md', 'sections': []}
    for m in project_materials:
        if m['category'] == category:
            this_section['sections'].append({'file': f"projects/{category}/{m['link']}"})
            pre_process_notebook(f"projects/{category}/{m['link']}")
    toc[part]['chapters'].append(this_section)
    print(category)
    
    # Add project templates
    project_datasets = {'file': 'projects/docs/projects_overview.md', 'sections': []}
    # Loop over project categories
    for category in ['ComputerVision', 'ReinforcementLearning', 'NaturalLanguageProcessing', 'Neuroscience']:
        print(category)
        # Add each category section
        this_section = {'file': f'projects/{category}/README.md',
                        'sections': [{'file': f'projects/{category}/slides.md'},
                                     {'file': f'projects/{category}/ideas_and_datasets.md'}]}
        for m in project_materials:
            if m['category'] == category:
                # Add and process all notebooks
                try:
                    this_section['sections'].append({'file': f"projects/{category}/{m['link']}"})
                    pre_process_notebook(f"projects/{category}/{m['link']}")
                except:
                    pass
        project_datasets['sections'].append(this_section)
    toc[part]['chapters'].append(project_datasets)

    # Add models and datasets
    toc[part]['chapters'].append({'file': 'projects/docs/datasets_and_models.md'})
    # Turn toc into list
    toc_list = [{'file': 'tutorials/intro.ipynb'}]
    if os.path.exists("tutorials/intro.ipynb"):
        pre_process_notebook('tutorials/intro.ipynb')

    # TA training file
    if ARG == "instructor":
        chapter = {'chapters': [{'file': 'tatraining/TA_Training_DL.ipynb'}]}
        pre_process_notebook('tatraining/TA_Training_DL.ipynb')
        toc_list += [chapter]

    # Schedule chapter
    chapter = {'chapters': [{'file': 'tutorials/Schedule/schedule_intro.md',
                             'sections': [{'file': 'tutorials/Schedule/daily_schedules.md'},
                                          {'file': 'tutorials/Schedule/shared_calendars.md'},
                                          {'file': 'tutorials/Schedule/timezone_widget.md'}
                                         ]}]}
    toc_list += [chapter]

    # Technical help chapter
    chapter = {'chapters': [{'file': 'tutorials/TechnicalHelp/tech_intro.md', 
                             'sections': [{'file': 'tutorials/TechnicalHelp/Jupyterbook.md',
                                           'sections': [{'file': 'tutorials/TechnicalHelp/Tutorial_colab.md'},
                                                        {'file': 'tutorials/TechnicalHelp/Tutorial_kaggle.md'}
                                                       ]
                                          },
                                          {'file': 'tutorials/TechnicalHelp/Discord.md'}
                                         ]}]}
    toc_list += [chapter]

    # Links and Policy file
    chapter = {'chapters': [{'file': 'tutorials/TechnicalHelp/Links_Policy.md'}]}
    toc_list += [chapter]

    # Pre-reqs file
    chapter = {'chapters': [{'file': 'prereqs/DeepLearning.md'}]}
    toc_list += [chapter]

    for key in toc.keys():
        # Add wrap-up if it exists
        wrapup_name = f'tutorials/Module_WrapUps/{key.replace(" ", "")}.ipynb'
        if os.path.exists(wrapup_name):
            toc[key]['chapters'].append({'file': wrapup_name})

        toc_list.append(toc[key])

    with open('book/_toc.yml', 'w') as fh:
        yaml.dump(toc_list, fh)


def pre_process_notebook(file_path):

    with open(file_path, encoding="utf-8") as read_notebook:
        content = json.load(read_notebook)
    pre_processed_content = open_in_colab_new_tab(content)
    pre_processed_content = change_video_widths(pre_processed_content)
    pre_processed_content = link_hidden_cells(pre_processed_content)
    with open(file_path, "w", encoding="utf-8") as write_notebook:
        json.dump(pre_processed_content, write_notebook, indent=1, ensure_ascii=False)


def open_in_colab_new_tab(content):
    cells = content['cells']
    parsed_html = BeautifulSoup(cells[0]['source'][0], "html.parser")
    for anchor in parsed_html.findAll('a'):
        # Open in new tab
        anchor['target'] = '_blank'
    cells[0]['source'][0] = str(parsed_html)
    return content

def link_hidden_cells(content):
    cells = content['cells']
    updated_cells = cells.copy()

    i_updated_cell = 0
    for i_cell, cell in enumerate(cells):
        updated_cell = updated_cells[i_updated_cell]
        if "source" not in cell:
            continue
        source = cell['source'][0]

        if source.startswith("#") and cell['cell_type'] == 'markdown':
            header_level = source.count('#')
        elif source.startswith("---") and cell['cell_type'] == 'markdown':
            if len(cell['source']) > 1 and cell['source'][1].startswith("#") and cell['cell_type'] == 'markdown':
                header_level = cell['source'][1].count('#')

        if '@title' in source or '@markdown' in source:
            if 'metadata' not in cell:
                updated_cell['metadata'] = {}
            if 'tags' not in cell['metadata']:
                updated_cell['metadata']['tags'] = []

            # Check if cell is video one
            if 'YouTubeVideo' in ''.join(cell['source']) or 'IFrame' in ''.join(cell['source']):
                if "remove-input" not in cell['metadata']['tags']:
                    updated_cell['metadata']['tags'].append("remove-input")
            else:
                if "hide-input" not in cell['metadata']['tags']:
                    updated_cell['metadata']['tags'].append("hide-input")

            # If header is lost, create one in markdown
            if '@title' in source:

                if source.split('@title')[1] != '':
                    header_cell = {
                        'cell_type': 'markdown',
                        'metadata': {},
                        'source': ['#'*(header_level + 1) + ' ' + source.split('@title')[1]]}
                    updated_cells.insert(i_updated_cell, header_cell)
                    i_updated_cell += 1

            strings_with_markdown = [(i, string) for i, string in enumerate(cell['source']) if '@markdown' in string]
            if len(strings_with_markdown) == 1:
                i = strings_with_markdown[0][0]
                if cell['source'][i].split('@markdown')[1] != '':
                    header_cell = {
                        'cell_type': 'markdown',
                        'metadata': {},
                        'source': [cell['source'][i].split('@markdown')[1]]}
                    updated_cells.insert(i_updated_cell, header_cell)
                    i_updated_cell += 1

        i_updated_cell += 1

    content['cells'] = updated_cells
    return content

def change_video_widths(content):

    for i, cell in enumerate(content['cells']):
        if 'YouTubeVideo' in ''.join(cell['source']):

            for ind in range(len(cell['source'])):
                # Change sizes
                cell['source'][ind] = cell['source'][ind].replace('854', '730')
                cell['source'][ind] = cell['source'][ind].replace('480', '410')

        # Put slides in ipywidget so they don't overlap margin
        if '# @title Tutorial slides\n' in cell['source'] or '# @title Slides\n' in cell['source'] or '## Slides' in content['cells'][i-1]['source']:
            for line in cell['source']:
                if line.startswith('link_id'):
                    slide_link = line.split('"')[1]
            download_link = f"https://osf.io/download/{slide_link}/"
            render_link = f"https://mfr.ca-1.osf.io/render?url=https://osf.io/{slide_link}/?direct%26mode=render%26action=download%26mode=render"
            cell['source'] = ['# @markdown\n',
                              'from IPython.display import IFrame\n',
                              'from ipywidgets import widgets\n',
                              'out = widgets.Output()\n',
                              'with out:\n',
                              f'    print(f"If you want to download the slides: {download_link}")\n',
                              f'    display(IFrame(src=f"{render_link}", width=730, height=410))\n',
                              'display(out)']
    return content

if __name__ == '__main__':
    main()
