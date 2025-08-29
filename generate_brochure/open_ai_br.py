from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
import requests
import json
from IPython.display import Markdown, display, update_display

# ----------- CONSTANTS -------------- #
MODEL = 'gpt-4o-mini'
headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

# ----------- ENVIRONMENT -------------- #
load_dotenv()


# ----------- MODEL -------------- #
openai = OpenAI()

# ----------- WEBSITE ------------ #

class Website:
    def __init__(self, url):
        self.url = url
        response = requests.get(url, headers=headers)
        self.body = response.content
        soup = BeautifulSoup(self.body, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.text = ''
        links = [link.get('href') for link in soup.find_all('a')]
        self.links = [link for link in links if link]

    def get_contents(self):
        return f"Web Title:\n{self.title}\nWebpage Contents:\n{self.text}\n\n"

hugging = Website("https://huggingface.co")
# print(ed.links)

# ----------- SYSTEM PROMPT ------------ #
system_prompt = ("You are provided with a list of links found on a webpage. "
                 "You are able to decide which of the links would be most relevant to include in a brochure about the company,"
                 "such as links to an About page, or a Company page, or Careers/jobs pages.\n")
# One-shot prompt -> one example
system_prompt += "You should respond in JSON as in this example:\n"
system_prompt += ('''
{
"links" : [
    {'type' : "about page", "url" : "https://full.url/goes/here/about"},
    {'type' : "careers page", "url" : "https://another.full.url/careers"}
    ]
}
''')
system_prompt += "\n And another example:\n"
system_prompt += ('''
{
"links" : [
    {'type' : "partner", "url" : "https://partner.url/another/company/url"},
    {'type' : "event 2025", "url" : "https://event.full.url/2025"}
    ]
}
''')
system_prompt += "\n And another example:\n"
system_prompt += ('''
{
"links" : [
    {'type' : "workshop", "url" : "https://workshop.url/sign/up/here"},
    {'type' : "instagram", "url" : "https://instagram.full.url/name"}
    ]
}
''')
# print(system_prompt)

# ----------- USER PROMPT ------------ #
user_prompt = f"Here is the list of the link on the website of {hugging.url}\n"
user_prompt += ("Decide which of there are relevant web links for a brochure about the company, "
                "respond with the full https URL in JSON format. Do not include Terms of Service, Privacy, email links. \n")
user_prompt += "Links (some might be relative links):\n"
user_prompt += "\n".join(hugging.links)

# print(user_prompt)

# ----------- FILTER AND CLASSIFY LINKS ------------ #
open_ai_response = openai.chat.completions.create(
    model=MODEL,
    messages=[
        { "role" : "system", "content" : system_prompt},
        { "role" : "user", "content" : user_prompt}
    ],
    response_format={"type" : "json_object"}
)

result = open_ai_response.choices[0].message.content
smart_links = json.loads(result)

print(smart_links)

# ----------- OTHER WEBSITES ------------ #
links_prompt = "Landing page:\n"
for link in smart_links["links"]:
    links_prompt += f"\n\n{link['type']}\n"
    links_prompt += Website(link['url']).get_contents()

# ----------- SYSTEM PROMPT ------------ #
system_prompt_with_smart_links = "You are an assistant that analyzes the contents of several relevant pages from a company website \
and creates a short brochure about the company for prospective customers, investors and recruits. Respond in markdown.\
Include details of company culture, customers and careers/jobs if you have the information."

# ----------- USER PROMPT ------------ #
user_prompt_with_smart_links = f"You are looking at the company {hugging.title}\n"
user_prompt_with_smart_links += ("Here are the contents of its landing page and other relevant pages; "
                                 "use this information to build a short brochure of the company in markdown.\n")
user_prompt_with_smart_links += links_prompt
user_prompt_with_smart_links = user_prompt_with_smart_links[:5_000]

# ----------- CREATE BROCHURE ------------ #
open_ai_response_bro = openai.chat.completions.create(
    model=MODEL,
    messages=[
        {'role' : 'system', 'content' : system_prompt_with_smart_links},
        {'role' : 'user', 'content' : user_prompt_with_smart_links}],
    stream=True
)

# Use streams to write
brochure = ""
for chunk in open_ai_response_bro:
    brochure += chunk.choices[0].delta.content or ''
    brochure = brochure.replace("```","").replace("markdown", "")

# ----------- SAVE BROCHURE ------------ #
with open("brochure.md", "w", encoding="utf-8") as chat_response:
    chat_response.write(brochure)

# ----------- SYSTEM PROMPT ------------ #
system_prompt_translate = "You are an translator, which translates from English to Romanian a company brochure. You need to keep the structure of the brochure."

# ----------- USER PROMPT ------------ #
user_prompt_translate = f"You are looking at the company {hugging.title}\n"
user_prompt_translate += "Here are the contents of its brochure, in markdown, which needs to be translated from English to Romanian in a professional manner.\n"
user_prompt_translate += brochure


# ----------- TRANSLATE BROCHURE ------------ #
open_ai_response_translate = openai.chat.completions.create(
    model=MODEL,
    messages=[
        {'role': 'system', 'content': system_prompt_translate},
        {'role': 'user', 'content': user_prompt_translate}
    ],
)

# ----------- SAVE BROCHURE ------------ #
brochure_tr = open_ai_response_translate.choices[0].message.content

with open("brochure_RO.md", "w", encoding="utf-8") as chat_response:
    chat_response.write(brochure_tr)