import plotly.express as px
import plotly as pl 
from sentence_transformers import SentenceTransformer
import pandas as pd
from annoy import AnnoyIndex
from bertopic import BERTopic
import numpy as np 
import plotly.express as px
import plotly.graph_objects as go
import anthropic
import pandas as pd
import requests
import html
import csv
import re
import pandas as pd
from bs4 import BeautifulSoup
import os
import os
from dotenv import load_dotenv
import pandas as pd
import openai
import csv

load_dotenv()

model_path = os.path.join("backend", "JE_model")
data_path=os.path.join("sources", "data.csv")
data_us_path=os.path.join("sources", "data_us.csv")
resume_path=os.path.join("sources", "resume.csv")

def load_bertopic():
    bertopic_model=BERTopic.load(r'../backend/JE_model')
    return bertopic_model
model=load_bertopic()



def extract_sunburst_data(node, path=[], labels=None, parents=None, ids=None, values=None, index=0):
    if labels is None:
        labels, parents, ids, values = [], [], [], []

    label = node['label']
    # Use index for uniqueness in the ID
    id = "/".join(path + [f"{label}_{index}"])  
    parent_id = "/".join(path) if path else ""
    
    labels.append(label)
    ids.append(id)
    parents.append(parent_id)
    values.append(1)  # Or any other value representing this node
    
    node["id"] = id  # Add the unique ID to the node

    new_path = path + [f"{label}_{index}"]
    for idx, child in enumerate(node.get('children', [])):
        # Pass idx as index for each child
        extract_sunburst_data(child, new_path, labels, parents, ids, values, idx)
    
    return labels, parents, ids, values

alldata = pd.read_csv(data_path)
data=pd.read_csv(data_us_path)
def get_html_content(link) :
    if link in alldata['url'].values:
    
        content = alldata.loc[alldata['url'] == link, 'contenu']

    return  content
def get_content(link) :
    if link in data['url'].values:
    
        content = data.loc[data['url'] == link, 'titre_contenu']

    return  content

def llm1claude(content):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Client(api_key=api_key)
    prompt = f"""Here is a textual content for which I would like you to identify relevant themes to improve the internal linking of similar documents:
    {content}
    By analyzing this content, can you propose a list of 4 to 6 expressions that describe the overall content.

    You should respond only with a bulleted list that contains only expressions, without any other descriptive or explanatory text.”
            """

    response = client.messages.create(
        model="claude-2.1",
        temperature=0.6,
        max_tokens=1500,
        system=".",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    text = response.content[0].text.strip()
    return text
def get_documents_by_topic(dataframe, topic_number):
    filtered_data = dataframe.loc[dataframe['Topic'] == topic_number]
    return filtered_data['Document']
def get_dataframe(cluster_value):
       
    data = pd.read_csv(resume_path)

    docs = data["resume"].tolist()
  
    df = model.get_document_info(docs)    
    documents= get_documents_by_topic(df,cluster_value)
    resultats = []
    for resume in documents:
                url_correspondante = data.loc[data['resume'].str.strip() == resume.strip(), 'url']

                link = url_correspondante.iloc[0]
                index=resume.find("Summary complete")
                resume = resume[:index] if index != -1 else resume
             
                resultats.append({"url": link, "resume": resume})
    df_resultats = pd.DataFrame(resultats)
    return df_resultats

def get_all_candidats(topics): 
    

    data = pd.read_csv(resume_path)

    docs = data["resume"].tolist()
  
    df = model.get_document_info(docs)

    cluster_data = {}
    cluster_options = []
    links=[]
    for topic in topics:
            
            cluster_name = model.get_topic_info(topic[0]).CustomName.to_string(index=False).strip()
    
            cluster_option = f"{cluster_name} "
            cluster_options.append(cluster_option)

            documents = get_documents_by_topic(df, topic[0])
            resultats = []
            for resume in documents:
                url_correspondante = data.loc[data['resume'].str.strip() == resume.strip(), 'url']

                link = url_correspondante.iloc[0]
                index=resume.find("Résumé terminé")
                resume = resume[:index] if index != -1 else resume
                links.append(link)
                resultats.append({"URL": link, "Résumé": resume})

            cluster_data[cluster_option] =resultats


    return links
def scraper_resume(url):
    data=pd.read_csv(resume_path)
    if url in data['url'].values :
        content=data.loc[data['url']==url,'resume'].iloc[0]
        return content
    
def llm(content,links):

    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Client(api_key=api_key)
    prompt= f"""You are an expert in internal linking of websites. Your task is to analyze a specific content and select the most relevant links from a provided list of candidates, in order to create optimal internal links to improve the structure and navigation of the site.
    Content to analyze:
    {content}
    Candidate links:
    {links}
    Instructions:
    1. Carefully analyze the provided content and identify the key themes and concepts discussed.
    2. Examine each candidate link and evaluate its relevance to the analyzed content. Note: there are links that are very different, ignore them!
    3. Select up to 6 links that are the most relevant and can be coherently linked to the content.
    4. Provide a brief explanation for each selected link, justifying why it is relevant and how it can improve the navigation and user experience of the site.
    5. Present your response in the form of a list, indicating the selected links and your explanations.
    6. Keep in mind that the goal is to create a coherent and relevant internal linking structure that helps users easily navigate the site and discover quality related content"""
    response = client.messages.create(
        model="claude-3-opus-20240229",
        temperature=1,
        max_tokens=3000,
        system=".",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    text = response.content[0].text.strip()
    return text

def llm3v2(contenu, liens):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Client(api_key=api_key)
    prompt = f'''
    ###TASK###
    I will provide you with several elements:
    - a source article with existing urls
    - a list of links with a summary of the corresponding target article for each link
    Use the provided elements to add the links to the source article where it is relevant and in a natural way for readers. Use a link anchor that seems relevant to you in relation to the linked target article.

    Proceed in steps:
    1. the text contains already some links , leave them as they are 
    2. Analyze the article and the provided links to understand what each article is about
    3. Determine the best location for each link within the source article (Integrate the links naturally into the text paragraphs)
    4. Determine the link anchor to use for each link (The anchor should be short, descriptive and encourage the user to click. Do not use generic anchors like "Learn more".)
    5. Integrate the links using HTML syntax: <a href="url"style="color: red;"><strong>link anchor</strong></a> (Modify existing content if necessary to naturally integrate the link) 
    6. Output the full content in HTML format with the integrated links    
    Here is the content of the source article:
    """
    {contenu}
    """
    Here is the list of links with a summary of the corresponding target article for each link:
    """
    {liens}
    """
    ###TASK###
    '''
    

    response = client.messages.create(
        model="claude-3-opus-20240229",
        temperature=0.3,
        max_tokens=4000,
        system=".",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    text = response.content[0].text.strip()
    return text

def extract_links(text):
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    links = re.findall(pattern, text)
    
    return links    
