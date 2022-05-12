import os
from re import template
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert import HTMLExporter
from traitlets.config import Config

c = Config()
c.HTMLExporter.preprocessors = ['nbconvert.preprocessors.ExtractOutputPreprocessor']

def write_html(source, target):
    # read source notebook
    with open(source) as f:
        nb = nbformat.read(f, as_version=4)

    # execute notebook
    ep = ExecutePreprocessor(timeout=-1, kernel_name='python3')
    ep.preprocess(nb)

    # export to html
    html_exporter = HTMLExporter(config=c, template="lab")
    #html_exporter.exclude_input = True
    html_data, resources = html_exporter.from_notebook_node(nb)


    os.mkdir(target)
    # write to output file
    with open(target + "/index.html", "w", encoding="utf8") as f:
        f.write(html_data)

    for output in resources["outputs"]:
        with open(target + "/" + output, "wb") as f:
            f.write(resources["outputs"][output])


write_html("age-group-plots.ipynb", "public/age-group-plots")
write_html("global-trends.ipynb", "public/global-trends")
write_html("opnames.ipynb", "public/age-opnames")
write_html("sewage-trends.ipynb", "public/sewage-trends")



## create the new exporter using the custom config
#html_exporter_with_figs = HTMLExporter(config=c)
#html_exporter_with_figs.preprocessors
#
#(_, resources)          = html_exporter.from_notebook_node(jake_notebook)
#(_, resources_with_fig) = html_exporter_with_figs.from_notebook_node(jake_notebook)
#
#print("resources without figures:")
#print(sorted(resources.keys()))
#
#print("\nresources with extracted figures (notice that there's one more field called 'outputs'):")
#print(sorted(resources_with_fig.keys()))
#
#print("\nthe actual figures are:")
#print(sorted(resources_with_fig['outputs'].keys()))

