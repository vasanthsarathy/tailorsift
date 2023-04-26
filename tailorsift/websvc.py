import os
import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import json
import random


import os
import openai

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.YETI, dbc.icons.FONT_AWESOME])
server = app.server #nee

LINE_BREAK = dbc.Row(html.Br())
HLINE = dbc.Row(dbc.Col(html.Hr(), width={'size':6,'offset':1}))


notes_history = ""

# Top heading and logo
heading = [html.H2("🎸 TailorSIFT: Acronym Writer"),html.H5("Helping you stitch together acronyms that sound great")]

api_key_group = dbc.InputGroup([dbc.InputGroupText("OpenAI API Key:"),
                                dbc.Input("api-key", value=""),
                                dbc.Button("unlock", id="unlock-button", n_clicks=0)],
                               className="mb-3")


HEADER_ROW = dbc.Row([dbc.Col(heading, width={'size':3, 'offset':1}), dbc.Col([LINE_BREAK, api_key_group], width={'size':3, 'offset':0})])

# input row
keywords_group = dbc.InputGroup([dbc.InputGroupText("Keywords:"),
                                 dbc.Input(id="keywords", placeholder="")],
                                className="mb-3")


keywords_heading = html.H5("Keywords/Topics (Required)")
keywords_instruction = html.P("Provide a comma separated list of relevant keywords or phrases")
keywords = dbc.Textarea(id="keywords", style={"width": "100%", "height": "100px"})

INPUT_ROW = dbc.Row(dbc.Col([keywords_heading, keywords_instruction, keywords], width={'size':6, 'offset':1}))

GENERATE_BUTTON = dbc.Button("🧐 GENERATE", id="generate-button", color="success", className="me-1", disabled=True)

price_alert = html.P(id="price")

generate_price = dbc.Row([dbc.Col(GENERATE_BUTTON), dbc.Col(price_alert)])

# Output rows

acronym_group = dbc.InputGroup([dbc.InputGroupText("Acronym:"),
                                 dbc.Input(id="acronym", placeholder=""),
                                dbc.Button("↻", id="refresh-acronym",color="success")],
                                className="mb-3")

expansion_group = dbc.InputGroup([dbc.InputGroupText("Expansion:"),
                                 dbc.Textarea(id="expansion", placeholder=""),
                                  dbc.Button("↻", id="refresh-expansion",color="success")],
                                className="mb-3")

COPY_TO_NOTEPAD_BUTTON = dbc.Button("📋 Add to Notepad", id="copy-button", color="primary", className="me-1")


examples_heading = html.H5("Training Examples (Optional)")
examples_instruction = html.P("Provide an acronym and expansion for each example. Separate examples with blank line")
examples = dbc.Textarea(id="examples",
                        style={"width": "100%", "height": "300px"},
                        value="keywords: sequential-decision making, planning, reinforcement learning\nacronym: SPOTTER\nexpansion: Synthesizing Planning Operators Through Targeted Exploration and Reinforcement")



notes_heading = html.H5("Notepad")
notes_instruction = html.P("Use this space as a scratch pad and to collect promising acronyms and expansions")
notes = dbc.Textarea(id="notes",style={"width": "100%", "height": "570px"})
save_button = dbc.Button("💾 Save", id="save-button", color="primary", className="me-1")


clip_button = dcc.Clipboard(
        target_id="notes",
        title="copy",
        style={
            "display": "inline-block",
            "fontSize": 20,
            "verticalAlign": "top",
        })


output_column = dbc.Col([generate_price, LINE_BREAK, acronym_group, LINE_BREAK, expansion_group, COPY_TO_NOTEPAD_BUTTON, LINE_BREAK, examples_heading, examples_instruction, examples], width={'size':3, 'offset':1})
notes_column = dbc.Col([notes_heading, notes_instruction, notes, LINE_BREAK, clip_button],width={'size':3, 'offset':0})

OUTPUT_ROW = dbc.Row([output_column, notes_column])

# DASH APP LAYOUT
app.layout = html.Div([LINE_BREAK,
                       HEADER_ROW,
                       LINE_BREAK,
                       HLINE,
                       INPUT_ROW,
                       LINE_BREAK,
                       OUTPUT_ROW
                       ])


