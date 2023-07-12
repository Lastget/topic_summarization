# LLMs 
from langchain import PromptTemplate 
from langchain.llms import OpenAI 
from langchain.chat_models import ChatOpenAI 
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain 
from langchain.prompts import PromptTemplate 

# Scraping 
import requests 
from bs4 import BeautifulSoup 
from markdownify import markdownify as md

# Youtube
from langchain.document_loaders import YoutubeLoader

# Streamlit 
import streamlit as st 

# Env 
import os 
# openAI 
import openai
# API 
OPENAI_API_KEY = os.environ.get('OPEN_API_KEY') 


# load LLM funciton 
def load_llm():  
    llm = ChatOpenAI(temperature=.25, openai_api_key=OPENAI_API_KEY )  
    return llm 

# check openAI key 
def get_openai_api_key():
    input_text = st.text_input(label="OpenAI API Key (or set it as .env variable)",  placeholder="Ex: sk-2twmA8tfCb8un4...", key="openai_api_key_input")
    return input_text


# Pull data from web 
def pull_from_website(url):
    st.write("Getting webpages...")
    # Doing a try in case it doesn't work
    try:
        response = requests.get(url)
    except:
        # In case it doesn't work
        print ("error occured")
        return
    
    # Put your response in a beautiful soup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Get your text
    text = soup.get_text()

    # Convert your html to markdown. This reduces tokens and noise
    text = md(text)
     
    return text

# Pulling data from YouTube in text form
def get_video_transcripts(url):
    st.write("Getting YouTube Videos...")
    loader = YoutubeLoader.from_youtube_url(url, add_video_info=True)
    documents = loader.load()
    transcript = ' '.join([doc.page_content for doc in documents])
    return transcript


# Function to change long text about a topic into document 
def split_text(info):
    # make splitter 
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=50)

    # split info into docs 
    docs = text_splitter.create_documents([info])

    return docs 

# Define prompt 
response_types = {
    '1-Page Summary' : """
        Your goal is to generate a 1 page summary about them
        Please respond with a few short paragraphs that would prepare someone to talk to this person
    """
}


map_prompt = """You are a helpful AI bot that aids a user in research.
Below is information about a topic {topic_name}.
Information will include interview transcripts, and news about {topic_name}
Your goal is to sumemrize the topic {topic_name}
Use specifics from the research when possible

% START OF INFORMATION ABOUT {topic_name}:
{text}
% END OF INFORMATION ABOUT {topic_name}:

Please respond with a summary based on the topics above

YOUR RESPONSE:"""
map_prompt_template = PromptTemplate(template=map_prompt, input_variables=["text", "topic_name"])

combine_prompt = """
You are a helpful AI bot that aids a user in research.
You will be given a list of text about {topic_name}.

Please consolidate the text and return a summary

% INTERVIEW QUESTIONS
{text}
"""
combine_prompt_template = PromptTemplate(template=combine_prompt, input_variables=["text", "topic_name"])

# -----------------------------
# Start of Stramlit page 
st.set_page_config(page_title="Topic Summary App", page_icon=":robot:")

# Start top information 
st.header("Topic Summary App")


st.markdown("What to save time learning things from Youtube? This tool is meant to help you generate \
            an one page summary based on videos and webpages.\
            \n\nThis tool is powered by [BeautifulSoup](https://beautiful-soup-4.readthedocs.io/en/latest/#), [markdownify](https://pypi.org/project/markdownify/), [LangChain](https://langchain.com/), and [OpenAI](https://openai.com)" \
            )

# Collect information about the person you want to research
topic = st.text_input(label="Topic",  placeholder="Ex: Twitter Founders on Musk’s Tumultuous Takeover", key="topic")
youtube_videos = st.text_input(label="YouTube URLs (Use , to seperate videos)",  placeholder="Ex: https://www.youtube.com/watch?v=SKia5QUiGkE&t=16s", key="youtube_input")
webpages = st.text_input(label="Web Page URLs (Use , to seperate urls. Must include https://)",  placeholder="https://www.bbc.com/news/technology-63402338", key="webpage_input")


# Get URLs from a string
def parse_urls(urls_string):
    """Split the string by comma and strip leading/trailing whitespaces from each URL."""
    return [url.strip() for url in urls_string.split(',')]

# Get information from those URLs
def get_content_from_urls(urls, content_extractor):
    """Get contents from multiple urls using the provided content extractor function."""
    return "\n".join(content_extractor(url) for url in urls)

button_ind = st.button("*Generate Output*", type='secondary', help="Click to generate output based on information")

# Checking to see if the button_ind is true. If so, this means the button was clicked and we should process the links
if button_ind:
    if not (youtube_videos or webpages):
        st.warning('Please provide links to parse', icon="⚠️")
        st.stop()
    
    if not OPENAI_API_KEY:
        st.warning('Please insert OpenAI API Key. Instructions [here](https://help.openai.com/en/articles/4936850-where-do-i-find-my-secret-api-key)', icon="⚠️")
        st.stop() 
    
    if OPENAI_API_KEY == 'YourAPIKeyIfNotSet':
        # If the openai key isn't set in the env, put a text box out there
        OPENAI_API_KEY = get_openai_api_key()  

    # Go get your data
    video_text = get_content_from_urls(parse_urls(youtube_videos), get_video_transcripts) if youtube_videos else ""
    website_data = get_content_from_urls(parse_urls(webpages), pull_from_website) if webpages else ""

    topic_information = "\n".join([video_text, website_data])

    topic_information_docs = split_text(topic_information)    


    # Calls the function above
    llm = load_llm()

    chain = load_summarize_chain(llm,
                                 chain_type="map_reduce",
                                 map_prompt=map_prompt_template,
                                 combine_prompt=combine_prompt_template,
                                 # verbose=True
                                 )

      
    st.write("Sending to LLM...")

    #Pass our user information we gathered, the persons name and the response type from the radio button
    output = chain({"input_documents": topic_information_docs, # The seven docs that were created before
                    "topic_name": topic,
                    })

    st.markdown(f"#### Output:")
    st.write(output['output_text']) 


