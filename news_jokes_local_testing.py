import requests
from bs4 import BeautifulSoup

import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.organization = os.getenv("ORG_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_joke(article):
  prompt = "Write a short joke about the following news article:"
  prompt += article
  prompt += "\n Joke:"
  completion = openai.ChatCompletion.create(
    model="gpt-4",
    temperature=0.3,
    max_tokens=200,
    messages=[
      {"role": "system", "content": "You are comedian"},
      {"role": "user", "content": prompt}
    ]
  )
  return completion.choices[0].message.content


def scrape_news():
  URL = "https://apnews.com/"
  page = requests.get(URL)

  soup = BeautifulSoup(page.content, "html.parser")
  results = soup.find("div", class_="TopStories")
  top_stories = results.find_all("a", {"data-key": "card-headline"})
  minor_stories = results.find_all("a", {"data-key": "related-story-link"})

  # I found a lot of duplicates, so I decided to eliminate those by 
  # converting the array to a set
  headline_elements = set(
    ["https://apnews.com" + headline['href'].strip() for headline in (top_stories + minor_stories)]
  )

  for headline_url in headline_elements:
    headline_page = requests.get(headline_url)
    article_soup = BeautifulSoup(headline_page.content, "html.parser")
    article_headline = article_soup.find("h1").text
    article_body = article_soup.find("div", class_="Article")
    article_text = article_body.find_all("p")
    short_article_text = ""
    for paragraph in article_text[0:10]:
      short_article_text += paragraph.text
    print(article_headline)
    print(short_article_text)
    print(headline_url)
    