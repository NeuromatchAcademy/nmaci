import yaml
import sys
from bs4 import BeautifulSoup

ARG = sys.argv[1]

def main():
    with open('tutorials/materials.yml') as fh:
        materials = yaml.load(fh, Loader=yaml.FullLoader)

    html_directory = 'book/_build/html/'

    # Loop over days
    for m in materials:
        name = f"{m['day']}_{''.join(m['name'].split())}"

        # Loop over tutorials
        for i in range(m['tutorials']):

            # Load html file
            notebook_file_path = f"{html_directory}/tutorials/{name}/{ARG}/{m['day']}_Tutorial{i + 1}.html"
            with open(notebook_file_path, 'r') as f:
                contents = f.read()
            parsed_html = BeautifulSoup(contents, features="html.parser")

            # Find code output divs
            mydivs = parsed_html.find_all("div", {"class": "cell_output docutils container"})

            # Remove div if it has an error
            for div in mydivs:
                if 'NotImplementedError' in str(div) or 'NameError' in str(div):
                    div.decompose()

            # Put solution figures in center (to fix layout issues) 
            for img in parsed_html.find_all('img', alt= True):
                if img['alt'] == 'Solution hint':
                    img['align'] = 'center'
                    img['class'] = 'align-center'
                    
            # save out html
            with open(notebook_file_path, 'w') as f:
                f.write(str(parsed_html))


if __name__ == '__main__':
    main()