############# CALLBACKS ############################


@app.callback(Output('generate-button', 'disabled'),
              [Input('unlock-button', 'n_clicks'),
               State('api-key', 'value')])
def unlock(n, api_key):
    if n:
        print("clicked unlock button")
        if api_key:
            return False
        else:
            return True
    else:
        raise dash.exceptions.PreventUpdate


@app.callback([Output('acronym', 'value'),
               Output('expansion', 'value'),
               Output('price', 'children')],
              [Input('generate-button', 'n_clicks'),
               Input('refresh-acronym', 'n_clicks'),
               Input('refresh-expansion', 'n_clicks'),
               State('keywords', 'value'),
               State('examples', 'value'),
               State('acronym', 'value'),
               State('expansion', 'value'),
               State('api-key', 'value')])
def generate_clear(ngen, nacro, nexp, keywords, examples, acronym, expansion, api_key):
    if ngen or nacro or nexp:
        button_id = dash.ctx.triggered_id
        if button_id == "refresh-acronym":
            acronym = ""
        if button_id == "refresh-expansion":
            expansion = ""
        acronym, expansion, price = create(keywords, examples, acronym, expansion, api_key)

        return acronym, expansion, [price]
    else:
        raise dash.exceptions.PreventUpdate

@app.callback(Output('notes', 'value'),
              [Input('copy-button', 'n_clicks'),
               State('keywords', 'value'),
               State('acronym', 'value'),
               State('expansion', 'value'),
               State('notes', 'value')])
def notepad(n, keywords, acronym, expansion, current_notes):
    if n:
        if current_notes:
            notes = current_notes + f"keywords: {keywords}\nacronym:{acronym}\nexpansion:{expansion}\n\n"
        else:
            notes =f"keywords: {keywords}\nacronym:{acronym}\nexpansion:{expansion}\n\n"
        return notes
    else:
        raise dash.exceptions.PreventUpdate


########### MAIN LOGIC ############################

def create(keywords, examples, acronym, expansion, api_key):
    prompt, is_full_prompt = construct_prompt(keywords, examples, acronym, expansion)
    print("=== PROMPT ===")
    print(prompt)
    print("=== Running GPT3 ===")
    completion, price = get_completion(prompt, api_key)
    if is_full_prompt:
        acronym = completion.split("\n")[0]
        expansion = completion.split("\n")[1]
        if "expansion:" in expansion:
            expansion = expansion.replace("expansion:","")
    else:
        expansion= expansion + completion
    return acronym, expansion, price

def construct_prompt(keywords, examples, acronym, expansion):
    if not acronym:
        task_instruction = "Produce a word that is an acronym and its expansion for a grouping of ideas/keywords in any order. The word should represent something smart. The expansion should be grammatical and read like a phrase."
        prompt=f"{task_instruction}\n{examples}\nideas: {keywords}\nacronym:"
        return prompt, True
    elif not expansion:
        task_instruction = "Generate an expansion for an acronym that is semantically connected to the ideas/keywords. The expansion should be grammatical and read like a phrase."
        prompt=f"{task_instruction}\n{examples}\nideas: {keywords}\nword: {acronym}\nexpansion:"
        return prompt, False
    else:
        return ""


def get_completion(prompt, api_key):
    model="text-davinci-002"
    openai.api_key = api_key

    response_dict = openai.Completion.create(
        model=model,
        prompt=prompt,
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=2,
        presence_penalty=0
    )

    completion = response_dict['choices'][0]['text']
    if "davinci" in model:
        rate = 0.02
    elif "curie" in model:
        rate = 0.002
    elif "babbage" in model:
        rate = 0.0005
    elif "ada" in model:
        rate = 0.0004
    else:
        rate = 1000
    price = '{0:.3f}'.format(int(response_dict['usage']['total_tokens']) * rate/1000.0)
    print(completion)
    print("Rate: ",rate)
    return completion, "$"+str(price)


def main():
    server.run(debug=True, port=8010)

if __name__ == "__main__":
    app.run_server(debug=True)
